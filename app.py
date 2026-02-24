from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "ram_agencies_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")


def get_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT,
            address TEXT,
            product_id INTEGER,
            quantity INTEGER,
            status TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    """)

    # Insert products if empty
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            ("Parle-G 50g", 5),
            ("Parle-G 100g", 10),
            ("Parle-G 200g", 20),
            ("Parle-G Gold 100g", 15),
            ("Parle-G Gold 200g", 30),
            ("Monaco 50g", 10),
            ("Monaco 200g", 40),
            ("Krackjack 50g", 10),
            ("Krackjack 100g", 30),
        ]
        conn.executemany(
            "INSERT INTO products (name, price) VALUES (?, ?)", products
        )

    # Insert admin user
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', 'admin123', 'admin')
        )

    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# ---------------- HOME ----------------
@app.route('/')
def index():
    conn = get_connection()
    products = conn.execute(
        "SELECT * FROM products ORDER BY name ASC"
    ).fetchall()
    conn.close()

    success = request.args.get("success")
    return render_template("index.html", products=products, success=success)


# ---------------- PLACE ORDER ----------------
@app.route('/place_order', methods=['POST'])
def place_order():
    shop_name = request.form['shop_name']
    address = request.form['address']
    product_ids = request.form.getlist("product_id[]")
    quantities = request.form.getlist("quantity[]")

    conn = get_connection()

    for i in range(len(product_ids)):
        if product_ids[i] and quantities[i]:
            conn.execute(
                "INSERT INTO orders (shop_name, address, product_id, quantity, status) VALUES (?, ?, ?, ?, ?)",
                (shop_name, address, product_ids[i], quantities[i], "Pending")
            )

    conn.commit()
    conn.close()

    return redirect('/?success=1')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['role'] = user['role']
            session['user'] = user['username']
            return redirect('/admin')
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if 'role' not in session:
        return redirect('/login')

    conn = get_connection()
    orders = conn.execute("""
        SELECT 
            orders.id,
            orders.shop_name,
            orders.address,
            products.name,
            orders.quantity,
            orders.status
        FROM orders
        JOIN products ON orders.product_id = products.id
        ORDER BY orders.id DESC
    """).fetchall()
    conn.close()

    return render_template("admin.html", orders=orders)


# ---------------- MARK DELIVERED ----------------
@app.route('/deliver/<int:order_id>')
def deliver(order_id):
    if 'role' not in session:
        return redirect('/login')

    conn = get_connection()
    conn.execute(
        "UPDATE orders SET status='Delivered' WHERE id=?",
        (order_id,)
    )
    conn.commit()
    conn.close()

    return redirect('/admin')


if __name__ == "__main__":

    app.run(debug=True)

    app.run(debug=True)

