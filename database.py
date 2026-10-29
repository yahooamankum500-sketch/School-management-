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
# ============================================================
# PHASE 3: FEES MANAGEMENT
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
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_fee_structures(class_name=None):
    conn = get_conn()
    cur = conn.cursor()
    if class_name:
        cur.execute("SELECT id, class_name, fee_type, amount, frequency FROM fee_structure WHERE class_name=%s ORDER BY fee_type;", (class_name,))
    else:
        cur.execute("SELECT id, class_name, fee_type, amount, frequency FROM fee_structure ORDER BY class_name, fee_type;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def create_fee_payment(student_id, fee_type, amount, month, mode, note, admin_id):
    conn = get_conn()
    cur = conn.cursor()
    
    # Auto-generate receipt number
    import random
    receipt_no = f"RCPT-{random.randint(10000, 99999)}"
    
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

def get_recent_payments(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, s.name, s.class_name, p.fee_type, p.amount, p.month, p.mode, p.receipt_no, p.paid_at
        FROM fee_payments p
        JOIN students s ON s.id = p.student_id
        ORDER BY p.paid_at DESC LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
