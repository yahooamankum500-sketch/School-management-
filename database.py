from supabase_client import get_conn
from werkzeug.security import generate_password_hash, check_password_hash

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

def verify_admin(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, full_name, role FROM admins WHERE username=%s;", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row and check_password_hash(row[2], password):
        return {"id": row[0], "username": row[1], "full_name": row[3], "role": row[4] or "admin"}
    return None
