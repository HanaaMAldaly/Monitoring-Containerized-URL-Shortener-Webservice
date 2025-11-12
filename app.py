from flask import Flask, render_template, request
import sqlite3
import string
import random
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__)

DB_NAME = "database.db"

# -------- Database Setup --------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original TEXT NOT NULL,
            short TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def generate_short_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def get_short_url(original_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT short FROM urls WHERE original = ?", (original_url,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_url(original_url, short_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO urls (original, short) VALUES (?, ?)", (original_url, short_code))
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def home():
    short_url = None
    qr_data = None

    if request.method == "POST":
        url = request.form.get("url").strip()
        if url:
            existing = get_short_url(url)
            if existing:
                short_code = existing
            else:
                short_code = generate_short_code()
                save_url(url, short_code)

            short_url = request.host_url + short_code

            # Generate QR code
            qr_img = qrcode.make(short_url)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            qr_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render_template("index.html", short_url=short_url, qr_data=qr_data)

@app.route("/<short_code>")
def redirect_to_url(short_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT original FROM urls WHERE short = ?", (short_code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        from flask import redirect
        return redirect(row[0])
    return "<h3>URL not found!</h3>"

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
