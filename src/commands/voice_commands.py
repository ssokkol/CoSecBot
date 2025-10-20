import discord
from discord.ext import commands
import logging
import random
from .base_command import BaseCommand

logger = logging.getLogger(__name__)

class VoiceCommands(BaseCommand):
    CHANNEL_EMOJIS = [
        "🎮", "🎲", "🎯", "🎨", "🎭", "🎪", "🎢", "🎡", "🎠", "🎬", "🕹️", "🃏", "🎱",
        "🌟", "💫", "🌙", "☀️", "⚡", "🔥", "❄️", "🌈", "🌊", "☄️", "🌍", "🌌", "🪐",
        "🍀", "🌸", "🌺", "🌷", "🌹", "🌻", "🌼", "🌿", "☘️", "🍃", "🌴", "🌳", "🌲", 
        "🎵", "🎶", "🎼", "🎧", "🎤", "🎸", "🥁", "🎹", "🎷", "🎺", "🪘", "🎻", "🍁",
        "👾", "👻", "🤖", "🎃", "💎", "🔮", "⚔️", "🛡️", "🏹", "🗡️", "🪄", "🧙‍♂️", "🧙‍♀️",
        "🚀", "✈️", "🛸", "🛩️", "🚁", "🛶", "⛵", "🚂", "🚃", "🚤", "🛳️", "🗺️", "🧭",
        "🏰", "⛺", "🏠", "🌆", "🌃", "🏛️", "⛩️", "🏯", "🏚️", "🏘️", "🏙️", "🌉", "🌇",
        "🦁", "🐯", "🐺", "🦊", "🦝", "🐶", "🐱", "🦅", "🦉", "🦚", "🐉", "🐲", "🦋",
        "🍕", "🍜", "🍖", "🍗", "🥪", "🌮", "🌯", "🍱", "🍣", "🍦", "🍰", "🎂", "☕",
        "💠", "🔱", "✴️", "❇️", "〽️", "⚜️", "🔰", "🈁", "🔆", "🌐", "💮", "🍵", "🦄",
        "💥", "💢", "💦", "💨", "💪", "👊", "✌️", "🤘", "🤙", "👍", "💝", "💖", "🏖️",
    ]
    """Класс для управления динамическими голосовыми каналами"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.dynamic_voice_channels = {}  # Словарь для отслеживания созданных каналов

    async def handle_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Обработчик изменения состояния голосового канала"""
        try:
            # Если пользователь подключился к лобби-каналу
            if after.channel and after.channel.id == self.bot.config.DYNAMIC_VOICE_LOBBY_ID:
                await self._create_dynamic_channel(member)
            
            # Если пользователь покинул канал
            if before.channel and before.channel.category_id == self.bot.config.DYNAMIC_VOICE_CATEGORY_ID:
                if before.channel.id != self.bot.config.DYNAMIC_VOICE_LOBBY_ID:
                    await self._cleanup_empty_channel(before.channel)

        except Exception as e:
            logger.error(f"Ошибка при обработке изменения голосового состояния: {e}")

    async def _create_dynamic_channel(self, member: discord.Member):
        """Создает новый динамический голосовой канал"""
        try:
            category = self.bot.get_channel(self.bot.config.DYNAMIC_VOICE_CATEGORY_ID)
            if category:
                # Выбираем случайный эмодзи из списка
                random_emoji = random.choice(self.CHANNEL_EMOJIS)
                channel_name = f"{random_emoji} | {member.display_name}"
                new_channel = await member.guild.create_voice_channel(
                    name=channel_name,
                    category=category,
                    bitrate=96000
                )
                
                # Настраиваем права для создателя канала
                await new_channel.set_permissions(member,
                    manage_channels=True,
                    manage_permissions=True,
                    connect=True,
                    speak=True
                )
                
                # Сохраняем информацию о владельце канала
                self.dynamic_voice_channels[new_channel.id] = member.id
                
                # Перемещаем пользователя в новый канал
                await member.move_to(new_channel)
                logger.info(f"Создан динамический канал {channel_name} для пользователя {member.name}")

        except Exception as e:
            logger.error(f"Ошибка при создании динамического канала: {e}")

    async def _cleanup_empty_channel(self, channel: discord.VoiceChannel):
        """Удаляет пустой динамический канал"""
        try:
            if len(channel.members) == 0:
                await channel.delete()
                if channel.id in self.dynamic_voice_channels:
                    del self.dynamic_voice_channels[channel.id]
                logger.info(f"Удален пустой динамический канал {channel.name}")
        
        except Exception as e:
            logger.error(f"Ошибка при удалении динамического канала: {e}")

    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """
        Этот метод необходим для соответствия абстрактному классу BaseCommand,
        но не используется напрямую, так как класс работает через события
        """
        await interaction.response.send_message(
            "Эта команда не предназначена для прямого использования. "
            "Просто зайдите в канал лобби для создания персонального канала.",
            ephemeral=True
        )