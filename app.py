import os
import sqlite3

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from ai_partner import AIPartner
from memory import init_memory_table, get_user_memory, save_memory
from payment import payment_bp, init_payment_table
from partner import partner_bp, init_partner_table, get_user_partner

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_this_secret_key")

app.register_blueprint(payment_bp)
app.register_blueprint(partner_bp)

DATABASE = "app.db"
def is_singlish(text):
    sinhala_words = ["moko", "oya", "kohomada", "hari", "mata", "enne", "mokak", "dawas"]
    return any(word in text.lower() for word in sinhala_words)

def save_memory_if_needed(email, message):
    text = message.lower()

    triggers = [
        "my name is",
        "i like",
        "i love",
        "my favorite",
        "call me",
        "i feel",
        "i am",
        "i'm",
        "i work",
        "my job",
        "my goal",
        "i want"
    ]

    if any(trigger in text for trigger in triggers):
        save_memory(email, message)


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hashed_password)
            )
            conn.commit()
            conn.close()

            flash("Account created successfully. Please login.")
            return redirect(url_for('home'))

        except sqlite3.IntegrityError:
            flash("Email already exists")
            return redirect(url_for('signup'))

    return render_template('signup.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email'].strip()
    password = request.form['password']

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        session['user_email'] = email
        return redirect(url_for('partner.partner_setup'))

    flash("Invalid email or password")
    return redirect(url_for('home'))

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    saved_partner = get_user_partner(session["user_email"])

    if saved_partner:
        partner_name, partner_gender, partner_personality, partner_avatar, partner_description = saved_partner
    else:
        partner_name = "Luna"
        partner_avatar = "/static/default-avatar.png"
        partner_personality = "sweet and caring"
        partner_description = ""

    greeting = f"Hi, I’m {partner_name} 😊 I’m {partner_personality}. I’m happy to chat with you."

    return render_template(
        'index.html',
        partner_name=partner_name,
        partner_avatar=partner_avatar,
        greeting=greeting
    )

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({"reply": "Please login first."}), 401

    data = request.get_json()
    user_message = data.get("message", "").strip()

    original_user_message = user_message

    if is_singlish(user_message):
        ai_user_message = f"Reply in Sinhala Unicode only: {user_message}"
    else:
        ai_user_message = f"Reply in English only: {user_message}"

    if not user_message:
        return jsonify({"reply": "Please type a message."})

    if "chat_history" not in session:
        session["chat_history"] = []

    chat_history = session["chat_history"]

    memory_text = get_user_memory(session["user_email"])

    saved_partner = get_user_partner(session["user_email"])

    if saved_partner:
        partner_name, partner_gender, partner_personality, partner_avatar, partner_description = saved_partner
    else:
        partner_name, partner_gender, partner_personality, partner_description = "Luna", "female", "sweet and caring", ""

    dynamic_partner = AIPartner(partner_name)

    ai_reply = dynamic_partner.reply(
        ai_user_message,
        chat_history=chat_history,
        memory_text=f"""
Partner name: {partner_name}
Partner gender: {partner_gender}
Partner personality: {partner_personality}

User memory:
{memory_text}
"""
    )

    chat_history.append({"role": "user", "content": original_user_message})
    chat_history.append({"role": "assistant", "content": ai_reply})

    session["chat_history"] = chat_history[-20:]

    save_memory_if_needed(session["user_email"], user_message)

    return jsonify({"reply": ai_reply})



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


init_db()
init_memory_table()
init_payment_table()
init_partner_table()


if __name__ == '__main__':
    app.run(debug=True)