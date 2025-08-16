import discord
from discord import app_commands
from discord.ext import commands
import locale
import logging
from .base_command import BaseCommand
from ..config import Config
from ..database import UserDatabase

# Настройка логирования
logger = logging.getLogger(__name__)

class EconomyCommands(BaseCommand):
    """Класс для экономических команд"""
    
    def __init__(self, bot: commands.Bot, user_db: UserDatabase):
        super().__init__(bot)
        self.user_db = user_db
        self.config = Config()
        
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
    
    async def transfer_money(self, interaction: app_commands.Interaction, user: discord.Member, amount: int) -> None:
        """Переводит деньги между пользователями"""
        if amount <= 0:
            await interaction.response.send_message('Вы как собрались `0руб` переводить?')
            return
        
        try:
            sender_balance = await self.user_db.get_money(interaction.user.id)
            commission = int(amount * self.config.TRANSFER_COMMISSION_RATE)
            total_cost = amount + commission
            
            if sender_balance < total_cost:
                await interaction.response.send_message('У вас не хватает денег')
                return
            
            # Выполняем перевод
            await self.user_db.rem_money(interaction.user.id, total_cost)
            await self.user_db.add_money(self.config.ADMIN_USER_ID, commission)  # Комиссия серверу
            await self.user_db.add_money(user.id, amount)
            
            # Отправляем уведомления
            await self._send_transfer_notifications(interaction, user, amount, commission, total_cost)
            
            await interaction.response.send_message('Готово!')
            
        except Exception as e:
            logger.error(f"Ошибка при переводе: {e}")
            await interaction.response.send_message(f'Ошибка при переводе: {e}', ephemeral=True)
    
    async def _send_transfer_notifications(self, interaction: app_commands.Interaction, recipient: discord.Member, 
                                         amount: int, commission: int, total_cost: int):
        """Отправляет уведомления о переводе"""
        try:
            # Уведомление отправителю
            sender_channel = await interaction.user.create_dm()
            sender_balance = await self.user_db.get_money(interaction.user.id)
            
            embed1 = discord.Embed(
                color=0xfade34, 
                title='Перевод',
                description=f'Перевод пользователю {recipient.mention}\n'
                           f'С вашего счета списано `{self.format_money(amount)}руб+({self.format_money(commission)}руб комиссии)`\n'
                           f'Ваш баланс: `{self.format_money(sender_balance)}руб`'
            )
            await sender_channel.send(embed=embed1)
            
            # Уведомление получателю
            recipient_channel = await recipient.create_dm()
            recipient_balance = await self.user_db.get_money(recipient.id)
            
            embed2 = discord.Embed(
                color=0xfade34, 
                title='Пополнение',
                description=f'Перевод от пользователя {interaction.user.mention}\n'
                           f'На ваш счет зачислено `{self.format_money(amount)}руб`\n'
                           f'Ваш баланс: `{self.format_money(recipient_balance)}руб`'
            )
            await recipient_channel.send(embed=embed2)
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомлений о переводе: {e}")
    
    async def buy_ring(self, interaction: app_commands.Interaction) -> None:
        """Покупает кольцо для коллекции"""
        try:
            current_rings = await self.user_db.get_ring(interaction.user.id)
            
            if current_rings > 0:
                await interaction.response.send_message('У вас уже есть кольцо')
                return
            
            user_balance = await self.user_db.get_money(interaction.user.id)
            commission = int(self.config.RING_PRICE * self.config.TRANSFER_COMMISSION_RATE)
            total_cost = self.config.RING_PRICE + commission
            
            if user_balance < total_cost:
                # Отправляем уведомление об ошибке
                channel = await interaction.user.create_dm()
                embed = discord.Embed(
                    color=0xff0000, 
                    title='Ошибка',
                    description=f'Покупка кольца\nНедостаточно средств для совершения операции\nВаш баланс: `{self.format_money(user_balance)}руб`'
                )
                await channel.send(embed=embed)
                await interaction.response.send_message('Ошибка')
                return
            
            # Покупаем кольцо
            await self.user_db.rem_money(interaction.user.id, total_cost)
            await self.user_db.add_money(self.config.ADMIN_USER_ID, total_cost)  # Деньги серверу
            await self.user_db.add_ring(interaction.user.id, 1)
            
            # Отправляем уведомление об успешной покупке
            channel = await interaction.user.create_dm()
            new_balance = await self.user_db.get_money(interaction.user.id)
            
            embed = discord.Embed(
                color=0xfade34, 
                title='Транзакция',
                description=f'Покупка кольца\nС вашего счета списано `{self.format_money(self.config.RING_PRICE)}руб+({self.format_money(commission)}руб комиссии)`\nВаш баланс: `{self.format_money(new_balance)}руб`'
            )
            await channel.send(embed=embed)
            
            await interaction.response.send_message('Успешно!')
            
        except Exception as e:
            logger.error(f"Ошибка при покупке кольца: {e}")
            await interaction.response.send_message(f'Ошибка при покупке кольца: {e}', ephemeral=True)
