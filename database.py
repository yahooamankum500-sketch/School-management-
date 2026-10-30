from supabase_client import get_supabase

def get_database():
    client = get_supabase()

    if client is None:
        raise RuntimeError("Supabase database is not connected")

    return client


def get_students():
    db = get_database()

    response = (
        db.table("students")
        .select("*")
        .execute()
    )

    return response.data


def add_student(student_data):
    db = get_database()

    response = (
        db.table("students")
        .insert(student_data)
        .execute()
    )

    return response.data
