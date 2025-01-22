import requests
import json
import time
from datetime import datetime, timedelta

# Введите ваш токен и ID пользователя
TOKEN = "tokin😋"
INPUT_USER_ID = "698844733954588692"  # ID пользователя, чьи сообщения будут в input
RESPONSE_USER_ID = "998266043946504313"  # ID пользователя, чьи сообщения будут в response
LIMIT = 50  # Количество сообщений за один запрос
TOTAL_MESSAGES = 2000  # Общее количество сообщений для парсинга

# URL для получения сообщений из личного чата
url = f"https://discord.com/api/v9/users/@me/channels"

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

# Получаем список каналов (включая ЛС)
response = requests.get(url, headers=headers)
channels = response.json()

# Находим личный канал с указанным пользователем (RESPONSE_USER_ID)
dm_channel = None
for channel in channels:
    if channel["type"] == 1 and RESPONSE_USER_ID in [user["id"] for user in channel["recipients"]]:
        dm_channel = channel["id"]
        break

if dm_channel:
    messages_dict = {}
    last_message_id = None
    total_fetched = 0

    # Получаем сообщения
    while total_fetched < TOTAL_MESSAGES:
        params = {"limit": LIMIT}
        if last_message_id:
            params["before"] = last_message_id

        url_messages = f"https://discord.com/api/v9/channels/{dm_channel}/messages"
        response = requests.get(url_messages, headers=headers, params=params)
        
        
        # Проверка на успешный запрос
        if response.status_code != 200:
            print(f"Ошибка запроса: {response.status_code}")
            break
        
        messages = response.json()

        # Проверка на пустой ответ
        if not messages:
            print("Достигнут конец сообщений, больше сообщений нет.")
            break

        for message in messages:
            timestamp_str = message["timestamp"]
            # Парсим временную метку с учетом смещения по времени
            message_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if message["content"]:  # Проверяем, что сообщение не пустое
                messages_dict[message["id"]] = {
                    "content": message["content"],
                    "timestamp": message_time,
                    "author_id": message["author"]["id"]
                }

        last_message_id = messages[-1]["id"]
        total_fetched += len(messages)

        print(f"Получено {total_fetched} сообщений...")

        if len(messages) < LIMIT:
            print("Меньше сообщений, чем лимит. Возможно, достигнут конец истории сообщений.")
            break

        time.sleep(1)  # Пауза для избегания превышения лимита запросов

    # Найдем пары сообщений и ответов и создадим форматированный вывод
    message_pairs = []
    input_messages = []  # Список для хранения последовательных сообщений пользователя
    used_messages = set()  # Множество для отслеживания использованных сообщений
    message_counter = 1045  # Счетчик для уникальных идентификаторов сообщений

    def get_user_id(author_id):
        return "u0" if author_id == INPUT_USER_ID else "u2"  # Присваиваем идентификаторы пользователям

    for message_id, message_data in messages_dict.items():
        if message_id in used_messages:
            continue

        if message_data["author_id"] == INPUT_USER_ID or message_data["author_id"] == RESPONSE_USER_ID:
            formatted_message = f"L{message_counter} +++$+++ {get_user_id(message_data['author_id'])} +++$+++ m0 +++$+++ {'BIANCA' if message_data['author_id'] == INPUT_USER_ID else 'CAMERON'} +++$+++ {message_data['content']}"
            message_pairs.append(formatted_message)
            message_counter += 1
            used_messages.add(message_id)

    # Сохраняем форматированные пары сообщений в файл
    with open("dialogues_formatted.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(message_pairs))

    print(f"Сообщения успешно сохранены в dialogues_formatted.txt")
else:
    print(f"Не удалось найти ЛС с пользователем с ID {RESPONSE_USER_ID}")
