import discord
from discord.ext import commands
from typing import Optional
from .base_command import BaseCommand
from ..config import Config
from ..database import UserDatabase

class AdminCommands(BaseCommand):
    """Класс для административных команд"""
    
    def __init__(self, bot: commands.Bot, user_db: UserDatabase):
        super().__init__(bot)
        self.user_db = user_db
        self.config = Config()
    
    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """
        Базовый метод выполнения административной команды
        """
        pass

    def has_admin_role(self, member: discord.Member) -> bool:
        """Проверяет, есть ли у пользователя административная роль"""
        user_roles = [str(role.id) for role in member.roles]
        return any(role_id in self.config.ADMIN_ROLES for role_id in user_roles)
    
    async def ban_user(self, interaction: discord.Interaction, user: discord.Member, reason: str) -> None:
        """Банит пользователя"""
        if not self.has_admin_role(interaction.user):
            await interaction.response.send_message('У вас нет прав для выполнения этой команды', ephemeral=True)
            return
        
        try:
            # Отправляем сообщение о бане в личку
            channel = await user.create_dm()
            embed = discord.Embed(
                color=0xff0000, 
                title='Бан',
                description=f'Вас забанили\nПо причине: {reason} by {interaction.user.mention}'
            )
            embed.set_footer(text=str(interaction.user), icon_url=interaction.user.avatar)
            await channel.send(embed=embed)
            
            # Баним пользователя
            await user.ban(delete_message_days=7, reason=reason)
            
            await interaction.response.send_message(
                f'{user.mention}({user.id}) забанен {interaction.user.mention}\nПричина: {reason}',
                ephemeral=False
            )
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при бане: {e}', ephemeral=True)
    
    async def kick_user(self, interaction: discord.Interaction, user: discord.Member, reason: str) -> None:
        """Кикает пользователя"""
        if not self.has_admin_role(interaction.user):
            await interaction.response.send_message('У вас нет прав для выполнения этой команды', ephemeral=True)
            return
        
        try:
            # Отправляем сообщение о кике в личку
            channel = await user.create_dm()
            embed = discord.Embed(
                color=0xffa500, 
                title='Кик',
                description=f'Вас кикнули\nПо причине: {reason} by {interaction.user.mention}'
            )
            embed.set_footer(text=str(interaction.user), icon_url=interaction.user.avatar)
            await channel.send(embed=embed)
            
            # Кикаем пользователя
            await user.kick(reason=reason)
            
            await interaction.response.send_message(
                f'{user.mention}({user.id}) кикнут {interaction.user.mention}\nПричина: {reason}',
                ephemeral=False
            )
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при кике: {e}', ephemeral=True)
    
    async def mute_user(self, interaction: discord.Interaction, user: discord.Member, reason: str, time: int) -> None:
        """Мьютит пользователя"""
        if not self.has_admin_role(interaction.user):
            await interaction.response.send_message('У вас нет прав для выполнения этой команды', ephemeral=True)
            return
        
        if time > 38880:  # Максимум 38880 минут
            await interaction.response.send_message('Максимальное время мута: 38880 минут', ephemeral=True)
            return
        
        try:
            from datetime import timedelta
            import discord.utils
            
            # Отправляем сообщение о муте в личку
            channel = await user.create_dm()
            embed = discord.Embed(
                color=0xffff00, 
                title='Мьют',
                description=f'Вы замьючены на {time} минут\nПо причине: {reason} by {interaction.user.mention}'
            )
            embed.set_footer(text=str(interaction.user), icon_url=interaction.user.avatar)
            await channel.send(embed=embed)
            
            # Мьютим пользователя
            timeout_until = discord.utils.utcnow() + timedelta(minutes=time)
            await user.edit(timed_out_until=timeout_until, reason=reason)
            
            await interaction.response.send_message(
                f'{user.mention}({user.id}) в мьюте на {time} минут {interaction.user.mention}\nПричина: {reason}',
                ephemeral=False
            )
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при муте: {e}', ephemeral=True)
    
    async def give_money(self, interaction: discord.Interaction, user: discord.Member, amount: int) -> None:
        """Выдает деньги пользователю (только для админа)"""
        if interaction.user.id != self.config.ADMIN_USER_ID:
            await interaction.response.send_message('У вас нет прав для выполнения этой команды', ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message('Сумма должна быть положительной', ephemeral=True)
            return
        
        try:
            await self.user_db.add_money(user.id, amount)
            
            # Отправляем уведомление в личку
            channel = await user.create_dm()
            new_balance = await self.user_db.get_money(user.id)
            
            embed = discord.Embed(
                color=0xfade34, 
                title='Пополнение',
                description=f'Перевод со счета сервера\nНа ваш счет зачислено `{amount}руб`\nВаш баланс: `{new_balance}руб`'
            )
            await channel.send(embed=embed)
            
            await interaction.response.send_message(f'Успешно выдано {amount}руб пользователю {user.mention}')
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при выдаче денег: {e}', ephemeral=True)
    
    async def remove_money(self, interaction: discord.Interaction, user: discord.Member, amount: int) -> None:
        """Снимает деньги у пользователя (только для админа)"""
        if interaction.user.id != self.config.ADMIN_USER_ID:
            await interaction.response.send_message('У вас нет прав для выполнения этой команды', ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message('Сумма должна быть положительной', ephemeral=True)
            return
        
        try:
            await self.user_db.rem_money(user.id, amount)
            await self.user_db.add_money(interaction.user.id, amount)
            
            # Отправляем уведомление в личку
            channel = await user.create_dm()
            new_balance = await self.user_db.get_money(user.id)
            
            embed = discord.Embed(
                color=0xff0000, 
                title='Списание',
                description=f'С вашего счета было списано `{amount}руб`\nВаш баланс: `{new_balance}руб`'
            )
            await channel.send(embed=embed)
            
            await interaction.response.send_message(f'Успешно спиздил {amount}руб у пользователя {user.mention}')
            
        except Exception as e:
            await interaction.response.send_message(f'Ошибка при снятии денег: {e}', ephemeral=True)
