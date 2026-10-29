import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from database import verify_admin

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = verify_admin(username, password)
        
        if admin:
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"] or admin["username"]
            return redirect(url_for("dashboard"))
            
        return "Galat Username ya Password. <br><a href='/login'>Wapas try karein</a>"
        
    # Ek basic HTML string taaki pehle template banane ki zaroorat na pade
    return """
    <div style="font-family:sans-serif; max-width:300px; margin:50px auto; padding:20px; border:1px solid #ccc; border-radius:10px;">
        <h2>Admin Login</h2>
        <form method="POST">
            <input name="username" placeholder="Username" style="width:100%; padding:10px; margin-bottom:10px;"><br>
            <input name="password" type="password" placeholder="Password" style="width:100%; padding:10px; margin-bottom:10px;"><br>
            <button type="submit" style="width:100%; padding:10px; background:#1e293b; color:white; border:none; border-radius:5px;">Login</button>
        </form>
    </div>
    """

@app.route("/dashboard")
def dashboard():
    if "admin_id" not in session:
        return redirect(url_for("login"))
    return f"Welcome {session['admin_name']}! App successfully chal raha hai. <br><a href='/logout'>Logout</a>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
