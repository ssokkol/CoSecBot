import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import locale
import logging
from typing import Optional
from datetime import datetime, date
import os

from src.config import Config
from src.database import DatabaseManager, UserDatabase, TopDatabase
from src.image_generator import ProfileImageGenerator
from src.commands.admin_commands import AdminCommands
from src.commands.economy_commands import EconomyCommands
from src.commands.top_commands import TopCommands
from src.commands.profile_commands import ProfileCommands
from src.commands.global_commands import GlobalCommands
from src.commands.voice_commands import VoiceCommands
from src.commands.music_commands import MusicCommands

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
        
        # Отслеживание последней отправки базы данных
        self._last_backup_date = None

        # Инициализация глобальных команд
        self.global_commands = GlobalCommands(self)
        self.tree.add_command(self.global_commands)

        # Добавление глобальной команды ping
        @self.tree.command(name="ping", guild=None)
        async def ping(interaction: discord.Interaction):
            """Простая команда для проверки задержки бота"""
            await interaction.response.send_message(
                f"🏓 Понг!",
                ephemeral=True
            )

        # Инициализация базы данных
        self.db_manager = DatabaseManager(self.config.DATABASE_PATH)
        self.user_db = UserDatabase(self.db_manager)
        self.top_db = TopDatabase(self.db_manager)
        
        # Инициализация генератора изображений
        self.image_generator = ProfileImageGenerator()
        
        # Инициализация команд
        self.admin_commands = AdminCommands(self, self.user_db)
        self.economy_commands = EconomyCommands(self, self.user_db)
        self.top_commands = TopCommands(self, self.top_db)
        self.profile_commands = ProfileCommands(self, self.user_db)
        self.voice_commands = VoiceCommands(self)
        self.music_commands = MusicCommands(self)
        
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
        
        # Запуск задачи отправки базы данных
        self.database_backup.start()
        
        logger.info("DiscordBot инициализирован успешно")
    
    def setup_events(self):
        """Настраивает события бота"""

        @self.event
        async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
            """Обработчик изменения состояния голосового канала"""
            await self.voice_commands.handle_voice_state_update(member, before, after)
            
            # Проверяем, нужно ли отключить музыкального бота
            if before.channel and not member.bot:
                guild_id = before.channel.guild.id
                vc = self.music_commands.player.get_voice_client(guild_id)
                if vc and vc.channel and vc.channel.id == before.channel.id:
                    # Проверяем, остались ли люди в канале
                    human_members = [m for m in before.channel.members if not m.bot]
                    if len(human_members) == 0:
                        await self.music_commands.player.check_inactivity(guild_id)

        @self.event
        async def on_ready():
            """Событие готовности бота"""
            logger.info(f'{self.user} успешно подключился к Discord!')

            # Синхронизация команд
            try:
                # Синхронизируем глобальные команды
                await self.tree.sync()
                logger.info("Глобальные команды обновлены")

                # Синхронизируем команды сервера
                await self.tree.sync(guild=discord.Object(id=self.config.GUILD_ID))
                logger.info("Серверные команды обновлены")
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
                            else:
                                # Проверяем, не глушит ли пользователь сам себя
                                if not member.voice.self_mute:
                                    await self.user_db.add_voice_time(member.id, self.config.VOICE_TIME_REWARD)
                                    await self.user_db.add_money(member.id, self.config.VOICE_MONEY_REWARD)
        except Exception as e:
            logger.error(f"Ошибка проверки голосовых каналов: {e}")
    
    @voice_check.before_loop
    async def before_voice_check(self):
        """Ожидает готовности бота перед запуском задачи"""
        await self.wait_until_ready()
    
    @tasks.loop(hours=24)
    async def database_backup(self):
        """Отправляет базу данных в канал каждый 4-й день месяца"""
        try:
            today = datetime.now()
            today_date = today.date()
            
            # Проверяем, является ли сегодня 4-м числом месяца
            if today.day == 4:
                # Проверяем, не отправляли ли мы уже сегодня
                if self._last_backup_date == today_date:
                    return
                
                backup_channel_id = 1406254861351125132
                channel = self.get_channel(backup_channel_id)
                
                if not channel:
                    logger.warning(f"Канал {backup_channel_id} не найден")
                    return
                
                db_path = self.config.DATABASE_PATH
                
                # Проверяем существование файла базы данных
                if not os.path.exists(db_path):
                    logger.warning(f"Файл базы данных {db_path} не найден")
                    return
                
                # Отправляем файл базы данных
                try:
                    with open(db_path, 'rb') as db_file:
                        # Формируем имя файла с датой
                        date_str = today.strftime('%Y-%m-%d')
                        filename = f"backup_{date_str}_{os.path.basename(db_path)}"
                        
                        file = discord.File(db_file, filename=filename)
                        await channel.send(
                            f"📦 Резервная копия базы данных от {date_str}",
                            file=file
                        )
                        self._last_backup_date = today_date
                        logger.info(f"База данных отправлена в канал {backup_channel_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки базы данных: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка в задаче резервного копирования: {e}")
    
    @database_backup.before_loop
    async def before_database_backup(self):
        """Ожидает готовности бота перед запуском задачи"""
        await self.wait_until_ready()
        # Небольшая задержка после запуска
        await asyncio.sleep(60)  # Ждем 1 минуту после запуска
    
    def setup_commands(self):
        """Настраивает команды бота"""
        
        @self.tree.command(
            name="help", 
            description="Список команд",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def help(interaction: discord.Interaction):
            """Команда для отображения справки"""
            help_text = (
                '/profile - Ваша статистика на сервере\n\n'
                '**Банковские операции**\n'
                '/transfer - перевести деньги пользователю(комиссия 10%)\n\n'
                '**Топ участников**\n'
                '/voice - топ по времени в войсе\n'
                '/messages - топ по сообщениям\n'
                '/balance - топ по балансу\n\n'
                '**Музыка**\n'
                '/play - воспроизвести трек (YouTube/Spotify URL или поиск)\n'
                '/skip - пропустить текущий трек\n'
                '/queue - показать очередь воспроизведения\n'
                '/stop - остановить воспроизведение\n'
                '/pause - пауза/возобновление\n\n'
                '**Административные команды**\n'
                '/ban - забанить пользователя\n'
                '/kick - кикнуть пользователя\n'
                '/mute - замутить пользователя\n'
                '/give - выдать деньги\n'
                '/rem - снять деньги'
            )
            await interaction.response.send_message(help_text, ephemeral=True)
        
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
            description="Перевести деньги пользователю (ко��иссия 10%)",
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
        
        # Музыкальные команды
        @self.tree.command(
            name="play",
            description="Воспроизвести трек (YouTube/Spotify URL или поисковый запрос)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        @app_commands.describe(query="URL или название трека для поиска")
        async def play(interaction: discord.Interaction, query: str):
            """Команда воспроизведения музыки"""
            await self.music_commands.play(interaction, query)
        
        @self.tree.command(
            name="skip",
            description="Пропустить текущий трек",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def skip(interaction: discord.Interaction):
            """Команда пропуска трека"""
            await self.music_commands.skip(interaction)
        
        @self.tree.command(
            name="queue",
            description="Показать очередь воспроизведения",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def queue(interaction: discord.Interaction):
            """Команда отображения очереди"""
            await self.music_commands.show_queue(interaction)
        
        @self.tree.command(
            name="stop",
            description="Остановить воспроизведение и очистить очередь",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def stop(interaction: discord.Interaction):
            """Команда остановки воспроизведения"""
            await self.music_commands.stop(interaction)
        
        @self.tree.command(
            name="pause",
            description="Поставить на паузу или возобновить воспроизведение",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def pause(interaction: discord.Interaction):
            """Команда паузы/возобновления"""
            await self.music_commands.pause(interaction)
        
        @self.tree.command(
            name="loop",
            description="Переключить режим повтора (трек/очередь/выкл)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def loop(interaction: discord.Interaction):
            """Команда переключения режима повтора"""
            await self.music_commands.loop(interaction)
        
        @self.tree.command(
            name="clear",
            description="Очистить очередь треков (требует прав модератора)",
            guild=discord.Object(id=self.config.GUILD_ID)
        )
        async def clear(interaction: discord.Interaction):
            """Команда очистки очереди"""
            await self.music_commands.clear(interaction)
    
    async def handle_message_statistics(self, message):
        """Об��абатывает статистику сообщений"""
        try:
            if not await self.user_db.user_exists(message.author.id):
                await self.user_db.add_user(message.author.id)
                await self.user_db.add_message(message.author.id, self.config.INITIAL_MESSAGES)
                await self.user_db.add_money(message.author.id, self.config.INITIAL_MONEY)
            else:
                await self.user_db.add_message(message.author.id, 1)
        except Exception as e:
            logger.error(f"Ош��бка обработки статистики сообщений: {e}")

    async def run_bot(self):
        """Запускает бота"""
        try:
            await self.start(self.config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Ошибк�� запуска бота: {e}")
            raise
