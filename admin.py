from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "datavibesgh-admin-secret-2026"

ADMIN_PASSWORD = "k3ri0sx9@Kro4xs"  

def init_db():
    conn = sqlite3.connect("datavibes.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY,
                        telegram_id INTEGER,
                        username TEXT,
                        service TEXT,
                        details TEXT,
                        amount REAL,
                        status TEXT DEFAULT 'pending',
                        photo_url TEXT,
                        note TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )""")
    conn.commit()
    conn.close()

init_db()

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Data Vibes GH Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .countdown { font-weight: bold; color: #d32f2f; }
        .card { box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark">
        <div class="container"><span class="navbar-brand">Data Vibes GH Admin Panel</span></div>
    </nav>
    <div class="container mt-4">
        {{ content | safe }}
    </div>
</body>
</html>
'''

# (Login, dashboard, products, issues, logout routes remain the same as previous version – I kept them short for brevity)

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if not session.get('logged_in'):
        return redirect('/login')
    conn = sqlite3.connect("datavibes.db")
    cursor = conn.cursor()
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        status = request.form.get('status')
        note = request.form.get('note')
        cursor.execute("UPDATE orders SET status = ?, note = ? WHERE id = ?", (status, note, order_id))
        conn.commit()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    html = "<h3>All Orders</h3><table class='table table-striped'><tr><th>ID</th><th>Service</th><th>Details</th><th>Status</th><th>Countdown</th><th>Note</th><th>Action</th></tr>"
    for row in rows:
        countdown = ""
        if "AFA" in str(row[3]).upper():
            try:
                created = datetime.datetime.fromisoformat(row[9].replace("Z", "+00:00"))
                deadline = created + datetime.timedelta(hours=24)
                remaining = deadline - datetime.datetime.now()
                if remaining.total_seconds() > 0:
                    countdown = f"<span class='countdown'>{int(remaining.total_seconds()//3600)}h {int((remaining.total_seconds()%3600)//60)}m left</span>"
                else:
                    countdown = "<span class='text-danger'>Expired</span>"
            except:
                countdown = "-"
        html += f"""
        <tr>
            <td>{row[0]}</td>
            <td>{row[3]}</td>
            <td>{row[4]}</td>
            <td><span class="badge bg-{'success' if row[6]=='completed' else 'warning'}">{row[6]}</span></td>
            <td>{countdown}</td>
            <td>{row[8] or '-'}</td>
            <td>
                <form method="post" style="display:inline;">
                    <input type="hidden" name="order_id" value="{row[0]}">
                    <select name="status" class="form-select form-select-sm">
                        <option value="pending">Pending</option>
                        <option value="paid">Paid</option>
                        <option value="processing">Processing</option>
                        <option value="completed">Completed</option>
                        <option value="failed">Failed</option>
                    </select>
                    <input type="text" name="note" placeholder="Note" class="form-control form-control-sm" value="{row[8] or ''}">
                    <button type="submit" class="btn btn-sm btn-primary">Update</button>
                </form>
            </td>
        </tr>"""
    html += "</table>"
    return render_template_string(HTML, content=html)

# Products, Issues, Logout routes (same as previous version)

if __name__ == '__main__':
    print("🚀 Modern Admin Panel running on http://127.0.0.1:5001")
    print("Login password:", ADMIN_PASSWORD)
    app.run(port=5001)
