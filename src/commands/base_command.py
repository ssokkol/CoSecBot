from abc import ABC, abstractmethod
from discord import app_commands
from discord.ext import commands
from typing import Any

class BaseCommand(ABC):
    """Базовый класс для всех команд бота"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @abstractmethod
    async def execute(self, interaction: app_commands.Interaction, **kwargs) -> None:
        """Выполняет команду"""
        pass
    
    def get_command_data(self) -> dict:
        """Возвращает данные команды для регистрации"""
        return {
            'name': getattr(self, 'name', ''),
            'description': getattr(self, 'description', ''),
            'guild_only': getattr(self, 'guild_only', True),
            'guild_id': getattr(self, 'guild_id', None)
        }

class CommandRegistry:
    """Реестр команд для бота"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.commands: dict[str, BaseCommand] = {}
    
    def register_command(self, command: BaseCommand) -> None:
        """Регистрирует команду в реестре"""
        command_data = command.get_command_data()
        self.commands[command_data['name']] = command
    
    def get_command(self, name: str) -> BaseCommand:
        """Получает команду по имени"""
        return self.commands.get(name)
    
    def get_all_commands(self) -> dict[str, BaseCommand]:
        """Получает все зарегистрированные команды"""
        return self.commands.copy()
