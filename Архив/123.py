import disnake
from disnake.ext import commands
import asyncio
import websockets
import json
import random
import logging
from PIL import Image, ImageDraw, ImageFont
import io
import time
import string
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота
intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Словари для хранения задержек
cooldowns = {
    'players': {}
}

# Вспомогательная функция для генерации случайного значения для RANDOMCHEAT
def generate_random_cheat():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Вспомогательная функция для выполнения /join запроса и получения токена и хоста
async def join_lobby_and_get_token(lobby_id, nickname="default_nickname"):
    url = "https://api.eg.rivet.gg/matchmaker/lobbies/join"
    headers = {
        "Origin": "https://devast.io"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json={"lobby_id": lobby_id, "nickname": nickname}, headers=headers) as response:
                logging.info(f"POST {url} with payload {json.dumps({'lobby_id': lobby_id, 'nickname': nickname})} responded with status {response.status}")
                if response.status == 200:
                    data = await response.json()
                    player_token = data.get("player", {}).get("token", "")
                    hostname = data.get("ports", {}).get("default", {}).get("hostname", "")
                    return player_token, hostname
                else:
                    logging.error(f"Ошибка при запросе /join: {response.status}, тело ответа: {await response.text()}")
                    return "", ""
        except Exception as e:
            logging.error(f"Ошибка при выполнении запроса /join: {e}")
            return "", ""

# Вспомогательная функция для работы с WebSocket и получения данных о игроках
async def get_player_data_from_server(token, hostname):
    ws_url = f"wss://{hostname}/?token={token}"
    try:
        async with websockets.connect(ws_url) as ws:
            random_cheat = generate_random_cheat()
            token_id = random.randint(1, 10000)

            # Отправляем сообщение с использованием токена
            message = [30, random_cheat, str(token_id), 62, 0, random_cheat, 0, 0, 0]
            await ws.send(json.dumps(message))
            logging.info(f"Сообщение отправлено через WebSocket: {message}")

            # Получаем только первое сообщение
            response = await ws.recv()
            logging.info(f"Получено сообщение от WebSocket: {response}")

            # Преобразование строки в JSON-объект
            try:
                response_list = json.loads(response)
                logging.info(f"Декодированный ответ от WebSocket: {response_list}")
            except json.JSONDecodeError:
                logging.error(f"Ошибка декодирования JSON: {response}")
                return None

            # Логика обработки ответа
            if isinstance(response_list, list):
                # Игнорируем первое и последнее значение
                filtered_response = response_list[1:-1]

                # Создаем список кортежей (никнейм, ID в списке)
                players = [(str(item), index + 1) for index, item in enumerate(filtered_response) if isinstance(item, str)]
                return players
            else:
                logging.error(f"Получен неожиданный формат данных: {response_list}")
                return None

    except Exception as e:
        logging.error(f"Ошибка при работе с WebSocket: {e}, URL: {ws_url}")
        return None

# Функция для форматирования текста с игроками
def format_players_text(players):
    # Параметры
    max_length = 16  # Максимум символов для никнейма
    max_line_length = 80  # Максимум символов в строке
    separator = ' ' * 4  # Разделитель между элементами

    lines = []
    current_line = ""

    for name, player_id in players:
        formatted_player = f"{name[:max_length]}#{player_id}"
        if len(current_line) + len(formatted_player) + len(separator) <= max_line_length:
            if current_line:
                current_line += separator
            current_line += formatted_player
        else:
            lines.append(current_line)
            current_line = formatted_player
    
    if current_line:
        lines.append(current_line)

    # Добавляем общее количество игроков
    total_text = f"\n\nВсего игроков: {len(players)}"
    return "\n".join(lines) + total_text

# Команда /players
@bot.slash_command(description="Получить список игроков из лобби")
async def players(ctx, lobby_id: str):
    await ctx.response.defer()  # Откладываем ответ, чтобы избежать тайм-аутов

    user_id = ctx.author.id
    current_time = time.time()

    # Проверка задержки для пользователя
    if user_id in cooldowns['players'] and current_time - cooldowns['players'][user_id] < 60:
        remaining_time = 60 - (current_time - cooldowns['players'][user_id])
        await ctx.edit_original_response(content=f"Пожалуйста, подождите {remaining_time:.1f} секунд перед следующим использованием команды.")
        return

    # Получение токена и хоста через /join запрос
    player_token, hostname = await join_lobby_and_get_token(lobby_id)
    if not player_token or not hostname:
        await ctx.edit_original_response(content="Не удалось получить токен или хост для лобби. Попробуйте позже.")
        return

    player_data = await get_player_data_from_server(player_token, hostname)

    if player_data:
        # Форматирование текста с игроками
        player_list_text = format_players_text(player_data)

        # Отправка текста с игроками
        await ctx.edit_original_response(content=f"```{player_list_text}```")
        cooldowns['players'][user_id] = current_time
    else:
        await ctx.edit_original_response(content="Не удалось получить данные о игроках. Попробуйте позже.")

# Запуск бота
bot.run('tokin😋')