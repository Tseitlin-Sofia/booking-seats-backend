from pwdlib import PasswordHash

ph = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    """Хеширует пароль для последующего хранения в БД."""
    return ph.hash(password)
