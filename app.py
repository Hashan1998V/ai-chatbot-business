from memory import init_memory_table, get_user_memory, save_memory
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from ai_partner import AIPartner
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from payment import payment_bp, init_payment_table
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
import os
load_dotenv(override=True)
print("KEY FOUND:", os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.register_blueprint(payment_bp)
partner = AIPartner("Luna")
app.secret_key = "your_secret_key_here"
DATABASE = "app.db"


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
            cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
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
        return redirect(url_for('chat'))
    else:
        flash("Invalid email or password")
        return redirect(url_for('home'))


@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({"reply": "Please login first."}), 401

    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please type a message."})

    if "chat_history" not in session:
        session["chat_history"] = []

    chat_history = session["chat_history"]

    memory_text = ""
    if "user_email" in session:
        memory_text = get_user_memory(session["user_email"])

    ai_reply = partner.reply(user_message, chat_history=chat_history, memory_text=memory_text)

    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": ai_reply})

    session["chat_history"] = chat_history[-20:]

    save_memory_if_needed(session["user_email"], user_message)

    return jsonify({"reply": ai_reply})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    init_db()
    init_memory_table()
    init_payment_table()
    app.run(debug=True)