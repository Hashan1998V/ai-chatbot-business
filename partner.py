import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session
from generate_avatar import generate_partner_avatar

partner_bp = Blueprint("partner", __name__)

DATABASE = "app.db"


def init_partner_table():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT UNIQUE NOT NULL,
            partner_name TEXT NOT NULL,
            partner_gender TEXT NOT NULL,
            partner_personality TEXT NOT NULL,
            partner_avatar TEXT,
            partner_description TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_user_partner(email):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        SELECT partner_name, partner_gender, partner_personality, partner_avatar, partner_description
        FROM partners
        WHERE user_email = ?
    """, (email,))

    partner = cur.fetchone()
    conn.close()
    return partner


@partner_bp.route("/partner", methods=["GET", "POST"])
def partner_setup():
    if "user_id" not in session:
        return redirect(url_for("home"))

    email = session["user_email"]

    if request.method == "POST":
        partner_name = request.form["partner_name"]
        partner_gender = request.form["partner_gender"]
        partner_personality = request.form["partner_personality"]
        partner_avatar = request.form.get("partner_avatar", "")
        partner_description = request.form.get("partner_description", "")

        body_type = request.form.get("body_type", "")
        hair_style = request.form.get("hair_style", "")
        fashion_style = request.form.get("fashion_style", "")
        partner_description = request.form.get("partner_description", "")

        image_prompt = f"""
        Create a realistic AI partner avatar.
        Gender: {partner_gender}
        Body type: {body_type}
        Hair style: {hair_style}
        Fashion style: {fashion_style}
        Extra description: {partner_description}
        Safe, friendly, non-explicit portrait style.
        """

        partner_avatar = generate_partner_avatar(image_prompt)

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO partners
            (user_email, partner_name, partner_gender, partner_personality, partner_avatar, partner_description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email, partner_name, partner_gender, partner_personality, partner_avatar, partner_description))

        conn.commit()
        conn.close()

        return redirect(url_for("chat"))

    return render_template("partner.html")