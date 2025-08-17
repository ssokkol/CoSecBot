import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import locale
import logging
from typing import Optional

from src.config import Config
from src.database import DatabaseManager, UserDatabase, TopDatabase
from src.image_generator import ProfileImageGenerator
from src.commands.admin_commands import AdminCommands
from src.commands.economy_commands import EconomyCommands
from src.commands.top_commands import TopCommands
from src.commands.profile_commands import ProfileCommands

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    """Основной класс Discord бота"""
    
    def __init__(self):
        intents = discord.Intents.all()  # defining intents
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

        # Инициализация конфигурации
        self.config = Config()

        # Инициализация базы данных
        self.db_manager = DatabaseManager('database.db')
        self.user_db = UserDatabase(self.db_manager)
        self.top_db = TopDatabase(self.db_manager)
        
        # Инициализация генератора изображений
        self.image_generator = ProfileImageGenerator()
        
        # Инициализация команд
        self.admin_commands = AdminCommands(self, self.user_db)
        self.economy_commands = EconomyCommands(self, self.user_db)
        self.top_commands = TopCommands(self, self.top_db)
        self.profile_commands = ProfileCommands(self, self.user_db)
        
        # Настройка локали
        try:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            except:
                logger.warning("Не удалось установить русскую локаль")
        
        # Регистрация событий
        self.setup_events()
        
        # Регистрация команд
        self.setup_commands()
        
        # Запуск задачи проверки голосовых каналов
        self.voice_check.start()
        
        logger.info("DiscordBot инициализирован успешно")
    
    def setup_events(self):
        """Настраивает события бота"""
        
        @self.event
        async def on_ready():
            """Событие готовности бота"""
            logger.info(f'{self.user} успешно подключился к Discord!')
            
            # Синхронизация команд
            try:
                synced = await self.tree.sync(guild=discord.Object(id=self.config.GUILD_ID))
                logger.info(f"Синхронизировано {len(synced)} команд")
            except Exception as e:
                logger.error(f"Ошибка синхронизации команд: {e}")
            
            # Установка активности
            activity = discord.Activity(
                type=discord.ActivityType.listening, 
                name=self.config.BOT_ACTIVITY_NAME
            )
            await self.change_presence(
                activity=activity, 
                status=discord.Status.do_not_disturb
            )
            logger.info('Sombra Online')
        
        @self.event
        async def on_message(message):
            """Событие получения сообщения"""
            if message.author.bot:
                return
            
            # Обработка сообщений для статистики
            await self.handle_message_statistics(message)
            
            # Обработка команд
            await self.process_commands(message)
    
    @tasks.loop(minutes=1)
    async def voice_check(self):
        """Проверяет пользователей в голосовых каналах каждую минуту"""
        try:
            for guild in self.guilds:
                for channel in guild.voice_channels:
                    for member in channel.members:
                        if not member.bot and not member.voice.self_deaf and not member.voice.afk:
                            if not await self.user_db.user_exists(member.id):
                                await self.user_db.add_user(member.id)
                                await self.user_db.add_voice_time(member.id, self.config.VOICE_TIME_REWARD)
                                await self.user_db.add_money(member.id, self.config.VOICE_MONEY_REWARD)
                                logger.info(f'Пользователь {member.name} получил {self.config.VOICE_TIME_REWARD} минут и {self.config.VOICE_MONEY_REWARD} рублей')
                            else:
                                # Проверяем, не глушит ли пользователь сам себя
                                if not member.voice.self_mute:
                                    await self.user_db.add_voice_time(member.id, self.config.VOICE_TIME_REWARD)
                                    await self.user_db.add_money(member.id, self.config.VOICE_MONEY_REWARD)
                                    logger.info(f'Пользователь {member.name} получил {self.config.VOICE_TIME_REWARD} минут и {self.config.VOICE_MONEY_REWARD} рублей')
        except Exception as e:
            logger.error(f"Ошибка проверки голосовых каналов: {e}")
    
    @voice_check.before_loop
    async def before_voice_check(self):
        """Ожидает готовности бота перед запуском задачи"""
        await self.wait_until_ready()
    
    def setup_commands(self):
        """Настраивает команды бота"""
        
        @self.tree.command(
            name="rules", 
            description="Правила сервера",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def rules(interaction: discord.Interaction):
            """Команда для отображения правил сервера"""
            embed = discord.Embed(
                color=0xffffff,
                description='\n**1. Запрещено оскорбление администрации без причины**\n```БАН```\n'
                           '**2. Запрещено оскорбление РФ**\n```БАН```\n'
                           '**3. Запрещена пропаганда лгбт**\n```БАН```\n'
                           '**4. Если вы хохол**\n```БАН```\n\n'
                           '**5. Мемчики любого рода разрешены**\n'
                           '**6. Нельзя спамить, спам мемчиков не в счет)**\n'
                           '**7. Никаких разговоров про Геншин**'
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        @self.tree.command(
            name="help", 
            description="Список команд",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def help(interaction: discord.Interaction):
            """Команда для отображения справки"""
            help_text = (
                '/rules - список правил\n'
                '/report - отправить жалобу на пользователя\n'
                '/profile - ваша статистика на сервере\n\n'
                '**Банковские операции**\n'
                '/transfer - перевести деньги пользователю(комиссия 10%)\n\n'
                '**Топ участников**\n'
                '/voice - топ по времени в войсе\n'
                '/messages - топ по сообщениям\n'
                '/balance - топ по балансу\n\n'
                '**Административные команды**\n'
                '/ban - забанить пользователя\n'
                '/kick - кикнуть пользователя\n'
                '/mute - замутить пользователя\n'
                '/give - выдать деньги\n'
                '/rem - снять деньги'
            )
            await interaction.response.send_message(help_text, ephemeral=True)
        
        @self.tree.command(
            name="report", 
            description="Написать репорт на юзера",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def report(interaction: discord.Interaction, user: discord.Member, reason: str):
            """Команда для отправки жалобы на пользователя"""
            await interaction.response.send_message(
                f'Репорт на пользователя {user.mention} отправлен\nПричина: {reason}',
                ephemeral=True
            )
            
            # Отправляем уведомление администрации
            admin_mentions = ' '.join([f'<@&{role_id}>' for role_id in self.config.ADMIN_ROLES])
            channel = self.get_channel(1065741036615389226)  # ID канала для жалоб
            
            if channel:
                await channel.send(
                    f"{admin_mentions}\n"
                    f"Репорт на {user.mention} от {interaction.user.mention}\n"
                    f"Причина: {reason}"
                )
        
        @self.tree.command(
            name="profile", 
            description="Ваш профиль и статистика",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def profile(interaction: discord.Interaction, user: discord.Member = None):
            """Команда для показа профиля пользователя"""
            if user is None:
                user = interaction.user
            await self.profile_commands.show_profile(interaction, user)
        
        # Административные команды
        @self.tree.command(
            name="ban", 
            description="Забанить пользователя (бан вечный)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def ban(interaction: discord.Interaction, user: discord.Member, reason: str):
            """Команда для бана пользователя"""
            await self.admin_commands.ban_user(interaction, user, reason)
        
        @self.tree.command(
            name="kick", 
            description="Кикнуть пользователя",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
            """Команда для кика пользователя"""
            await self.admin_commands.kick_user(interaction, user, reason)
        
        @self.tree.command(
            name="mute", 
            description="Замутить пользователя (время в минутах, максимум 38880)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def mute(interaction: discord.Interaction, user: discord.Member, reason: str, time: int):
            """Команда для мута пользователя"""
            await self.admin_commands.mute_user(interaction, user, reason, time)
        
        @self.tree.command(
            name="give", 
            description="Выдать деньги пользователю (только для админа)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def give(interaction: discord.Interaction, user: discord.Member, amount: int):
            """Команда для выдачи денег"""
            await self.admin_commands.give_money(interaction, user, amount)
        
        @self.tree.command(
            name="rem", 
            description="Снять деньги у пользователя (только для админа)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def rem(interaction: discord.Interaction, user: discord.Member, amount: int):
            """Команда для снятия денег"""
            await self.admin_commands.remove_money(interaction, user, amount)
        
        # Экономические команды
        @self.tree.command(
            name="transfer", 
            description="Перевести деньги пользователю (комиссия 10%)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def transfer(interaction: discord.Interaction, user: discord.Member, amount: int):
            """Команда для перевода денег"""
            await self.economy_commands.transfer_money(interaction, user, amount)
        
        # Команды топов
        @self.tree.command(
            name="voice", 
            description="Топ по времени в голосовых каналах",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def voice(interaction: discord.Interaction):
            """Команда для показа топа по голосовым каналам"""
            await self.top_commands.show_voice_top(interaction)
        
        @self.tree.command(
            name="messages", 
            description="Топ по сообщениям",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def messages(interaction: discord.Interaction):
            """Команда для показа топа по сообщениям"""
            await self.top_commands.show_messages_top(interaction)
        
        @self.tree.command(
            name="balance", 
            description="Топ по балансу",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def balance(interaction: discord.Interaction):
            """Команда для показа топа по балансу"""
            await self.top_commands.show_balance_top(interaction)
    
    async def handle_message_statistics(self, message):
        """Обрабатывает статистику сообщений"""
        try:
            if not await self.user_db.user_exists(message.author.id):
                await self.user_db.add_user(message.author.id)
                await self.user_db.add_message(message.author.id, self.config.INITIAL_MESSAGES)
                await self.user_db.add_money(message.author.id, self.config.INITIAL_MONEY)
            else:
                await self.user_db.add_message(message.author.id, 1)
        except Exception as e:
            logger.error(f"Ошибка обработки статистики сообщений: {e}")
    
    async def run_bot(self):
        """Запускает бота"""
        try:
            await self.start(self.config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise
