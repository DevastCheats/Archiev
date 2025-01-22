import re

def decode_obfuscated_strings(code):
    """Декодирует обфусцированные строки, закодированные в шестнадцатеричном формате."""
    def replacer(match):
        return bytes.fromhex(match.group(1)).decode('utf-8')
    
    return re.sub(r'\\x([0-9a-fA-F]{2})', replacer, code)

def replace_obfuscated_names(code, mapping):
    """Заменяет обфусцированные имена на понятные имена на основе словаря."""
    for obfuscated_name, clear_name in mapping.items():
        # Использование \b для целых слов
        code = re.sub(r'\b{}\b'.format(re.escape(obfuscated_name)), clear_name, code)
    return code

def read_code_from_file(filename):
    """Читает код из файла, поддерживает большие файлы, читая их по частям."""
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

def write_code_to_file(filename, code):
    """Записывает декодированный и деобфусцированный код в файл."""
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(code)

def create_name_mapping():
    """Создает словарь маппинга обфусцированных имен на понятные имена."""
    # Пример маппинга, заполните его на основе анализа кода
    return {
    }

def deobfuscate_code(input_filename, output_filename):
    """Процесс деобфускации кода: чтение, декодирование и запись в новый файл."""
    # Шаг 1: Чтение обфусцированного кода из файла
    obfuscated_code = read_code_from_file(input_filename)
    
    # Шаг 2: Декодирование строк
    decoded_code = decode_obfuscated_strings(obfuscated_code)
    
    # Шаг 3: Создание маппинга имен
    name_mapping = create_name_mapping()
    
    # Шаг 4: Замена обфусцированных имен
    clear_code = replace_obfuscated_names(decoded_code, name_mapping)
    
    # Шаг 5: Запись декодированного и деобфусцированного кода в новый файл
    write_code_to_file(output_filename, clear_code)

    print(f"Декодированный и деобфусцированный код сохранен в {output_filename}")

# Укажите путь к вашему исходному файлу и файлу для сохранения
input_filename = '44.txt'
output_filename = '45.txt'

# Запуск процесса деобфускации
deobfuscate_code(input_filename, output_filename)