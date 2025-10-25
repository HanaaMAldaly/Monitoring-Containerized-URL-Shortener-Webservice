from flask import Flask, request, redirect, render_template, url_for, flash
import sqlite3, os, string, random, datetime

APP_BASE = os.getenv("BASE_URL", "http://localhost:5000")
DB_PATH = os.getenv("DB_PATH", "shorty.db")
SHORT_LEN = 6
ALPHABET = string.ascii_letters + string.digits

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        target TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def gen_code(length=SHORT_LEN):
    return ''.join(random.choice(ALPHABET) for _ in range(length))

def make_unique_code():
    conn = get_db()
    for _ in range(10):
        c = gen_code()
        r = conn.execute("SELECT 1 FROM links WHERE code = ?", (c,)).fetchone()
        if not r:
            conn.close()
            return c
    # fallback: extend length
    while True:
        c = gen_code(length=SHORT_LEN+2)
        r = conn.execute("SELECT 1 FROM links WHERE code = ?", (c,)).fetchone()
        if not r:
            conn.close()
            return c

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        target = request.form.get("target", "").strip()
        custom = request.form.get("custom", "").strip()
        if not target:
            flash("Please enter a valid URL", "error")
            return render_template("index.html")
        conn = get_db()
        if custom:
            # check availability
            r = conn.execute("SELECT 1 FROM links WHERE code = ?", (custom,)).fetchone()
            if r:
                flash("Custom code already in use", "error")
                conn.close()
                return render_template("index.html")
            code = custom
        else:
            code = make_unique_code()
        conn.execute("INSERT INTO links (code, target, created_at) VALUES (?, ?, ?)",
                     (code, target, datetime.datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        short_url = f"{APP_BASE.rstrip('/')}/{code}"
        return render_template("info.html", short=short_url, target=target)
    return render_template("index.html")

@app.route("/<code>")
def redirect_short(code):
    conn = get_db()
    r = conn.execute("SELECT target FROM links WHERE code = ?", (code,)).fetchone()
    conn.close()
    if not r:
        return ("Not Found", 404)
    return redirect(r["target"], code=302)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
