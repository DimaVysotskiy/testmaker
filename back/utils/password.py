from pwdlib import PasswordHash


class PasswordChacker:
    def __init__(self):
        self.password_hash = PasswordHash.recommended()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.password_hash.hash(password)


password_checker = PasswordChacker()