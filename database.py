from werkzeug.security import generate_password_hash, check_password_hash

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
