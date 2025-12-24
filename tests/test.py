from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Передаем список, содержащий один объект-хешер
hasher = PasswordHash([Argon2Hasher()])

def main():
    password = input("Введите новый пароль: ")
    
    # Генерация хеша
    hashed_password = hasher.hash(password)
    
    print(f"\nВаш хеш Argon2:\n{hashed_password}\n")

    test_pass = input("Введите пароль еще раз для проверки: ")
    
    if hasher.verify(test_pass, hashed_password):
        print("✅ Успех!")
    else:
        print("❌ Ошибка!")

if __name__ == "__main__":
    main()