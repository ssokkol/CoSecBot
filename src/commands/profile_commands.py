import discord
from discord.ext import commands
import os
from datetime import timedelta
import locale
import logging
from .base_command import BaseCommand
from ..database import UserDatabase
from ..image_generator import ProfileImageGenerator

# Настройка логирования
logger = logging.getLogger(__name__)

class ProfileCommands(BaseCommand):
    """Класс для команд профиля"""
    
    def __init__(self, bot: commands.Bot, user_db: UserDatabase):
        super().__init__(bot)
        self.user_db = user_db
        self.image_generator = ProfileImageGenerator()
        
        # Настройка локали для форматирования чисел
        try:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            except:
                logger.warning("Не удалось установить русскую локаль")
    
    def format_money(self, amount: int) -> str:
        """Форматирует сумму денег с разделителями"""
        try:
            return locale.format_string('%d', amount, grouping=True)
        except:
            return str(amount)
    
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
    
    def truncate_text(self, text: str, max_length: int) -> str:
        """Обрезает текст до максимальной длины"""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text
    
    async def show_profile(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Показывает профиль пользователя"""
        await interaction.response.defer()
        
        try:
            # Получаем данные пользователя
            messages = await self.user_db.get_messages(user.id)
            money = await self.user_db.get_money(user.id)
            voice_time = await self.user_db.get_voice_time(user.id)

            # Форматируем данные
            messages_formatted = self.format_money(messages)
            messages_formatted = self.truncate_text(messages_formatted, 14)
            
            money_formatted = self.format_money(money)
            money_formatted = self.truncate_text(money_formatted, 19)
            
            voice_time_formatted = self.format_time(voice_time)
            voice_time_formatted = self.truncate_text(voice_time_formatted, 17)
            
            # Даты
            created_date = user.created_at.strftime("%d.%m.%Y")
            joined_date = user.joined_at.strftime("%d.%m.%Y") if user.joined_at else "Неизвестно"
            
            # Ник
            nickname = self.truncate_text(str(user.name), 12)
            member = interaction.guild.get_member(user.id)
            # Подготавливаем данные для генерации изображения
            user_data = {
                'status': str(member.status),
                'avatar_url': str(user.avatar.url) if user.avatar else None,
                'nickname': nickname,
                'created_date': created_date,
                'joined_date': joined_date,
                'balance': money_formatted,
                'messages': messages_formatted,
                'voice_time': voice_time_formatted
            }
            
            # Генерируем изображение профиля
            output_path = f'output_{user.id}.png'
            success = await self.image_generator.generate_profile_image(user_data, output_path)
            
            if not success:
                await interaction.followup.send('Ошибка генерации изображения профиля', ephemeral=True)
                return
            
            # Добавляем значки
            await self.image_generator.add_badges_to_profile(output_path, [str(role.id) for role in user.roles])

            # Отправляем файл
            if os.path.exists(output_path):
                file = discord.File(output_path)
                await interaction.followup.send(file=file)
                
                # Удаляем временный файл
                try:
                    os.remove(output_path)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл: {e}")
            else:
                await interaction.followup.send('Ошибка: файл профиля не найден', ephemeral=True)
                
        except Exception as e:
            logger.error(f"Ошибка при получении профиля: {e}")
            await interaction.followup.send(f'Ошибка при получении профиля: {e}', ephemeral=True)

    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """
        Базовый метод выполнения команд профиля
        """
        pass
