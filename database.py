"""
Supabase API converted to Raw SQL (Same as first code)
======================================================
This code now uses get_conn() from supabase_client.py (psycopg2)
"""

from supabase_client import get_conn


def get_students():
    """Fetch all students using Raw SQL"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM students;")
        columns = [desc[0] for desc in cur.description]  # Get column names
        rows = cur.fetchall()
        
        # Convert tuple rows to dictionary (just like Supabase does)
        students = [dict(zip(columns, row)) for row in rows]
        return students
        
    finally:
        cur.close()
        conn.close()


def add_student(student_data: dict):
    """Add a student using Raw SQL"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Extract values from the dictionary
        name = student_data.get("name")
        roll_no = student_data.get("roll_no")
        class_name = student_data.get("class_name")
        section = student_data.get("section")
        gender = student_data.get("gender")
        dob = student_data.get("dob")
        parent_name = student_data.get("parent_name")
        parent_phone = student_data.get("parent_phone")
        address = student_data.get("address")
        
        cur.execute("""
            INSERT INTO students 
            (name, roll_no, class_name, section, gender, dob, parent_name, parent_phone, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """, (name, roll_no, class_name, section, gender, dob, parent_name, parent_phone, address))
        
        row = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        conn.commit()
        
        # Return the newly inserted student
        return [dict(zip(columns, row))]
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
