import os
import requests
from PIL import Image, ImageDraw, ImageOps, ImageFont
from typing import Optional
from io import BytesIO
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class ProfileImageGenerator:
    """Генератор изображений профилей для Discord бота"""
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = assets_path
        self.font_path = os.path.join(assets_path, "fonts", "AB.otf")
        
        # Пути к шаблонам
        self.templates = {
            'online': os.path.join(assets_path, 'templates', 'otemplate.png'),
            'idle': os.path.join(assets_path, 'templates', 'itemplate.png'),
            'dnd': os.path.join(assets_path, 'templates', 'dnttemplate.png'),
            'offline': os.path.join(assets_path, 'templates', 'offtemplate.png')
        }
        
        # Путь к аватару по умолчанию
        self.default_avatar = os.path.join(assets_path, 'avatars', 'avatar.jpg')
    
    async def download_avatar(self, avatar_url: str) -> Optional[Image.Image]:
        """Загружает аватар пользователя"""
        try:
            response = requests.get(avatar_url, timeout=10)
            response.raise_for_status()
            
            img_data = response.content
            img = Image.open(BytesIO(img_data)).convert("RGBA")
            return img
        except Exception as e:
            logger.error(f"Ошибка загрузки аватара: {e}")
            return None
    
    async def _create_rounded_avatar(self, image: Image.Image, size: tuple) -> Optional[Image.Image]:
        """Создает круглый аватар из изображения"""
        try:
            # Создаем маску
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)

            # Изменяем размер изображения и применяем маску
            output = ImageOps.fit(image, size, centering=(0.5, 0.5))
            output.putalpha(mask)

            return output
        except Exception as e:
            logger.error(f"Ошибка создания круглого аватара: {e}")
            return None

    async def _add_text(self, image: Image.Image, text: str, position: tuple,
                     font_size: int, color: tuple = (255, 255, 255)) -> None:
        """Добавляет текст на изображение"""
        try:
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(self.font_path, font_size)
            draw.text(position, text, font=font, fill=color)
        except Exception as e:
            logger.error(f"Ошибка добавления текста: {e}")

    def create_circular_avatar(self, avatar: Image.Image, size: tuple) -> Image.Image:
        """Создает круглый аватар"""
        try:
            # Изменяем размер
            avatar = avatar.resize(size)
            
            # Создаем маску для круглой формы
            bigsize = (avatar.size[0] * 3, avatar.size[1] * 3)
            mask = Image.new('L', bigsize, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + bigsize, fill=255)
            
            # Применяем маску
            mask = mask.resize(avatar.size, Image.Resampling.LANCZOS)
            avatar.putalpha(mask)
            
            return avatar
        except Exception as e:
            logger.error(f"Ошибка создания круглого аватара: {e}")
            return avatar
    
    def add_text_to_image(self, img: Image.Image, text: str, position: tuple, 
                          font_size: int = 64, color: tuple = (255, 255, 255)) -> Image.Image:
        """Добавляет текст на изображение"""
        try:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(self.font_path, font_size)
            draw.text(position, text, font=font, fill=color)
        except Exception as e:
            logger.error(f"Ошибка добавления текста: {e}")

        return img
    
    def truncate_text(self, text: str, max_length: int) -> str:
        """Обрезает текст до максимальной длины"""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text
    
    async def generate_profile_image(self, user_data: dict, output_path: str = "output.png") -> bool:
        """Генерирует изображение профиля пользователя"""
        try:
            # Получаем статус пользователя и конвертируем его в строчный вид
            status = str(user_data.get('status', 'online')).lower()
            # Маппинг статусов discord на наши шаблоны
            status_mapping = {
                'online': 'otemplate.png',
                'idle': 'itemplate.png',
                'dnd': 'dnttemplate.png',
                'offline': 'offtemplate.png'
            }

            template_name = status_mapping.get(status, 'otemplate.png')
            template_path = os.path.join(self.assets_path, 'templates', template_name)

            # Загружаем шаблон
            if not os.path.exists(template_path):
                logger.error(f"Шаблон не найден: {template_path}")
                return False
            
            background = Image.open(template_path)
            
            # Загружаем и обрабатываем аватар
            avatar_url = user_data.get('avatar_url')
            if avatar_url:
                avatar = await self.download_avatar(avatar_url)
                if avatar:
                    circular_avatar = self.create_circular_avatar(avatar, (238, 238))
                    background.paste(circular_avatar, (70, 158), circular_avatar)
            
            # Добавляем информацию о пользователе
            img = background
            
            # Ник пользователя
            nick = self.truncate_text(user_data.get('nickname', ''), 12)
            img = self.add_text_to_image(img, nick, (344, 207), 100)
            
            # Дата создания/присоединения
            dates = f"{user_data.get('created_date', '')}/{user_data.get('joined_date', '')}"
            dates = self.truncate_text(dates, 21)
            img = self.add_text_to_image(img, dates, (135, 448), 40)

            # Баланс
            balance = f"{user_data.get('balance', 0)} руб"
            balance = self.truncate_text(balance, 26)
            img = self.add_text_to_image(img, balance, (91, 667), 64)
            
            # Сообщения
            messages = f"{user_data.get('messages', 0)} сообщений"
            messages = self.truncate_text(messages, 27)
            img = self.add_text_to_image(img, messages, (91, 793), 64)
            
            # Время в голосовых каналах
            voice_time = f"{user_data.get('voice_time', '0:00:00')} в войсе"
            voice_time = self.truncate_text(voice_time, 28)
            img = self.add_text_to_image(img, voice_time, (91, 918), 64)
            
            # Сохраняем изображение
            img.save(output_path, optimize=True, quality=95)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return False
    
    async def add_badges_to_profile(self, profile_path: str, user_roles: list, 
                                   badges_path: str = "assets/badges") -> bool:
        """Добавляет значки на профиль пользователя"""
        try:
            if not os.path.exists(profile_path):
                logger.error(f"Файл профиля не найден: {profile_path}")
                return False
            
            img = Image.open(profile_path)
            
            # Проходим по всем ролям пользователя
            for role_id in user_roles:
                badge_path = os.path.join(badges_path, f"{role_id}.png")
                
                if os.path.exists(badge_path):
                    try:
                        badge = Image.open(badge_path)
                        
                        # Создаем новое изображение с альфа-каналом
                        img2 = Image.new("RGBA", img.size)
                        img2 = Image.alpha_composite(img2, img)
                        img2 = Image.alpha_composite(img2, badge)
                        
                        # Сохраняем результат
                        img2.save(profile_path, optimize=True, quality=95)
                        img = img2
                    except Exception as e:
                        logger.warning(f"Не удалось добавить значок {role_id}: {e}")
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления значков: {e}")
            return False
