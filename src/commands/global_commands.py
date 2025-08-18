from discord import app_commands, Interaction
import discord

class GlobalCommands(app_commands.Group):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="ping", description="Проверить задержку бота")
    async def ping(self, interaction: Interaction):
        """Простая команда для проверки задержки бота"""
        await interaction.response.send_message(
            f"🏓 Понг!\nЗадержка бота: {round(self.bot.latency * 1000)}мс",
            ephemeral=True
        )
