#!/usr/bin/env python3
"""
Генератор SECRET_KEY для Flask
"""

import secrets
import string

def generate_secret_key(length=32):
    """Генерувати безпечний SECRET_KEY"""
    # Використовуємо букви, цифри та деякі спеціальні символи
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_hex_key(length=32):
    """Генерувати hex SECRET_KEY"""
    return secrets.token_hex(length)

if __name__ == "__main__":
    print("🔐 Генератор SECRET_KEY для Flask\n")
    
    # Генеруємо різні варіанти
    simple_key = generate_secret_key(32)
    hex_key = generate_hex_key(16)  # 16 bytes = 32 hex chars
    
    print("Варіант 1 (рекомендований для .env):")
    print(f"SECRET_KEY={simple_key}")
    
    print(f"\nВаріант 2 (hex):")
    print(f"SECRET_KEY={hex_key}")
    
    print(f"\nВиберіть будь-який варіант та вставте в ваш .env файл")
    print("Без лапок, без префіксів, просто як рядок!")