# scripts/generate_hash.py
from passlib.hash import bcrypt
pwd = "password123"    # поменяй на желаемый пароль
print(bcrypt.hash(pwd))
