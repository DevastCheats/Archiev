import discord
from discord.ext import commands
import json
import os
import logging
import traceback

# Log file setup
LOG_FILE = "bot_errors.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_error(error):
    logging.error(f"Exception occurred: {error}")
    logging.error(traceback.format_exc())

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "voice_channels.json"
CHANNEL_ID_FILE = "channel_id.txt"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def load_channel_id():
    if os.path.exists(CHANNEL_ID_FILE):
        with open(CHANNEL_ID_FILE, "r") as file:
            return file.read().strip()
    return None

def save_channel_id(channel_id):
    with open(CHANNEL_ID_FILE, "w") as file:
        file.write(channel_id)

voice_channels = load_data()
existing_channel_id = load_channel_id()

class VoiceRoomView(discord.ui.View):
    def __init__(self, is_leader):
        super().__init__(timeout=None)
        self.is_leader = is_leader
        self.setup_buttons()

    def setup_buttons(self):
        if self.is_leader:
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="rename", emoji="<:emoji:1283321369555238912>"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="set_limit", emoji="<:emoji:1283321181625122847>"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="close_open_room", emoji="<:emoji:1283321100687642659>"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="reset", emoji="🔁"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="kick_and_deny", emoji="<:emoji:1283321053392666685>"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="grant_role_access", emoji="<:emoji:1283321307102052353>"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="change_leader", emoji="<:emoji:1283321260436099123>"))
            self.add_item(discord.ui.Button(label="", style=discord.ButtonStyle.secondary, custom_id="move_up", emoji="<:emoji:1283320991207915520>"))
        else:
            for button in self.children:
                button.disabled = True

class RenameRoomModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Изменить название комнаты")
        self.channel_id = channel_id
        self.new_name = discord.ui.TextInput(label="Новое название", placeholder="Введите новое название комнаты", required=True)
        self.add_item(self.new_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                await channel.edit(name=self.new_name.value)
                await interaction.response.send_message(f"Название комнаты изменено на {self.new_name.value}.", ephemeral=True)
        except Exception as error:
            log_error(error)
            await interaction.response.send_message("Произошла ошибка при изменении названия комнаты.", ephemeral=True)

class SetLimitModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Установить лимит участников")
        self.channel_id = channel_id
        self.limit_input = discord.ui.TextInput(label="Лимит участников", placeholder="Введите число от 1 до 99", required=True)
        self.add_item(self.limit_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel = interaction.guild.get_channel(self.channel_id)
            limit = int(self.limit_input.value)
            if channel and 1 <= limit <= 99:
                await channel.edit(user_limit=limit)
                await interaction.response.send_message(f"Лимит участников изменён на {limit}.", ephemeral=True)
            else:
                await interaction.response.send_message("Введите корректное значение лимита (от 1 до 99).", ephemeral=True)
        except Exception as error:
            log_error(error)
            await interaction.response.send_message("Произошла ошибка при установке лимита.", ephemeral=True)

class UserSelectMenu(discord.ui.Select):
    def __init__(self, options, channel_id):
        super().__init__(placeholder="Выберите пользователя для выгнания", options=options)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_user_id = int(self.values[0])
            voice_channel = interaction.guild.get_channel(self.channel_id)
            if voice_channel:
                user = interaction.guild.get_member(selected_user_id)
                if user:
                    await user.move_to(None)
                    await voice_channel.set_permissions(user, connect=False)
                    await interaction.response.send_message(f"{user.display_name} был выгнан и лишен доступа.", ephemeral=True)
                else:
                    await interaction.response.send_message("Выбранный участник не найден.", ephemeral=True)
            else:
                await interaction.response.send_message("Комната не найдена.", ephemeral=True)
        except Exception as error:
            log_error(error)
            await interaction.response.send_message("Произошла ошибка при выгнании участника.", ephemeral=True)

class RoleSelectMenu(discord.ui.Select):
    def __init__(self, options, channel_id):
        super().__init__(placeholder="Выберите роль для предоставления доступа", options=options)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_role_id = int(self.values[0])
            voice_channel = interaction.guild.get_channel(self.channel_id)
            role = interaction.guild.get_role(selected_role_id)
            
            if not voice_channel:
                await interaction.response.send_message("Голосовой канал не найден.", ephemeral=True)
                return
            
            if not role:
                await interaction.response.send_message("Роль не найдена.", ephemeral=True)
                return

            await voice_channel.set_permissions(role, connect=True)
            await interaction.response.send_message(f"Доступ к комнате предоставлен роли {role.name}.", ephemeral=True)

            current_permissions = voice_channel.overwrites_for(interaction.guild.default_role)
            new_perms = not current_permissions.connect

            # Устанавливаем права для всех
            await voice_channel.set_permissions(interaction.guild.default_role, connect=False)

            # Убедимся, что лидер всегда имеет права на подключение
            await voice_channel.set_permissions(member, connect=True)
                
            status = 'открыта' if new_perms else 'закрыта'
            await interaction.response.send_message(f"Комната теперь {status} для всех.", ephemeral=True)

        except Exception as error:
            log_error(error)
            await interaction.response.send_message("Произошла ошибка при предоставлении доступа роли.", ephemeral=True)


class LeaderSelectMenu(discord.ui.Select):
    def __init__(self, options, channel_id):
        super().__init__(placeholder="Выберите нового лидера", options=options)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_user_id = int(self.values[0])
            if interaction.user.id == voice_channels[self.channel_id]["leader_id"]:
                voice_channels[self.channel_id]["leader_id"] = selected_user_id
                save_data(voice_channels)
                
                selected_user = interaction.guild.get_member(selected_user_id)
                if selected_user:
                    await interaction.response.send_message(f"{selected_user.display_name} теперь является лидером комнаты.", ephemeral=True)
                else:
                    await interaction.response.send_message("Выбранный участник не найден.", ephemeral=True)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)
        except Exception as error:
            log_error(error)
            await interaction.response.send_message("Произошла ошибка при выборе нового лидера.", ephemeral=True)

@bot.event
async def on_ready():
    global voice_channels
    for channel_id in list(voice_channels.keys()):
        channel = bot.get_channel(channel_id)
        if not channel:
            del voice_channels[channel_id]
    save_data(voice_channels)
    
    # Проверка существующего голосового канала
    if existing_channel_id:
        existing_channel = bot.get_channel(int(existing_channel_id))
        if existing_channel:
            print(f"Использование существующего канала для создания войса: {existing_channel.name}")
            if existing_channel.id not in voice_channels:
                # Добавляем существующий канал как новый
                voice_channels[existing_channel.id] = {
                    "owner_id": None,
                    "type": "create_room"
                }
                save_data(voice_channels)
                print(f"Канал {existing_channel.name} добавлен в активные.")
        else:
            print("Существующий ID голосового канала недействителен или канал не существует.")
            save_channel_id("")  # Очистить недействительный ID

    print(f"Bot {bot.user} is ready!")

@bot.command(name="create_voice")
@commands.has_permissions(administrator=True)
async def create_voice(ctx):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.voice_channels, name=" + | Создать канал")
    if existing_channel:
        await ctx.send(f"Комната для создания уже существует: {existing_channel.name}")
        save_channel_id(str(existing_channel.id))
        return

    voice_channel = await guild.create_voice_channel(f" + | Создать канал")
    voice_channels[voice_channel.id] = {"owner_id": None, "type": "create_room"}
    save_data(voice_channels)
    save_channel_id(str(voice_channel.id))
    await ctx.send(f"Создан войс: {voice_channel.name}")

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if after.channel and after.channel.id in voice_channels:
            if voice_channels[after.channel.id]["type"] == "create_room":
                category = after.channel.category
                new_voice_channel = await after.channel.guild.create_voice_channel(f"Комната {member.display_name}", category=category, user_limit=3)
                
                overwrite = discord.PermissionOverwrite()
                overwrite.connect = True
                # Используем after.channel.guild для получения гильдии
                await new_voice_channel.set_permissions(after.channel.guild.default_role, overwrite=overwrite)
                
                await member.move_to(new_voice_channel)

                voice_channels[new_voice_channel.id] = {
                    "owner_id": member.id,
                    "type": "private_room",
                    "leader_id": member.id
                }
                save_data(voice_channels)

        if before.channel and before.channel.id in voice_channels:

            if len(before.channel.members) == 0 and voice_channels[before.channel.id]["type"] == "private_room":
                del voice_channels[before.channel.id]
                save_data(voice_channels)
                await before.channel.delete()
            if len(before.channel.members) == 1 and voice_channels[before.channel.id]["type"] == "private_room":
                last_member = before.channel.members[0]
                voice_channels[before.channel.id]["leader_id"] = last_member.id
    except Exception as error:
        log_error(error)

async def send_room_menu(member, voice_channel):
    leader_id = voice_channels[voice_channel.id]["leader_id"]
    is_leader = leader_id == member.id
    embed = discord.Embed(title=f"Управление комнатой", description="Управление вашей голосовой комнатой. \n<:emoji:1283321100687642659> - Закрыть/Открыть комнату\n<:emoji:1283321369555238912> - Изменить название комнаты\n<:emoji:1283321053392666685> - Выгнать и закрыть вход пользователю\n<:emoji:1283321260436099123> - Передать лидерство\n<:emoji:1283321181625122847> - Задать лимит пользователей\n<:emoji:1283320991207915520> - Поднять комнату в верх\n<:emoji:1283321307102052353> - Дать доступ роли\n🔁 - Ресет изменений этого войса. ")
    view = VoiceRoomView(voice_channel.id, is_leader)
    # Отправляем сообщение в текстовый канал, в который был вызван бот
    await member.send(embed=embed, view=view)

# Команда для отправки меню
@bot.command(name="menu")
@commands.has_permissions(administrator=True)
async def menu(ctx):
    embed = discord.Embed(
        title=f"Управление комнатой",
        description="<:emoji:1283321100687642659> Закрыть/Открыть комнату\n"
                    "<:emoji:1283321369555238912> Изменить название комнаты\n"
                    "<:emoji:1283321053392666685> Выгнать и закрыть доступ пользователю\n"
                    "<:emoji:1283321260436099123> Передать лидерство\n"
                    "<:emoji:1283321181625122847> Задать лимит пользователей\n"
                    "<:emoji:1283320991207915520> Поднять комнату в верх\n"
                    "<:emoji:1283321307102052353> Дать доступ роли\n"
                    "🔁 Ресет изменений этого войса."
    )
    view = VoiceRoomView(is_leader=True)
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        member = interaction.user
        channel_id = None
        custom_id = interaction.data.get("custom_id")
        voice_channel_id = interaction.channel.id

        # Найти канал, где пользователь является лидером
        for channel, data in voice_channels.items():
            if data.get("leader_id") == member.id:
                channel_id = channel
                break

        if channel_id is None:
            await interaction.response.send_message("Вы не являетесь лидером ни одной комнаты или данные о канале отсутствуют.", ephemeral=True)
            return

        voice_channel = interaction.guild.get_channel(int(channel_id))

        if voice_channel is None:
            await interaction.response.send_message("Голосовой канал не найден или был удален.", ephemeral=True)
            return

        if custom_id == "rename":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                modal = RenameRoomModal(voice_channel.id)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)

        elif custom_id == "set_limit":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                modal = SetLimitModal(voice_channel.id)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)

        if custom_id == "close_open_room":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                current_permissions = voice_channel.overwrites_for(interaction.guild.default_role)
                new_perms = not current_permissions.connect

                # Устанавливаем права для всех
                await voice_channel.set_permissions(interaction.guild.default_role, connect=new_perms)

                # Убедимся, что лидер всегда имеет права на подключение
                await voice_channel.set_permissions(member, connect=True)
                
                status = 'открыта' if new_perms else 'закрыта'
                await interaction.response.send_message(f"Комната теперь {status} для всех.", ephemeral=True)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)

        elif custom_id == "reset":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                leader_id = voice_channels[voice_channel.id].get("leader_id")
                if leader_id:
                    leader = interaction.guild.get_member(leader_id)
                    await voice_channel.edit(name=f"Комната {leader.display_name if leader else 'Лидер'}")
                
                # Удаление всех пользовательских прав у ролей
                for role in interaction.guild.roles:
                    if role.id != interaction.guild.default_role.id:
                        current_perms = voice_channel.overwrites_for(role)
                        if current_perms.connect:
                            await voice_channel.set_permissions(role, connect=None)
                
                # Сброс лимита пользователей и открытие доступа для всех
                await voice_channel.edit(user_limit=None)
                await voice_channel.set_permissions(interaction.guild.default_role, connect=True)
                
                await interaction.response.send_message("Настройки комнаты были сброшены.", ephemeral=True)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)


        elif custom_id == "kick_and_deny":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                members = [m for m in voice_channel.members]
                if members:
                    options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members]
                    view = discord.ui.View()
                    select_menu = UserSelectMenu(options, voice_channel_id)
                    view.add_item(select_menu)
                    await interaction.response.send_message("Выберите пользователя для выгнания:", view=view, ephemeral=True)
                else:
                    await interaction.response.send_message("В комнате нет участников для выгнания.", ephemeral=True)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)

        elif custom_id == "grant_role_access":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                # Найти голосовой канал, в котором находится лидер
                leader_voice_channel = member.voice.channel
                if leader_voice_channel is None:
                    await interaction.response.send_message("Вы не находитесь в голосовом канале.", ephemeral=True)
                    return
                
                # Получить роли, которые лидер может предоставить
                roles = [r for r in interaction.guild.roles if r.id in [role.id for role in member.roles]]
                if roles:
                    options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles]
                    view = discord.ui.View()
                    select_menu = RoleSelectMenu(options, leader_voice_channel.id)
                    view.add_item(select_menu)
                    await interaction.response.send_message("Выберите роль для предоставления доступа:", view=view, ephemeral=True)
                else:
                    await interaction.response.send_message("У вас нет ролей для предоставления доступа.", ephemeral=True)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)

        elif custom_id == "change_leader":
            members = [m for m in voice_channel.members if m.id != voice_channels[voice_channel.id]["leader_id"]]
            if members:
                options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members]
                view = discord.ui.View()
                select_menu = LeaderSelectMenu(options, voice_channel.id)
                view.add_item(select_menu)
                await interaction.response.send_message("Выберите нового лидера:", view=view, ephemeral=True)
            else:
                await interaction.response.send_message("Нет участников для передачи лидерства.", ephemeral=True)

        elif custom_id == "move_up":
            if member.id == voice_channels[voice_channel.id]["leader_id"]:
                await voice_channel.edit(position=2)
                await interaction.response.send_message("Комната была поднята в верх списка.", ephemeral=True)
            else:
                await interaction.response.send_message("Вы не являетесь лидером этой комнаты.", ephemeral=True)
                
    except Exception as error:
        log_error(error)
        await interaction.response.send_message("Произошла ошибка.", ephemeral=True)

bot.run("tokin😋")