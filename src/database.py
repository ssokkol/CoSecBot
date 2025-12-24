import aiosqlite
import asyncio
from typing import Optional, Tuple, List
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных для Discord бота"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        # Инициализация будет выполнена при первом подключении
    
    async def _init_database(self):
        """Инициализирует базу данных с нужными таблицами"""
        try:
            import os
            # Создаем директорию для базы данных, если её нет
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            # Создаем файл базы данных, если его нет
            if not os.path.exists(self.db_path):
                open(self.db_path, 'a').close()
                # Устанавливаем права на запись
                try:
                    os.chmod(self.db_path, 0o666)
                except Exception:
                    pass  # Игнорируем ошибки прав в Windows
            
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        messages INTEGER DEFAULT 0,
                        voice_time INTEGER DEFAULT 0,
                        money INTEGER DEFAULT 0
                    )
                ''')
                await conn.commit()
                logger.info(f"База данных инициализирована успешно: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных {self.db_path}: {e}")
            raise
    
    async def execute_query(self, query: str, params: tuple = ()) -> bool:
        """Выполняет SQL запрос с блокировкой"""
        async with self._lock:
            try:
                # Инициализируем БД при первом использовании
                if not hasattr(self, '_initialized'):
                    await self._init_database()
                    self._initialized = True
                
                async with aiosqlite.connect(self.db_path) as conn:
                    await conn.execute(query, params)
                    await conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Ошибка выполнения запроса: {e}")
                return False
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Получает одну запись из БД"""
        async with self._lock:
            try:
                # Инициализируем БД при первом использовании
                if not hasattr(self, '_initialized'):
                    await self._init_database()
                    self._initialized = True
                
                async with aiosqlite.connect(self.db_path) as conn:
                    async with conn.execute(query, params) as cursor:
                        return await cursor.fetchone()
            except Exception as e:
                logger.error(f"Ошибка получения записи: {e}")
                return None
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        """Получает все записи из БД"""
        async with self._lock:
            try:
                # Инициализируем БД при первом использовании
                if not hasattr(self, '_initialized'):
                    await self._init_database()
                    self._initialized = True
                
                async with aiosqlite.connect(self.db_path) as conn:
                    async with conn.execute(query, params) as cursor:
                        return await cursor.fetchall()
            except Exception as e:
                logger.error(f"Ошибка получения записей: {e}")
                return []

class UserDatabase:
    """Класс для работы с пользователями в БД"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def user_exists(self, user_id: int) -> bool:
        """Проверяет существование пользователя"""
        result = await self.db.fetch_one(
            "SELECT `id` FROM `users` WHERE `user_id` = ?", 
            (user_id,)
        )
        return bool(result)
    
    async def add_user(self, user_id: int) -> bool:
        """Добавляет нового пользователя"""
        try:
            await self.db.execute_query(
                "INSERT INTO `users` (user_id, messages, voice_time, money) VALUES (?,?,?,?)",
                (user_id, 0, 0, 0)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    async def get_money(self, user_id: int) -> int:
        """Получает баланс пользователя"""
        result = await self.db.fetch_one(
            "SELECT `money` FROM `users` WHERE `user_id` = ?", 
            (user_id,)
        )
        return result[0] if result else 0
    
    async def add_money(self, user_id: int, amount: int) -> bool:
        """Добавляет деньги пользователю"""
        try:
            await self.db.execute_query(
                'UPDATE `users` SET `money` = money + ? WHERE user_id = ?', 
                (amount, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления денег: {e}")
            return False
    
    async def rem_money(self, user_id: int, amount: int) -> bool:
        """Снимает деньги с пользователя"""
        try:
            await self.db.execute_query(
                'UPDATE `users` SET `money` = money - ? WHERE user_id = ?', 
                (amount, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка снятия денег: {e}")
            return False
    
    async def get_messages(self, user_id: int) -> int:
        """Получает количество сообщений пользователя"""
        result = await self.db.fetch_one(
            "SELECT `messages` FROM `users` WHERE `user_id` = ?", 
            (user_id,)
        )
        return result[0] if result else 0
    
    async def add_message(self, user_id: int, count: int = 1) -> bool:
        """Добавляет сообщения пользователю"""
        try:
            await self.db.execute_query(
                "UPDATE `users` SET `messages` = messages + ? WHERE user_id = ?", 
                (count, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления сообщений: {e}")
            return False
    
    async def get_voice_time(self, user_id: int) -> int:
        """Получает время в голосовых каналах"""
        result = await self.db.fetch_one(
            "SELECT `voice_time` FROM `users` WHERE `user_id` = ?", 
            (user_id,)
        )
        return result[0] if result else 0
    
    async def add_voice_time(self, user_id: int, minutes: int) -> bool:
        """Добавляет время в голосовых каналах"""
        try:
            await self.db.execute_query(
                "UPDATE `users` SET `voice_time` = voice_time + ? WHERE user_id = ?", 
                (minutes, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления времени в войсе: {e}")
            return False

class TopDatabase:
    """Класс для работы с топами в БД"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_voice_top(self, limit: int = 5) -> List[Tuple[int, int]]:
        """Получает топ по времени в голосовых каналах"""
        return await self.db.fetch_all(
            "SELECT user_id, voice_time FROM users ORDER BY voice_time DESC LIMIT ?",
            (limit,)
        )
    
    async def get_messages_top(self, limit: int = 5) -> List[Tuple[int, int]]:
        """Получает топ по сообщениям"""
        return await self.db.fetch_all(
            "SELECT user_id, messages FROM users ORDER BY messages DESC LIMIT ?",
            (limit,)
        )
    
    async def get_balance_top(self, limit: int = 5) -> List[Tuple[int, int]]:
        """Получает топ по балансу"""
        return await self.db.fetch_all(
            "SELECT user_id, money FROM users ORDER BY money DESC LIMIT ?",
            (limit,)
        )
