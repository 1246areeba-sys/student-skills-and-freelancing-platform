"""Payment routes: student earnings, client payments, admin overview."""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models.payment import Payment, Withdrawal
from models.project import Project
from models.student import StudentProfile
from models.client import ClientProfile

payment_bp = Blueprint("payment", __name__, url_prefix="/payments")


@payment_bp.route("/student")
@login_required
def student_payments():
    if not current_user.is_student:
        abort(403)
    student = current_user.student_profile
    payments = Payment.query.filter_by(student_id=student.id).order_by(
        Payment.created_at.desc()
    ).all()
    total = db.session.query(func.coalesce(func.sum(Payment.student_amount), 0)).filter(
        Payment.student_id == student.id, Payment.status == "paid"
    ).scalar() or 0
    return render_template(
        "student/earnings.html",
        payments=payments,
        total_earned=float(total or 0),
        pending=0,
        withdrawn=0,
        fees=0,
        available=float(total or 0),
        withdrawals=[],
    )


@payment_bp.route("/client")
@login_required
def client_payments():
    if not current_user.is_client:
        abort(403)
    client = current_user.client_profile
    payments = Payment.query.filter_by(client_id=client.id).order_by(
        Payment.created_at.desc()
    ).all()
    total = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.client_id == client.id, Payment.status == "paid"
    ).scalar() or 0
    return render_template(
        "client/payments.html",
        payments=payments,
        total_spent=float(total or 0),
        pending=0,
    )
