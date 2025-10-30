from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# DB CONNECTION

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# HOME

@app.route("/")
def home():
    return render_template("index.html")

# REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, password, role, verified) VALUES (?, ?, ?, ?)",
            (username, password, role, 0),
        )
        conn.commit()
        conn.close()

        flash("Registration submitted ✅ Please wait for admin approval.", "info")
        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        conn.close()

        if user:
            stored_password = user["password"]

            if stored_password == password or check_password_hash(stored_password, password):
                if user["verified"] == 0:
                    flash("Your account is awaiting admin approval.", "warning")
                    return redirect(url_for("login"))

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]

                flash("Login successful 🎉", "success")
                return redirect(url_for("dashboard"))

        flash("Invalid username or password ❌", "danger")

    return render_template("login.html")

# LOGOUT

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out 👋", "info")
    return render_template("logout.html")


# DASHBOARD

@app.route("/dashboard")
def dashboard():
    if "user_id" in session:
        return render_template(
            "dashboard.html", role=session["role"], username=session["username"]
        )
    return redirect(url_for("login"))

@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    filter_status = request.args.get("filter", "all")

    conn = get_db_connection()
    query = """
        SELECT donations.*, 
               u1.username AS donor_name, 
               u2.username AS ngo_name
        FROM donations
        JOIN users u1 ON donations.donor_id = u1.id
        LEFT JOIN users u2 ON donations.claimed_by = u2.id
    """

    if filter_status != "all":
        query += " WHERE donations.status = ?"
        donations = conn.execute(query, (filter_status,)).fetchall()
    else:
        donations = conn.execute(query).fetchall()
    conn.close()

    return render_template("admin_dashboard.html", donations=donations, current_filter=filter_status)

# DONATE FOOD

@app.route("/donate", methods=["GET", "POST"])
def donate():
    if "user_id" not in session or session["role"] != "Donor":
        flash("Only donors can donate food.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        food = request.form["food"]
        quantity = request.form["quantity"]
        location = request.form["location"]
        expiry_date = request.form.get("expiry_date")

        conn = get_db_connection()
        conn.execute(
            """INSERT INTO donations (donor_id, food, quantity, location, expiry_date, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session["user_id"], food, quantity, location, expiry_date, "Available"),
        )
        conn.commit()
        conn.close()

        flash("Donation added successfully ✅", "success")
        return redirect(url_for("dashboard"))

    return render_template("donate.html")


# VIEW DONATIONS (NGO)
@app.route("/donations")
def donations():
    conn = get_db_connection()
    all_donations = conn.execute("""
        SELECT d.id, d.food, d.quantity, d.location, d.expiry_date, d.status,
               d.created_at,
               u1.username AS donor_name,
               u2.username AS ngo_name
        FROM donations d
        JOIN users u1 ON d.donor_id = u1.id
        LEFT JOIN users u2 ON d.claimed_by = u2.id
    """).fetchall()
    conn.close()
    return render_template("view_donations.html", donations=all_donations)

# CLAIM DONATION (NGO)

@app.route("/claim/<int:donation_id>", methods=["POST"])
def claim_donation(donation_id):
    if "user_id" not in session or session.get("role") != "NGO":
        flash("Only NGOs can claim donations.", "danger")
        return redirect(url_for("donations"))

    conn = get_db_connection()
    conn.execute(
        "UPDATE donations SET status='Claimed', claimed_by=? WHERE id=? AND status='Available'",
        (session["user_id"], donation_id),
    )
    conn.commit()
    conn.close()

    flash("Donation claimed successfully 🎉", "success")
    return redirect(url_for("donations"))

# COMPLETE DONATION (NGO after pickup)

@app.route("/complete/<int:donation_id>", methods=["POST"])
def complete_donation(donation_id):
    if "user_id" in session and session["role"] == "NGO":
        conn = get_db_connection()
        conn.execute(
            "UPDATE donations SET status=? WHERE id=? AND claimed_by=?",
            ("Completed", donation_id, session["user_id"]),
        )
        conn.commit()
        conn.close()
        flash("Donation marked as completed 🎉", "info")
        return redirect(url_for("claims"))
    flash("Unauthorized action", "danger")
    return redirect(url_for("home"))

@app.route("/mark_completed/<int:donation_id>", methods=["POST"])
def mark_completed(donation_id):
    if session.get("role") != "Admin":
        flash("Unauthorized!", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    conn.execute("UPDATE donations SET status = 'Completed' WHERE id = ?", (donation_id,))
    conn.commit()
    conn.close()

    flash("Donation marked as Completed ✅", "success")
    return redirect(url_for("admin_dashboard"))

# DONATION HISTORY (Donor)

@app.route("/history")
def history():
    if "user_id" in session and session["role"] == "Donor":
        conn = get_db_connection()
        donations = conn.execute(
            "SELECT * FROM donations WHERE donor_id=?", (session["user_id"],)
        ).fetchall()
        conn.close()
        return render_template("history.html", donations=donations)
    flash("Unauthorized", "danger")
    return redirect(url_for("home"))


# CLAIMS (NGO)

@app.route("/claims")
def claims():
    if "user_id" in session and session["role"] == "NGO":
        conn = get_db_connection()
        donations = conn.execute(
            """SELECT d.*, u.username as donor_name
               FROM donations d
               JOIN users u ON d.donor_id = u.id
               WHERE d.claimed_by=?""",
            (session["user_id"],),
        ).fetchall()
        conn.close()
        return render_template("claims.html", donations=donations)
    flash("Unauthorized", "danger")
    return redirect(url_for("home"))

# ADMIN: VERIFY USERS

@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    if "user_id" in session and session["role"] == "Admin":
        conn = get_db_connection()
        if request.method == "POST":
            user_id = request.form["user_id"]
            action = request.form["action"]
            if action == "approve":
                conn.execute("UPDATE users SET verified=1 WHERE id=?", (user_id,))
            elif action == "reject":
                conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            flash(f"User {action}d ✅", "success")

        users = conn.execute("SELECT * FROM users WHERE verified=0").fetchall()
        conn.close()
        return render_template("verify_users.html", users=users)
    flash("Unauthorized", "danger")
    return redirect(url_for("home"))

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)
