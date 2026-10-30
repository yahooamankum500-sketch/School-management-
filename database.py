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
