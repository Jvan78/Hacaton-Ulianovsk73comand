from passlib.hash import bcrypt

password = "password123"  # ≤72 символов
hashed = bcrypt.hash(password)

print(hashed)
