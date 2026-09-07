from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import random

BASE = Path(__file__).resolve().parent
DB = BASE / "studyos.db"

app = Flask(__name__)
app.secret_key = "studyos-local-secret-change-me"

SUBJECTS = ["Physics", "Chemistry", "Mathematics"]

QUOTES = [
    "Small progress is still progress.",
    "Consistency beats intensity.",
    "Do the next useful thing.",
    "Your future self will thank you for today's effort.",
    "One focused session at a time.",
    "Mistakes are data. Use them.",
    "You do not need a perfect day. You need a productive next hour.",
]

CHAPTERS = {
    "Physics": [
        "Units & Dimensions","Kinematics","Laws of Motion","Work, Energy & Power",
        "System of Particles","Rotational Motion","Gravitation","Properties of Matter",
        "Thermodynamics","Kinetic Theory","Oscillations","Waves","Electrostatics",
        "Current Electricity","Magnetism","Electromagnetic Induction","Alternating Current",
        "Ray Optics","Wave Optics","Dual Nature","Atoms & Nuclei","Semiconductors"
    ],
    "Chemistry": [
        "Some Basic Concepts","Atomic Structure","Chemical Bonding","States of Matter",
        "Thermodynamics","Equilibrium","Redox Reactions","Solutions","Electrochemistry",
        "Chemical Kinetics","Periodic Classification","p-Block","d- and f-Block",
        "Coordination Compounds","Organic Chemistry Basics","Hydrocarbons","Haloalkanes",
        "Alcohols, Phenols & Ethers","Aldehydes & Ketones","Amines","Biomolecules",
        "Polymers","Chemistry in Everyday Life"
    ],
    "Mathematics": [
        "Sets & Relations","Functions","Quadratic Equations","Sequences & Series",
        "Trigonometry","Complex Numbers","Permutations & Combinations","Binomial Theorem",
        "Coordinate Geometry","Straight Lines","Circles","Conic Sections","Limits",
        "Continuity & Differentiability","Application of Derivatives","Integrals",
        "Differential Equations","Matrices","Determinants","Vectors","3D Geometry",
        "Probability","Statistics"
    ]
}


@app.get("/sw.js")
def service_worker():
    """Serve the service worker from / so it can control the whole app."""
    return send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, test_date TEXT NOT NULL,
        physics REAL NOT NULL, chemistry REAL NOT NULL,
        mathematics REAL NOT NULL, maximum REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL, chapter TEXT NOT NULL,
        completed INTEGER DEFAULT 0, revised INTEGER DEFAULT 0,
        pyq_completed INTEGER DEFAULT 0,
        UNIQUE(subject, chapter)
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL, task_date TEXT NOT NULL,
        completed INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, body TEXT NOT NULL,
        note_type TEXT NOT NULL, updated TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL, topic TEXT NOT NULL,
        mistake TEXT NOT NULL, solution TEXT, created TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_date TEXT NOT NULL, minutes INTEGER NOT NULL
    );
    """)
    for key, value in {
        "name": "Student",
        "exam_name": "JEE",
        "exam_date": (date.today() + timedelta(days=120)).isoformat()
    }.items():
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))
    for subject, chapters in CHAPTERS.items():
        for chapter in chapters:
            c.execute("INSERT OR IGNORE INTO chapters(subject,chapter) VALUES(?,?)", (subject,chapter))
    c.commit()
    c.close()

def setting(key, default=""):
    c = conn()
    r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    c.close()
    return r["value"] if r else default

def all_tests():
    c = conn()
    rows = c.execute("SELECT * FROM tests ORDER BY id DESC").fetchall()
    c.close()
    return rows

def percentage(t):
    return ((t["physics"] + t["chemistry"] + t["mathematics"]) / t["maximum"] * 100) if t["maximum"] else 0

def subject_pct(t, subject):
    key = {"Physics":"physics","Chemistry":"chemistry","Mathematics":"mathematics"}[subject]
    max_subject = t["maximum"] / 3
    return (t[key] / max_subject * 100) if max_subject else 0

def subject_average(subject):
    tests = all_tests()
    return sum(subject_pct(t, subject) for t in tests) / len(tests) if tests else 0

def chapter_stats():
    c = conn()
    rows = c.execute("SELECT * FROM chapters ORDER BY subject,id").fetchall()
    c.close()
    total = len(rows)
    done = sum(r["completed"] for r in rows)
    revised = sum(r["revised"] for r in rows)
    pyq = sum(r["pyq_completed"] for r in rows)
    return rows, total, done, revised, pyq

def today_minutes():
    c = conn()
    r = c.execute("SELECT COALESCE(SUM(minutes),0) x FROM study_sessions WHERE session_date=?", (date.today().isoformat(),)).fetchone()
    c.close()
    return int(r["x"])

def total_minutes():
    c = conn()
    r = c.execute("SELECT COALESCE(SUM(minutes),0) x FROM study_sessions").fetchone()
    c.close()
    return int(r["x"])

def format_minutes(n):
    n = int(n)
    return f"{n//60}h {n%60}m" if n >= 60 else f"{n}m"

def smart_advice():
    tests = all_tests()
    advice = []
    if not tests:
        advice.append("Take your first mock test so StudyOS can establish a performance baseline.")
    else:
        avgs = {s: subject_average(s) for s in SUBJECTS}
        weak = min(avgs, key=avgs.get)
        strong = max(avgs, key=avgs.get)
        advice.append(f"Focus more on {weak}; it currently has your lowest normalized average.")
        advice.append(f"Maintain {strong} with regular timed practice.")
        if len(tests) >= 2:
            diff = percentage(tests[0]) - percentage(tests[1])
            if diff < 0:
                advice.append("Your latest mock score dropped. Review your mistake log before another full mock.")
            elif diff > 0:
                advice.append("Your latest mock improved. Identify what worked and repeat that study pattern.")
    rows, total, done, revised, pyq = chapter_stats()
    if total - done:
        advice.append(f"You have {total-done} chapter entries still incomplete.")
    if done - revised:
        advice.append(f"{done-revised} completed chapters are not marked as revised yet.")
    if today_minutes() < 60:
        advice.append("You have less than one hour of logged study time today. Try one focused session.")
    c = conn()
    mistakes = c.execute("SELECT COUNT(*) n FROM mistakes").fetchone()["n"]
    c.close()
    if mistakes:
        advice.append("Review your Mistake Log regularly; recurring errors should become revision priorities.")
    return advice

@app.context_processor
def globals():
    try:
        exam = datetime.strptime(setting("exam_date"), "%Y-%m-%d").date()
        days = max(0, (exam - date.today()).days)
    except ValueError:
        days = 0
    return {
        "app_name": "StudyOS",
        "username": setting("name","Student"),
        "exam_name": setting("exam_name","JEE"),
        "exam_date": setting("exam_date"),
        "days_left": days
    }

@app.route("/")
def home():
    tests = all_tests()
    rows,total,done,revised,pyq = chapter_stats()
    tasks = get_today_tasks()
    return render_template("dashboard.html",
        page="Home", quote=random.choice(QUOTES), tests=tests[:5],
        test_average=sum(percentage(t) for t in tests)/len(tests) if tests else 0,
        syllabus=(done/total*100 if total else 0),
        today_minutes=today_minutes(), total_minutes=total_minutes(),
        tasks=tasks, completed_tasks=sum(t["completed"] for t in tasks),
        advice=smart_advice())

@app.route("/dashboard")
def dashboard():
    tests = all_tests()
    return render_template("dashboard.html", page="Dashboard",
        quote=random.choice(QUOTES), tests=tests[:5],
        test_average=sum(percentage(t) for t in tests)/len(tests) if tests else 0,
        syllabus=(chapter_stats()[2]/chapter_stats()[1]*100 if chapter_stats()[1] else 0),
        today_minutes=today_minutes(), total_minutes=total_minutes(),
        tasks=get_today_tasks(), completed_tasks=sum(t["completed"] for t in get_today_tasks()),
        advice=smart_advice())

@app.route("/tests", methods=["GET","POST"])
def tests():
    if request.method == "POST":
        try:
            name = request.form.get("name","Mock Test").strip() or "Mock Test"
            p=float(request.form["physics"]); c=float(request.form["chemistry"])
            m=float(request.form["mathematics"]); maximum=float(request.form["maximum"])
            if maximum <= 0 or min(p,c,m) < 0: raise ValueError
            db=conn()
            db.execute("INSERT INTO tests(name,test_date,physics,chemistry,mathematics,maximum) VALUES(?,?,?,?,?,?)",
                       (name,date.today().isoformat(),p,c,m,maximum))
            db.commit(); db.close()
            flash("Test analyzed and saved permanently.", "success")
            return redirect(url_for("tests"))
        except ValueError:
            flash("Please enter valid numeric marks.", "error")
    return render_template("tests.html", page="Mock Tests", tests=all_tests())

@app.route("/chapters")
def chapters():
    subject=request.args.get("subject","Physics")
    if subject not in SUBJECTS: subject="Physics"
    rows=[r for r in chapter_stats()[0] if r["subject"]==subject]
    return render_template("chapters.html", page="Chapters", subject=subject, subjects=SUBJECTS, rows=rows)

@app.post("/chapters/<int:chapter_id>")
def update_chapter(chapter_id):
    field=request.form.get("field")
    value=1 if request.form.get("value")=="1" else 0
    if field in {"completed","revised","pyq_completed"}:
        db=conn(); db.execute(f"UPDATE chapters SET {field}=? WHERE id=?", (value,chapter_id)); db.commit(); db.close()
    return redirect(url_for("chapters", subject=request.form.get("subject","Physics")))

@app.route("/revision")
def revision():
    rows=chapter_stats()[0]
    by={}
    for s in SUBJECTS:
        by[s]=[r for r in rows if r["subject"]==s]
    return render_template("revision.html", page="Revision", by=by)

def get_today_tasks():
    db=conn(); rows=db.execute("SELECT * FROM tasks WHERE task_date=? ORDER BY id DESC",(date.today().isoformat(),)).fetchall(); db.close(); return rows

@app.route("/tasks", methods=["GET","POST"])
def tasks():
    if request.method=="POST":
        task=request.form.get("task","").strip()
        if task:
            db=conn(); db.execute("INSERT INTO tasks(task,task_date) VALUES(?,?)",(task,date.today().isoformat())); db.commit(); db.close()
            flash("Task added.", "success")
    return render_template("tasks.html", page="Tasks", tasks=get_today_tasks())

@app.post("/tasks/<int:task_id>")
def update_task(task_id):
    value=1 if request.form.get("completed")=="1" else 0
    db=conn(); db.execute("UPDATE tasks SET completed=? WHERE id=?",(value,task_id)); db.commit(); db.close()
    return redirect(url_for("tasks"))

@app.route("/timer")
def timer():
    return render_template("timer.html", page="Focus Timer")

@app.post("/sessions")
def sessions():
    try: minutes=max(1,int(request.form["minutes"]))
    except (ValueError,KeyError): return jsonify({"ok":False}),400
    db=conn(); db.execute("INSERT INTO study_sessions(session_date,minutes) VALUES(?,?)",(date.today().isoformat(),minutes)); db.commit(); db.close()
    return jsonify({"ok":True,"today":today_minutes(),"total":total_minutes()})

@app.route("/progress")
def progress():
    tests=all_tests()
    values=[round(percentage(t),2) for t in reversed(tests)]
    subject_values={s:round(subject_average(s),2) for s in SUBJECTS}
    return render_template("progress.html", page="Progress", tests=tests, values=values, subject_values=subject_values)

@app.route("/notes", methods=["GET","POST"])
def notes():
    if request.method=="POST":
        title=request.form.get("title","").strip()
        body=request.form.get("body","").strip()
        typ=request.form.get("note_type","General")
        if title and body:
            db=conn(); db.execute("INSERT INTO notes(title,body,note_type,updated) VALUES(?,?,?,?)",
                                  (title,body,typ,datetime.now().isoformat(timespec="seconds"))); db.commit(); db.close()
            flash("Note saved permanently.", "success")
    db=conn(); rows=db.execute("SELECT * FROM notes ORDER BY id DESC").fetchall(); db.close()
    return render_template("notes.html", page="Notes", notes=rows)

@app.route("/mistakes", methods=["GET","POST"])
def mistakes():
    if request.method=="POST":
        vals=(request.form.get("subject","Physics"),request.form.get("topic","").strip(),
              request.form.get("mistake","").strip(),request.form.get("solution","").strip(),
              datetime.now().isoformat(timespec="seconds"))
        if vals[1] and vals[2]:
            db=conn(); db.execute("INSERT INTO mistakes(subject,topic,mistake,solution,created) VALUES(?,?,?,?,?)",vals); db.commit(); db.close()
            flash("Mistake saved.", "success")
    db=conn(); rows=db.execute("SELECT * FROM mistakes ORDER BY id DESC").fetchall(); db.close()
    return render_template("mistakes.html", page="Mistakes", mistakes=rows)

@app.route("/settings", methods=["GET","POST"])
def settings():
    if request.method=="POST":
        name=request.form.get("name","Student").strip() or "Student"
        exam=request.form.get("exam_name","JEE").strip() or "JEE"
        exam_date=request.form.get("exam_date","").strip()
        try: datetime.strptime(exam_date,"%Y-%m-%d")
        except ValueError:
            flash("Exam date must use YYYY-MM-DD.", "error")
            return redirect(url_for("settings"))
        db=conn()
        for k,v in {"name":name,"exam_name":exam,"exam_date":exam_date}.items():
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(k,v))
        db.commit(); db.close()
        flash("Settings saved.", "success")
        return redirect(url_for("home"))
    return render_template("settings.html", page="Settings")

@app.route("/api/summary")
def api_summary():
    tests=all_tests()
    rows,total,done,revised,pyq=chapter_stats()
    return jsonify({
        "days_left": globals()["days_left"] if "days_left" in globals() else 0,
        "tests": len(tests),
        "average": round(sum(percentage(t) for t in tests)/len(tests),2) if tests else 0,
        "syllabus": round(done/total*100,2) if total else 0,
        "today_minutes": today_minutes(),
        "total_minutes": total_minutes()
    })

init_db()

if __name__ == "__main__":
    app.run(debug=True)
