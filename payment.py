import os
import sqlite3
import stripe
from flask import Blueprint, render_template, redirect, request, session, url_for, jsonify
from dotenv import load_dotenv

load_dotenv()

payment_bp = Blueprint("payment", __name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DATABASE = "app.db"


PACKAGES = {
    "basic": {
        "name": "Basic Plan",
        "price": 499,  # $4.99
        "currency": "usd",
        "messages": 300
    },
    "premium": {
        "name": "Premium Plan",
        "price": 999,  # $9.99
        "currency": "usd",
        "messages": 1000
    }
}


def init_payment_table():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            package_name TEXT NOT NULL,
            messages_limit INTEGER NOT NULL,
            payment_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@payment_bp.route("/packages")
def packages():
    if "user_id" not in session:
        return redirect(url_for("home"))

    return render_template("packages.html", packages=PACKAGES)


@payment_bp.route("/create-checkout-session/<package_key>", methods=["POST"])
def create_checkout_session(package_key):
    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    if package_key not in PACKAGES:
        return jsonify({"error": "Invalid package"}), 400

    selected_package = PACKAGES[package_key]
    domain_url = os.getenv("DOMAIN_URL", "http://127.0.0.1:5000")

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=session.get("user_email"),
        line_items=[
            {
                "price_data": {
                    "currency": selected_package["currency"],
                    "product_data": {
                        "name": selected_package["name"],
                    },
                    "unit_amount": selected_package["price"],
                },
                "quantity": 1,
            }
        ],
        metadata={
            "email": session.get("user_email"),
            "package_key": package_key,
            "messages": selected_package["messages"]
        },
        success_url=domain_url + "/payment-success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=domain_url + "/payment-cancel",
    )

    return redirect(checkout_session.url, code=303)


@payment_bp.route("/payment-success")
def payment_success():
    session_id = request.args.get("session_id")

    if not session_id:
        return "Payment session missing."

    checkout_session = stripe.checkout.Session.retrieve(session_id)

    if checkout_session.payment_status == "paid":
        email = checkout_session.metadata.get("email")
        package_key = checkout_session.metadata.get("package_key")
        messages = int(checkout_session.metadata.get("messages"))

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_packages 
            (email, package_name, messages_limit, payment_status)
            VALUES (?, ?, ?, ?)
        """, (email, package_key, messages, "paid"))
        conn.commit()
        conn.close()

        return render_template("payment_success.html", package_name=package_key)

    return "Payment not completed."


@payment_bp.route("/payment-cancel")
def payment_cancel():
    return render_template("payment_cancel.html")