import json
import re
import time

# Тут путь указать надо, до файлика с RO правилами
json_file_path = 'input.json'


# А тут уже путь до скрипта, в котором нужно сделать замену
target_file_path = 'output.js'



with open(json_file_path, 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

replacements = {}
for item in data.get('data', []):
    for rule in item.get('rules', []):
        if rule.get('on') and rule.get('type') == 'normalOverride':
            match_url = rule['match'].replace('https://devast.io/', '')
            replace_url = rule['replace'].replace('https://devast.io/', '')
            replacements[match_url] = replace_url

with open(target_file_path, 'r', encoding='utf-8') as target_file:
    file_content = target_file.read()

for match, replace in replacements.items():
    file_content = re.sub(re.escape(match), replace, file_content)

with open(target_file_path, 'w', encoding='utf-8') as target_file:
    target_file.write(file_content)

print("Замены выполнены успешно.")
time.sleep(10)