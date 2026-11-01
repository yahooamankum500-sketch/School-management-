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
    # ============================================================
# PHASE 9: LIBRARY MANAGEMENT
# ============================================================
def create_book(data):
    return db_insert("books", {
        "title": data.get("title"),
        "author": data.get("author"),
        "total_copies": int(data.get("total_copies") or 1),
        "available_copies": int(data.get("total_copies") or 1)
    })

def get_books():
    return db_select("books", order_by="title")

def issue_book(book_id, student_id):
    # 1. Book ki availability check karo
    book = db_get("books", book_id)
    if not book or book["available_copies"] <= 0:
        raise ValueError("Ye book abhi available nahi hai.")
        
    # 2. Book issue record banao
    db_insert("book_issues", {
        "book_id": book_id,
        "student_id": student_id,
        "status": "issued"
    })
    
    # 3. Available copies kam karo
    db_update("books", book_id, {"available_copies": book["available_copies"] - 1})

def return_book(issue_id):
    # 1. Issue record fetch karo
    issue = db_get("book_issues", issue_id)
    if not issue or issue["status"] == "returned":
        raise ValueError("Ye book pehle hi return ho chuki hai.")
        
    # 2. Status update karo aur aaj ki date daalo
    from datetime import date
    today = date.today().isoformat()
    db_update("book_issues", issue_id, {"status": "returned", "return_date": today})
    
    # 3. Available copies badhao
    book = db_get("books", issue["book_id"])
    if book:
        db_update("books", book["id"], {"available_copies": book["available_copies"] + 1})

def get_active_issues():
    # Sirf wo books jo abhi tak return nahi hui
    issues = db_select("book_issues", {"status": "issued"})
    
    # Student aur Book ka naam fetch karo (Dictionary approach)
    for i in issues:
        book = db_get("books", i["book_id"])
        student = db_get("students", i["student_id"])
        i["book_title"] = book.get("title") if book else "Unknown"
        i["student_name"] = student.get("name") if student else "Unknown"
        i["class_name"] = student.get("class_name") if student else "-"
        
    return issues
    # ============================================================
# PHASE 10: TRANSPORT / BUS ROUTES
# ============================================================
def create_bus_route(data):
    return db_insert("bus_routes", {
        "route_name": data.get("route_name"),
        "driver_name": data.get("driver_name"),
        "driver_phone": data.get("driver_phone"),
        "vehicle_no": data.get("vehicle_no")
    })

def get_bus_routes():
    return db_select("bus_routes", order_by="route_name")

def create_bus_stop(data):
    return db_insert("bus_stops", {
        "route_id": int(data.get("route_id")),
        "stop_name": data.get("stop_name"),
        "pickup_time": data.get("pickup_time"),
        "sequence": int(data.get("sequence") or 1)
    })

def get_bus_stops(route_id):
    return db_select("bus_stops", {"route_id": route_id}, order_by="sequence")

def assign_transport(student_id, route_id, stop_id):
    # Upsert logic: Agar student pehle se kisi bus mein hai, toh update kar do
    return db_upsert("student_transport", {
        "student_id": student_id,
        "route_id": route_id,
        "stop_id": stop_id
    }, on_conflict="student_id")

def get_student_transport_details(student_id):
    # Fetch assignment
    rows = db_select("student_transport", {"student_id": student_id})
    if not rows:
        return None
        
    assignment = rows[0]
    
    # Fetch Route
    route = db_get("bus_routes", assignment["route_id"])
    # Fetch Stop
    stop = db_get("bus_stops", assignment["stop_id"])
    
    return {
        "route_name": route.get("route_name") if route else "Unknown",
        "driver_name": route.get("driver_name") if route else "-",
        "driver_phone": route.get("driver_phone") if route else "-",
        "vehicle_no": route.get("vehicle_no") if route else "-",
        "stop_name": stop.get("stop_name") if stop else "Unknown",
        "pickup_time": stop.get("pickup_time") if stop else "-"
    }

def get_students_on_route(route_id):
    assignments = db_select("student_transport", {"route_id": route_id})
    result = []
    for a in assignments:
        student = db_get("students", a["student_id"])
        stop = db_get("bus_stops", a["stop_id"])
        if student and stop:
            result.append({
                "student_name": student.get("name"),
                "class_name": student.get("class_name"),
                "parent_phone": student.get("parent_phone"),
                "stop_name": stop.get("stop_name"),
                "pickup_time": stop.get("pickup_time")
            })
    return result
    # ============================================================
# PHASE 11: HOSTEL MANAGEMENT
# ============================================================
def create_hostel(data):
    return db_insert("hostels", {
        "name": data.get("name"),
        "warden_name": data.get("warden_name"),
        "warden_phone": data.get("warden_phone")
    })

def get_hostels():
    return db_select("hostels", order_by="name")

def create_hostel_room(hostel_id, data):
    return db_insert("hostel_rooms", {
        "hostel_id": hostel_id,
        "room_no": data.get("room_no"),
        "capacity": int(data.get("capacity") or 4),
        "fee": float(data.get("fee") or 0)
    })

def get_hostel_rooms(hostel_id):
    # Rooms fetch karo
    rooms = db_select("hostel_rooms", {"hostel_id": hostel_id}, order_by="room_no")
    
    # Har room mein kitne students hain, calculate karo
    allocations = db_select("hostel_allocations", {"status": "active"})
    
    for room in rooms:
        occupied = sum(1 for a in allocations if a["room_id"] == room["id"])
        room["occupied"] = occupied
        room["available"] = room["capacity"] - occupied
        
    return rooms

def allocate_hostel_room(student_id, room_id):
    # Check karo room full toh nahi hai
    allocations = db_select("hostel_allocations", {"room_id": room_id, "status": "active"})
    room = db_get("hostel_rooms", room_id)
    
    if not room:
        raise ValueError("Room nahi mila.")
    if len(allocations) >= room["capacity"]:
        raise ValueError("Ye room full hai.")
        
    # Upsert (agar pehle se kisi room mein hai toh shift ho jayega)
    return db_upsert("hostel_allocations", {
        "student_id": student_id,
        "room_id": room_id,
        "status": "active"
    }, on_conflict="student_id")

def checkout_hostel(student_id):
    return db_update("hostel_allocations", student_id, {"status": "checked_out"}, id_column="student_id")

def get_hostel_inmates(hostel_id):
    # Us hostel ke saare rooms ki IDs nikaalo
    rooms = db_select("hostel_rooms", {"hostel_id": hostel_id})
    room_ids = [r["id"] for r in rooms]
    
    if not room_ids:
        return []
        
    # Sirf un rooms ki active allocations fetch karo
    allocations = db_select("hostel_allocations", {"status": "active"})
    active_allocs = [a for a in allocations if a["room_id"] in room_ids]
    
    result = []
    for a in active_allocs:
        student = db_get("students", a["student_id"])
        room = db_get("hostel_rooms", a["room_id"])
        if student and room:
            result.append({
                "student_id": student["id"],
                "student_name": student["name"],
                "class_name": student["class_name"],
                "room_no": room["room_no"],
                "check_in": a["created_at"][:10]
            })
    return result
    # ============================================================
# PHASE 12: STAFF & SALARY MANAGEMENT
# ============================================================
def create_staff(data):
    return db_insert("staff", {
        "name": data.get("name"),
        "role": data.get("role"),
        "phone": data.get("phone"),
        "salary": float(data.get("salary") or 0)
    })

def get_staff_list():
    return db_select("staff", {"status": "active"}, order_by="name")

def generate_monthly_salary(month):
    # 1. Saare active staff fetch karo
    staff_list = get_staff_list()
    created_count = 0
    
    # 2. Har staff ke liye us month ki salary record banao (agar pehle se na ho)
    for s in staff_list:
        if s["salary"] > 0:
            try:
                db_insert("salary_records", {
                    "staff_id": s["id"],
                    "month": month,
                    "amount": s["salary"],
                    "status": "pending"
                })
                created_count += 1
            except Exception:
                # Agar record pehle se hai (Unique constraint), toh skip kar do
                pass
                
    return created_count

def get_salary_records(month):
    # Is month ke saare records fetch karo
    records = db_select("salary_records", {"month": month})
    
    # Staff ka naam jodo
    for r in records:
        staff = db_get("staff", r["staff_id"])
        r["staff_name"] = staff.get("name") if staff else "Unknown"
        r["role"] = staff.get("role") if staff else "-"
        
    return records

def mark_salary_paid(record_id):
    from datetime import datetime
    return db_update("salary_records", record_id, {
        "status": "paid",
        "paid_at": datetime.now().isoformat()
    })
    # ============================================================
# PHASE 13: EXPENSES & PROFIT/LOSS
# ============================================================
def create_expense(data):
    return db_insert("expenses", {
        "category": data.get("category"),
        "description": data.get("description"),
        "amount": float(data.get("amount") or 0),
        "expense_date": data.get("expense_date") or None
    })

def get_expenses(month=None):
    # month format: 'YYYY-MM'
    filters = {}
    rows = db_select("expenses", order_by="expense_date", descending=True)
    
    if month:
        # Python se filter kar lenge kyunki supabase-py mein date prefix query thodi tricky hoti hai
        rows = [r for r in rows if r.get("expense_date") and r["expense_date"].startswith(month)]
        
    return rows

def get_pnl(month):
    # 1. Total Income (Fees Collected in that month)
    fee_payments = db_select("fee_payments", {"month": month})
    total_fees = sum(float(f.get("amount") or 0) for f in fee_payments)

    # 2. Total Salary Paid in that month
    salary_records = db_select("salary_records", {"month": month, "status": "paid"})
    total_salary = sum(float(s.get("amount") or 0) for s in salary_records)

    # 3. Total Other Expenses in that month
    exp_records = get_expenses(month)
    total_expenses = sum(float(e.get("amount") or 0) for e in exp_records)

    # 4. Net Profit / Loss
    total_outflow = total_salary + total_expenses
    net_profit = total_fees - total_outflow

    return {
        "month": month,
        "fees": total_fees,
        "salary": total_salary,
        "expenses": total_expenses,
        "total_outflow": total_outflow,
        "net": net_profit,
        "is_profit": net_profit >= 0
    }
    # ============================================================
# PHASE 14: DASHBOARD ANALYTICS
# ============================================================
def get_dashboard_stats():
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Total Active Students
    students = db_select("students", {"status": "active"})
    total_students = len(students)
    
    # 2. Fees Collected (This Month)
    fees = db_select("fee_payments", {"month": current_month})
    total_fees = sum(float(f.get("amount") or 0) for f in fees)
    
    # 3. Expenses (This Month)
    expenses = db_select("expenses", order_by="expense_date", descending=True)
    month_expenses = [e for e in expenses if e.get("expense_date") and e["expense_date"].startswith(current_month)]
    total_expenses = sum(float(e.get("amount") or 0) for e in month_expenses)
    
    # 4. Today's Attendance
    today_att = db_select("attendance", {"attendance_date": today_date})
    present_count = sum(1 for a in today_att if a.get("status") == "present")
    absent_count = sum(1 for a in today_att if a.get("status") == "absent")
    
    return {
        "total_students": total_students,
        "total_fees": total_fees,
        "total_expenses": total_expenses,
        "today_present": present_count,
        "today_absent": absent_count,
        "current_month": current_month
    }
# ============================================================
# PHASE 17: TIMETABLE MANAGEMENT
# ============================================================
def create_timetable_entry(data):
    return db_insert("timetable", {
        "class_name": data.get("class_name"),
        "day_of_week": data.get("day_of_week"),
        "period_number": int(data.get("period_number")),
        "subject": data.get("subject"),
        "teacher_name": data.get("teacher_name")
    })

def get_timetable(class_name):
    return db_select("timetable", {"class_name": class_name}, order_by="period_number")

def delete_timetable_entry(entry_id):
    return db_delete("timetable", entry_id)
    # ============================================================
# PHASE 18: FEE DISCOUNTS
# ============================================================
def add_discount(student_id, name, dtype, value):
    return db_insert("student_discounts", {
        "student_id": student_id,
        "discount_name": name,
        "discount_type": dtype,
        "discount_value": float(value)
    })

def get_student_discounts(student_id):
    return db_select("student_discounts", {"student_id": student_id})

def delete_discount(discount_id):
    return db_delete("student_discounts", discount_id)

def calculate_student_fee(student_id, class_name):
    # 1. Class ki total fees nikaalo
    structures = db_select("fee_structure", {"class_name": class_name})
    base_fee = sum(float(s.get("amount") or 0) for s in structures)
    
    if base_fee == 0:
        return {"base_fee": 0, "discount": 0, "final_fee": 0}

    # 2. Us student ke discounts nikaalo
    discounts = get_student_discounts(student_id)
    
    total_discount_amount = 0
    for d in discounts:
        if d["discount_type"] == "percent":
            total_discount_amount += (base_fee * (float(d["discount_value"]) / 100))
        else:
            total_discount_amount += float(d["discount_value"])
            
    # Final fee 0 se kam nahi ho sakti
    final_fee = max(base_fee - total_discount_amount, 0)
    
    return {
        "base_fee": base_fee,
        "discount": total_discount_amount,
        "final_fee": final_fee
    }
    # ============================================================
# PHASE 19: STAFF ATTENDANCE & LEAVES
# ============================================================
def mark_staff_attendance(staff_id, date_str, status):
    return db_upsert("staff_attendance", {
        "staff_id": staff_id,
        "attendance_date": date_str,
        "status": status
    }, on_conflict="staff_id,attendance_date")

def get_staff_attendance_for_date(date_str):
    # 1. Saare active staff fetch karo
    staff_list = db_select("staff", {"status": "active"}, order_by="name")
    
    # 2. Us din ki attendance fetch karo
    att_rows = db_select("staff_attendance", {"attendance_date": date_str})
    att_map = {str(a["staff_id"]): a["status"] for a in att_rows}
    
    # 3. Dono ko merge karo
    result = []
    for s in staff_list:
        result.append({
            "id": s["id"],
            "name": s["name"],
            "role": s["role"],
            "status": att_map.get(str(s["id"]), None)
        })
    return result

def apply_leave(staff_id, from_date, to_date, reason):
    return db_insert("leave_requests", {
        "staff_id": staff_id,
        "from_date": from_date,
        "to_date": to_date,
        "reason": reason
    })

def get_leave_requests(status=None):
    filters = {"status": status} if status else None
    rows = db_select("leave_requests", filters, order_by="created_at", descending=True)
    
    # Staff ka naam jodo
    for r in rows:
        staff = db_get("staff", r["staff_id"])
        r["staff_name"] = staff.get("name") if staff else "Unknown"
        
    return rows

def update_leave_status(leave_id, status):
    return db_update("leave_requests", leave_id, {"status": status})
