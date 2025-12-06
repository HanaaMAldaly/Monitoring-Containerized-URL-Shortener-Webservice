import os
import io
import time
import base64
import qrcode
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, send_file, Response, g
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- DB config from env ---
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "shorty")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password")

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port="5432"
    )

# --- Prometheus metrics ---
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['endpoint'])
URL_CREATED = Counter('urls_created_total', 'Total URLs created')
QR_GENERATED = Counter('qr_generated_total', 'Total QR codes generated')
REDIRECTS = Counter('redirect_total', 'Total redirects', ['status'])

# --- request timing hooks ---
@app.before_request
def start_timer():
    g._start_time = time.time()

@app.after_request
def record_metrics(response):
    try:
        latency = time.time() - g._start_time
    except Exception:
        latency = 0
    endpoint = request.path
    status = response.status_code if hasattr(response, 'status_code') else 200
    REQUEST_COUNT.labels(request.method, endpoint, str(status)).inc()
    REQUEST_LATENCY.labels(endpoint).observe(latency)
    return response

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# --- init DB (creates table if doesn't exist) ---
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visits INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Try to initialize DB at startup (if DB not ready, ignore - container orchestration handles depends_on)
try:
    init_db()
except Exception as e:
    app.logger.warning("Could not initialize DB at startup: %s", e)

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    qr_code = None

    if request.method == 'POST':
        original_url = request.form.get('url')
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
            URL_CREATED.inc()

        cur.close()
        conn.close()

        short_url = request.host_url + short_code

        # QR generation
        img = qrcode.QRCode(version=1, box_size=8, border=2)
        img.add_data(short_url)
        img.make(fit=True)
        qr_img = img.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")
        QR_GENERATED.inc()

    return render_template('index.html', short_url=short_url, qr_code=qr_code)

@app.route('/<short_code>')
def redirect_short_url(short_code):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT original_url FROM urls WHERE short_code = %s;", (short_code,))
        url_data = cur.fetchone()

        if url_data is None:
            REDIRECTS.labels('fail').inc()
            cur.close()
            conn.close()
            return "URL not found", 404

        cur.execute("UPDATE urls SET visits = visits + 1 WHERE short_code = %s;", (short_code,))
        conn.commit()
        cur.close()
        conn.close()

        REDIRECTS.labels('success').inc()
        return redirect(url_data["original_url"])
    except Exception as e:
        REDIRECTS.labels('fail').inc()
        return f"Internal Server Error: {e}", 500

@app.route('/download_qr/<short_code>')
def download_qr(short_code):
    short_url = request.host_url + short_code

    img = qrcode.QRCode(version=1, box_size=8, border=2)
    img.add_data(short_url)
    img.make(fit=True)
    qr_img = img.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    QR_GENERATED.inc()

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
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_RUN_PORT", 5000)))
 
