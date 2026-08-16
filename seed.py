"""Seed script for SkillBridge.

Populates the database with realistic demo data so the platform can be
explored immediately after running migrations.

Run with:  flask seed
(or)       python seed.py
"""
from datetime import datetime, timedelta, date

from app import create_app
from config import Config
from extensions import db

from models.user import User
from models.student import StudentProfile, StudentSkill
from models.client import ClientProfile
from models.category import Category
from models.skill import Skill
from models.project import Project, ProjectSkill, Hire
from models.proposal import Proposal
from models.milestone import Milestone
from models.payment import Payment, Withdrawal
from models.review import Review
from models.notification import Notification
from models.message import Message
from models.certificate import Certificate
from models.portfolio import Portfolio
from models.wishlist import Wishlist
from models.assessment import Assessment, AssessmentQuestion, AssessmentResult


PLATFORM_FEE = Config.PLATFORM_FEE_PERCENT


def _clear():
    """Remove existing rows so the seed can be re-run safely.

    Wrapped in try/except so tables that don't exist yet (e.g. before the
    first migration) are simply skipped.
    """
    # Order matters because of foreign keys.
    for model in (
        AssessmentResult, AssessmentQuestion, Assessment,
        Wishlist, Notification, Message, Review, Payment, Withdrawal,
        Milestone, Hire, Proposal, ProjectSkill, Project,
        Certificate, Portfolio, StudentSkill,
        StudentProfile, ClientProfile,
        Skill, Category, User,
    ):
        try:
            db.session.query(model).delete()
        except Exception:
            db.session.rollback()
    db.session.commit()


def _make_user(email, name, role, password="password123", **kwargs):
    u = User(email=email, name=name, role=role, **kwargs)
    u.set_password(password)
    db.session.add(u)
    db.session.flush()
    return u


def seed_all():
    app = create_app(Config)
    with app.app_context():
        # Ensure all tables exist (works with SQLite fallback or after migrations).
        db.create_all()
        _clear()
        print("Cleared existing data.")

        # ---------------------------------------------------------------
        # Admin
        # ---------------------------------------------------------------
        admin = _make_user(
            "admin@skillbridge.com", "Platform Admin", "admin",
            password="admin123", phone="+1-555-0001", city="San Francisco",
        )
        db.session.commit()
        print("Created admin user.")

        # ---------------------------------------------------------------
        # Categories
        # ---------------------------------------------------------------
        categories = {
            "Web Development": Category(name="Web Development", description="Websites, web apps and APIs", icon="code"),
            "Mobile Development": Category(name="Mobile Development", description="iOS, Android and cross-platform apps", icon="smartphone"),
            "Design": Category(name="Design", description="UI/UX, graphic and brand design", icon="palette"),
            "Data & AI": Category(name="Data & AI", description="Data science, ML and analytics", icon="database"),
            "Writing": Category(name="Writing", description="Content, copy and technical writing", icon="pen-tool"),
            "Marketing": Category(name="Marketing", description="SEO, social media and growth", icon="trending-up"),
        }
        for c in categories.values():
            db.session.add(c)
        db.session.commit()

        # ---------------------------------------------------------------
        # Skills
        # ---------------------------------------------------------------
        skill_data = {
            "Python": "Data & AI",
            "JavaScript": "Web Development",
            "React": "Web Development",
            "Vue.js": "Web Development",
            "Node.js": "Web Development",
            "Flask": "Web Development",
            "Django": "Web Development",
            "HTML/CSS": "Web Development",
            "Swift": "Mobile Development",
            "Kotlin": "Mobile Development",
            "Flutter": "Mobile Development",
            "React Native": "Mobile Development",
            "Figma": "Design",
            "UI/UX Design": "Design",
            "Graphic Design": "Design",
            "Logo Design": "Design",
            "Machine Learning": "Data & AI",
            "Data Analysis": "Data & AI",
            "SQL": "Data & AI",
            "Content Writing": "Writing",
            "Technical Writing": "Writing",
            "SEO": "Marketing",
            "Social Media Marketing": "Marketing",
        }
        skills = {}
        for name, cat in skill_data.items():
            s = Skill(name=name, category_id=categories[cat].id)
            skills[name] = s
            db.session.add(s)
        db.session.commit()

        # ---------------------------------------------------------------
        # Students
        # ---------------------------------------------------------------
        student_data = [
            {
                "email": "alex@student.com", "name": "Alex Morgan",
                "university": "Stanford University", "bio": "Full-stack developer passionate about clean code and great UX.",
                "experience": "Intermediate", "hourly_rate": 25, "availability": "Part Time",
                "languages": "English, Spanish", "verification_status": "verified",
                "skills": [("Python", "Advanced"), ("Flask", "Advanced"), ("React", "Intermediate"), ("JavaScript", "Intermediate"), ("SQL", "Intermediate")],
                "portfolios": [
                    {"title": "Campus Event Platform", "description": "A Flask + React app for managing university events.", "technologies": "Python, Flask, React, PostgreSQL", "project_url": "https://example.com/campus", "github_url": "https://github.com/alex/campus"},
                    {"title": "Study Buddy Bot", "description": "Telegram bot that quizzes students using spaced repetition.", "technologies": "Python, SQLite", "github_url": "https://github.com/alex/studybot"},
                ],
                "certificates": [
                    {"title": "Meta Front-End Developer", "organization": "Coursera", "credential_id": "MFE-2023-9981", "verified": True},
                    {"title": "Python for Everybody", "organization": "University of Michigan", "credential_id": "PYE-2022-4412", "verified": True},
                ],
            },
            {
                "email": "mia@student.com", "name": "Mia Chen",
                "university": "UC Berkeley", "bio": "UI/UX designer who loves turning complex problems into simple interfaces.",
                "experience": "Advanced", "hourly_rate": 30, "availability": "Full Time",
                "languages": "English, Mandarin", "verification_status": "verified",
                "skills": [("Figma", "Expert"), ("UI/UX Design", "Expert"), ("Graphic Design", "Advanced"), ("Logo Design", "Intermediate"), ("HTML/CSS", "Intermediate")],
                "portfolios": [
                    {"title": "Fintech Mobile App", "description": "End-to-end design of a budgeting app for students.", "technologies": "Figma, Illustrator", "project_url": "https://example.com/fintech"},
                ],
                "certificates": [
                    {"title": "Google UX Design", "organization": "Google", "credential_id": "GUX-2023-7710", "verified": True},
                ],
            },
            {
                "email": "sam@student.com", "name": "Sam Patel",
                "university": "MIT", "bio": "ML enthusiast building models that actually ship to production.",
                "experience": "Advanced", "hourly_rate": 35, "availability": "Part Time",
                "languages": "English, Hindi", "verification_status": "verified",
                "skills": [("Python", "Expert"), ("Machine Learning", "Advanced"), ("Data Analysis", "Advanced"), ("SQL", "Advanced"), ("Django", "Intermediate")],
                "portfolios": [
                    {"title": "House Price Predictor", "description": "Regression model with 92% accuracy on test data.", "technologies": "Python, scikit-learn, pandas", "github_url": "https://github.com/sam/housing"},
                ],
                "certificates": [
                    {"title": "Deep Learning Specialization", "organization": "deeplearning.ai", "credential_id": "DLS-2023-2200", "verified": True},
                ],
            },
            {
                "email": "jordan@student.com", "name": "Jordan Lee",
                "university": "University of Washington", "bio": "Mobile developer focused on delightful cross-platform apps.",
                "experience": "Intermediate", "hourly_rate": 28, "availability": "Weekends",
                "languages": "English", "verification_status": "pending",
                "skills": [("Flutter", "Advanced"), ("React Native", "Intermediate"), ("Swift", "Intermediate"), ("Kotlin", "Beginner")],
                "portfolios": [
                    {"title": "Habit Tracker", "description": "Cross-platform habit tracker with offline sync.", "technologies": "Flutter, Firebase", "project_url": "https://example.com/habits"},
                ],
                "certificates": [],
            },
            {
                "email": "emma@student.com", "name": "Emma Wilson",
                "university": "NYU", "bio": "Content strategist and technical writer with a marketing edge.",
                "experience": "Intermediate", "hourly_rate": 22, "availability": "Full Time",
                "languages": "English, French", "verification_status": "verified",
                "skills": [("Content Writing", "Advanced"), ("Technical Writing", "Advanced"), ("SEO", "Intermediate"), ("Social Media Marketing", "Intermediate")],
                "portfolios": [
                    {"title": "Developer Blog Series", "description": "12-part tutorial series on REST APIs.", "technologies": "Markdown, SEO", "project_url": "https://example.com/blog"},
                ],
                "certificates": [
                    {"title": "Content Marketing", "organization": "HubSpot", "credential_id": "CM-2023-5521", "verified": True},
                ],
            },
        ]

        students = []
        for data in student_data:
            u = _make_user(data["email"], data["name"], "student", phone="+1-555-0100", city="California")
            sp = StudentProfile(
                user_id=u.id,
                university=data["university"],
                bio=data["bio"],
                experience=data["experience"],
                hourly_rate=data["hourly_rate"],
                availability=data["availability"],
                languages=data["languages"],
                verification_status=data["verification_status"],
                student_id="SB-" + str(1000 + len(students)),
            )
            db.session.add(sp)
            db.session.flush()

            for skill_name, level in data["skills"]:
                db.session.add(StudentSkill(student_id=sp.id, skill_id=skills[skill_name].id, skill_level=level))

            for p in data.get("portfolios", []):
                db.session.add(Portfolio(
                    student_id=sp.id, title=p["title"], description=p.get("description"),
                    technologies=p.get("technologies"), project_url=p.get("project_url"),
                    github_url=p.get("github_url"),
                    completion_date=date.today() - timedelta(days=30 * (len(students) + 1)),
                ))

            for c in data.get("certificates", []):
                db.session.add(Certificate(
                    student_id=sp.id, title=c["title"], organization=c["organization"],
                    credential_id=c.get("credential_id"), verified=c.get("verified", False),
                    issue_date=date.today() - timedelta(days=120),
                ))

            students.append(sp)
        db.session.commit()
        print(f"Created {len(students)} student profiles.")

        # ---------------------------------------------------------------
        # Clients
        # ---------------------------------------------------------------
        client_data = [
            {"email": "techcorp@client.com", "name": "TechCorp Inc.", "company": "TechCorp Inc.", "city": "San Jose", "description": "A fast-growing SaaS company building developer tools."},
            {"email": "brightlabs@client.com", "name": "Bright Labs", "company": "Bright Labs LLC", "city": "Austin", "description": "Research lab looking for ML and data talent."},
            {"email": "studiobloom@client.com", "name": "Studio Bloom", "company": "Studio Bloom", "city": "New York", "description": "Boutique design and branding agency."},
        ]
        clients = []
        for data in client_data:
            u = _make_user(data["email"], data["name"], "client", phone="+1-555-0200", city=data["city"])
            cp = ClientProfile(user_id=u.id, company_name=data["company"], description=data["description"], phone="+1-555-0200", city=data["city"])
            db.session.add(cp)
            db.session.flush()
            clients.append(cp)
        db.session.commit()
        print(f"Created {len(clients)} client profiles.")

        # ---------------------------------------------------------------
        # Assessments
        # ---------------------------------------------------------------
        py_assess = Assessment(title="Python Fundamentals", description="Test your core Python knowledge.", skill_id=skills["Python"].id, passing_score=70, duration_minutes=15)
        db.session.add(py_assess)
        db.session.flush()
        py_questions = [
            ("What is the output of `type(3.14)`?", "int", "float", "str", "list", "B"),
            ("Which keyword defines a function?", "func", "def", "function", "lambda", "B"),
            ("How do you create a list?", "[1,2,3]", "{1,2,3}", "(1,2,3)", "<1,2,3>", "A"),
            ("What does `len('hello')` return?", "4", "5", "6", "Error", "B"),
        ]
        for q, a, b, c, d, ans in py_questions:
            db.session.add(AssessmentQuestion(assessment_id=py_assess.id, question=q, option_a=a, option_b=b, option_c=c, option_d=d, correct_answer=ans))

        ux_assess = Assessment(title="UI/UX Basics", description="Fundamentals of user-centered design.", skill_id=skills["UI/UX Design"].id, passing_score=70, duration_minutes=10)
        db.session.add(ux_assess)
        db.session.flush()
        ux_questions = [
            ("What does UX stand for?", "User Experience", "Unix Express", "Ultra Xtreme", "User Exit", "A"),
            ("Which is a prototyping tool?", "Figma", "Excel", "Photoshop only", "Terminal", "A"),
        ]
        for q, a, b, c, d, ans in ux_questions:
            db.session.add(AssessmentQuestion(assessment_id=ux_assess.id, question=q, option_a=a, option_b=b, option_c=c, option_d=d, correct_answer=ans))
        db.session.commit()

        # Assessment results for verified students
        db.session.add(AssessmentResult(student_id=students[0].id, assessment_id=py_assess.id, score=4, percentage=100, passed=True))
        db.session.add(AssessmentResult(student_id=students[2].id, assessment_id=py_assess.id, score=3, percentage=75, passed=True))
        db.session.add(AssessmentResult(student_id=students[1].id, assessment_id=ux_assess.id, score=2, percentage=100, passed=True))
        db.session.commit()



        # ---------------------------------------------------------------
        # Wishlist
        # ---------------------------------------------------------------
        db.session.add(Wishlist(user_id=students[0].user_id, item_type="student", item_id=students[1].id))
        db.session.add(Wishlist(user_id=clients[0].user_id, item_type="student", item_id=students[2].id))
        db.session.commit()

        # ---------------------------------------------------------------
        # Withdrawal (for earnings demo)
        # ---------------------------------------------------------------
        db.session.add(Withdrawal(
            student_id=students[1].id, amount=400, method="Bank Transfer",
            account_details="**** 4821", status="pending",
        ))
        db.session.commit()

        print("Seed complete! Demo accounts:")
        print("  Admin : admin@skillbridge.com / admin123")
        print("  Student: alex@student.com / password123")
        print("  Client : techcorp@client.com / password123")


if __name__ == "__main__":
    seed_all()
