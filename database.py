# ============================================================
# PHASE 1: ADMIN & AUTH
# ============================================================
def create_admin(username, password, full_name=""):
    from werkzeug.security import generate_password_hash
    return db_insert("admins", {
        "username": username,
        "password_hash": generate_password_hash(password),
        "full_name": full_name,
        "role": "super_admin",
        "is_active": True
    })

def verify_admin(username, password):
    from werkzeug.security import check_password_hash
    rows = db_select("admins", {"username": username}, limit=1)
    if not rows:
        return None
    row = rows[0]
    if check_password_hash(row.get("password_hash", ""), password):
        return {"id": row["id"], "username": row["username"], "full_name": row.get("full_name"), "role": row.get("role")}
    return None
