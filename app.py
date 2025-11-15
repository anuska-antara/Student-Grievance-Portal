from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_connection

app = Flask(__name__)
app.secret_key = "secret_key"

# Helper values for templates and role checks
from flask import g

@app.context_processor
def inject_user_state():
    is_logged = "user_id" in session
    role_id = session.get("role_id")   # correct session key
    is_admin = False

    # Admin = role_id 2; Super Admin = role_id 3
    if role_id in (2, 3):
        is_admin = True

    return {
        "is_logged_in": is_logged,
        "is_admin": is_admin,
        "current_user_name": session.get("name"),
        "current_user_email": session.get("email"),
    }

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Users WHERE email=%s AND password_hash=%s", (email, password))
        user = cur.fetchone()

        if user:
            # Fetch role name
            cur.execute("SELECT role_name FROM Roles WHERE role_id=%s", (user["role_id"],))
            role_name = cur.fetchone()["role_name"]

            # Save essential session data
            session["user_id"] = user["user_id"]
            session["role_id"] = user["role_id"]
            session["role"] = role_name         # <-- ADD THIS
            session["name"] = user["first_name"]

            cur.close()
            conn.close()

            # Redirect by role
            if user["role_id"] == 1:
                return redirect(url_for("student_dashboard"))
            elif user["role_id"] == 2:
                return redirect(url_for("admin_dashboard"))
            elif user["role_id"] == 3:
                return redirect(url_for("superadmin_dashboard"))

        else:
            cur.close()
            conn.close()
            flash("Invalid credentials!", "error")

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student")
def student_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("CALL sp_get_student_grievances(%s)", (session["user_id"],))
    grievances = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("student_dashboard.html", grievances=grievances, name=session["name"])


# Add grievance form
@app.route("/new_grievance", methods=["GET", "POST"])
def new_grievance():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        dept_id = request.form["department_id"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Grievances (title, description, student_id, department_id) VALUES (%s, %s, %s, %s)",
                    (title, description, session["user_id"], dept_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Grievance submitted successfully!", "success")
        return redirect(url_for("student_dashboard"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT department_id, department_name FROM Departments")
    departments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("new_grievance.html", departments=departments)


# ---------------- STUDENT — VIEW GRIEVANCE DETAILS ----------------
@app.route("/grievance/<int:gid>")
def grievance_detail(gid):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM Grievances WHERE grievance_id = %s", (gid,))
    grievance = cur.fetchone()

    cur.close()
    conn.close()

    if not grievance:
        return "Grievance not found", 404

    return render_template("grievance_detail.html", grievance=grievance, name=session["name"])


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    # fetch admin's department
    cur.execute("SELECT department_id FROM Admins WHERE user_id=%s", (session["user_id"],))
    dept = cur.fetchone()
    cur.execute("CALL sp_get_grievances_by_department(%s)", (dept["department_id"],))
    grievances = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin_dashboard.html", grievances=grievances, name=session["name"])


# Update grievance status
@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):
    new_status = request.form["status"]
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SET @current_user_id=%s", (session["user_id"],))
        cur.execute("UPDATE Grievances SET status=%s WHERE grievance_id=%s", (new_status, id))
        conn.commit()
        flash("Status updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    except Exception as e:
        conn.rollback()
        print("Error updating grievance:", e)
        flash(f"Error updating grievance: {e}", "error")
        return redirect(url_for("admin_dashboard"))
    finally:
        cur.close()
        conn.close()


# ---------------- SUPER ADMIN DASHBOARD ----------------
@app.route("/superadmin")
def superadmin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT department_id, department_name FROM Departments")
    departments = cur.fetchall()
    stats = []
    for d in departments:
        cur.execute("SELECT fn_get_open_grievance_count(%s)", (d["department_id"],))
        open_count = list(cur.fetchone().values())[0]
        cur.execute("SELECT fn_get_avg_resolution_time(%s)", (d["department_id"],))
        avg_time = list(cur.fetchone().values())[0]
        stats.append({
            "name": d["department_name"],
            "open_count": open_count,
            "avg_time": avg_time
        })
    cur.close()
    conn.close()
    return render_template("superadmin_dashboard.html", stats=stats, name=session["name"])


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # 1. Get basic user info
    cur.execute("""
        SELECT user_id, first_name, last_name, email, role_id
        FROM Users
        WHERE user_id = %s
    """, (user_id,))
    user = cur.fetchone()

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("login"))

    full_name = f"{user['first_name']} {user['last_name']}"

    # 2. Determine role
    cur.execute("SELECT role_name FROM Roles WHERE role_id = %s", (user["role_id"],))
    role_name = cur.fetchone()["role_name"]

    profile_data = {
        "name": full_name,
        "email": user["email"],
        "role": role_name
    }

    # 3. If Student → fetch USN and program
    if role_name == "Student":
        cur.execute("""
            SELECT usn, program_of_study
            FROM Students
            WHERE user_id = %s
        """, (user_id,))
        s = cur.fetchone()

        profile_data["id_label"] = "USN"
        profile_data["id_value"] = s["usn"]
        profile_data["department"] = s["program_of_study"]

    # 4. If Admin or Super Admin → fetch staff_id and department
    elif role_name in ("Admin", "Super Admin"):
        cur.execute("""
            SELECT staff_id, department_id
            FROM Admins
            WHERE user_id = %s
        """, (user_id,))
        a = cur.fetchone()

        profile_data["id_label"] = "Staff ID"
        profile_data["id_value"] = a["staff_id"]

        cur.execute("SELECT department_name FROM Departments WHERE department_id = %s",
                    (a["department_id"],))
        dept = cur.fetchone()

        profile_data["department"] = dept["department_name"]

    cur.close()
    conn.close()

    return render_template("profile.html", profile=profile_data)


# ---------------- ACTIVITY LOG ----------------
@app.route("/activity_log")
def activity_log():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch student's grievances
    cur.execute("""
        SELECT grievance_id, title, status, submission_date, resolved_at
        FROM Grievances
        WHERE student_id = %s
        ORDER BY submission_date DESC
    """, (session["user_id"],))
    grievances = cur.fetchall()

    # Build timeline from ActivityLog (your DB already has this)
    cur.execute("""
        SELECT log_timestamp, action_description
        FROM ActivityLog
        WHERE user_id = %s
        ORDER BY log_timestamp DESC
    """, (session["user_id"],))
    logs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("activity_log.html", grievances=grievances, logs=logs)


# ---------------- REPORTS (admin-only) ----------------
@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("login"))

    role_id = session.get("role_id")
    is_admin = role_id in (2, 3)   # Admin or Super Admin

    if not is_admin:
        flash("Access denied: reports are for admins only.", "error")
        return redirect(url_for("student_dashboard"))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Total grievances count
    cur.execute("SELECT COUNT(*) AS total FROM Grievances")
    total = cur.fetchone()["total"]

    # Count by status
    cur.execute("SELECT status, COUNT(*) AS cnt FROM Grievances GROUP BY status")
    by_status = cur.fetchall()

    # Count by department WITH department names
    cur.execute("""
        SELECT d.department_name, COUNT(*) AS cnt
        FROM Grievances g
        JOIN Departments d ON g.department_id = d.department_id
        GROUP BY g.department_id
    """)
    by_dept = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("reports.html", total=total, by_status=by_status, by_dept=by_dept)


if __name__ == "__main__":
    app.run(debug=True)