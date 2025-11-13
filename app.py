import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for
from psycopg2.extras import RealDictCursor
import qrcode
import io
import base64

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "shorty")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password")

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "shorty"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "db"),
        port="5432"
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visits INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    qr_code = None

    if request.method == 'POST':
        original_url = request.form['url']
        short_code = os.urandom(3).hex()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT short_code FROM urls WHERE original_url = %s;", (original_url,))
        existing = cur.fetchone()

        if existing:
            short_code = existing[0]
        else:
            cur.execute(
                "INSERT INTO urls (original_url, short_code) VALUES (%s, %s);",
                (original_url, short_code)
            )
            conn.commit()

        cur.close()
        conn.close()

        short_url = request.host_url + short_code

        img = qrcode.QRCode(
            version=1,
            box_size=8,
            border=2
        )
        img.add_data(short_url)
        img.make(fit=True)
        qr_img = img.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template('index.html', short_url=short_url, qr_code=qr_code)


@app.route('/<short_code>')
def redirect_short_url(short_code):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM urls WHERE short_code = %s;", (short_code,))
        url_data = cur.fetchone()

        if url_data is None:
            cur.close()
            conn.close()
            return "URL not found", 404

        cur.execute("UPDATE urls SET visits = visits + 1 WHERE short_code = %s;", (short_code,))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_data["original_url"])
    except Exception as e:
        return f"Internal Server Error: {e}", 500



from flask import send_file

@app.route('/download_qr/<short_code>')
def download_qr(short_code):
    """Generate and return a QR code PNG for the given short code."""
    short_url = request.host_url + short_code

    img = qrcode.QRCode(
        version=1,
        box_size=8,
        border=2
    )
    img.add_data(short_url)
    img.make(fit=True)
    qr_img = img.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{short_code}_qrcode.png"
    )


@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT original_url, short_code, visits, created_at FROM urls ORDER BY visits DESC;")
    urls = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', urls=urls)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

