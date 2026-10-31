from werkzeug.security import generate_password_hash, check_password_hash
from typing import Any, Optional
import random
from datetime import datetime

# ============================================================
# HELPER FUNCTIONS (Supabase API ke liye)
# ============================================================
def _client():
    from supabase_client import get_supabase
    client = get_supabase()
    if client is None:
        raise RuntimeError("Supabase client is not connected")
    return client

def _safe(value: Any) -> Any:
    from datetime import date, datetime
    from decimal import Decimal
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    return value

def _data(response):
    return getattr(response, "data", None) or []

def _one(response):
    rows = _data(response)
    return rows[0] if rows else None

def _table(name: str):
    return _client().table(name)

def db_select(table: str, filters: dict = None, *, columns: str = "*", order_by: str = None, descending: bool = False, limit: int = None):
    query = _table(table).select(columns)
    for key, value in (filters or {}).items():
        query = query.is_(key, "null") if value is None else query.eq(key, _safe(value))
    if order_by:
        query = query.order(order_by, desc=descending)
    if limit is not None:
        query = query.limit(int(limit))
    return _data(query.execute())

def db_insert(table: str, values: dict):
    return _one(_table(table).insert(_safe(values)).execute())

def db_update(table: str, row_id: Any, values: dict, *, id_column: str = "id"):
    return _one(_table(table).update(_safe(values)).eq(id_column, row_id).execute())

def db_delete(table: str, row_id: Any, *, id_column: str = "id"):
    return _data(_table(table).delete().eq(id_column, row_id).execute())

def db_get(table: str, row_id: Any, *, id_column: str = "id"):
    query = _table(table).select("*").eq(id_column, row_id).limit(1)
    return _one(query.execute())

def db_upsert(table: str, values: dict, on_conflict: str):
    return _one(_table(table).upsert(_safe(values), on_conflict=on_conflict).execute())

def get_classes_list():
    rows = db_select("students", columns="class_name")
    classes = {r.get("class_name") for r in rows if r.get("class_name")}
    return sorted(list(classes))


# ============================================================
# PHASE 1: ADMIN & AUTH
# ============================================================
def create_admin(username, password, full_name=""):
    return db_insert("admins", {
        "username": username,
        "password_hash": generate_password_hash(password),
        "full_name": full_name,
        "role": "super_admin",
        "is_active": True
    })

def get_admin_by_username(username):
    rows = db_select("admins", {"username": username}, limit=1)
    return rows[0] if rows else None

def verify_admin(username, password):
    row = get_admin_by_username(username)
    if not row:
        return None
        
    if check_password_hash(row.get("password_hash", ""), password):
        return {
            "id": row["id"], 
            "username": row["username"], 
            "full_name": row.get("full_name"), 
            "role": row.get("role")
        }
    return None


# ============================================================
# PHASE 2: STUDENTS MANAGEMENT
# ============================================================
def create_student(data):
    if not data.get("name") or not data.get("class_name"):
        raise ValueError("Name aur Class zaroori hai")
    return db_insert("students", {
        "name": data.get("name"),
        "roll_no": data.get("roll_no"),
        "class_name": data.get("class_name"),
        "section": data.get("section"),
        "gender": data.get("gender"),
        "dob": data.get("dob") or None,
        "parent_name": data.get("parent_name"),
        "parent_phone": data.get("parent_phone"),
        "address": data.get("address"),
        "status": data.get("status") or "active"
    })

def get_students(search=None, class_name=None, status="active"):
    filters = {}
    if status and status != "all":
        filters["status"] = status
    if class_name:
        filters["class_name"] = class_name
        
    rows = db_select("students", filters or None, order_by="class_name")
    
    if search:
        term = str(search).lower()
        rows = [r for r in rows if any(term in str(r.get(k) or "").lower() 
                for k in ("name", "roll_no", "parent_phone"))]
                
    return rows

def get_student(student_id):
    return db_get("students", student_id)

def update_student(student_id, data):
    allowed = {"name", "roll_no", "class_name", "section", "gender", "dob", 
               "parent_name", "parent_phone", "address", "status"}
    clean_data = {k: v for k, v in data.items() if k in allowed}
    return db_update("students", student_id, clean_data)

def delete_student(student_id):
    return db_delete("students", student_id)


# ============================================================
# PHASE 3: FEES MANAGEMENT
# ============================================================
def create_fee_structure(class_name, fee_type, amount, frequency):
    return db_insert("fee_structure", {
        "class_name": class_name,
        "fee_type": fee_type,
        "amount": float(amount),
        "frequency": frequency
    })

def get_fee_structures(class_name=None):
    filters = {"class_name": class_name} if class_name else None
    return db_select("fee_structure", filters, order_by="class_name")

def delete_fee_structure(fid):
    return db_delete("fee_structure", fid)

def create_fee_payment(student_id, fee_type, amount, month, mode, note, admin_id):
    receipt_no = f"RCPT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    return db_insert("fee_payments", {
        "student_id": student_id,
        "fee_type": fee_type,
        "amount": float(amount),
        "month": month,
        "mode": mode,
        "receipt_no": receipt_no,
        "note": note,
        "recorded_by": admin_id
    })

def get_recent_payments(limit=50):
    payments = db_select("fee_payments", order_by="paid_at", descending=True, limit=limit)
    
    for p in payments:
        student = db_get("students", p["student_id"])
        if student:
            p["student_name"] = student.get("name", "Unknown")
            p["class_name"] = student.get("class_name", "-")
        else:
            p["student_name"] = "Unknown"
            p["class_name"] = "-"
            
    return payments


# ============================================================
# PHASE 4: ATTENDANCE MANAGEMENT
# ============================================================
def mark_attendance(student_id, date_str, status, admin_id):
    return db_upsert("attendance", {
        "student_id": student_id,
        "attendance_date": date_str,
        "status": status,
        "marked_by": admin_id
    }, on_conflict="student_id,attendance_date")

def get_attendance_for_date(class_name, date_str):
    students = db_select("students", {"class_name": class_name, "status": "active"}, order_by="roll_no")
    att_rows = db_select("attendance", {"attendance_date": date_str})
    att_map = {str(a["student_id"]): a for a in att_rows}
    
    result = []
    for s in students:
        status = att_map.get(str(s["id"]), {}).get("status", None)
        result.append({
            "id": s["id"],
            "name": s["name"],
            "roll_no": s.get("roll_no"),
            "status": status
        })
    return result 


# ============================================================
# PHASE 5: EXAMS & MARKS MANAGEMENT
# ============================================================
def create_exam(data):
    return db_insert("exams", {
        "name": data.get("name"),
        "class_name": data.get("class_name"),
        "exam_date": data.get("exam_date") or None,
        "max_marks": float(data.get("max_marks") or 100)
    })

def get_exams(class_name=None):
    filters = {"class_name": class_name} if class_name else None
    return db_select("exams", filters, order_by="exam_date", descending=True)

def get_exam(exam_id):
    return db_get("exams", exam_id)

def delete_exam(exam_id):
    return db_delete("exams", exam_id)

def save_exam_marks(exam_id, student_id, marks_obtained):
    return db_upsert("marks", {
        "exam_id": exam_id,
        "student_id": student_id,
        "marks_obtained": float(marks_obtained)
    }, on_conflict="exam_id,student_id")

def get_exam_marks(exam_id):
    rows = db_select("marks", {"exam_id": exam_id})
    marks_map = {}
    for r in rows:
        marks_map[str(r["student_id"])] = r["marks_obtained"]
    return marks_map
    # ============================================================
# PHASE 6: NOTICES & EVENTS
# ============================================================
def create_notice(data):
    return db_insert("notices", {
        "title": data.get("title"),
        "content": data.get("content"),
        "priority": data.get("priority") or "normal",
        "target_class": data.get("target_class") or None
    })

def get_notices(limit=50):
    return db_select("notices", order_by="created_at", descending=True, limit=limit)

def delete_notice(notice_id):
    return db_delete("notices", notice_id)

def create_event(data):
    return db_insert("events", {
        "title": data.get("title"),
        "description": data.get("description"),
        "event_date": data.get("event_date"),
        "venue": data.get("venue")
    })

def get_events(limit=50):
    return db_select("events", order_by="event_date", limit=limit)

def delete_event(event_id):
    return db_delete("events", event_id)
    # ============================================================
# PHASE 7: PARENT PORTAL
# ============================================================
def create_parent_account(phone, password, name):
    return db_insert("parents", {
        "phone": phone,
        "password_hash": generate_password_hash(password),
        "name": name
    })

def verify_parent(phone, password):
    rows = db_select("parents", {"phone": phone}, limit=1)
    if not rows:
        return None
    row = rows[0]
    if check_password_hash(row.get("password_hash", ""), password):
        return {"id": row["id"], "phone": row["phone"], "name": row.get("name")}
    return None

def get_children_for_parent(phone):
    # Students table se us phone number wale bachche fetch karo
    return db_select("students", {"parent_phone": phone, "status": "active"})

def get_child_attendance_summary(student_id):
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    
    # Is student ki saari attendance fetch karo
    rows = db_select("attendance", {"student_id": student_id})
    
    present = 0
    total = 0
    for r in rows:
        # Filter for current month
        if r.get("attendance_date") and r["attendance_date"].startswith(current_month):
            total += 1
            if r["status"] == "present":
                present += 1
                
    percent = round((present / total * 100), 1) if total > 0 else 0
    return {"present": present, "total": total, "percent": percent}

def get_child_pending_fees(student_id):
    student = db_get("students", student_id)
    if not student or not student.get("class_name"):
        return 0
        
    # Class ki total fees
    structures = db_select("fee_structure", {"class_name": student["class_name"]})
    due = sum(float(s.get("amount") or 0) for s in structures)
    
    # Student ne kitna pay kiya
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    payments = db_select("fee_payments", {"student_id": student_id, "month": current_month})
    paid = sum(float(p.get("amount") or 0) for p in payments)
    
    return max(due - paid, 0)
    # ============================================================
# PHASE 8: TEACHER PORTAL
# ============================================================
def create_teacher_account(name, phone, password, assigned_class, assigned_section):
    return db_insert("teachers", {
        "name": name,
        "phone": phone,
        "password_hash": generate_password_hash(password),
        "assigned_class": assigned_class,
        "assigned_section": assigned_section or None
    })

def verify_teacher(phone, password):
    rows = db_select("teachers", {"phone": phone}, limit=1)
    if not rows:
        return None
    row = rows[0]
    if check_password_hash(row.get("password_hash", ""), password):
        return {
            "id": row["id"], 
            "name": row["name"], 
            "phone": row["phone"], 
            "assigned_class": row["assigned_class"],
            "assigned_section": row.get("assigned_section")
        }
    return None

def get_teacher_students(assigned_class, assigned_section):
    filters = {"class_name": assigned_class, "status": "active"}
    if assigned_section:
        filters["section"] = assigned_section
    return db_select("students", filters, order_by="roll_no")
