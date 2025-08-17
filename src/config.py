import os
from dotenv import load_dotenv

class Config:
    """Класс конфигурации для бота"""

    def __init__(self):
        load_dotenv()

        # Discord конфигурация
        self.DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
        self.GUILD_ID = int(os.getenv('GUILD_ID', 0))

        # Роли администраторов разных уровней
        admin_roles = os.getenv('ADMIN_ROLES', '').split(',')
        self.ADMIN_ROLE_LVL0 = int(admin_roles[0]) if len(admin_roles) > 0 else 0  # Полный доступ
        self.ADMIN_ROLE_LVL1 = int(admin_roles[1]) if len(admin_roles) > 1 else 0  # Полный доступ
        self.ADMIN_ROLE_LVL2 = int(admin_roles[2]) if len(admin_roles) > 2 else 0  # Ограниченный доступ (kick, mute)

        # Экономика
        self.TRANSFER_COMMISSION_RATE = float(os.getenv('TRANSFER_COMMISSION_RATE', 0.1))
        self.INITIAL_MONEY = int(os.getenv('INITIAL_MONEY', 10))
        self.INITIAL_MESSAGES = int(os.getenv('INITIAL_MESSAGES', 1))

        # Роли
        self.BADGE_ROLES = [int(role_id) for role_id in os.getenv('BADGE_ROLES', '').split(',') if role_id]
        self.CONTRIBUTOR_ROLE_ID = int(os.getenv('CONTRIBUTOR_ROLE_ID', 0))
        self.TESTER_ROLE_ID = int(os.getenv('TESTER_ROLE_ID', 0))
        self.MAINTAINER_ROLE_ID = int(os.getenv('MAINTAINER_ROLE_ID', 0))

        # База данных
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'club.db')

        # Активность бота
        self.BOT_ACTIVITY_NAME = os.getenv('BOT_ACTIVITY_NAME', 'Playing')

        # Награды за войс
        self.VOICE_TIME_REWARD = int(os.getenv('VOICE_TIME_REWARD', 1))
        self.VOICE_MONEY_REWARD = int(os.getenv('VOICE_MONEY_REWARD', 20))
        self.VOICE_CHECK_INTERVAL = int(os.getenv('VOICE_CHECK_INTERVAL', 1))
