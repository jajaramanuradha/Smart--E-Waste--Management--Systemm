from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart-ewaste-project"
DATABASE = "ewaste.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS waste_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL, category TEXT NOT NULL, condition TEXT NOT NULL,
        quantity INTEGER NOT NULL, recommendation TEXT NOT NULL, created_at TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS collection_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT NOT NULL, address TEXT NOT NULL,
        item_type TEXT NOT NULL, preferred_date TEXT NOT NULL,
        status TEXT DEFAULT 'Pending', created_at TEXT NOT NULL)""")
    conn.commit(); conn.close()

def get_recommendation(condition):
    if condition == "Working": return "Reuse, donate, or sell the device."
    if condition == "Repairable": return "Repair the device and reuse it."
    return "Send the device to an authorized e-waste recycler."

@app.route("/")
def index(): return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    conn = get_db()
    total_items = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM waste_items").fetchone()[0]
    total_categories = conn.execute("SELECT COUNT(DISTINCT category) FROM waste_items").fetchone()[0]
    total_requests = conn.execute("SELECT COUNT(*) FROM collection_requests").fetchone()[0]
    damaged_items = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM waste_items WHERE condition='Damaged'").fetchone()[0]
    recent = conn.execute("SELECT * FROM waste_items ORDER BY id DESC LIMIT 8").fetchall()
    conn.close()
    return render_template("dashboard.html", total_items=total_items, total_categories=total_categories,
                           total_requests=total_requests, damaged_items=damaged_items, recent=recent)

@app.route("/add-waste", methods=["GET","POST"])
def add_waste():
    if request.method == "POST":
        item_name=request.form["item_name"].strip(); category=request.form["category"]
        condition=request.form["condition"]; quantity=int(request.form["quantity"])
        conn=get_db(); conn.execute("""INSERT INTO waste_items
            (item_name,category,condition,quantity,recommendation,created_at) VALUES (?,?,?,?,?,?)""",
            (item_name,category,condition,quantity,get_recommendation(condition),datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close(); flash("E-waste item added successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("add-waste.html")

@app.route("/collection", methods=["GET","POST"])
def collection():
    if request.method == "POST":
        data=(request.form["name"].strip(),request.form["phone"].strip(),request.form["address"].strip(),
              request.form["item_type"],request.form["preferred_date"],datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        conn=get_db(); conn.execute("""INSERT INTO collection_requests
            (name,phone,address,item_type,preferred_date,created_at) VALUES (?,?,?,?,?,?)""",data)
        conn.commit(); conn.close(); flash("Collection request submitted successfully!", "success")
        return redirect(url_for("collection"))
    conn=get_db(); requests=conn.execute("SELECT * FROM collection_requests ORDER BY id DESC").fetchall(); conn.close()
    return render_template("collection.html", requests=requests)

@app.route("/recycling")
def recycling(): return render_template("recycling.html")
@app.route("/about")
def about(): return render_template("about.html")

@app.route("/api/stats")
def api_stats():
    conn=get_db(); data={
        "total_items":conn.execute("SELECT COALESCE(SUM(quantity),0) FROM waste_items").fetchone()[0],
        "total_requests":conn.execute("SELECT COUNT(*) FROM collection_requests").fetchone()[0],
        "damaged_items":conn.execute("SELECT COALESCE(SUM(quantity),0) FROM waste_items WHERE condition='Damaged'").fetchone()[0]}
    conn.close(); return jsonify(data)

if __name__ == "__main__":
    init_db(); app.run(debug=True)
