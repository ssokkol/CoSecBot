from discord import app_commands, Interaction
import discord
from ..config import Config

class GlobalCommands(app_commands.Group):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config()

    @app_commands.command(name="ping", description="Проверить задержку бота")
    async def ping(self, interaction: Interaction):
        """Простая команда для проверки задержки бота"""
        await interaction.response.send_message(
            f"🏓 Понг!\nЗадержка бота: {round(self.bot.latency * 1000)}мс",
            ephemeral=True
        )

    @app_commands.command(name="help", description="Показать список доступных команд")
    async def help(self, interaction: Interaction):
        """Показывает список доступных команд в зависимости от роли пользователя"""
        from .admin_commands import AdminCommands
        admin_handler = AdminCommands(self.bot, None)  # None для user_db так как он не нужен для проверки ролей
        
        embed = discord.Embed(
            title="📚 Список команд",
            color=0x00ff00
        )

        # Общие команды для всех
        embed.add_field(
            name="Общие команды",
            value="• `/help` - Показать список команд\n"
                  "• `/ping` - Проверить задержку бота\n"
                  "• `/balance` - Проверить баланс\n"
                  "• `/transfer` - Перевести деньги другому пользователю\n"
                  "• `/top` - Посмотреть топ пользователей\n"
                  "• `/profile` - Посмотреть профиль",
            inline=False
        )

        # Получаем уровень роли пользователя
        role_level = admin_handler.get_role_level(interaction.user)
        
        # Команды для пользователей с высшим уровнем доступа (0 и 1 в иерархии)
        if role_level <= 1:
            admin_commands = [
                "• `/ban` - Забанить пользователя\n",
                "• `/kick` - Кикнуть пользователя\n",
                "• `/mute` - Замьютить пользователя"
            ]
            
            # Добавляем команды /give и /rem только для главного админа
            if str(interaction.user.id) == str(self.config.ADMIN_USER_ID):
                admin_commands.extend([
                    "• `/give` - Выдать деньги пользователю\n",
                    "• `/rem` - Снять деньги у пользователя"
                ])
            
            embed.add_field(
                name="Команды администратора",
                value="".join(admin_commands),
                inline=False
            )
        
        # Команды для модераторов (2 и 3 уровень в иерархии)
        elif role_level <= 3:
            embed.add_field(
                name="Команды модератора",
                value="• `/kick` - Кикнуть пользователя\n"
                      "• `/mute` - Замьютить пользователя",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
