import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory, Response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "polytechnic-college-library-secret-2026")

db_url = os.environ.get("DATABASE_URL", "sqlite:///library.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

YEARS = {1: "First Year", 2: "Second Year", 3: "Third Year"}

# ─── Database Models ──────────────────────────────────────────────────────────

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(150), default="Polytechnic College Library")
    hero_title = db.Column(db.String(200), default="Polytechnic College Library")
    hero_subtitle = db.Column(db.String(300), default="Your centralized hub for textbooks, notes, question papers, and study materials")
    announcement = db.Column(db.String(300), default="Semester exams start next month — download updated branch notes and question papers!")
    show_announcement = db.Column(db.Boolean, default=True)
    footer_text = db.Column(db.String(250), default="Polytechnic College Library — Your Academic Resource Hub")
    admin_username = db.Column(db.String(80), default="admin")
    admin_password = db.Column(db.String(120), default=os.environ.get("ADMIN_PASSWORD", "admin2026"))

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(60), default="bi-building")
    color = db.Column(db.String(30), default="#4f46e5")

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    branch = db.Column(db.String(80), default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(80), default="Lecture Notes")
    description = db.Column(db.Text, default="")
    filename = db.Column(db.String(255), default="")
    size_mb = db.Column(db.Float, default=4.4)
    downloads = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DownloadLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship("Student", backref="download_logs")
    material = db.relationship("Material", backref="download_logs")

# ─── Initial Seeding ──────────────────────────────────────────────────────────

def seed_initial_data():
    if not SiteSettings.query.first():
        db.session.add(SiteSettings())

    if Department.query.count() == 0:
        default_depts = [
            Department(slug="civil", name="Civil Engineering", icon="bi-building", color="#e67e22"),
            Department(slug="mechanical", name="Mechanical Engineering", icon="bi-gear-wide-connected", color="#e74c3c"),
            Department(slug="it", name="Information Technology", icon="bi-laptop", color="#2ecc71"),
            Department(slug="electrical", name="Electrical Engineering", icon="bi-lightning-charge-fill", color="#f59e0b"),
            Department(slug="electronics", name="Electronics & Telecomm.", icon="bi-cpu-fill", color="#06b6d4"),
            Department(slug="chemical", name="Chemical Engineering", icon="bi-droplet-half", color="#d946ef"),
            Department(slug="cst", name="Computer Science (CST)", icon="bi-terminal-fill", color="#6366f1"),
            Department(slug="automobile", name="Automobile Engineering", icon="bi-speedometer2", color="#14b8a6"),
        ]
        db.session.add_all(default_depts)

    if Material.query.count() == 0:
        samples = [
            Material(title="Python Notes", subject="Python", year=2, department="it", category="Lecture Notes",
                     description="Complete Python programming guide from fundamentals to OOP, automation, and web backends.", size_mb=4.4, downloads=38),
            Material(title="Electrical Machines & Power Systems", subject="Electrical Machines", year=2, department="electrical", category="Lecture Notes",
                     description="DC generators, DC motors, single-phase and 3-phase transformers, induction motors, and switchgear protection.", size_mb=5.4, downloads=29),
            Material(title="Chemical Process Calculations & Unit Ops", subject="Chemical Process Tech", year=2, department="chemical", category="Textbook",
                     description="Stoichiometry, material and energy balances, fluid flow, heat exchangers, and distillation operations.", size_mb=6.8, downloads=21),
            Material(title="Microcontrollers & Embedded C Lab Manual", subject="Microcontrollers (8051)", year=3, department="electronics", category="Lab Manual",
                     description="8051 architecture, timer/interrupt programming, sensor interfacing, and VLSI basics.", size_mb=4.1, downloads=25),
            Material(title="Engineering Mechanics & Strength of Materials", subject="Engineering Mechanics", year=1, department="civil", category="Textbook",
                     description="Force systems, equilibrium, friction, centroid, moment of inertia, and simple stress-strain analysis.", size_mb=6.2, downloads=33),
            Material(title="Thermal Engineering & IC Engines Notes", subject="Thermodynamics", year=2, department="mechanical", category="Lecture Notes",
                     description="Laws of thermodynamics, Otto/Diesel cycles, steam boilers, turbines, and air compressors.", size_mb=5.1, downloads=19),
        ]
        db.session.add_all(samples)

    db.session.commit()

with app.app_context():
    db.create_all()
    seed_initial_data()

# ─── Helpers & Decorators ─────────────────────────────────────────────────────

def get_settings():
    return SiteSettings.query.first()

def get_departments_dict():
    return {d.slug: {"id": d.id, "name": d.name, "icon": d.icon, "color": d.color} for d in Department.query.all()}

def get_current_student():
    sid = session.get("student_id")
    return Student.query.get(sid) if sid else None

@app.context_processor
def inject_globals():
    return {
        "site_settings": get_settings(),
        "departments": get_departments_dict(),
        "years": YEARS,
        "current_student": get_current_student(),
        "is_admin": session.get("is_admin", False),
    }

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in with Administrator credentials to access the Admin Panel.", "warning")
            return redirect(url_for("login", role="admin", next=request.path))
        return f(*args, **kwargs)
    return decorated

def build_dashboard_context(materials_query, active_filter=None):
    all_materials = Material.query.all()
    depts = get_departments_dict()
    year_counts = {yr: sum(1 for m in all_materials if m.year == yr) for yr in YEARS}
    dept_counts = {dk: sum(1 for m in all_materials if m.department == dk) for dk in depts}
    return {
        "materials": materials_query,
        "total_count": len(all_materials),
        "total_downloads": sum(m.downloads for m in all_materials),
        "year_counts": year_counts,
        "dept_counts": dept_counts,
        "active_filter": active_filter,
    }

# ─── Public & Multi-Page Student Routes (No Login Required to Browse/View) ────

@app.route("/")
def index():
    materials = Material.query.order_by(Material.created_at.desc()).all()
    return render_template("index.html", **build_dashboard_context(materials))

@app.route("/year/<int:year_id>")
def filter_by_year(year_id):
    materials = Material.query.filter_by(year=year_id).order_by(Material.created_at.desc()).all()
    label = YEARS.get(year_id, f"Year {year_id}")
    return render_template("index.html", **build_dashboard_context(materials, active_filter=label))

@app.route("/department/<dept_key>")
def filter_by_department(dept_key):
    materials = Material.query.filter_by(department=dept_key).order_by(Material.created_at.desc()).all()
    depts = get_departments_dict()
    label = depts.get(dept_key, {}).get("name", dept_key.title())
    return render_template("index.html", **build_dashboard_context(materials, active_filter=label))

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if q:
        like_q = f"%{q}%"
        materials = Material.query.filter(
            (Material.title.ilike(like_q)) |
            (Material.subject.ilike(like_q)) |
            (Material.description.ilike(like_q))
        ).order_by(Material.created_at.desc()).all()
    else:
        materials = Material.query.order_by(Material.created_at.desc()).all()
    return render_template("index.html", **build_dashboard_context(materials, active_filter=f'Search: "{q}"' if q else None))

@app.route("/view/<int:mat_id>")
def view_material(mat_id):
    """Students can view/read notes freely WITHOUT logging in."""
    mat = Material.query.get_or_404(mat_id)
    if mat.filename and os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], mat.filename)):
        return send_from_directory(app.config["UPLOAD_FOLDER"], mat.filename)
    return render_template("view_note.html", material=mat)

# ─── Download Route (Requires Student Name + Email Login or Admin) ────────────

@app.route("/download/<int:mat_id>")
def download_material(mat_id):
    mat = Material.query.get_or_404(mat_id)
    student = get_current_student()

    if not student and not session.get("is_admin"):
        flash(f'Please enter your Name and Email to download "{mat.title}".', "info")
        return redirect(url_for("login", next=url_for("download_material", mat_id=mat.id), download_title=mat.title))

    mat.downloads = (mat.downloads or 0) + 1
    if student:
        db.session.add(DownloadLog(student_id=student.id, material_id=mat.id))
    db.session.commit()

    if mat.filename and os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], mat.filename)):
        return send_from_directory(app.config["UPLOAD_FOLDER"], mat.filename, as_attachment=True)

    depts = get_departments_dict()
    dept_name = depts.get(mat.department, {}).get("name", mat.department)
    year_name = YEARS.get(mat.year, f"Year {mat.year}")
    content = (
        f"{get_settings().site_name.upper()} - STUDY NOTES\n"
        f"==================================================\n"
        f"Title: {mat.title}\n"
        f"Subject: {mat.subject}\n"
        f"Category: {mat.category}\n"
        f"Academic Year: {year_name} | Branch: {dept_name}\n\n"
        f"Overview & Notes:\n{mat.description}\n"
    )
    safe_name = secure_filename(mat.title.lower().replace(" ", "_")) or "study_material"
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={safe_name}.txt"}
    )

# ─── Authentication Routes (Student Name+Email & Admin Credentials) ───────────

@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")
    active_role = request.args.get("role", "student")
    download_title = request.args.get("download_title", "")

    if request.method == "POST":
        login_type = request.form.get("login_type", "student")

        if login_type == "student":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            branch = request.form.get("branch", "General").strip()

            if not name or not email or "@" not in email:
                flash("Please enter both your full name and a valid email address.", "danger")
                return redirect(url_for("login", next=next_url, role="student"))

            student = Student.query.filter_by(email=email).first()
            if not student:
                student = Student(name=name, email=email, branch=branch)
                db.session.add(student)
            else:
                student.name = name
                if branch:
                    student.branch = branch
                student.last_login = datetime.utcnow()
            db.session.commit()

            session["student_id"] = student.id
            flash(f"Welcome, {student.name}! You are now signed in.", "success")
            return redirect(next_url)

        elif login_type == "admin":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            settings = get_settings()

            if username == settings.admin_username and password == settings.admin_password:
                session["is_admin"] = True
                flash("Signed in to Administrator Control Panel.", "success")
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Invalid admin username or password.", "danger")
                return redirect(url_for("login", role="admin"))

    return render_template("login.html", next_url=next_url, active_role=active_role, download_title=download_title)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

@app.route("/my-downloads")
def student_profile():
    student = get_current_student()
    if not student:
        flash("Sign in with your Name and Email to view your download history.", "info")
        return redirect(url_for("login", next=url_for("student_profile")))
    logs = DownloadLog.query.filter_by(student_id=student.id).order_by(DownloadLog.downloaded_at.desc()).all()
    return render_template("student_profile.html", student=student, logs=logs)

# ─── Full-Control Admin Panel Routes ──────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_dashboard():
    materials = Material.query.order_by(Material.created_at.desc()).all()
    students = Student.query.order_by(Student.last_login.desc()).all()
    logs = DownloadLog.query.order_by(DownloadLog.downloaded_at.desc()).limit(50).all()
    dept_objs = Department.query.all()
    return render_template(
        "admin.html",
        materials=materials,
        students=students,
        logs=logs,
        dept_objs=dept_objs,
        total_downloads=sum(m.downloads for m in materials),
    )

@app.route("/admin/settings", methods=["POST"])
@admin_required
def admin_update_settings():
    s = get_settings()
    s.site_name = request.form.get("site_name", s.site_name).strip()
    s.hero_title = request.form.get("hero_title", s.hero_title).strip()
    s.hero_subtitle = request.form.get("hero_subtitle", s.hero_subtitle).strip()
    s.announcement = request.form.get("announcement", s.announcement).strip()
    s.show_announcement = request.form.get("show_announcement") == "on"
    s.footer_text = request.form.get("footer_text", s.footer_text).strip()
    s.admin_username = request.form.get("admin_username", s.admin_username).strip()
    new_pw = request.form.get("admin_password", "").strip()
    if new_pw:
        s.admin_password = new_pw
    db.session.commit()
    flash("Site settings, branding, and admin credentials updated!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/department/add", methods=["POST"])
@admin_required
def admin_add_department():
    slug = secure_filename(request.form.get("slug", "").lower().strip())
    name = request.form.get("name", "").strip()
    icon = request.form.get("icon", "bi-building").strip()
    color = request.form.get("color", "#4f46e5").strip()
    if slug and name and not Department.query.filter_by(slug=slug).first():
        db.session.add(Department(slug=slug, name=name, icon=icon, color=color))
        db.session.commit()
        flash(f'Added branch "{name}"!', "success")
    else:
        flash("Branch slug already exists or fields were empty.", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/department/delete/<int:dept_id>", methods=["POST"])
@admin_required
def admin_delete_department(dept_id):
    d = Department.query.get_or_404(dept_id)
    db.session.delete(d)
    db.session.commit()
    flash(f'Removed branch "{d.name}".', "warning")
    return redirect(url_for("admin_dashboard"))

@app.route("/upload", methods=["GET", "POST"])
@admin_required
def upload():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        year = int(request.form.get("year", 1))
        department = request.form.get("department", "it")
        category = request.form.get("category", "Lecture Notes")
        description = request.form.get("description", "").strip()
        uploaded_file = request.files.get("file")

        filename = ""
        size_mb = 2.5
        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            uploaded_file.save(save_path)
            size_mb = round(max(0.1, os.path.getsize(save_path) / (1024 * 1024)), 1)

        db.session.add(Material(
            title=title, subject=subject, year=year, department=department,
            category=category, description=description, filename=filename, size_mb=size_mb
        ))
        db.session.commit()
        flash(f'Published "{title}" to the library!', "success")
        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("admin_dashboard"))

@app.route("/delete/<int:mat_id>", methods=["POST"])
@admin_required
def delete_material(mat_id):
    mat = Material.query.get_or_404(mat_id)
    db.session.delete(mat)
    db.session.commit()
    flash(f'Deleted "{mat.title}".', "warning")
    return redirect(request.referrer or url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)