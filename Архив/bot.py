import os
import disnake
from disnake.ext import commands
import asyncio
import json
from typing import Dict

# Токен бота и ID владельца
TOKEN = "tokin😋"
OWNER_ID = "698844733954588692"

# Пути к файлам данных
DATA_FOLDER = "data"
BOUND_CHANNELS_FILE = os.path.join(DATA_FOLDER, "bound_channels.json")
SENT_CLIPS_FILE = os.path.join(DATA_FOLDER, "sent_clips.json")
USER_LANGUAGES_FILE = os.path.join(DATA_FOLDER, "user_languages.json")

# Проверяем, существует ли папка данных
os.makedirs(DATA_FOLDER, exist_ok=True)

# Функции для загрузки и сохранения JSON
def load_json(file_path: str) -> Dict:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_json(file_path: str, data: Dict):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Загружаем сохранённые данные
bound_channels = load_json(BOUND_CHANNELS_FILE)
sent_clips = load_json(SENT_CLIPS_FILE)
user_languages = load_json(USER_LANGUAGES_FILE)

# Сообщения об ошибках
ERROR_CODES = {
    "KeyError": "❌ Ошибка: Неверный путь к папке. Проверьте, существует ли папка.",
    "FileNotFoundError": "❌ Ошибка: Файл не найден. Проверьте, существует ли файл.",
    "PermissionError": "❌ Ошибка: У вас недостаточно прав для доступа к этому файлу.",
    "OSError": "❌ Ошибка: Произошла ошибка файловой системы.",
}

# Инициализация бота
intents = disnake.Intents.default()
intents.message_content = True
bot = commands.InteractionBot(intents=intents)

# Функция отправки сообщения об ошибке
async def send_error_message(interaction, error_code: str):
    error_message = ERROR_CODES.get(error_code, "❌ Ошибка: Неизвестная ошибка.")
    await interaction.response.send_message(f"{error_message}", ephemeral=False)

# Команда информации
@bot.slash_command(name="info", description="Информация о боте и его создателе.")
async def info(interaction: disnake.ApplicationCommandInteraction):
    info_message = (
        "🤖 Информация о боте:\n"
        "Этот бот помогает управлять клипами и их отправкой.\n\n"
        "Создатель: @vencyeditor"
    )
    await interaction.response.send_message(info_message, ephemeral=False)

# Главная команда для настроек
@bot.slash_command(name="settings", description="Настройки бота через выпадающее меню.")
async def settings(interaction: disnake.ApplicationCommandInteraction):
    select = disnake.ui.StringSelect(
        placeholder="🔧 Выберите настройку для конфигурации",
        options=[
            disnake.SelectOption(label="📁 Привязка папки", description="Привязать папку к каналу", value="bind_folder"),
            disnake.SelectOption(label="📤 Отправить клипы", description="Отправить клипы из папки", value="send_clips"),
            disnake.SelectOption(label="🌍 Смена языка", description="Изменить язык интерфейса", value="change_language"),
        ]
    )

    async def select_callback(interaction: disnake.MessageInteraction):
        selected_option = interaction.data["values"][0]

        if selected_option == "bind_folder":
            await interaction.response.send_message("Введите путь к папке для привязки:", ephemeral=True)

            def check(msg):
                return msg.author == interaction.user and isinstance(msg.channel, disnake.TextChannel)

            try:
                msg = await bot.wait_for("message", check=check, timeout=60)
                folder_path = msg.content

                if os.path.isdir(folder_path):
                    bound_channels[str(interaction.channel.id)] = folder_path
                    sent_clips[folder_path] = set()
                    save_json(BOUND_CHANNELS_FILE, bound_channels)
                    save_json(SENT_CLIPS_FILE, sent_clips)
                    await interaction.channel.send(f"📁 Папка `{folder_path}` успешно привязана к каналу `{interaction.channel.name}`.")
                else:
                    await send_error_message(interaction, "KeyError")
            except asyncio.TimeoutError:
                await interaction.response.send_message("⏰ Время ожидания истекло. Попробуйте снова.", ephemeral=True)

        elif selected_option == "send_clips":
            second_select = disnake.ui.StringSelect(
                placeholder="📤 Выберите опцию для отправки клипов",
                options=[
                    disnake.SelectOption(label="📁 Отправить все клипы в этот канал", description="Отправить все клипы в текущий канал", value="send_all_this_channel"),
                    disnake.SelectOption(label="📤 Отправить все клипы по всем каналам", description="Отправить все клипы по всем привязанным каналам", value="send_all_channels"),
                    disnake.SelectOption(label="🆕 Отправить все новые клипы в этот канал", description="Отправить только новые клипы в текущий канал", value="send_new_this_channel"),
                    disnake.SelectOption(label="🆕 Отправить все новые клипы по всем каналам", description="Отправить только новые клипы по всем привязанным каналам", value="send_new_channels"),
                ]
            )

            async def second_select_callback(interaction: disnake.MessageInteraction):
                second_option = interaction.data["values"][0]

                if second_option == "send_all_this_channel":
                    await send_all(interaction)
                elif second_option == "send_all_channels":
                    await send_all_channels(interaction)
                elif second_option == "send_new_this_channel":
                    await send_new(interaction)
                elif second_option == "send_new_channels":
                    await send_new_channels(interaction)

            second_select.callback = second_select_callback
            await interaction.response.send_message("📤 Выберите опцию для отправки клипов:", components=[disnake.ui.ActionRow(second_select)])

        elif selected_option == "change_language":
            language_select = disnake.ui.StringSelect(
                placeholder="🌐 Выберите язык интерфейса",
                options=[
                    disnake.SelectOption(label="Русский", description="Изменить язык на русский", value="ru"),
                    disnake.SelectOption(label="Английский", description="Изменить язык на английский", value="en"),
                ]
            )

            async def language_select_callback(interaction: disnake.MessageInteraction):
                language = interaction.data["values"][0]

                if language in ["ru", "en"]:
                    user_languages[str(interaction.user.id)] = language
                    save_json(USER_LANGUAGES_FILE, user_languages)
                    await interaction.response.send_message(f"🌐 Язык интерфейса изменён на `{language.upper()}`.", ephemeral=True)
                else:
                    await interaction.response.send_message("🚫 Неверный язык. Пожалуйста, выберите RU или EN.", ephemeral=True)

            language_select.callback = language_select_callback
            await interaction.response.send_message("🌐 Выберите язык интерфейса:", components=[disnake.ui.ActionRow(language_select)])

    select.callback = select_callback
    await interaction.response.send_message("🔧 Выберите настройку для конфигурации", components=[disnake.ui.ActionRow(select)])

# Функции отправки клипов
async def send_all(interaction: disnake.ApplicationCommandInteraction):
    if str(interaction.channel.id) in bound_channels:
        folder_path = bound_channels[str(interaction.channel.id)]
        clips = os.listdir(folder_path)
        for clip in clips:
            try:
                with open(os.path.join(folder_path, clip), "rb") as f:
                    await interaction.channel.send(file=disnake.File(f, clip))
                sent_clips[folder_path].add(clip)
            except Exception as e:
                await send_error_message(interaction, type(e).__name__)
        save_json(SENT_CLIPS_FILE, sent_clips)
        await interaction.response.send_message("📤 Все клипы были отправлены.")
    else:
        await interaction.response.send_message("🚫 Папка не привязана к этому каналу.")

async def send_new(interaction: disnake.ApplicationCommandInteraction):
    if str(interaction.channel.id) in bound_channels:
        folder_path = bound_channels[str(interaction.channel.id)]
        new_clips = [clip for clip in os.listdir(folder_path) if clip not in sent_clips.get(folder_path, set())]
        for clip in new_clips:
            try:
                with open(os.path.join(folder_path, clip), "rb") as f:
                    await interaction.channel.send(file=disnake.File(f, clip))
                sent_clips[folder_path].add(clip)
            except Exception as e:
                await send_error_message(interaction, type(e).__name__)
        save_json(SENT_CLIPS_FILE, sent_clips)
        await interaction.response.send_message("🆕 Новые клипы были отправлены.")
    else:
        await interaction.response.send_message("🚫 Папка не привязана к этому каналу.")

async def send_all_channels(interaction: disnake.ApplicationCommandInteraction):
    if bound_channels:
        for channel_id, folder_path in bound_channels.items():
            channel = bot.get_channel(int(channel_id))
            if channel:
                clips = os.listdir(folder_path)
                for clip in clips:
                    try:
                        with open(os.path.join(folder_path, clip), "rb") as f:
                            await channel.send(file=disnake.File(f, clip))
                        sent_clips[folder_path].add(clip)
                    except Exception as e:
                        await send_error_message(interaction, type(e).__name__)
        save_json(SENT_CLIPS_FILE, sent_clips)
        await interaction.response.send_message("📤 Все клипы были отправлены по всем каналам.")
    else:
        await interaction.response.send_message("🚫 Нет привязанных каналов.")

async def send_new_channels(interaction: disnake.ApplicationCommandInteraction):
    if bound_channels:
        for channel_id, folder_path in bound_channels.items():
            channel = bot.get_channel(int(channel_id))
            if channel:
                new_clips = [clip for clip in os.listdir(folder_path) if clip not in sent_clips.get(folder_path, set())]
                for clip in new_clips:
                    try:
                        with open(os.path.join(folder_path, clip), "rb") as f:
                            await channel.send(file=disnake.File(f, clip))
                        sent_clips[folder_path].add(clip)
                    except Exception as e:
                        await send_error_message(interaction, type(e).__name__)
        save_json(SENT_CLIPS_FILE, sent_clips)
        await interaction.response.send_message("🆕 Новые клипы были отправлены по всем каналам.")
    else:
        await interaction.response.send_message("🚫 Нет привязанных каналов.")

# Запуск бота
bot.run(TOKEN)
