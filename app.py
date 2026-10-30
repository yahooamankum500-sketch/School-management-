"""
School Management System — Complete Application
================================================
Combines all 51 phases into a single app.py
"""

import os
from datetime import datetime

from flask import (
    Flask, render_template, request, session,
    redirect, url_for, jsonify, Response, send_from_directory
)
from flask_session import Session
from werkzeug.exceptions import HTTPException

from config import Config

# Supabase Initialize Import (From your 2nd code snippet)
try:
    from supabase_client import init_supabase, get_supabase
except ImportError:
    init_supabase = lambda: None
    get_supabase = lambda: None

# ============================================================
# 1. CONFIG VALIDATION (This prevents the Render Deploy Error)
# ============================================================
# This will raise an error immediately if SECRET_KEY is missing or < 32 chars
Config.validate()

# ============================================================
# APP INITIALIZATION
# ============================================================
app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Initialize Supabase connection
init_supabase()


# ============================================================
# BLUEPRINT IMPORTS
# ============================================================
# Phase 1 — Auth
from modules.auth import auth_bp, login_required, role_required

# Phase 2-8 — Core Modules
from modules.students import students_bp
from modules.fees import fees_bp
from modules.attendance import attendance_bp
from modules.exams import exams_bp
from modules.notices import notices_bp
from modules.parent import parent_bp
from modules.settings import settings_bp

# Phase 9-17 — Reports, Bulk, WhatsApp, Backup, Bills, ID Card
from modules.reports import reports_bp
from modules.bulk_import import bulk_bp
from modules.whatsapp import whatsapp_bp
from modules.backup import backup_bp
from modules.bills import bills_bp
from modules.id_card import id_card_bp

# Phase 18-25 — Timetable, Salary, Homework, Transport, Expenses, Certificates, Events, Library
from modules.timetable import timetable_bp
from modules.salary import salary_bp
from modules.homework import homework_bp
from modules.transport import transport_bp
from modules.expenses import expenses_bp
from modules.certificates import certificates_bp
from modules.events import events_bp
from modules.library import library_bp

# Phase 26-32 — Promotion, Teacher Portal, Medical, Alerts, Admin Users, Hostel, QR
from modules.promotion import promotion_bp
from modules.teacher_portal import teacher_portal_bp
from modules.teachers_admin import teachers_admin_bp
from modules.medical import medical_bp
from modules.alerts import alerts_bp
from modules.admin_users import admin_users_bp
from modules.hostel import hostel_bp
from modules.qr_attendance import qr_attendance_bp

# Phase 33-37 — System, Annual Report, Help, Public Site, Admissions, Payments
from modules.system import system_bp
from modules.annual_report import annual_report_bp
from modules.help import help_bp, get_help_slug
from modules.help_data import HELP_TOPICS
from modules.public import public_bp
from modules.admissions import admissions_bp
from modules.public_content import public_content_bp
from modules.payments import payments_bp
from modules.admin_payments import admin_payments_bp

# Phase 39-51 — Staff Attendance, Leave, Discounts, Visitors, Advances, Chat,
# Online Exams, Automation, Hall Tickets, Photos, Report Cards, Password Reset
from modules.staff_attendance import staff_att_bp
from modules.leave import leave_bp
from modules.discounts import discounts_bp
from modules.visitors import visitors_bp
from modules.advances import advances_bp
from modules.chat import chat_bp
from modules.online_exams import online_exams_bp
from modules.automation import automation_bp
from modules.hall_tickets import hall_tickets_bp
from modules.photos import photos_bp
from modules.report_cards import report_cards_bp
from modules.password_reset import password_reset_bp


# ============================================================
# REGISTER ALL BLUEPRINTS (Phase 1 → Phase 51)
# ============================================================
# Phase 1 — Auth (must be first)
app.register_blueprint(auth_bp)

# Phase 2-8 — Core
app.register_blueprint(students_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(exams_bp)
app.register_blueprint(notices_bp)
app.register_blueprint(parent_bp)
app.register_blueprint(settings_bp)

# Phase 9-17
app.register_blueprint(reports_bp)
app.register_blueprint(bulk_bp)
app.register_blueprint(whatsapp_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(bills_bp)
app.register_blueprint(id_card_bp)

# Phase 18-25
app.register_blueprint(timetable_bp)
app.register_blueprint(salary_bp)
app.register_blueprint(homework_bp)
app.register_blueprint(transport_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(certificates_bp)
app.register_blueprint(events_bp)
app.register_blueprint(library_bp)

# Phase 26-32
app.register_blueprint(promotion_bp)
app.register_blueprint(teacher_portal_bp)
app.register_blueprint(teachers_admin_bp)
app.register_blueprint(medical_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(hostel_bp)
app.register_blueprint(qr_attendance_bp)

# Phase 33-37
app.register_blueprint(system_bp)
app.register_blueprint(annual_report_bp)
app.register_blueprint(help_bp)
app.register_blueprint(public_bp)
app.register_blueprint(admissions_bp)
app.register_blueprint(public_content_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(admin_payments_bp)

# Phase 39-51
app.register_blueprint(staff_att_bp)
app.register_blueprint(leave_bp)
app.register_blueprint(discounts_bp)
app.register_blueprint(visitors_bp)
app.register_blueprint(advances_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(online_exams_bp)
app.register_blueprint(automation_bp)
app.register_blueprint(hall_tickets_bp)
app.register_blueprint(photos_bp)
app.register_blueprint(report_cards_bp)
app.register_blueprint(password_reset_bp)


# ============================================================
# DIRECT ROUTES
# ============================================================

@app.route("/")
def home():
    """Homepage — gradient landing with login links"""
    return render_template("home.html")


@app.route("/health")
def health_check():
    """Health check — for uptime monitoring"""
    from database import get_conn
    status = {
        "status": "ok",
        "app": "School Management",
        "timestamp": datetime.now().isoformat(),
    }
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = "error"
        status["db_error"] = str(e)[:100]
        return jsonify(status), 503
    return jsonify(status), 200

@app.route("/api/system-status")
def system_status():
    """Check Application and Supabase status (From 2nd code)"""
    supa_status = "not_configured"
    if get_supabase() is not None:
        supa_status = "configured"
        
    return jsonify({
        "application": "School Work ERP",
        "flask": "running",
        "supabase": supa_status,
        "secret_key_status": "valid" # Since validate() passed
    })


@app.route("/dashboard")
@login_required
def dashboard():
    """
    Main dashboard — Phase 38 V2 with all widgets.
    Defensive coding: missing functions default to safe values.
    """
    from database import (
        count_students, total_collected, today_attendance_percent,
        count_unread_notices, get_fees_monthly_trend,
        get_attendance_trend, get_students_by_class,
        count_new_enquiries, count_active_staff, count_homework_this_week,
        get_computed_alerts, get_custom_alerts,
        get_upcoming_events, count_upcoming_events,
        get_today_snapshot, get_month_fee_progress,
        get_birthdays_today, get_recent_activity,
        get_top_performers, get_class_attendance_today,
        get_staff_attendance_today_summary,
        count_transport_students,
        get_visitors_summary,
        get_pending_leave_count,
        get_total_advance_outstanding,
    )

    today_str = datetime.now().strftime("%Y-%m-%d")

    def safe(fn, default=None, *args, **kwargs):
        """Defensive caller — never crash dashboard"""
        try:
            return fn(*args, **kwargs)
        except Exception:
            return default

    return render_template(
        "dashboard.html",
        # ---- Phase 2-8 core KPIs ----
        total_students=safe(count_students, 0),
        fees_collected=safe(total_collected, 0),
        attendance_today=safe(today_attendance_percent, None, today_str),
        recent_notices=safe(count_unread_notices, 0, 7),
        new_enquiries=safe(count_new_enquiries, 0),
        total_staff=safe(count_active_staff, 0),
        homework_week=safe(count_homework_this_week, 0),
        upcoming_events_count=safe(count_upcoming_events, 0, 7),

        # ---- Phase 8 charts ----
        fees_trend=safe(get_fees_monthly_trend, [], 6),
        att_trend=safe(get_attendance_trend, [], 7),
        class_dist=safe(get_students_by_class, []),

        # ---- Phase 24, 29 alerts & events ----
        computed_alerts=safe(get_computed_alerts, []),
        custom_alerts=safe(get_custom_alerts, [], True, 2),
        upcoming_events_list=safe(get_upcoming_events, [], 30, None, 5),

        # ---- Phase 38 Dashboard V2 ----
        today_snap=safe(get_today_snapshot, {}),
        fee_progress=safe(get_month_fee_progress, {}),
        birthdays=safe(get_birthdays_today, []),
        recent_activity=safe(get_recent_activity, [], 8),
        top_performers=safe(get_top_performers,
                             {"exam": None, "students": []}, 5),
        class_att_bars=safe(get_class_attendance_today, []),

        # ---- Phase 39-44 newer widgets ----
        staff_att_today=safe(get_staff_attendance_today_summary, {}),
        transport_students=safe(count_transport_students, 0),
        visitors_today=safe(get_visitors_summary, {}),
        pending_leave=safe(get_pending_leave_count, 0),
        advance_outstanding=safe(get_total_advance_outstanding,
                                  {"outstanding": 0, "active_count": 0}),
    )


@app.route("/quick-search")
@login_required
def quick_search_api():
    """Phase 38 — Command palette global search"""
    from database import quick_search
    q = request.args.get("q", "").strip()
    return jsonify(quick_search(q))


@app.route("/manifest.json")
def manifest_route():
    """Phase 10 — PWA manifest with dynamic school name"""
    from database import get_settings
    try:
        s = get_settings()
    except Exception:
        s = {"school_name": "School"}
    manifest = {
        "name": s.get("school_name", "School Management"),
        "short_name": s.get("school_name", "School")[:12],
        "description": s.get("tagline", "School Management System"),
        "start_url": "/dashboard",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#f5f6fa",
        "theme_color": "#1e293b",
        "icons": [{
            "src": "/static/icon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any maskable",
        }],
    }
    return jsonify(manifest)


@app.route("/sw.js")
def sw_route():
    """Phase 10 — Service worker at root scope"""
    resp = send_from_directory(app.static_folder, "sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Content-Type"] = "application/javascript"
    return resp


# ============================================================
# CONTEXT PROCESSORS
# ============================================================

@app.context_processor
def inject_school():
    """Phase 8 — school info available in every template"""
    from database import get_settings
    try:
        return {"school": get_settings()}
    except Exception:
        return {"school": {"school_name": "School Management"}}


@app.context_processor
def inject_alert_count():
    """Phase 29 — alerts count in sidebar"""
    if "admin_id" not in session:
        return {"alert_count": 0}
    try:
        from database import get_computed_alerts
        return {"alert_count": len(get_computed_alerts())}
    except Exception:
        return {"alert_count": 0}


@app.context_processor
def inject_chat_unread():
    """Phase 45 — chat unread messages in sidebar"""
    if "admin_id" not in session:
        return {"chat_unread": 0}
    try:
        from database import count_unread_threads_for_admin
        return {"chat_unread": count_unread_threads_for_admin()}
    except Exception:
        return {"chat_unread": 0}


@app.context_processor
def inject_help_context():
    """Phase 35 — contextual help icon per page"""
    if "admin_id" not in session:
        return {"help_topic": None, "help_slug": None}
    slug = get_help_slug(request.path)
    topic = HELP_TOPICS.get(slug) if slug else None
    return {"help_topic": topic, "help_slug": slug}


# ============================================================
# ERROR HANDLERS (Phase 33)
# ============================================================

@app.errorhandler(404)
def not_found(e):
    """404 — JSON for API, HTML for pages"""
    if request.path.startswith(("/api", "/qr-attendance/mark",
                                 "/qr-attendance/summary", "/quick-search")):
        return jsonify({"error": "not found"}), 404
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    """403 — access denied"""
    if request.path.startswith(("/api", "/qr-attendance")):
        return jsonify({"error": "forbidden"}), 403
    return render_template("errors/403.html"), 403


@app.errorhandler(500)
def server_error(e):
    """500 — server error"""
    import traceback
    traceback.print_exc()
    return render_template("errors/500.html"), 500


@app.errorhandler(Exception)
def catch_all(e):
    """Catch-all for unhandled exceptions"""
    if isinstance(e, HTTPException):
        return e
    import traceback
    traceback.print_exc()
    return render_template("errors/500.html"), 500


# ============================================================
# BEFORE REQUEST — Rate Limiting (Phase 33)
# ============================================================

from collections import defaultdict
from time import time as _time

_rate_store = defaultdict(list)


def _rate_limit_check(ip, endpoint, max_per_minute=60):
    """Sliding-window rate limit per IP per endpoint"""
    now = _time()
    key = f"{ip}:{endpoint}"
    _rate_store[key] = [t for t in _rate_store[key] if now - t < 60]
    if len(_rate_store[key]) >= max_per_minute:
        return False
    _rate_store[key].append(now)
    return True


@app.before_request
def rate_limit_guard():
    """Rate limit sensitive endpoints"""
    sensitive = [
        "/qr-attendance/mark", "/login", "/parent/login",
        "/teacher/login", "/reset/",
    ]
    path = request.path
    if any(path.startswith(p) for p in sensitive):
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?")
        ip = ip.split(",")[0].strip()
        max_per_min = 300 if "qr-attendance" in path else 20
        if not _rate_limit_check(ip, path, max_per_min):
            return jsonify({
                "error": "Too many requests — thodi der baad try karo"
            }), 429


# ============================================================
# AFTER REQUEST — Security, Cache, Audit
# ============================================================

@app.after_request
def add_security_headers(response):
    """Phase 33 — security headers"""
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = \
            "max-age=31536000; includeSubDomains"
    return response


@app.after_request
def cache_static(response):
    """Phase 33 — cache-control"""
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=604800"
    elif request.path in ["/sw.js", "/manifest.json"]:
        response.headers["Cache-Control"] = "no-cache"
    return response


# Phase 30 — Audit auto-logger
_AUDIT_EXCLUDE = [
    "/login", "/teacher/", "/parent/", "/site",
    "/reset/", "/alerts/log-send", "/pay/", "/automation/cron",
]


@app.after_request
def auto_audit(response):
    """Auto-log POST/PUT/DELETE for audit trail"""
    try:
        if "admin_id" not in session:
            return response
        if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
            return response
        path = request.path
        if any(path.startswith(p) for p in _AUDIT_EXCLUDE):
            return response
        if 200 <= response.status_code < 400:
            entity = None
            entity_map = {
                "/students/": "student", "/fees/": "fees",
                "/staff/": "staff", "/exams/": "exams",
                "/salary/": "salary", "/admin-users/": "admin_users",
                "/notices/": "notices", "/events/": "events",
                "/library/": "library", "/hostel/": "hostel",
                "/transport/": "transport", "/visitors/": "visitors",
                "/advances/": "advances", "/leave/": "leave",
                "/automation/": "automation",
            }
            for prefix, ent in entity_map.items():
                if path.startswith(prefix):
                    entity = ent
                    break
            from database import log_audit
            log_audit(
                session["admin_id"],
                session.get("admin_username", "?"),
                action=f"{request.method.lower()}_request",
                method=request.method,
                path=path[:255],
                entity=entity,
                ip=request.remote_addr,
            )
    except Exception:
        pass
    return response


# ============================================================
# MAIN (For Local Testing & Render Deployment)
# ============================================================

if __name__ == "__main__":
    # Render provides the PORT via environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
