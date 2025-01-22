import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
import json
import os

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

LOG_CHANNEL_ID = 123456789012345678  # Замените на ваш ID канала для логов
PUNISHMENTS_FILE = "punishments.json"
ROLE_BAN = 123456789012345678  # Замените на ваш ID роли для бана
ROLE_TEXT_MUTE = 123456789012345678  # Замените на ваш ID роли для текстового мута
ROLE_VOICE_MUTE = 123456789012345678  # Замените на ваш ID роли для голосового мута

class PunishmentTypeView(disnake.ui.View):
    def __init__(self, member: disnake.Member):
        super().__init__()
        self.member = member

    @disnake.ui.button(label="Ban", style=disnake.ButtonStyle.primary)
    async def ban(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        embed = disnake.Embed(title="Выберите длительность наказания")
        view = PunishmentDurationView(self.member, ROLE_BAN)
        await inter.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(label="Text Mute", style=disnake.ButtonStyle.primary)
    async def text_mute(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        embed = disnake.Embed(title="Выберите длительность наказания")
        view = PunishmentDurationView(self.member, ROLE_TEXT_MUTE)
        await inter.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(label="Voice Mute", style=disnake.ButtonStyle.primary)
    async def voice_mute(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        embed = disnake.Embed(title="Выберите длительность наказания")
        view = PunishmentDurationView(self.member, ROLE_VOICE_MUTE)
        await inter.response.edit_message(embed=embed, view=view)


class PunishmentDurationView(disnake.ui.View):
    def __init__(self, member: disnake.Member, punishment_role_id: int):
        super().__init__()
        self.member = member
        self.punishment_role_id = punishment_role_id

    @disnake.ui.button(label="1 hour", style=disnake.ButtonStyle.primary)
    async def one_hour(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 1)

    @disnake.ui.button(label="2 hours", style=disnake.ButtonStyle.primary)
    async def two_hours(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 2)

    @disnake.ui.button(label="4 hours", style=disnake.ButtonStyle.primary)
    async def four_hours(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 4)

    @disnake.ui.button(label="12 hours", style=disnake.ButtonStyle.primary)
    async def twelve_hours(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 12)

    @disnake.ui.button(label="1 day", style=disnake.ButtonStyle.primary)
    async def one_day(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 24)

    @disnake.ui.button(label="7 days", style=disnake.ButtonStyle.primary)
    async def seven_days(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 168)

    @disnake.ui.button(label="15 days", style=disnake.ButtonStyle.primary)
    async def fifteen_days(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 360)

    @disnake.ui.button(label="30 days", style=disnake.ButtonStyle.primary)
    async def thirty_days(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.select_duration(inter, 720)

    async def select_duration(self, inter: disnake.MessageInteraction, hours: int):
        end_time = datetime.utcnow() + timedelta(hours=hours)
        duration_seconds = hours * 3600

        modal = disnake.ui.Modal(
            title="Введите причину наказания",
            components=[
                disnake.ui.TextInput(
                    label="Причина",
                    placeholder="Введите причину наказания",
                    custom_id="reason"
                )
            ]
        )

        async def on_modal_submit(modal_inter: disnake.ModalInteraction):
            reason = modal_inter.text_inputs["reason"]
            embed = disnake.Embed(title="Наказание выдано", description=f"{self.member.mention} был наказан.", color=disnake.Color.green())
            embed.add_field(name="Тип наказания", value=disnake.utils.get(inter.guild.roles, id=self.punishment_role_id).name)
            embed.add_field(name="Причина", value=reason)
            embed.add_field(name="Длительность", value=f"{hours} часов")
            await modal_inter.response.send_message(embed=embed, ephemeral=True)

            punishments = []
            if os.path.exists(PUNISHMENTS_FILE):
                with open(PUNISHMENTS_FILE, "r") as file:
                    punishments = json.load(file)

            punishment = {
                "user_id": self.member.id,
                "punishment_role_id": self.punishment_role_id,
                "end_time": end_time.timestamp(),
                "active": True,
                "reason": reason,
                "guild_id": inter.guild.id
            }
            punishments.append(punishment)

            with open(PUNISHMENTS_FILE, "w") as file:
                json.dump(punishments, file, indent=4)

            role = inter.guild.get_role(self.punishment_role_id)
            if role:
                await self.member.add_roles(role)

            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            log_embed = disnake.Embed(title="Наказание выдано", color=disnake.Color.green())
            log_embed.add_field(name="Пользователь", value=self.member.mention)
            log_embed.add_field(name="Наказание выдано", value=role.name)
            log_embed.add_field(name="Причина", value=reason)
            await log_channel.send(embed=log_embed)

        modal.on_submit = on_modal_submit
        await inter.response.send_modal(modal)


class PunishmentHistoryView(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.current_page = 1

    async def update_history(self, inter: disnake.MessageInteraction):
        punishments = []
        if os.path.exists(PUNISHMENTS_FILE):
            with open(PUNISHMENTS_FILE, "r") as file:
                punishments = json.load(file)

        user_punishments = [p for p in punishments if p["user_id"] == self.user_id]
        user_punishments.sort(key=lambda x: x["end_time"], reverse=True)

        embed = disnake.Embed(title="История наказаний", color=disnake.Color.blue())
        for punishment in user_punishments[(self.current_page - 1) * 15:self.current_page * 15]:
            embed.add_field(
                name="Наказание",
                value=f"Тип: {disnake.utils.get(inter.guild.roles, id=punishment['punishment_role_id']).name}\n"
                      f"Причина: {punishment['reason']}\n"
                      f"Длительность: {timedelta(seconds=punishment['end_time'] - datetime.utcnow().timestamp()).total_seconds() / 3600} часов\n"
                      f"Активен: {'Да' if punishment['active'] else 'Нет'}"
            )

        if len(user_punishments) > 15:
            prev_button = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.primary, disabled=self.current_page == 1)
            next_button = disnake.ui.Button(label="Вперед", style=disnake.ButtonStyle.primary, disabled=self.current_page * 15 >= len(user_punishments))

            prev_button.callback = self.prev_page
            next_button.callback = self.next_page

            view = disnake.ui.View()
            view.add_item(prev_button)
            view.add_item(next_button)
        else:
            view = disnake.ui.View()

        await inter.response.edit_message(embed=embed, view=view)

    async def prev_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.current_page -= 1
        await self.update_history(inter)

    async def next_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.current_page += 1
        await self.update_history(inter)


@bot.event
async def on_interaction(inter: disnake.Interaction):
    if inter.type == disnake.InteractionType.component:
        if inter.data["custom_id"] == "history":
            view = PunishmentHistoryView(user_id=inter.user.id)
            await view.update_history(inter)
        elif inter.data["custom_id"] == "action":
            view = PunishmentTypeView(member=inter.target)
            await inter.response.edit_message(view=view)
        else:
            # Handling of other component interactions
            pass


@bot.command()
@commands.has_permissions(administrator=True)
async def action(ctx, member: disnake.Member):
    embed = disnake.Embed(title="Выберите действие")
    view = PunishmentTypeView(member)
    await ctx.send(embed=embed, view=view)


bot.run('tokin😋')
