from werkzeug.security import generate_password_hash
new_password = "Aman@500"
hashed = generate_password_hash(new_password)

print("Generated Hash:", hashed)
