import base64

def decode_base64_to_16bit(encoded_str):
    # Декодируем строку Base64 в байты
    decoded_bytes = base64.b64decode(encoded_str)
    
    # Проверяем, что длина данных кратна 2, иначе это невалидные 16-битные данные
    if len(decoded_bytes) % 2 != 0:
        raise ValueError("Длина данных должна быть кратна 2 для 16-битного декодирования.")
    
    # Преобразуем байты в 16-битные числа (big-endian)
    decoded_16bit = [
        (decoded_bytes[i] << 8) | decoded_bytes[i + 1]  # Объединяем два байта в 16-битное число
        for i in range(0, len(decoded_bytes), 2)
    ]
    
    return decoded_16bit

while True:
    # Запрос на ввод Base64 строки
    encoded_str = input("Введите строку Base64 для расшифровки (или 'выход' для завершения): ")
    
    # Проверяем, хочет ли пользователь выйти
    if encoded_str.lower() == 'выход':
        print("Завершение программы.")
        break
    
    try:
        decoded_data = decode_base64_to_16bit(encoded_str)
        print("Расшифрованные 16-битные данные:", decoded_data)
    except Exception as e:
        print("Ошибка при расшифровке:", str(e))
