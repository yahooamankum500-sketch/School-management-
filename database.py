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
    # ============================================================
# PHASE 2: STUDENTS
# ============================================================
def create_student(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students
        (name, roll_no, class_name, section, gender, parent_name, parent_phone, address)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        data.get("name"), data.get("roll_no"), data.get("class_name"),
        data.get("section"), data.get("gender"),
        data.get("parent_name"), data.get("parent_phone"), data.get("address")
    ))
    sid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return sid

def get_students():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, roll_no, class_name, section, parent_phone FROM students ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
