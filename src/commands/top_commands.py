import discord
from discord.ext import commands
from typing import List, Tuple
from datetime import timedelta
import locale
from .base_command import BaseCommand
from ..database import TopDatabase

class TopCommands(BaseCommand):
    """Класс для команд топов"""
    
    def __init__(self, bot: commands.Bot, top_db: TopDatabase):
        super().__init__(bot)
        self.top_db = top_db
        
        # Настройка локали для форматирования времени
        try:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            except:
                pass
    
    def format_time(self, minutes: int) -> str:
        """Форматирует время в минутах в читаемый вид на русском языке"""
        try:
            if minutes < 60:
                return f"{minutes} мин"
            elif minutes < 1440:  # меньше дня
                hours = minutes // 60
                mins = minutes % 60
                if mins == 0:
                    return f"{hours} ч"
                else:
                    return f"{hours} ч {mins} мин"
            else:  # больше дня
                days = minutes // 1440
                remaining_minutes = minutes % 1440
                hours = remaining_minutes // 60
                mins = remaining_minutes % 60
                
                if hours == 0 and mins == 0:
                    if days == 1:
                        return f"{days} день"
                    elif days < 5:
                        return f"{days} дня"
                    else:
                        return f"{days} дней"
                elif mins == 0:
                    if days == 1:
                        return f"{days} день {hours} ч"
                    elif days < 5:
                        return f"{days} дня {hours} ч"
                    else:
                        return f"{days} дней {hours} ч"
                else:
                    if hours == 0:
                        if days == 1:
                            return f"{days} день {mins} мин"
                        elif days < 5:
                            return f"{days} дня {mins} мин"
                        else:
                            return f"{days} дней {mins} мин"
                    else:
                        if days == 1:
                            return f"{days} день {hours} ч {mins} мин"
                        elif days < 5:
                            return f"{days} дня {hours} ч {mins} мин"
                        else:
                            return f"{days} дней {hours} ч {mins} мин"
        except:
            return f"{minutes} мин"
    
    def format_money(self, amount: int) -> str:
        """Форматирует сумму денег с разделителями"""
        try:
            return locale.format_string('%d', amount, grouping=True)
        except:
            return str(amount)
    
    async def show_voice_top(self, interaction: discord.Interaction, limit: int = 5) -> None:
        """Показывает топ по времени в голосовых каналах"""
        try:
            top_data = await self.top_db.get_voice_top(limit)
            
            if not top_data:
                await interaction.response.send_message('Нет данных для отображения топа')
                return
            
            top_list = []
            for i, (user_id, voice_time) in enumerate(top_data, 1):
                formatted_time = self.format_time(voice_time)
                top_list.append(f'**{i}. <@{user_id}> время - `{formatted_time}`**\n')
            
            await interaction.response.send_message(''.join(top_list))
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при получении топа: {e}', ephemeral=True)
    
    async def show_messages_top(self, interaction: discord.Interaction, limit: int = 5) -> None:
        """Показывает топ по сообщениям"""
        try:
            top_data = await self.top_db.get_messages_top(limit)
            
            if not top_data:
                await interaction.response.send_message('Нет данных для отображения топа')
                return
            
            top_list = []
            for i, (user_id, messages) in enumerate(top_data, 1):
                top_list.append(f'**{i}. <@{user_id}> сообщений - `{messages}`**\n')
            
            await interaction.response.send_message(''.join(top_list))
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при получении топа: {e}', ephemeral=True)
    
    async def show_balance_top(self, interaction: discord.Interaction, limit: int = 5) -> None:
        """Показывает топ по балансу"""
        try:
            top_data = await self.top_db.get_balance_top(limit)
            
            if not top_data:
                await interaction.response.send_message('Нет данных для отображения топа')
                return
            
            top_list = []
            for i, (user_id, money) in enumerate(top_data, 1):
                formatted_money = self.format_money(money)
                top_list.append(f'**{i}. <@{user_id}> баланс - `{formatted_money}руб`**\n')
            
            await interaction.response.send_message(''.join(top_list))
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при получении топа: {e}', ephemeral=True)
    
    async def show_general_top(self, interaction: discord.Interaction, top_type: str, limit: int = 5) -> None:
        """Показывает общий топ по указанному типу"""
        try:
            if top_type == "voice":
                await self.show_voice_top(interaction, limit)
            elif top_type == "messages":
                await self.show_messages_top(interaction, limit)
            elif top_type == "balance":
                await self.show_balance_top(interaction, limit)
            else:
                await interaction.response.send_message('Неизвестный тип топа. Доступные: voice, messages, balance', ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при получении топа: {e}', ephemeral=True)

    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """
        Базовый метод выполнения команд топов
        """
        pass
