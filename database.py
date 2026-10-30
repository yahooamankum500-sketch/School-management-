"""
School Management System — Complete Database Layer
====================================================
All 51 phases combined into single database.py

Structure:
    - Imports & Helpers
    - Phase 1: Admin
    - Phase 2: Students
    - Phase 3: Fees
    - Phase 4: Attendance
    - Phase 5: Exams & Marks
    - Phase 6: Notices
    - Phase 7: Parents
    - Phase 8: Settings & Charts
    - Phase 9: Reports
    - Phase 13: Bulk Import
    - Phase 14: WhatsApp
    - Phase 15: Backup
    - Phase 16: Bills
    - Phase 18: Timetable
    - Phase 19: Salary
    - Phase 20: Homework
    - Phase 21: Transport
    - Phase 22: Expenses & P&L
    - Phase 23: Certificates
    - Phase 24: Events
    - Phase 25: Library
    - Phase 26: Promotion
    - Phase 27: Teachers
    - Phase 28: Medical
    - Phase 29: Alerts
    - Phase 30: Multi-Admin & Audit
    - Phase 31: Hostel
    - Phase 32: QR Attendance
    - Phase 34: Annual Reports
    - Phase 36: Public Content
    - Phase 37: Online Payments
    - Phase 38: Dashboard V2
    - Phase 39: Staff Attendance
    - Phase 40: Leave
    - Phase 41: Discounts
    - Phase 42: SMS
    - Phase 43: Visitors
    - Phase 44: Advances
    - Phase 45: Chat
    - Phase 46: Online Exams
    - Phase 47: Automation
    - Phase 48: Hall Tickets
    - Phase 49: Photos & Documents
    - Phase 50: Report Cards
    - Phase 51: Password Reset, Duplicate Detection
"""

# ============================================================
# IMPORTS & CONSTANTS
# ============================================================
import os
import json as _json
import random as _random
import secrets
from datetime import datetime, date, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from supabase_client import get_conn


# ---- Global Constants ----
BACKUP_TABLES = [
    "settings", "admins", "students", "fee_structure",
    "fee_payments", "attendance", "exams", "marks",
    "notices", "parents", "enquiries", "staff",
    "whatsapp_templates", "whatsapp_logs",
]

ADMIN_ROLES = ["super_admin", "admin", "accountant", "viewer"]

CERT_TYPES = [
    "Transfer Certificate",
    "Bonafide Certificate",
    "Character Certificate",
    "Study Certificate",
    "Fee Clearance Certificate",
]

CERT_TEMPLATES = {
    "Transfer Certificate": (
        "This is to certify that {name}, son/daughter of {parent_name}, "
        "was a student of this school in Class {class_name}{section} "
        "(Roll No. {roll}) during the academic year {ay}. "
        "His/her conduct and character were found to be satisfactory. "
        "All dues have been cleared."
    ),
    "Bonafide Certificate": (
        "This is to certify that {name}, son/daughter of {parent_name}, "
        "is a bonafide student of this school, currently studying in "
        "Class {class_name}{section} (Roll No. {roll}) during AY {ay}."
    ),
    "Character Certificate": (
        "This is to certify that {name}, son/daughter of {parent_name}, "
        "was a student of this school in Class {class_name}{section}. "
        "His/her conduct was good and satisfactory."
    ),
    "Study Certificate": (
        "This is to certify that {name}, son/daughter of {parent_name}, "
        "is currently studying in Class {class_name}{section} "
        "(Roll No. {roll}) at this school during AY {ay}."
    ),
    "Fee Clearance Certificate": (
        "This is to certify that all fees and dues of {name}, son/daughter "
        "of {parent_name}, studying in Class {class_name}{section}, have "
        "been cleared up to the date of this certificate."
    ),
}

EVENT_TYPES = ["holiday", "exam", "meeting", "sports", "cultural", "other"]
BOOK_CATEGORIES = ["Textbook", "Reference", "Fiction", "Non-fiction",
                   "Magazine", "Comics", "Biography", "Other"]
LIBRARY_FINE_PER_DAY = 2

EXPENSE_CATEGORIES = [
    "Rent", "Utilities", "Maintenance", "Stationery", "Books",
    "Transport", "Food", "Events", "Marketing", "Equipment", "Other",
]

CLASS_SEQUENCE = [
    "Nursery", "LKG", "UKG",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

ROOM_TYPES = ["single", "double", "triple", "shared", "dormitory"]

DISCOUNT_CATEGORIES = ["sibling", "staff", "merit", "sports",
                       "rte", "need_based", "other"]

VISITOR_PURPOSES = ["meeting", "fee", "enquiry", "delivery",
                    "interview", "event", "other"]

ADVANCE_TYPES = ["advance", "loan"]

DOC_TYPES = [
    ("aadhaar", "Aadhaar Card"),
    ("birth_cert", "Birth Certificate"),
    ("marksheet", "Previous Marksheet"),
    ("tc", "Transfer Certificate"),
    ("caste", "Caste Certificate"),
    ("income", "Income Certificate"),
    ("photo", "Photo"),
    ("other", "Other"),
]


# ============================================================
# HELPERS
# ============================================================
def _json_safe(value):
    """Convert datetime/Decimal/list/dict to JSON-safe"""
    from datetime import date as _d, datetime as _dt
    from decimal import Decimal
    if value is None:
        return None
    if isinstance(value, (_dt, _d)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return value


def _academic_year_for_cert():
    """Current academic year like '2024-25'"""
    now = datetime.now()
    y = now.year
    if now.month >= 4:
        return f"{y}-{str(y + 1)[-2:]}"
    return f"{y - 1}-{str(y)[-2:]}"


def get_current_academic_year():
    return _academic_year_for_cert()


def get_academic_year_options():
    today = date.today()
    current_start = today.year if today.month >= 4 else today.year - 1
    return [f"{y}-{str(y + 1)[-2:]}" for y in range(current_start, current_start - 5, -1)]


def _fy_range(fy_year):
    """2024 → (2024-04-01, 2025-03-31)"""
    return date(fy_year, 4, 1), date(fy_year + 1, 3, 31)


def _academic_year_range(year_label):
    """'2024-25' → (date, date)"""
    parts = year_label.split("-")
    start_year = int(parts[0])
    return date(start_year, 4, 1), date(start_year + 1, 3, 31)


# ============================================================
# PHASE 1 — ADMIN
# ============================================================
def create_admin(username, password, full_name=""):
    conn = get_conn()
    cur = conn.cursor()
    pwd_hash = generate_password_hash(password)
    cur.execute(
        "INSERT INTO admins (username, password_hash, full_name) "
        "VALUES (%s, %s, %s) RETURNING id;",
        (username, pwd_hash, full_name)
    )
    uid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return uid


def get_admin_by_username(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, password_hash, full_name, role, is_active
        FROM admins WHERE username=%s;
    """, (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def verify_admin(username, password):
    row = get_admin_by_username(username)
    if not row:
        return None
    if not row[5]:
        return None
    if check_password_hash(row[2], password):
        return {"id": row[0], "username": row[1],
                "full_name": row[3], "role": row[4] or "admin"}
    return None


def count_admins():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM admins;")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


def get_admin(admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, full_name, role, is_active, created_at
        FROM admins WHERE id=%s;
    """, (admin_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "username": row[1], "full_name": row[2],
            "role": row[3], "is_active": row[4], "created_at": row[5]}


def update_admin_profile(admin_id, full_name, username):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE admins SET full_name=%s, username=%s
            WHERE id=%s RETURNING id;
        """, (full_name, username, admin_id))
        res = cur.fetchone()
        conn.commit()
        return res[0] if res else None
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def change_admin_password(admin_id, old_password, new_password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM admins WHERE id=%s;", (admin_id,))
    row = cur.fetchone()
    if not row or not check_password_hash(row[0], old_password):
        cur.close()
        conn.close()
        return False
    new_hash = generate_password_hash(new_password)
    cur.execute("UPDATE admins SET password_hash=%s WHERE id=%s;",
                (new_hash, admin_id))
    conn.commit()
    cur.close()
    conn.close()
    return True


# ============================================================
# PHASE 2 — STUDENTS
# ============================================================
def create_student(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students
        (name, roll_no, class_name, section, gender, dob,
         parent_name, parent_phone, address, admission_date, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id;
    """, (
        data.get("name"), data.get("roll_no"), data.get("class_name"),
        data.get("section"), data.get("gender"), data.get("dob") or None,
        data.get("parent_name"), data.get("parent_phone"),
        data.get("address"), data.get("admission_date") or None,
        data.get("status") or "active"
    ))
    sid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return sid


def get_students(search=None, class_name=None, status="active"):
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT id, name, roll_no, class_name, section, parent_phone, status FROM students WHERE 1=1"
    params = []
    if status and status != "all":
        q += " AND status=%s"
        params.append(status)
    if search:
        q += " AND (name ILIKE %s OR roll_no ILIKE %s OR parent_phone ILIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]
    if class_name:
        q += " AND class_name=%s"
        params.append(class_name)
    q += " ORDER BY class_name, section, roll_no;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_student(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, roll_no, class_name, section, gender, dob,
               parent_name, parent_phone, address, admission_date, status, created_at
        FROM students WHERE id=%s;
    """, (student_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def update_student(student_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE students SET
            name=%s, roll_no=%s, class_name=%s, section=%s, gender=%s,
            dob=%s, parent_name=%s, parent_phone=%s, address=%s,
            admission_date=%s, status=%s
        WHERE id=%s RETURNING id;
    """, (
        data.get("name"), data.get("roll_no"), data.get("class_name"),
        data.get("section"), data.get("gender"), data.get("dob") or None,
        data.get("parent_name"), data.get("parent_phone"),
        data.get("address"), data.get("admission_date") or None,
        data.get("status") or "active", student_id
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_student(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=%s;", (student_id,))
    conn.commit()
    cur.close()
    conn.close()


def count_students():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students WHERE status='active';")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


def get_classes_list():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT class_name FROM students WHERE class_name IS NOT NULL ORDER BY class_name;")
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def get_students_full(class_name=None, section=None):
    """Full student records — used by ID cards, hall tickets"""
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, name, roll_no, class_name, section, gender, dob,
               parent_name, parent_phone, address, admission_date, status,
               photo_url
        FROM students WHERE status='active'
    """
    params = []
    if class_name:
        q += " AND class_name=%s"
        params.append(class_name)
    if section:
        q += " AND section=%s"
        params.append(section)
    q += " ORDER BY class_name, section, roll_no, name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    keys = ["id","name","roll_no","class_name","section","gender","dob",
            "parent_name","parent_phone","address","admission_date","status","photo_url"]
    return [dict(zip(keys, r)) for r in rows]


def update_student_photo_url(student_id, photo_url):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE students SET photo_url=%s WHERE id=%s RETURNING id;",
                (photo_url, student_id))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def get_students_without_photos(class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, name, roll_no, class_name, section
        FROM students
        WHERE status='active' AND (photo_url IS NULL OR photo_url = '')
    """
    params = []
    if class_name:
        q += " AND class_name=%s"
        params.append(class_name)
    q += " ORDER BY class_name, section, roll_no;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "roll": r[2],
             "class_name": r[3], "section": r[4]} for r in rows]


def count_students_with_photos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE photo_url IS NOT NULL AND photo_url != '') AS with_photo,
            COUNT(*) FILTER (WHERE photo_url IS NULL OR photo_url = '') AS without_photo,
            COUNT(*) AS total
        FROM students WHERE status='active';
    """)
    r = cur.fetchone()
    cur.close()
    conn.close()
    return {"with_photo": r[0] or 0, "without_photo": r[1] or 0,
            "total": r[2] or 0}


# ============================================================
# PHASE 3 — FEES
# ============================================================
def create_fee_structure(class_name, fee_type, amount, frequency):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fee_structure (class_name, fee_type, amount, frequency)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (class_name, fee_type, amount, frequency))
        fid = cur.fetchone()[0]
        conn.commit()
        return fid
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_fee_structures(class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    if class_name:
        cur.execute("""
            SELECT id, class_name, fee_type, amount, frequency
            FROM fee_structure WHERE class_name=%s ORDER BY fee_type;
        """, (class_name,))
    else:
        cur.execute("""
            SELECT id, class_name, fee_type, amount, frequency
            FROM fee_structure ORDER BY class_name, fee_type;
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def delete_fee_structure(fid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM fee_structure WHERE id=%s;", (fid,))
    conn.commit()
    cur.close()
    conn.close()


def generate_receipt_no():
    today = datetime.now().strftime("%Y%m%d")
    rand = _random.randint(1000, 9999)
    return f"RCPT-{today}-{rand}"


def create_fee_payment(student_id, fee_type, amount, month, mode, note, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    receipt_no = generate_receipt_no()
    for _ in range(5):
        cur.execute("SELECT 1 FROM fee_payments WHERE receipt_no=%s;", (receipt_no,))
        if not cur.fetchone():
            break
        receipt_no = generate_receipt_no()

    cur.execute("""
        INSERT INTO fee_payments
        (student_id, fee_type, amount, month, mode, receipt_no, note, recorded_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (student_id, fee_type, amount, month, mode, receipt_no, note, admin_id))
    pid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": pid, "receipt_no": receipt_no}


def get_payment(payment_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.student_id, p.fee_type, p.amount, p.month, p.mode,
               p.receipt_no, p.note, p.paid_at,
               s.name, s.roll_no, s.class_name, s.section, s.parent_name, s.parent_phone
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        WHERE p.id=%s;
    """, (payment_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_payments(student_id=None, month=None, limit=200):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT p.id, p.student_id, s.name, s.class_name, s.section,
               p.fee_type, p.amount, p.month, p.mode, p.receipt_no, p.paid_at
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        WHERE 1=1
    """
    params = []
    if student_id:
        q += " AND p.student_id=%s"
        params.append(student_id)
    if month:
        q += " AND p.month=%s"
        params.append(month)
    q += " ORDER BY p.paid_at DESC LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def delete_payment(payment_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM fee_payments WHERE id=%s;", (payment_id,))
    conn.commit()
    cur.close()
    conn.close()


def total_collected(month=None):
    conn = get_conn()
    cur = conn.cursor()
    if month:
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM fee_payments WHERE month=%s;", (month,))
    else:
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM fee_payments;")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


def pending_amount_for_student(student_id, month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT class_name FROM students WHERE id=%s;", (student_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        cur.close()
        conn.close()
        return 0
    class_name = row[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM fee_structure WHERE class_name=%s;",
                (class_name,))
    due = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM fee_payments WHERE student_id=%s AND month=%s;",
                (student_id, month))
    paid = cur.fetchone()[0]
    cur.close()
    conn.close()
    return max(due - paid, 0)


def get_defaulters(month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.name, s.roll_no, s.class_name, s.section, s.parent_phone,
               COALESCE(fs.total,0) AS due,
               COALESCE(fp.paid,0) AS paid
        FROM students s
        LEFT JOIN (
            SELECT class_name, SUM(amount) AS total
            FROM fee_structure GROUP BY class_name
        ) fs ON fs.class_name = s.class_name
        LEFT JOIN (
            SELECT student_id, SUM(amount) AS paid
            FROM fee_payments WHERE month=%s GROUP BY student_id
        ) fp ON fp.student_id = s.id
        WHERE s.status='active'
          AND COALESCE(fs.total,0) > COALESCE(fp.paid,0)
        ORDER BY s.class_name, s.section, s.roll_no;
    """, (month,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_receipts_for_bulk_print(month, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT p.id, p.receipt_no, p.paid_at, p.month, p.fee_type,
               p.amount, p.mode, p.note,
               s.name, s.roll_no, s.class_name, s.section,
               s.parent_name, s.parent_phone
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        WHERE p.month=%s
    """
    params = [month]
    if class_name:
        q += " AND s.class_name=%s"
        params.append(class_name)
    q += " ORDER BY s.class_name, s.section, s.roll_no, p.paid_at;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "receipt_no": r[1], "paid_at": r[2],
             "month": r[3], "fee_type": r[4], "amount": float(r[5] or 0),
             "mode": r[6], "note": r[7],
             "student_name": r[8], "roll": r[9],
             "class_name": r[10], "section": r[11],
             "parent_name": r[12], "parent_phone": r[13]} for r in rows]


def get_student_fee_dues(student_id):
    month = datetime.now().strftime("%Y-%m")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT class_name FROM students WHERE id=%s;", (student_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        cur.close()
        conn.close()
        return {"month": month, "due": 0, "paid": 0, "pending": 0}
    class_name = row[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM fee_structure WHERE class_name=%s;",
                (class_name,))
    due = float(cur.fetchone()[0] or 0)
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM fee_payments WHERE student_id=%s AND month=%s;",
                (student_id, month))
    paid = float(cur.fetchone()[0] or 0)
    cur.close()
    conn.close()
    return {"month": month, "due": due, "paid": paid,
            "pending": max(due - paid, 0)}


# ============================================================
# PHASE 4 — ATTENDANCE
# ============================================================
def get_attendance_for_date(class_name, section, date_str):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT s.id, s.name, s.roll_no, s.class_name, s.section, a.status
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.id AND a.date=%s
        WHERE s.status='active' AND s.class_name=%s
    """
    params = [date_str, class_name]
    if section:
        q += " AND s.section=%s"
        params.append(section)
    q += " ORDER BY s.roll_no, s.name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def mark_attendance(student_id, date_str, status, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attendance (student_id, date, status, marked_by)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (student_id, date)
        DO UPDATE SET status=%s, marked_by=%s, marked_at=NOW();
    """, (student_id, date_str, status, admin_id, status, admin_id))
    conn.commit()
    cur.close()
    conn.close()


def bulk_mark_attendance(class_name, section, date_str, status, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        INSERT INTO attendance (student_id, date, status, marked_by)
        SELECT id, %s, %s, %s FROM students
        WHERE status='active' AND class_name=%s
    """
    params = [date_str, status, admin_id, class_name]
    if section:
        q += " AND section=%s"
        params.append(section)
    q += """
        ON CONFLICT (student_id, date)
        DO UPDATE SET status=EXCLUDED.status, marked_by=EXCLUDED.marked_by,
                      marked_at=NOW();
    """
    cur.execute(q, tuple(params))
    conn.commit()
    cur.close()
    conn.close()


def get_attendance_summary(student_id, month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status='present') AS present,
            COUNT(*) FILTER (WHERE status='absent') AS absent,
            COUNT(*) FILTER (WHERE status='late') AS late,
            COUNT(*) FILTER (WHERE status='leave') AS leave,
            COUNT(*) AS total
        FROM attendance
        WHERE student_id=%s AND TO_CHAR(date, 'YYYY-MM')=%s;
    """, (student_id, month))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return {"present":0,"absent":0,"late":0,"leave":0,"total":0,"percent":0}
    present = row[0] or 0
    total = row[4] or 0
    percent = round(((present + (row[2] or 0) * 0.5) / total) * 100, 1) if total else 0
    return {"present": present, "absent": row[1] or 0,
            "late": row[2] or 0, "leave": row[3] or 0,
            "total": total, "percent": percent}


def get_attendance_calendar(student_id, month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, status FROM attendance
        WHERE student_id=%s AND TO_CHAR(date, 'YYYY-MM')=%s
        ORDER BY date;
    """, (student_id, month))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r[0].strftime("%Y-%m-%d"): r[1] for r in rows}


def class_attendance_today(class_name, section, date_str):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT
            COUNT(*) FILTER (WHERE a.status='present') AS present,
            COUNT(*) FILTER (WHERE a.status='absent') AS absent,
            COUNT(*) FILTER (WHERE a.status IS NULL) AS unmarked,
            COUNT(s.id) AS total
        FROM students s
        LEFT JOIN attendance a ON a.student_id=s.id AND a.date=%s
        WHERE s.status='active' AND s.class_name=%s
    """
    params = [date_str, class_name]
    if section:
        q += " AND s.section=%s"
        params.append(section)
    cur.execute(q, tuple(params))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {"present": row[0] or 0, "absent": row[1] or 0,
            "unmarked": row[2] or 0, "total": row[3] or 0}


def today_attendance_percent(date_str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FILTER (WHERE status='present'),
               COUNT(*) FILTER (WHERE status IN ('present','absent','late','leave'))
        FROM attendance WHERE date=%s;
    """, (date_str,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not row[1]:
        return None
    return round((row[0] / row[1]) * 100, 1)


# ============================================================
# PHASE 5 — EXAMS & MARKS
# ============================================================
def create_exam(name, class_name, exam_date, subjects, max_marks=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO exams (name, class_name, exam_date, subjects, max_marks)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """, (name, class_name, exam_date or None, subjects, max_marks))
    eid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return eid


def get_exams(class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    if class_name:
        cur.execute("""
            SELECT id, name, class_name, exam_date, subjects, max_marks
            FROM exams WHERE class_name=%s ORDER BY exam_date DESC NULLS LAST, id DESC;
        """, (class_name,))
    else:
        cur.execute("""
            SELECT id, name, class_name, exam_date, subjects, max_marks
            FROM exams ORDER BY exam_date DESC NULLS LAST, id DESC;
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_exam(exam_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, class_name, exam_date, subjects, max_marks
        FROM exams WHERE id=%s;
    """, (exam_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def delete_exam(exam_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM exams WHERE id=%s;", (exam_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_marks_grid(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        return None, [], []
    subjects = exam[4] or []
    class_name = exam[2]

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, roll_no, section
        FROM students
        WHERE status='active' AND class_name=%s
        ORDER BY section, roll_no, name;
    """, (class_name,))
    students = [{"id": r[0], "name": r[1], "roll": r[2], "section": r[3]}
                for r in cur.fetchall()]

    cur.execute("SELECT student_id, subject, obtained FROM marks WHERE exam_id=%s;", (exam_id,))
    marks = {}
    for r in cur.fetchall():
        marks.setdefault(r[0], {})[r[1]] = r[2]
    cur.close()
    conn.close()

    exam_dict = {"id": exam[0], "name": exam[1], "class_name": exam[2],
                 "exam_date": exam[3], "subjects": subjects, "max_marks": exam[5]}
    return exam_dict, students, marks


def save_mark(exam_id, student_id, subject, obtained):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO marks (exam_id, student_id, subject, obtained)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (exam_id, student_id, subject)
        DO UPDATE SET obtained=EXCLUDED.obtained;
    """, (exam_id, student_id, subject, obtained))
    conn.commit()
    cur.close()
    conn.close()


def get_student_marks_report(exam_id, student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT subject, obtained FROM marks WHERE exam_id=%s AND student_id=%s;",
                (exam_id, student_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r[0]: r[1] for r in rows}


def get_merit_list(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        return []
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.name, s.roll_no, s.section,
               COALESCE(SUM(m.obtained), 0) AS total,
               COUNT(m.id) AS subj_count
        FROM students s
        LEFT JOIN marks m ON m.student_id = s.id AND m.exam_id=%s
        WHERE s.status='active' AND s.class_name=%s
        GROUP BY s.id, s.name, s.roll_no, s.section
        ORDER BY total DESC, s.name;
    """, (exam_id, exam[2]))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_exam_stats(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        return None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE total >= %s * 0.33) AS passed,
            COUNT(*) FILTER (WHERE total < %s * 0.33) AS failed,
            COALESCE(AVG(total), 0) AS avg,
            COALESCE(MAX(total), 0) AS top
        FROM (
            SELECT student_id, SUM(obtained) AS total
            FROM marks WHERE exam_id=%s
            GROUP BY student_id
        ) t;
    """, (exam[5], exam[5], exam_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {"passed": row[0] or 0, "failed": row[1] or 0,
            "avg": round(float(row[2] or 0), 1), "top": row[3] or 0}


# ============================================================
# PHASE 6 — NOTICES
# ============================================================
def create_notice(data, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notices
        (title, content, category, priority, target_class, is_public, published, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """, (
        data["title"], data["content"],
        data.get("category") or "general",
        data.get("priority") or "normal",
        data.get("target_class") or None,
        data.get("is_public") == "on",
        data.get("published") == "on",
        admin_id
    ))
    nid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return nid


def get_notices(public_only=False, category=None, limit=100):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, title, content, category, priority, target_class,
               is_public, published, created_at
        FROM notices WHERE 1=1
    """
    params = []
    if public_only:
        q += " AND is_public=TRUE AND published=TRUE"
    if category:
        q += " AND category=%s"
        params.append(category)
    q += " ORDER BY priority DESC, created_at DESC LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_notice(notice_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, content, category, priority, target_class,
               is_public, published, created_at
        FROM notices WHERE id=%s;
    """, (notice_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def update_notice(notice_id, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE notices SET
            title=%s, content=%s, category=%s, priority=%s,
            target_class=%s, is_public=%s, published=%s, updated_at=NOW()
        WHERE id=%s RETURNING id;
    """, (
        data["title"], data["content"],
        data.get("category") or "general",
        data.get("priority") or "normal",
        data.get("target_class") or None,
        data.get("is_public") == "on",
        data.get("published") == "on",
        notice_id
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_notice(notice_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM notices WHERE id=%s;", (notice_id,))
    conn.commit()
    cur.close()
    conn.close()


def count_unread_notices(days=7):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM notices
        WHERE published=TRUE AND created_at > NOW() - INTERVAL '%s days';
    """, (days,))
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


def students_phone_list(class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT name, parent_phone, class_name, section
        FROM students
        WHERE status='active' AND parent_phone IS NOT NULL AND parent_phone != ''
    """
    params = []
    if class_name:
        q += " AND class_name=%s"
        params.append(class_name)
    q += " ORDER BY class_name, section, name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ============================================================
# PHASE 7 — PARENTS
# ============================================================
def create_parent(phone, password, name=""):
    conn = get_conn()
    cur = conn.cursor()
    pwd_hash = generate_password_hash(password)
    try:
        cur.execute(
            "INSERT INTO parents (phone, password_hash, name) VALUES (%s, %s, %s) RETURNING id;",
            (phone, pwd_hash, name)
        )
        pid = cur.fetchone()[0]
        conn.commit()
        return pid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_parent_by_phone(phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, phone, password_hash, name FROM parents WHERE phone=%s;", (phone,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def verify_parent(phone, password):
    row = get_parent_by_phone(phone)
    if not row:
        return None
    if check_password_hash(row[2], password):
        return {"id": row[0], "phone": row[1], "name": row[3]}
    return None


def phone_exists_in_students(phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM students WHERE parent_phone=%s LIMIT 1;", (phone,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def get_children_for_parent(phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, roll_no, class_name, section
        FROM students
        WHERE parent_phone=%s AND status='active'
        ORDER BY name;
    """, (phone,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "roll": r[2],
             "class_name": r[3], "section": r[4]} for r in rows]


def get_exams_for_class(class_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, exam_date, subjects, max_marks
        FROM exams WHERE class_name=%s
        ORDER BY exam_date DESC NULLS LAST, id DESC;
    """, (class_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "exam_date": r[2],
             "subjects": r[3] or [], "max_marks": r[4]} for r in rows]


def get_notices_for_class(class_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, content, category, priority, target_class, created_at
        FROM notices
        WHERE published=TRUE
          AND (is_public=TRUE OR target_class=%s OR target_class IS NULL)
        ORDER BY priority DESC, created_at DESC LIMIT 50;
    """, (class_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "category": r[3],
             "priority": r[4], "target_class": r[5], "created_at": r[6]}
            for r in rows]


def get_parent_info(parent_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, phone, name FROM parents WHERE id=%s;", (parent_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "phone": row[1], "name": row[2] or row[1]}


# ============================================================
# PHASE 8 — SETTINGS & DASHBOARD CHARTS
# ============================================================
def get_settings():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, school_name, tagline, address, phone, email, logo_url
        FROM settings WHERE id=1;
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return {"school_name": "My School", "tagline": "",
                "address": "", "phone": "", "email": "", "logo_url": ""}
    return {"school_name": row[1] or "My School", "tagline": row[2] or "",
            "address": row[3] or "", "phone": row[4] or "",
            "email": row[5] or "", "logo_url": row[6] or ""}


def update_settings(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE settings SET
            school_name=%s, tagline=%s, address=%s,
            phone=%s, email=%s, logo_url=%s, updated_at=NOW()
        WHERE id=1;
    """, (
        data.get("school_name") or "My School",
        data.get("tagline") or "",
        data.get("address") or "",
        data.get("phone") or "",
        data.get("email") or "",
        data.get("logo_url") or ""
    ))
    conn.commit()
    cur.close()
    conn.close()


def get_fees_monthly_trend(months=6):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT month, SUM(amount) AS total
        FROM fee_payments
        WHERE month IS NOT NULL AND month != ''
        GROUP BY month ORDER BY month DESC LIMIT %s;
    """, (months,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    rows = list(reversed(rows))
    return [{"label": r[0], "value": float(r[1] or 0)} for r in rows]


def get_attendance_trend(days=7):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT date,
               COUNT(*) FILTER (WHERE status='present') AS present,
               COUNT(*) FILTER (WHERE status IN ('present','absent','late','leave')) AS total
        FROM attendance
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY date ORDER BY date;
    """, (days,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    out = []
    for r in rows:
        total = r[2] or 0
        pct = round((r[1] / total) * 100, 1) if total else 0
        out.append({"label": r[0].strftime("%d %b"), "value": pct})
    return out


def get_students_by_class():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(class_name, 'Unassigned') AS c, COUNT(*) AS n
        FROM students WHERE status='active'
        GROUP BY class_name ORDER BY class_name NULLS LAST;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"label": r[0], "value": r[1]} for r in rows]


def get_fees_summary():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0), COUNT(*) FROM fee_payments;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {"total": float(row[0] or 0), "payments": row[1] or 0}


# ============================================================
# PHASE 9 — REPORTS
# ============================================================
def get_fee_report(start_date, end_date, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT p.id, p.receipt_no, p.paid_at, p.month, p.fee_type,
               p.amount, p.mode,
               s.name, s.roll_no, s.class_name, s.section
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        WHERE DATE(p.paid_at) BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    if class_name:
        q += " AND s.class_name=%s"
        params.append(class_name)
    q += " ORDER BY p.paid_at DESC;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "receipt_no": r[1], "paid_at": r[2],
             "month": r[3], "fee_type": r[4], "amount": float(r[5] or 0),
             "mode": r[6], "student_name": r[7], "roll": r[8],
             "class_name": r[9], "section": r[10]} for r in rows]


def get_fee_report_summary(start_date, end_date, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT COALESCE(SUM(p.amount),0), COUNT(p.id)
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        WHERE DATE(p.paid_at) BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    if class_name:
        q += " AND s.class_name=%s"
        params.append(class_name)
    cur.execute(q, tuple(params))
    row = cur.fetchone()
    total = float(row[0] or 0)
    count = row[1] or 0

    q2 = """
        SELECT p.mode, COALESCE(SUM(p.amount),0)
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        WHERE DATE(p.paid_at) BETWEEN %s AND %s
    """
    p2 = [start_date, end_date]
    if class_name:
        q2 += " AND s.class_name=%s"
        p2.append(class_name)
    q2 += " GROUP BY p.mode ORDER BY 2 DESC;"
    cur.execute(q2, tuple(p2))
    modes = [{"mode": r[0], "amount": float(r[1] or 0)} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return {"total": total, "count": count, "modes": modes}


def get_attendance_report(month, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT s.id, s.name, s.roll_no, s.class_name, s.section,
            COUNT(a.id) FILTER (WHERE a.status='present') AS present,
            COUNT(a.id) FILTER (WHERE a.status='absent') AS absent,
            COUNT(a.id) FILTER (WHERE a.status='late') AS late,
            COUNT(a.id) FILTER (WHERE a.status='leave') AS leave,
            COUNT(a.id) AS total
        FROM students s
        LEFT JOIN attendance a
            ON a.student_id = s.id
            AND TO_CHAR(a.date, 'YYYY-MM') = %s
        WHERE s.status='active'
    """
    params = [month]
    if class_name:
        q += " AND s.class_name=%s"
        params.append(class_name)
    q += " GROUP BY s.id, s.name, s.roll_no, s.class_name, s.section"
    q += " ORDER BY s.class_name, s.section, s.roll_no;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    out = []
    for r in rows:
        present = r[5] or 0
        late = r[7] or 0
        total = r[9] or 0
        pct = round(((present + late * 0.5) / total) * 100, 1) if total else 0
        out.append({"id": r[0], "name": r[1], "roll": r[2],
                    "class_name": r[3], "section": r[4],
                    "present": present, "absent": r[6] or 0,
                    "late": late, "leave": r[8] or 0,
                    "total": total, "percent": pct})
    return out


# ============================================================
# PHASE 13 — BULK IMPORT
# ============================================================
def check_roll_no_exists(roll_no):
    if not roll_no:
        return False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM students WHERE roll_no=%s LIMIT 1;", (roll_no,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def get_existing_roll_nos(roll_nos):
    if not roll_nos:
        return set()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT roll_no FROM students WHERE roll_no = ANY(%s);", (roll_nos,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r[0] for r in rows}


def bulk_create_students(rows):
    if not rows:
        return 0, []
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    failed = []
    for idx, r in enumerate(rows):
        try:
            cur.execute("""
                INSERT INTO students
                (name, roll_no, class_name, section, gender, dob,
                 parent_name, parent_phone, address, admission_date, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """, (
                r["name"], r.get("roll_no") or None,
                r.get("class_name") or None, r.get("section") or None,
                r.get("gender") or None, r.get("dob") or None,
                r.get("parent_name") or None, r.get("parent_phone") or None,
                r.get("address") or None, r.get("admission_date") or None,
                "active"
            ))
            inserted += 1
        except Exception as e:
            failed.append({"row": idx + 1, "name": r.get("name", "?"),
                           "error": str(e)[:120]})
    conn.commit()
    cur.close()
    conn.close()
    return inserted, failed


def check_duplicate_student(name, roll_no, parent_phone, exclude_id=None):
    conn = get_conn()
    cur = conn.cursor()
    conds = []
    params = []
    if roll_no:
        conds.append("roll_no=%s")
        params.append(roll_no)
    if parent_phone:
        conds.append("parent_phone=%s")
        params.append(parent_phone)
    if name:
        conds.append("LOWER(name)=LOWER(%s)")
        params.append(name.strip())
    if not conds:
        cur.close()
        conn.close()
        return []
    q = f"SELECT id, name, roll_no, class_name, section, parent_phone FROM students WHERE ({' OR '.join(conds)})"
    if exclude_id:
        q += " AND id != %s"
        params.append(exclude_id)
    q += " LIMIT 10;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "roll": r[2],
             "class_name": r[3], "section": r[4],
             "parent_phone": r[5]} for r in rows]


# ============================================================
# PHASE 14 — WHATSAPP
# ============================================================
def get_whatsapp_templates(category=None):
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT id, name, category, body, created_at FROM whatsapp_templates"
    params = []
    if category:
        q += " WHERE category=%s"
        params.append(category)
    q += " ORDER BY category, name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "category": r[2],
             "body": r[3], "created_at": r[4]} for r in rows]


def get_whatsapp_template(tid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, category, body FROM whatsapp_templates WHERE id=%s;", (tid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "category": row[2], "body": row[3]}


def create_whatsapp_template(name, category, body):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO whatsapp_templates (name, category, body)
        VALUES (%s, %s, %s) RETURNING id;
    """, (name, category, body))
    tid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return tid


def update_whatsapp_template(tid, name, category, body):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE whatsapp_templates SET name=%s, category=%s, body=%s
        WHERE id=%s RETURNING id;
    """, (name, category, body, tid))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_whatsapp_template(tid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM whatsapp_templates WHERE id=%s;", (tid,))
    conn.commit()
    cur.close()
    conn.close()


def log_whatsapp(student_id, template_id, phone, message, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO whatsapp_logs (student_id, template_id, phone, message, sent_by)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """, (student_id, template_id, phone, message, admin_id))
    lid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return lid


def get_recent_whatsapp_logs(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT wl.id, wl.sent_at, wl.phone, s.name, s.class_name,
               wt.name AS template_name
        FROM whatsapp_logs wl
        LEFT JOIN students s ON s.id = wl.student_id
        LEFT JOIN whatsapp_templates wt ON wt.id = wl.template_id
        ORDER BY wl.sent_at DESC LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "sent_at": r[1], "phone": r[2],
             "student_name": r[3], "class_name": r[4],
             "template_name": r[5]} for r in rows]


def was_sent_recently(student_id, template_id, days=7):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT sent_at FROM whatsapp_logs
        WHERE student_id=%s AND template_id=%s
          AND sent_at > NOW() - INTERVAL '%s days'
        ORDER BY sent_at DESC LIMIT 1;
    """, (student_id, template_id, days))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def get_students_for_reminder(month, min_att_percent=None, only_defaulters=False, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT s.id, s.name, s.roll_no, s.class_name, s.section, s.parent_name, s.parent_phone,
            COALESCE(fs.total,0) AS fee_due,
            COALESCE(fp.paid,0) AS fee_paid,
            COALESCE(att.att_pct, NULL) AS att_pct
        FROM students s
        LEFT JOIN (
            SELECT class_name, SUM(amount) AS total FROM fee_structure GROUP BY class_name
        ) fs ON fs.class_name = s.class_name
        LEFT JOIN (
            SELECT student_id, SUM(amount) AS paid FROM fee_payments WHERE month=%s GROUP BY student_id
        ) fp ON fp.student_id = s.id
        LEFT JOIN (
            SELECT student_id,
                   ROUND((COUNT(*) FILTER (WHERE status='present') * 100.0 /
                          NULLIF(COUNT(*),0))::numeric, 1) AS att_pct
            FROM attendance
            WHERE TO_CHAR(date, 'YYYY-MM') = %s
            GROUP BY student_id
        ) att ON att.student_id = s.id
        WHERE s.status='active' AND s.parent_phone IS NOT NULL AND s.parent_phone != ''
    """
    params = [month, month]
    if class_name:
        q += " AND s.class_name=%s"
        params.append(class_name)
    if only_defaulters:
        q += " AND COALESCE(fs.total,0) > COALESCE(fp.paid,0)"
    q += " ORDER BY s.class_name, s.section, s.roll_no;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    out = []
    for r in rows:
        due = float(r[7] or 0)
        paid = float(r[8] or 0)
        pending = max(due - paid, 0)
        att = float(r[9]) if r[9] is not None else None
        if min_att_percent is not None:
            if att is None or att >= min_att_percent:
                continue
        out.append({"id": r[0], "name": r[1], "roll": r[2],
                    "class_name": r[3], "section": r[4],
                    "parent_name": r[5], "phone": r[6],
                    "pending_fees": pending, "attendance_pct": att})
    return out


# ============================================================
# PHASE 15 — BACKUP
# ============================================================
def backup_all_tables():
    conn = get_conn()
    cur = conn.cursor()
    result = {"backup_at": datetime.now().isoformat(), "tables": {}}
    for table in BACKUP_TABLES:
        try:
            cur.execute(f"SELECT * FROM {table};")
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            result["tables"][table] = {
                "columns": cols,
                "rows": [{c: _json_safe(v) for c, v in zip(cols, row)}
                         for row in rows],
                "count": len(rows)
            }
        except Exception as e:
            result["tables"][table] = {"error": str(e), "rows": [], "count": 0}
    cur.close()
    conn.close()
    return result


def restore_table(table, rows):
    if table not in BACKUP_TABLES:
        return 0, [f"Table '{table}' not allowed"]
    if not rows:
        return 0, []
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    errors = []
    for idx, row in enumerate(rows):
        cols = list(row.keys())
        placeholders = ",".join(["%s"] * len(cols))
        col_names = ",".join([f'"{c}"' for c in cols])
        try:
            cur.execute(
                f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})',
                [row[c] for c in cols]
            )
            inserted += 1
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)[:150]})
    conn.commit()
    cur.close()
    conn.close()
    try:
        _reset_sequence(table)
    except Exception:
        pass
    return inserted, errors


def _reset_sequence(table):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table}), 1),
                true
            );
        """)
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def count_all_rows():
    conn = get_conn()
    cur = conn.cursor()
    result = {}
    for table in BACKUP_TABLES:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            result[table] = cur.fetchone()[0]
        except Exception:
            result[table] = "?"
    cur.close()
    conn.close()
    return result


# ============================================================
# PHASE 16 — BILLS
# ============================================================
def generate_bills_for_class(class_name, month, section=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT fee_type, amount FROM fee_structure
        WHERE class_name=%s ORDER BY fee_type;
    """, (class_name,))
    items = [{"fee_type": r[0], "amount": float(r[1])} for r in cur.fetchall()]
    if not items:
        cur.close()
        conn.close()
        return {"created": 0, "skipped": 0, "error": "Fee structure nahi hai"}

    base_total = sum(item["amount"] for item in items)
    items_json = _json.dumps(items)

    q = "SELECT id FROM students WHERE status='active' AND class_name=%s"
    params = [class_name]
    if section:
        q += " AND section=%s"
        params.append(section)
    cur.execute(q, tuple(params))
    student_ids = [r[0] for r in cur.fetchall()]

    created = 0
    skipped = 0
    total_discounted = 0.0
    for sid in student_ids:
        try:
            discount_amount, discount_items = compute_student_discount(base_total, sid)
            final_total = max(base_total - discount_amount, 0)
            disc_json = _json.dumps(discount_items)
            cur.execute("""
                INSERT INTO bills
                (student_id, month, total_amount, base_amount,
                 discount_amount, discount_items, items, status)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, 'pending');
            """, (sid, month, final_total, base_total,
                  discount_amount, disc_json, items_json))
            created += 1
            total_discounted += discount_amount
        except Exception:
            skipped += 1
            conn.rollback()
            continue
    conn.commit()
    cur.close()
    conn.close()
    return {"created": created, "skipped": skipped, "error": None,
            "total_students": len(student_ids), "total_amount": base_total,
            "total_discounted": total_discounted}


def get_bills(month, status=None, class_name=None, search=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT b.id, b.student_id, b.month, b.total_amount, b.status, b.generated_at,
               s.name, s.roll_no, s.class_name, s.section, s.parent_name, s.parent_phone,
               COALESCE(p.paid, 0) AS paid_amount
        FROM bills b
        JOIN students s ON s.id = b.student_id
        LEFT JOIN (
            SELECT student_id, SUM(amount) AS paid
            FROM fee_payments WHERE month=%s GROUP BY student_id
        ) p ON p.student_id = b.student_id
        WHERE b.month=%s
    """
    params = [month, month]
    if class_name:
        q += " AND s.class_name=%s"
        params.append(class_name)
    if search:
        q += " AND (s.name ILIKE %s OR s.roll_no ILIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    q += " ORDER BY s.class_name, s.section, s.roll_no, s.name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    out = []
    for r in rows:
        total = float(r[3] or 0)
        paid = float(r[12] or 0)
        pending = max(total - paid, 0)
        if paid >= total and total > 0:
            cstatus = "paid"
        elif paid > 0:
            cstatus = "partial"
        else:
            cstatus = "pending"
        if status and status != cstatus:
            continue
        out.append({"id": r[0], "student_id": r[1], "month": r[2],
                    "total": total, "status": cstatus,
                    "generated_at": r[5], "student_name": r[6],
                    "roll": r[7], "class_name": r[8], "section": r[9],
                    "parent_name": r[10], "phone": r[11],
                    "paid": paid, "pending": pending})
    return out


def get_bill(bill_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.student_id, b.month, b.total_amount,
               b.base_amount, b.discount_amount, b.discount_items,
               b.items, b.generated_at,
               s.name, s.roll_no, s.class_name, s.section,
               s.parent_name, s.parent_phone, s.address,
               COALESCE((SELECT SUM(amount) FROM fee_payments
                         WHERE student_id=b.student_id AND month=b.month), 0) AS paid
        FROM bills b
        JOIN students s ON s.id = b.student_id
        WHERE b.id=%s;
    """, (bill_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    items = row[7]
    if isinstance(items, str):
        items = _json.loads(items)
    discount_items = row[6]
    if isinstance(discount_items, str):
        discount_items = _json.loads(discount_items)
    return {"id": row[0], "student_id": row[1], "month": row[2],
            "total": float(row[3] or 0), "base": float(row[4] or 0),
            "discount": float(row[5] or 0), "discount_items": discount_items or [],
            "items": items or [],
            "generated_at": row[8], "student_name": row[9], "roll": row[10],
            "class_name": row[11], "section": row[12],
            "parent_name": row[13], "phone": row[14], "address": row[15],
            "paid": float(row[16] or 0)}


def delete_bills_for_month(month, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    if class_name:
        cur.execute("""
            DELETE FROM bills WHERE month=%s
            AND student_id IN (SELECT id FROM students WHERE class_name=%s);
        """, (month, class_name))
    else:
        cur.execute("DELETE FROM bills WHERE month=%s;", (month,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted


def get_bills_summary(month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(b.total_amount), 0)
        FROM bills b WHERE b.month=%s;
    """, (month,))
    row = cur.fetchone()
    total_bills = row[0] or 0
    total_amount = float(row[1] or 0)
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM fee_payments WHERE month=%s;", (month,))
    collected = float(cur.fetchone()[0] or 0)
    cur.close()
    conn.close()
    return {"total_bills": total_bills, "total_amount": total_amount,
            "collected": collected,
            "pending": max(total_amount - collected, 0)}


def check_bills_exist(month, class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    if class_name:
        cur.execute("""
            SELECT COUNT(*) FROM bills b
            JOIN students s ON s.id=b.student_id
            WHERE b.month=%s AND s.class_name=%s;
        """, (month, class_name))
    else:
        cur.execute("SELECT COUNT(*) FROM bills WHERE month=%s;", (month,))
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


# ============================================================
# PHASE 18 — TIMETABLE
# ============================================================
def get_timetable_grid(class_name, section=''):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.day_of_week, t.period_no, t.subject, t.staff_id, s.name
        FROM timetable t
        LEFT JOIN staff s ON s.id = t.staff_id
        WHERE t.class_name=%s AND t.section=%s;
    """, (class_name, section or ''))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    grid = {}
    for r in rows:
        grid[(r[0], r[1])] = {"subject": r[2], "staff_id": r[3], "staff_name": r[4]}
    return grid


def save_timetable_cell(class_name, section, day, period, subject, staff_id):
    conn = get_conn()
    cur = conn.cursor()
    section = section or ''
    subject = (subject or '').strip()
    if not subject:
        cur.execute("""
            DELETE FROM timetable
            WHERE class_name=%s AND section=%s AND day_of_week=%s AND period_no=%s;
        """, (class_name, section, day, period))
    else:
        cur.execute("""
            INSERT INTO timetable (class_name, section, day_of_week, period_no, subject, staff_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (class_name, section, day_of_week, period_no)
            DO UPDATE SET subject=EXCLUDED.subject,
                          staff_id=EXCLUDED.staff_id,
                          updated_at=NOW();
        """, (class_name, section, day, period, subject, staff_id or None))
    conn.commit()
    cur.close()
    conn.close()


def get_teacher_timetable(staff_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT day_of_week, period_no, class_name, section, subject
        FROM timetable WHERE staff_id=%s ORDER BY day_of_week, period_no;
    """, (staff_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ============================================================
# PHASE 19 — SALARY
# ============================================================
def _gen_slip_no():
    today = datetime.now().strftime("%Y%m%d")
    return f"SAL-{today}-{_random.randint(1000, 9999)}"


def generate_salary_for_month(month, staff_ids=None):
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT id, salary FROM staff WHERE status='active' AND salary IS NOT NULL AND salary > 0"
    params = []
    if staff_ids:
        q += " AND id = ANY(%s)"
        params.append(staff_ids)
    cur.execute(q, tuple(params))
    staff_rows = cur.fetchall()

    created = 0
    skipped = 0
    advance_deducted_total = 0

    for sid, base in staff_rows:
        try:
            advance = get_active_advance(sid, month)
            advance_deduction = 0
            advance_note = ""
            if advance:
                advance_deduction = min(advance["monthly"], advance["remaining"])
                advance_note = f"Advance EMI: ₹{advance_deduction:.0f} (Adv #{advance['id']})"
                advance_deducted_total += advance_deduction

            base_f = float(base)
            net = base_f - advance_deduction

            cur.execute("""
                INSERT INTO salary_records
                (staff_id, month, base_salary, bonus, deductions,
                 net_amount, status, note)
                VALUES (%s, %s, %s, 0, %s, %s, 'pending', %s);
            """, (sid, month, base_f, advance_deduction, net,
                  advance_note or None))
            created += 1
        except Exception:
            skipped += 1
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    return {"created": created, "skipped": skipped,
            "total_staff": len(staff_rows),
            "advance_deducted": advance_deducted_total}


def get_salary_records(month, status=None, search=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT sr.id, sr.staff_id, sr.month, sr.base_salary, sr.bonus,
               sr.deductions, sr.net_amount, sr.status, sr.paid_at,
               sr.mode, sr.slip_no,
               s.name, s.role, s.phone
        FROM salary_records sr
        JOIN staff s ON s.id = sr.staff_id
        WHERE sr.month=%s
    """
    params = [month]
    if status:
        q += " AND sr.status=%s"
        params.append(status)
    if search:
        q += " AND s.name ILIKE %s"
        params.append(f"%{search}%")
    q += " ORDER BY s.role, s.name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "staff_id": r[1], "month": r[2],
             "base": float(r[3] or 0), "bonus": float(r[4] or 0),
             "deductions": float(r[5] or 0), "net": float(r[6] or 0),
             "status": r[7], "paid_at": r[8], "mode": r[9], "slip_no": r[10],
             "name": r[11], "role": r[12], "phone": r[13]} for r in rows]


def get_salary_record(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT sr.id, sr.staff_id, sr.month, sr.base_salary, sr.bonus,
               sr.deductions, sr.net_amount, sr.status, sr.paid_at,
               sr.mode, sr.note, sr.slip_no, sr.created_at,
               s.name, s.role, s.phone, s.email, s.qualification
        FROM salary_records sr
        JOIN staff s ON s.id = sr.staff_id
        WHERE sr.id=%s;
    """, (rid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","staff_id","month","base","bonus","deductions","net",
            "status","paid_at","mode","note","slip_no","created_at",
            "name","role","phone","email","qualification"]
    d = dict(zip(keys, row))
    for k in ["base","bonus","deductions","net"]:
        d[k] = float(d[k] or 0)
    return d


def update_salary_adjustments(rid, bonus, deductions):
    bonus = float(bonus or 0)
    deductions = float(deductions or 0)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE salary_records SET
            bonus=%s, deductions=%s,
            net_amount = base_salary + %s - %s
        WHERE id=%s AND status='pending' RETURNING id;
    """, (bonus, deductions, bonus, deductions, rid))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def mark_salary_paid(rid, mode, note, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    slip_no = _gen_slip_no()
    for _ in range(5):
        cur.execute("SELECT 1 FROM salary_records WHERE slip_no=%s;", (slip_no,))
        if not cur.fetchone():
            break
        slip_no = _gen_slip_no()

    cur.execute("""
        UPDATE salary_records SET
            status='paid', paid_at=NOW(), mode=%s, note=%s,
            slip_no=%s, recorded_by=%s
        WHERE id=%s AND status='pending'
        RETURNING slip_no, staff_id, month, deductions, note;
    """, (mode, note or "", slip_no, admin_id, rid))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not res:
        return None

    salary_staff_id = res[1]
    salary_month = res[2]
    salary_deductions = float(res[3] or 0)
    salary_note = res[4] or ""

    if salary_deductions > 0 and "Advance EMI" in salary_note:
        adv = get_active_advance(salary_staff_id, salary_month)
        if adv:
            record_advance_repayment(adv["id"], salary_month,
                                      salary_deductions, rid)

    return res[0]


def delete_salary_record(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM salary_records WHERE id=%s AND status='pending';", (rid,))
    n = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return n


def get_salary_summary(month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status='paid') AS paid_count,
            COUNT(*) FILTER (WHERE status='pending') AS pending_count,
            COALESCE(SUM(net_amount) FILTER (WHERE status='paid'),0) AS paid_amt,
            COALESCE(SUM(net_amount) FILTER (WHERE status='pending'),0) AS pending_amt
        FROM salary_records WHERE month=%s;
    """, (month,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    return {"total": r[0] or 0, "paid_count": r[1] or 0,
            "pending_count": r[2] or 0,
            "paid_amount": float(r[3] or 0),
            "pending_amount": float(r[4] or 0)}


def get_staff_salary_history(staff_id, limit=12):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, month, net_amount, status, paid_at, slip_no
        FROM salary_records WHERE staff_id=%s
        ORDER BY month DESC LIMIT %s;
    """, (staff_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "month": r[1], "net": float(r[2] or 0),
             "status": r[3], "paid_at": r[4], "slip_no": r[5]} for r in rows]


# ============================================================
# PHASE 20 — HOMEWORK
# ============================================================
def create_homework(data, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO homework
        (class_name, section, subject, title, description, due_date,
         attachment_url, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        data["class_name"], data.get("section") or '',
        data["subject"], data["title"],
        data.get("description") or None,
        data.get("due_date") or None,
        data.get("attachment_url") or None,
        admin_id
    ))
    hid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return hid


def get_homework_list(class_name=None, section=None, subject=None, search=None, limit=100):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, class_name, section, subject, title, description,
               due_date, attachment_url, created_at
        FROM homework WHERE 1=1
    """
    params = []
    if class_name:
        q += " AND class_name=%s"
        params.append(class_name)
    if section is not None and section != '':
        q += " AND (section=%s OR section='')"
        params.append(section)
    if subject:
        q += " AND subject ILIKE %s"
        params.append(f"%{subject}%")
    if search:
        q += " AND (title ILIKE %s OR description ILIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    q += " ORDER BY COALESCE(due_date, created_at::date) DESC, created_at DESC LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "class_name": r[1], "section": r[2] or '',
             "subject": r[3], "title": r[4], "description": r[5],
             "due_date": r[6], "attachment_url": r[7],
             "created_at": r[8]} for r in rows]


def get_homework(hid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, class_name, section, subject, title, description,
               due_date, attachment_url, created_at, updated_at
        FROM homework WHERE id=%s;
    """, (hid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","class_name","section","subject","title","description",
            "due_date","attachment_url","created_at","updated_at"]
    return dict(zip(keys, row))


def update_homework(hid, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE homework SET
            class_name=%s, section=%s, subject=%s, title=%s,
            description=%s, due_date=%s, attachment_url=%s, updated_at=NOW()
        WHERE id=%s RETURNING id;
    """, (
        data["class_name"], data.get("section") or '',
        data["subject"], data["title"],
        data.get("description") or None,
        data.get("due_date") or None,
        data.get("attachment_url") or None,
        hid
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_homework(hid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM homework WHERE id=%s;", (hid,))
    conn.commit()
    cur.close()
    conn.close()


def get_homework_for_class(class_name, section='', limit=20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, subject, title, description, due_date,
               attachment_url, created_at
        FROM homework
        WHERE class_name=%s AND (section=%s OR section='')
        ORDER BY COALESCE(due_date, created_at::date) DESC, created_at DESC
        LIMIT %s;
    """, (class_name, section or '', limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "subject": r[1], "title": r[2], "description": r[3],
             "due_date": r[4], "attachment_url": r[5],
             "created_at": r[6]} for r in rows]


def count_homework_this_week():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM homework WHERE created_at > NOW() - INTERVAL '7 days';")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


# ============================================================
# PHASE 21 — TRANSPORT
# ============================================================
def create_bus_route(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bus_routes
        (name, driver_name, driver_phone, vehicle_no, capacity, fee_per_month, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        data["name"], data.get("driver_name") or None,
        data.get("driver_phone") or None, data.get("vehicle_no") or None,
        int(data.get("capacity") or 40),
        float(data.get("fee_per_month") or 0),
        data.get("status") or "active"
    ))
    rid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return rid


def get_bus_routes(search=None, status=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT r.id, r.name, r.driver_name, r.driver_phone, r.vehicle_no,
               r.capacity, r.fee_per_month, r.status,
               (SELECT COUNT(*) FROM bus_stops WHERE route_id=r.id) AS stop_count,
               (SELECT COUNT(*) FROM student_transport
                WHERE route_id=r.id AND status='active') AS student_count
        FROM bus_routes r WHERE 1=1
    """
    params = []
    if search:
        q += " AND (r.name ILIKE %s OR r.vehicle_no ILIKE %s OR r.driver_name ILIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]
    if status:
        q += " AND r.status=%s"
        params.append(status)
    q += " ORDER BY r.name;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "name": r[1], "driver_name": r[2], "driver_phone": r[3],
             "vehicle_no": r[4], "capacity": r[5], "fee_per_month": float(r[6] or 0),
             "status": r[7], "stop_count": r[8], "student_count": r[9]} for r in rows]


def get_bus_route(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, driver_name, driver_phone, vehicle_no,
               capacity, fee_per_month, status, created_at
        FROM bus_routes WHERE id=%s;
    """, (rid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","name","driver_name","driver_phone","vehicle_no",
            "capacity","fee_per_month","status","created_at"]
    d = dict(zip(keys, row))
    d["fee_per_month"] = float(d["fee_per_month"] or 0)
    return d


def update_bus_route(rid, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE bus_routes SET
            name=%s, driver_name=%s, driver_phone=%s, vehicle_no=%s,
            capacity=%s, fee_per_month=%s, status=%s
        WHERE id=%s RETURNING id;
    """, (
        data["name"], data.get("driver_name") or None,
        data.get("driver_phone") or None, data.get("vehicle_no") or None,
        int(data.get("capacity") or 40),
        float(data.get("fee_per_month") or 0),
        data.get("status") or "active", rid
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_bus_route(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM bus_routes WHERE id=%s;", (rid,))
    conn.commit()
    cur.close()
    conn.close()


def get_bus_stops(route_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, route_id, name, pickup_time, drop_time, sequence
        FROM bus_stops WHERE route_id=%s ORDER BY sequence, name;
    """, (route_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "route_id": r[1], "name": r[2],
             "pickup_time": r[3], "drop_time": r[4], "sequence": r[5]}
            for r in rows]


def get_bus_stop(sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, route_id, name, pickup_time, drop_time, sequence
        FROM bus_stops WHERE id=%s;
    """, (sid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "route_id": row[1], "name": row[2],
            "pickup_time": row[3], "drop_time": row[4], "sequence": row[5]}


def create_bus_stop(route_id, name, pickup_time, drop_time, sequence):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bus_stops (route_id, name, pickup_time, drop_time, sequence)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """, (route_id, name, pickup_time or None, drop_time or None, sequence or 1))
    sid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return sid


def update_bus_stop(sid, name, pickup_time, drop_time, sequence):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE bus_stops SET name=%s, pickup_time=%s, drop_time=%s, sequence=%s
        WHERE id=%s RETURNING id;
    """, (name, pickup_time or None, drop_time or None, sequence or 1, sid))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_bus_stop(sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM bus_stops WHERE id=%s;", (sid,))
    conn.commit()
    cur.close()
    conn.close()


def assign_student_transport(student_id, route_id, stop_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_transport (student_id, route_id, stop_id, status)
        VALUES (%s, %s, %s, 'active')
        ON CONFLICT (student_id) DO UPDATE SET
            route_id=EXCLUDED.route_id, stop_id=EXCLUDED.stop_id,
            status='active';
    """, (student_id, route_id, stop_id or None))
    conn.commit()
    cur.close()
    conn.close()


def remove_student_transport(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM student_transport WHERE student_id=%s;", (student_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_students_on_route(route_id, search=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT st.id, st.student_id, st.stop_id, st.status,
               s.name, s.roll_no, s.class_name, s.section, s.parent_phone,
               bs.name AS stop_name, bs.pickup_time, bs.drop_time
        FROM student_transport st
        JOIN students s ON s.id = st.student_id
        LEFT JOIN bus_stops bs ON bs.id = st.stop_id
        WHERE st.route_id=%s
    """
    params = [route_id]
    if search:
        q += " AND (s.name ILIKE %s OR s.roll_no ILIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    q += " ORDER BY bs.sequence NULLS LAST, s.class_name, s.section, s.roll_no;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "student_id": r[1], "stop_id": r[2], "status": r[3],
             "name": r[4], "roll": r[5], "class_name": r[6], "section": r[7],
             "phone": r[8], "stop_name": r[9],
             "pickup_time": r[10], "drop_time": r[11]} for r in rows]


def get_student_transport(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT st.id, st.route_id, st.stop_id,
               r.name AS route_name, r.driver_name, r.driver_phone, r.vehicle_no,
               bs.name AS stop_name, bs.pickup_time, bs.drop_time
        FROM student_transport st
        LEFT JOIN bus_routes r ON r.id = st.route_id
        LEFT JOIN bus_stops bs ON bs.id = st.stop_id
        WHERE st.student_id=%s AND st.status='active';
    """, (student_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "route_id": row[1], "stop_id": row[2],
            "route_name": row[3], "driver_name": row[4],
            "driver_phone": row[5], "vehicle_no": row[6],
            "stop_name": row[7], "pickup_time": row[8], "drop_time": row[9]}


def count_transport_students():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM student_transport WHERE status='active';")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


# ============================================================
# PHASE 22 — EXPENSES & P&L
# ============================================================
def create_expense(data, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO expenses
        (category, description, amount, expense_date, vendor,
         payment_mode, receipt_no, note, recorded_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        data["category"], data.get("description") or None,
        float(data["amount"]),
        data.get("expense_date") or None,
        data.get("vendor") or None,
        data.get("payment_mode") or "cash",
        data.get("receipt_no") or None,
        data.get("note") or None,
        admin_id
    ))
    eid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return eid


def get_expenses(month=None, category=None, search=None, limit=200):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, category, description, amount, expense_date,
               vendor, payment_mode, receipt_no, note, created_at
        FROM expenses WHERE 1=1
    """
    params = []
    if month:
        q += " AND TO_CHAR(expense_date, 'YYYY-MM')=%s"
        params.append(month)
    if category:
        q += " AND category=%s"
        params.append(category)
    if search:
        q += " AND (description ILIKE %s OR vendor ILIKE %s OR receipt_no ILIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]
    q += " ORDER BY expense_date DESC, id DESC LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "category": r[1], "description": r[2],
             "amount": float(r[3] or 0), "expense_date": r[4],
             "vendor": r[5], "payment_mode": r[6],
             "receipt_no": r[7], "note": r[8], "created_at": r[9]}
            for r in rows]


def get_expense(eid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, category, description, amount, expense_date,
               vendor, payment_mode, receipt_no, note, created_at
        FROM expenses WHERE id=%s;
    """, (eid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","category","description","amount","expense_date",
            "vendor","payment_mode","receipt_no","note","created_at"]
    d = dict(zip(keys, row))
    d["amount"] = float(d["amount"] or 0)
    return d


def update_expense(eid, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE expenses SET
            category=%s, description=%s, amount=%s, expense_date=%s,
            vendor=%s, payment_mode=%s, receipt_no=%s, note=%s
        WHERE id=%s RETURNING id;
    """, (
        data["category"], data.get("description") or None,
        float(data["amount"]),
        data.get("expense_date") or None,
        data.get("vendor") or None,
        data.get("payment_mode") or "cash",
        data.get("receipt_no") or None,
        data.get("note") or None,
        eid
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_expense(eid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=%s;", (eid,))
    conn.commit()
    cur.close()
    conn.close()


def get_expense_summary(month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT category, COUNT(*), SUM(amount)
        FROM expenses
        WHERE TO_CHAR(expense_date, 'YYYY-MM')=%s
        GROUP BY category ORDER BY 3 DESC;
    """, (month,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    cats = [{"category": r[0], "count": r[1], "total": float(r[2] or 0)}
            for r in rows]
    return {"categories": cats, "total": sum(c["total"] for c in cats),
            "count": len(cats)}


def get_pnl(month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM fee_payments WHERE month=%s;",
                (month,))
    fee_row = cur.fetchone()
    fees_collected = float(fee_row[0] or 0)
    fee_count = fee_row[1] or 0

    cur.execute("""
        SELECT
            COALESCE(SUM(net_amount) FILTER (WHERE status='paid'), 0),
            COALESCE(SUM(net_amount) FILTER (WHERE status='pending'), 0),
            COUNT(*) FILTER (WHERE status='paid'),
            COUNT(*) FILTER (WHERE status='pending')
        FROM salary_records WHERE month=%s;
    """, (month,))
    sal_row = cur.fetchone()
    salary_paid = float(sal_row[0] or 0)
    salary_pending = float(sal_row[1] or 0)

    cur.execute("""
        SELECT COALESCE(SUM(amount), 0), COUNT(*)
        FROM expenses WHERE TO_CHAR(expense_date, 'YYYY-MM')=%s;
    """, (month,))
    exp_row = cur.fetchone()
    expenses_total = float(exp_row[0] or 0)
    expenses_count = exp_row[1] or 0

    cur.execute("""
        SELECT category, SUM(amount) FROM expenses
        WHERE TO_CHAR(expense_date, 'YYYY-MM')=%s
        GROUP BY category ORDER BY 2 DESC;
    """, (month,))
    exp_cats = [{"category": r[0], "amount": float(r[1] or 0)}
                for r in cur.fetchall()]

    cur.close()
    conn.close()

    total_outflow = salary_paid + expenses_total
    net = fees_collected - total_outflow

    return {"month": month, "fees_collected": fees_collected,
            "fee_count": fee_count, "salary_paid": salary_paid,
            "salary_pending": salary_pending,
            "salary_paid_count": sal_row[2] or 0,
            "salary_pending_count": sal_row[3] or 0,
            "expenses_total": expenses_total, "expenses_count": expenses_count,
            "expense_categories": exp_cats,
            "total_outflow": total_outflow, "net": net,
            "profit": net >= 0}


def get_expense_monthly_trend(months=6):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TO_CHAR(expense_date, 'YYYY-MM'), SUM(amount)
        FROM expenses
        WHERE expense_date >= CURRENT_DATE - INTERVAL '%s months'
        GROUP BY 1 ORDER BY 1;
    """, (months,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"label": r[0], "value": float(r[1] or 0)} for r in rows]


def count_expenses_this_month():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses WHERE TO_CHAR(expense_date, 'YYYY-MM') = TO_CHAR(NOW(), 'YYYY-MM');
    """)
    n = float(cur.fetchone()[0] or 0)
    cur.close()
    conn.close()
    return n


# ============================================================
# PHASE 23 — CERTIFICATES
# ============================================================
def _build_default_body(cert_type, student):
    tpl = CERT_TEMPLATES.get(cert_type, "")
    if not tpl:
        return ""
    return tpl.format(
        name=student.get("name", ""),
        parent_name=student.get("parent_name") or "___",
        class_name=student.get("class_name") or "___",
        section=f"-{student.get('section')}" if student.get("section") else "",
        roll=student.get("roll_no") or "___",
        ay=_academic_year_for_cert()
    )


def _generate_cert_no(cert_type):
    year = datetime.now().year
    prefix = "".join([w[0] for w in cert_type.split()[:2]]).upper() or "CERT"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM certificates
        WHERE cert_type=%s AND EXTRACT(YEAR FROM created_at)=%s;
    """, (cert_type, year))
    n = (cur.fetchone()[0] or 0) + 1
    cur.close()
    conn.close()
    return f"{prefix}-{year}-{n:04d}"


def create_certificate(student_id, cert_type, body, remarks, admin_id, issue_date=None):
    row = get_student(student_id)
    if not row:
        raise ValueError("Student nahi mila")
    keys = ["id","name","roll_no","class_name","section","gender","dob",
            "parent_name","parent_phone","address","admission_date","status","created_at"]
    student = dict(zip(keys, row))
    if not body or not body.strip():
        body = _build_default_body(cert_type, student)

    conn = get_conn()
    cur = conn.cursor()
    cert_no = _generate_cert_no(cert_type)
    for _ in range(6):
        try:
            cur.execute("""
                INSERT INTO certificates
                (student_id, cert_type, cert_no, issue_date, body, remarks, issued_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, cert_no;
            """, (student_id, cert_type, cert_no,
                  issue_date or None, body, remarks or None, admin_id))
            res = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            return {"id": res[0], "cert_no": res[1]}
        except Exception:
            conn.rollback()
            cert_no = _generate_cert_no(cert_type) + f"-{_random.randint(1,9)}"
    cur.close()
    conn.close()
    raise RuntimeError("Certificate number generate nahi hua")


def get_certificates(cert_type=None, search=None, limit=200):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT c.id, c.student_id, c.cert_type, c.cert_no, c.issue_date,
               c.created_at, s.name, s.roll_no, s.class_name, s.section
        FROM certificates c
        JOIN students s ON s.id = c.student_id
        WHERE 1=1
    """
    params = []
    if cert_type:
        q += " AND c.cert_type=%s"
        params.append(cert_type)
    if search:
        q += " AND (s.name ILIKE %s OR c.cert_no ILIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    q += " ORDER BY c.created_at DESC LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "student_id": r[1], "cert_type": r[2],
             "cert_no": r[3], "issue_date": r[4], "created_at": r[5],
             "student_name": r[6], "roll": r[7],
             "class_name": r[8], "section": r[9]} for r in rows]


def get_certificate(cid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.student_id, c.cert_type, c.cert_no, c.issue_date,
               c.body, c.remarks, c.created_at,
               s.name, s.roll_no, s.class_name, s.section,
               s.parent_name, s.parent_phone, s.dob, s.admission_date
        FROM certificates c
        JOIN students s ON s.id = c.student_id
        WHERE c.id=%s;
    """, (cid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","student_id","cert_type","cert_no","issue_date",
            "body","remarks","created_at",
            "name","roll","class_name","section",
            "parent_name","parent_phone","dob","admission_date"]
    return dict(zip(keys, row))


def delete_certificate(cid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM certificates WHERE id=%s;", (cid,))
    conn.commit()
    cur.close()
    conn.close()


def count_certificates_this_month():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM certificates
        WHERE TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(NOW(), 'YYYY-MM');
    """)
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


# ============================================================
# PHASE 24 — EVENTS
# ============================================================
def create_event(data, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events
        (title, description, event_type, start_date, end_date,
         start_time, end_time, venue, target_class, is_public, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        data["title"], data.get("description") or None,
        data.get("event_type") or "other",
        data["start_date"], data.get("end_date") or data["start_date"],
        data.get("start_time") or None, data.get("end_time") or None,
        data.get("venue") or None, data.get("target_class") or None,
        data.get("is_public") == "on", admin_id
    ))
    eid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return eid


def get_events(month=None, event_type=None, upcoming_only=False, limit=200):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, title, description, event_type, start_date, end_date,
               start_time, end_time, venue, target_class, is_public, created_at
        FROM events WHERE 1=1
    """
    params = []
    if month:
        q += " AND (TO_CHAR(start_date, 'YYYY-MM')=%s OR TO_CHAR(end_date, 'YYYY-MM')=%s)"
        params += [month, month]
    if event_type:
        q += " AND event_type=%s"
        params.append(event_type)
    if upcoming_only:
        q += " AND (COALESCE(end_date, start_date) >= CURRENT_DATE)"
    q += " ORDER BY start_date ASC, start_time ASC NULLS FIRST LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "description": r[2], "event_type": r[3],
             "start_date": r[4], "end_date": r[5], "start_time": r[6],
             "end_time": r[7], "venue": r[8], "target_class": r[9],
             "is_public": r[10], "created_at": r[11]} for r in rows]


def get_event(eid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, description, event_type, start_date, end_date,
               start_time, end_time, venue, target_class, is_public, created_at
        FROM events WHERE id=%s;
    """, (eid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","title","description","event_type","start_date","end_date",
            "start_time","end_time","venue","target_class","is_public","created_at"]
    return dict(zip(keys, row))


def update_event(eid, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE events SET
            title=%s, description=%s, event_type=%s, start_date=%s, end_date=%s,
            start_time=%s, end_time=%s, venue=%s, target_class=%s, is_public=%s
        WHERE id=%s RETURNING id;
    """, (
        data["title"], data.get("description") or None,
        data.get("event_type") or "other",
        data["start_date"], data.get("end_date") or data["start_date"],
        data.get("start_time") or None, data.get("end_time") or None,
        data.get("venue") or None, data.get("target_class") or None,
        data.get("is_public") == "on", eid
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_event(eid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE id=%s;", (eid,))
    conn.commit()
    cur.close()
    conn.close()


def get_events_for_month_grid(year, month):
    first_day = date(year, month, 1)
    last_day = (date(year + 1, 1, 1) - timedelta(days=1)) if month == 12 \
               else (date(year, month + 1, 1) - timedelta(days=1))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, event_type, start_date, end_date,
               start_time, venue, target_class
        FROM events
        WHERE start_date <= %s AND COALESCE(end_date, start_date) >= %s
        ORDER BY start_date, start_time NULLS FIRST;
    """, (last_day, first_day))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    grid = {}
    for r in rows:
        s = r[3]
        e = r[4] or r[3]
        current = max(s, first_day)
        end = min(e, last_day)
        while current <= end:
            grid.setdefault(current, []).append({
                "id": r[0], "title": r[1], "type": r[2],
                "start_time": r[5], "venue": r[6],
                "is_multiday": s != e, "target_class": r[7]
            })
            current += timedelta(days=1)
    return grid


def get_upcoming_events(days=30, class_name=None, limit=10):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, title, event_type, start_date, end_date, start_time, venue
        FROM events
        WHERE COALESCE(end_date, start_date) >= CURRENT_DATE
          AND start_date <= CURRENT_DATE + INTERVAL '%s days'
          AND is_public = TRUE
    """
    params = [days]
    if class_name:
        q += " AND (target_class=%s OR target_class IS NULL OR target_class='')"
        params.append(class_name)
    q += " ORDER BY start_date, start_time NULLS FIRST LIMIT %s;"
    params.append(limit)
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "event_type": r[2],
             "start_date": r[3], "end_date": r[4],
             "start_time": r[5], "venue": r[6]} for r in rows]


def count_upcoming_events(days=7):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM events
        WHERE COALESCE(end_date, start_date) >= CURRENT_DATE
          AND start_date <= CURRENT_DATE + INTERVAL '%s days'
          AND is_public = TRUE;
    """, (days,))
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n


# ============================================================
# PHASE 25 — LIBRARY
# ============================================================
def create_book(data):
    conn = get_conn()
    cur = conn.cursor()
    total = int(data.get("total_copies") or 1)
    cur.execute("""
        INSERT INTO books
        (title, author, isbn, category, publisher, total_copies, available_copies, shelf_no)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        data["title"], data.get("author") or None,
        data.get("isbn") or None, data.get("category") or None,
        data.get("publisher") or None,
        total, total, data.get("shelf_no") or None
    ))
    bid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return bid


def get_books(search=None, category=None, only_available=False):
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, title, author, isbn, category, publisher,
               total_copies, available_copies, shelf_no
        FROM books WHERE 1=1
    """
    params = []
    if search:
        q += " AND (title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]
    if category:
        q += " AND category=%s"
        params.append(category)
    if only_available:
        q += " AND available_copies > 0"
    q += " ORDER BY title;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "author": r[2], "isbn": r[3],
             "category": r[4], "publisher": r[5], "total_copies": r[6],
             "available_copies": r[7], "shelf_no": r[8]} for r in rows]


def get_book(bid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, author, isbn, category, publisher,
               total_copies, available_copies, shelf_no, created_at
        FROM books WHERE id=%s;
    """, (bid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    keys = ["id","title","author","isbn","category","publisher",
            "total_copies","available_copies","shelf_no","created_at"]
    return dict(zip(keys, row))


def update_book(bid, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT total_copies, available_copies FROM books WHERE id=%s;", (bid,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None
    old_total, old_avail = row
    new_total = int(data.get("total_copies") or old_total)
    issued = old_total - old_avail
    new_available = max(new_total - issued, 0)
    cur.execute("""
        UPDATE books SET
            title=%s, author=%s, isbn=%s, category=%s, publisher=%s,
            total_copies=%s, available_copies=%s, shelf_no=%s
        WHERE id=%s RETURNING id;
    """, (
        data["title"], data.get("author") or None,
        data.get("isbn") or None, data.get("category") or None,
        data.get("publisher") or None,
        new_total, new_available, data.get("shelf_no") or None, bid
    ))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return res[0] if res else None


def delete_book(bid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM book_issues WHERE book_id=%s AND status='issued';",
                (bid,))
    active = cur.fetchone()[0]
    if active > 0:
        cur.close()
        conn.close()
        return False
    cur.execute("DELETE FROM books WHERE id=%s;", (bid,))
    conn.commit()
    cur.close()
    conn.close()
    return True


def create_book_issue(book_id, student_id, due_date, note, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT available_copies FROM books WHERE id=%s FOR UPDATE;", (book_id,))
    row = cur.fetchone()
    if not row or row[0] <= 0:
        cur.close()
        conn.close()
        raise ValueError("Book available nahi hai")
    cur.execute("""
        SELECT 1 FROM book_issues
        WHERE book_id=%s AND student_id=%s AND status='issued' LIMIT 1;
    """, (book_id, student_id))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise ValueError("Ye student ye book already le chuka hai")
    cur.execute("""
        INSERT INTO book_issues (book_id, student_id, due_date, note, issued_by, status)
        VALUES (%s, %s, %s, %s, %s, 'issued') RETURNING id;
    """, (book_id, student_id, due_date, note, admin_id))
    iid = cur.fetchone()[0]
    cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id=%s;",
                (book_id,))
    conn.commit()
    cur.close()
    conn.close()
    return iid


def return_book_issue(issue_id, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT book_id, due_date, status FROM book_issues WHERE id=%s;",
                (issue_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None
    book_id, due_date, status = row
    if status != 'issued':
        cur.close()
        conn.close()
        return None
    today = date.today()
    fine = 0
    if today > due_date:
        days = (today - due_date).days
        fine = days * LIBRARY_FINE_PER_DAY
    cur.execute("""
        UPDATE book_issues
        SET return_date=%s, fine=%s, status='returned', returned_by=%s
        WHERE id=%s RETURNING fine;
    """, (today, fine, admin_id, issue_id))
    returned_fine = cur.fetchone()[0]
    cur.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id=%s;",
                (book_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"fine": float(returned_fine or 0)}


def get_active_issues(search=None, only_overdue=False):
    today = date.today()
    conn = get_conn()
    cur = conn.cursor()
    q = """
        SELECT bi.id, bi.book_id, bi.student_id, bi.issue_date, bi.due_date,
               bi.status, b.title, b.author,
               s.name, s.roll_no, s.class_name, s.section, s.parent_phone
        FROM book_issues bi
        JOIN books b ON b.id = bi.book_id
        JOIN students s ON s.id = bi.student_id
        WHERE bi.status = 'issued'
    """
    params = []
    if search:
        q += " AND (b.title ILIKE %s OR s.name ILIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    if only_overdue:
        q += " AND bi.due_date < CURRENT_DATE"
    q += " ORDER BY bi.due_date;"
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    out = []
    for r in rows:
        due = r[4]
        days_overdue = (today - due).days if today > due else 0
        fine_est = days_overdue * LIBRARY_FINE_PER_DAY
        out.append({"id": r[0], "book_id": r[1], "student_id": r[2],
                    "issue_date": r[3], "due_date": due,
                    "book_title": r[6], "book_author": r[7],
                    "student_name": r[8], "roll": r[9],
                    "class_name": r[10], "section": r[11], "phone": r[12],
                    "days_overdue": days_overdue, "fine_est": fine_est})
    return out


def get_issue_history(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT bi.id, bi.issue_date, bi.due_date, bi.return_date, bi.fine, bi.status,
               b.title, s.name, s.class_name
        FROM book_issues bi
        JOIN books b ON b.id = bi.book_id
        JOIN students s ON s.id = bi.student_id
        WHERE bi.status='returned'
        ORDER BY bi.return_date DESC LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "issue_date": r[1], "due_date": r[2],
             "return_date": r[3], "fine": float(r[4] or 0), "status": r[5],
             "book_title": r[6], "student_name": r[7],
             "class_name": r[8]} for r in rows]


def get_student_library_history(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT bi.id, b.title, bi.issue_date, bi.due_date,
               bi.return_date, bi.fine, bi.status
        FROM book_issues bi
        JOIN books b ON b.id = bi.book_id
        WHERE bi.student_id=%s
        ORDER BY bi.issue_date DESC LIMIT 20;
    """, (student_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "book_title": r[1], "issue_date": r[2],
             "due_date": r[3], "return_date": r[4],
             "fine": float(r[5] or 0), "status": r[6]} for r in rows]


def get_library_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            (SELECT COUNT(*) FROM books) AS total_books,
            (SELECT COALESCE(SUM(total_copies),0) FROM books) AS total_copies,
            (SELECT COUNT(*) FROM book_issues WHERE status='issued') AS issued_count,
            (SELECT COUNT(*) FROM book_issues WHERE status='issued'
                AND due_date < CURRENT_DATE) AS overdue_count,
            (SELECT COALESCE(SUM(fine),0) FROM book_issues
                WHERE status='returned') AS total_fine_collected
    """)
    r = cur.fetchone()
    cur.close()
    conn.close()
    return {"total_books": r[0] or 0, "total_copies": r[1] or 0,
            "issued_count": r[2] or 0, "overdue_count": r[3] or 0,
            "total_fine_collected": float(r[4] or 0)}


# ============================================================
# CONTINUED IN PART 2
# ============================================================
