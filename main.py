
import asyncio
import json
import logging
import threading
import time
from enum import Enum
from typing import Dict, Any, List

import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.upload import VkUpload

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputMediaPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# --------------------------- CONFIG ---------------------------
TELEGRAM_TOKEN = "8295931339:AAEP07XBDZ7FBIGSZg7SOZ8g7Sc_hsml8h0"
TELEGRAM_CHAT_ID = "-1003166604153"  # admin/group chat where leads are sent
VK_TOKEN = "vk1.a.Do3IzROgiVPPGSjBVw3nFEg2eIAsy7673mBTpwakOxj_qNTtCxEXx8Pa9NS_q7FbDZqVlfecQgofYCYotRguILuXWAYu7DL2gkQocsu7zcRvk3M9R_0jCzzjErAJRLcy_Zx4jEZR87zCFUJvKIvkU_hLmJbfozuPkamZbBaElI1yZ8U3RpRNqMdjkdwm5SdFFS1HqCp7xxLu0EnF4JyVqA"
VK_GROUP_ID = "233089872"

# Photos (raw GitHub URLs) - provided by user
WELCOME_PHOTOS: List[str] = [
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(2).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(3).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(4).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(5).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(6).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(7).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58.jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-59.jpg",
]

MATERIALS_PHOTOS: List[str] = [
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-06_15-58-59%20(2).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-06_15-58-59%20(3).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-06_15-58-59.jpg",
]

# Updated welcome text
WELCOME_MESSAGE = (
    "Приветствуем!🤝\n"
    "На связи 2М ФАБРИКА МЕБЕЛИ!\n"
    "Мы изготавливаем корпусную и встроенную мебель с 1993 года, по индивидуальным размерам:\n"
    "кухни, шкафы-купе, гардеробные, мебель для ванной и многое другое.\n"
    "Собственное производство, работаем без посредников, делаем все сами от замера до установки.\n"
    "Широкий выбор материалов более 1000 расцветок, от ЛДСП до Эмали и фурнитуры (Blum, Hettich, Boyard и др.).\n"
    "Бесплатный замер, доставка и установка по городу.\n"
    "При установки НЕ БЕРЁМ платы за вырезы: под варочную поверхность, под сан узлы, под плинтуса, под мойку как это делают другие мебельные компании.\n"
    "Гарантия 24 месяца на всю продукцию!\n"
    "Цены приятно удивят!\n"
    "Рассрочка!!!"
)

# storage for users
user_data: Dict[int, Dict[str, Any]] = {}

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Platform(Enum):
    TELEGRAM = "telegram"
    VK = "vk"


# ----------------------- Keyboards -----------------------
class KeyboardManager:
    @staticmethod
    def get_initial_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Кухня", callback_data="кухня")],
                [InlineKeyboardButton("Шкаф", callback_data="шкаф")],
                [InlineKeyboardButton("Гардеробная", callback_data="гардеробная")],
                [InlineKeyboardButton("Прихожая", callback_data="прихожая")],
                [InlineKeyboardButton("Мебель для ванной", callback_data="ванная")],
                [InlineKeyboardButton("Другая мебель", callback_data="другое")],
                [InlineKeyboardButton("Свяжитесь со мной", callback_data="связаться_со_мной")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:
            # VK keyboard (keeps labels shorter to fit UI)
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {"action": {"type": "callback", "label": "🍳 Кухня", "payload": json.dumps({"command": "кухня"})}, "color": "primary"},
                        {"action": {"type": "callback", "label": "🚪 Шкаф", "payload": json.dumps({"command": "шкаф"})}, "color": "primary"}
                    ],
                    [
                        {"action": {"type": "callback", "label": "👔 Гардеробная", "payload": json.dumps({"command": "гардеробная"})}, "color": "primary"},
                        {"action": {"type": "callback", "label": "🛋 Прихожая", "payload": json.dumps({"command": "прихожая"})}, "color": "primary"}
                    ],
                    [
                        {"action": {"type": "callback", "label": "🛁 Ванная", "payload": json.dumps({"command": "ванная"})}, "color": "primary"},
                        {"action": {"type": "callback", "label": "🛋 Другое", "payload": json.dumps({"command": "другое"})}, "color": "secondary"}
                    ],
                    [
                        {"action": {"type": "callback", "label": "📞 Связь", "payload": json.dumps({"command": "связаться_со_мной"})}, "color": "positive"}
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_phone_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [[KeyboardButton("📱 Отправить номер", request_contact=True)], [KeyboardButton("Ввести вручную")]]
            return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        else:
            keyboard = {"inline": True, "buttons": [[{"action": {"type": "callback", "label": "📞 Ввести телефон", "payload": json.dumps({"command": "ввести_телефон"})}, "color": "positive"}]]}
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_kitchen_type_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Угловая", callback_data="кухня_угловая")],
                [InlineKeyboardButton("Прямая", callback_data="кухня_прямая")],
                [InlineKeyboardButton("П-образная", callback_data="кухня_п_образная")],
                [InlineKeyboardButton("С островом", callback_data="кухня_остров")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")],
            ]
            return InlineKeyboardMarkup(keyboard)
        else:
            keyboard = {"inline": True, "buttons": [[[{"action": {"type": "callback", "label": "📐 Угловая", "payload": json.dumps({"command": "кухня_угловая"})}, "color": "primary"}]], [[{"action": {"type": "callback", "label": "📏 Прямая", "payload": json.dumps({"command": "кухня_прямая"})}, "color": "primary"}]], [[{"action": {"type": "callback", "label": "🔄 П-образная", "payload": json.dumps({"command": "кухня_п_образная"})}, "color": "primary"}]], [[{"action": {"type": "callback", "label": "🏝 С островом", "payload": json.dumps({"command": "кухня_остров"})}, "color": "primary"}]], [[{"action": {"type": "callback", "label": "🔙 Назад", "payload": json.dumps({"command": "назад_категории"})}, "color": "negative"}]]]}
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_material_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("ЛДСП", callback_data="материал_лдсп")],
                [InlineKeyboardButton("АГТ", callback_data="материал_агт")],
                [InlineKeyboardButton("Эмаль", callback_data="материал_эмаль")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_размер")],
            ]
            return InlineKeyboardMarkup(keyboard)
        else:
            keyboard = {"inline": True, "buttons": [
                [{"action": {"type": "callback", "label": "🌳 ЛДСП", "payload": json.dumps({"command": "материал_лдсп"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "✨ АГТ", "payload": json.dumps({"command": "материал_агт"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "🎨 Эмаль", "payload": json.dumps({"command": "материал_эмаль"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "🔙 Назад", "payload": json.dumps({"command": "назад_размер"})}, "color": "negative"}],
            ]}
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_hardware_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Эконом — до 150 тыс. руб.", callback_data="фурнитура_эконом")],
                [InlineKeyboardButton("Стандарт — 150–300 тыс. руб.", callback_data="фурнитура_стандарт")],
                [InlineKeyboardButton("Премиум — от 300 тыс. руб.", callback_data="фурнитура_премиум")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_материал")],
            ]
            return InlineKeyboardMarkup(keyboard)
        else:
            keyboard = {"inline": True, "buttons": [
                [{"action": {"type": "callback", "label": "💰 Эконом — до 150k", "payload": json.dumps({"command": "фурнитура_эконом"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "💎 Стандарт — 150–300k", "payload": json.dumps({"command": "фурнитура_стандарт"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "👑 Премиум — от 300k", "payload": json.dumps({"command": "фурнитура_премиум"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "🔙 Назад", "payload": json.dumps({"command": "назад_материал"})}, "color": "negative"}],
            ]}
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_budget_keyboard(platform: Platform, back_callback: str = "назад_предыдущий"):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Эконом — доступные материалы, базовая фурнитура (до 150 тыс. руб.)", callback_data="бюджет_эконом")],
                [InlineKeyboardButton("Стандарт - оптимальное соотношение цены и качества (от 150 -300 тыс. руб.)", callback_data="бюджет_стандарт")],
                [InlineKeyboardButton("Премиум - эксклюзивные материалы, сложные конструкции, премиальная фурнитура (от 300 тыс. руб.)", callback_data="бюджет_премиум")],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
            ]
            return InlineKeyboardMarkup(keyboard)
        else:
            keyboard = {"inline": True, "buttons": [
                [{"action": {"type": "callback", "label": "💰 Эконом — до 150k", "payload": json.dumps({"command": "бюджет_эконом"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "💎 Стандарт — 150–300k", "payload": json.dumps({"command": "бюджет_стандарт"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "👑 Премиум — от 300k", "payload": json.dumps({"command": "бюджет_премиум"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "🔙 Назад", "payload": json.dumps({"command": back_callback})}, "color": "negative"}],
            ]}
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_deadline_keyboard(platform: Platform, back_callback: str = "назад_бюджет"):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Этот месяц", callback_data="срок_месяц")],
                [InlineKeyboardButton("1-2 месяца", callback_data="срок_1_2")],
                [InlineKeyboardButton("3 месяца", callback_data="срок_3")],
                [InlineKeyboardButton("Присматриваюсь", callback_data="срок_присмотр")],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
            ]
            return InlineKeyboardMarkup(keyboard)
        else:
            keyboard = {"inline": True, "buttons": [
                [{"action": {"type": "callback", "label": "🗓 Этот месяц", "payload": json.dumps({"command": "срок_месяц"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "⏳ 1-2 месяца", "payload": json.dumps({"command": "срок_1_2"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "📅 3 месяца", "payload": json.dumps({"command": "срок_3"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "👀 Присматриваюсь", "payload": json.dumps({"command": "срок_присмотр"})}, "color": "primary"}],
                [{"action": {"type": "callback", "label": "🔙 Назад", "payload": json.dumps({"command": back_callback})}, "color": "negative"}],
            ]}
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_contact_final_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [[KeyboardButton("🔄 Начать заново")]]
            return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите способ связи...")
        else:
            keyboard = {"inline": True, "buttons": [[{"action": {"type": "callback", "label": "📞 По телефону", "payload": json.dumps({"command": "по_телефону"})}, "color": "positive"}], [{"action": {"type": "callback", "label": "💬 Сообщение в Telegram", "payload": json.dumps({"command": "сообщение_тг"})}, "color": "primary"}], [{"action": {"type": "callback", "label": "🔄 Начать заново", "payload": json.dumps({"command": "начать_заново"})}, "color": "secondary"}]]}
            return json.dumps(keyboard, ensure_ascii=False)


# ----------------------- Core -----------------------
class FurnitureBotCore:
    def __init__(self):
        self.adapters = {}

    def register_adapter(self, platform: Platform, adapter):
        self.adapters[platform] = adapter

    async def send_message(self, platform: Platform, user_id: int, text: str, keyboard=None):
        if platform in self.adapters:
            await self.adapters[platform].send_message(user_id, text, keyboard)

    async def edit_message(self, platform: Platform, user_id: int, message_id: int, text: str, keyboard=None):
        if platform in self.adapters:
            await self.adapters[platform].edit_message(user_id, message_id, text, keyboard)

    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        if user_id not in user_data:
            user_data[user_id] = {}
        return user_data[user_id]

    def clear_user_data(self, user_id: int):
        if user_id in user_data:
            del user_data[user_id]

    async def handle_start(self, platform: Platform, user_id: int):
        self.clear_user_data(user_id)
        # send welcome text + photos
        if platform == Platform.TELEGRAM:
            # send welcome text first
            await self.send_message(platform, user_id, WELCOME_MESSAGE, KeyboardManager.get_initial_keyboard(platform))
            # send album of photos
            try:
                media = [InputMediaPhoto(url) for url in WELCOME_PHOTOS]
                await self.adapters[Platform.TELEGRAM].application.bot.send_media_group(chat_id=user_id, media=media)
                logger.info(f"Отправлено {len(WELCOME_PHOTOS)} welcome фото в Telegram")
            except Exception as e:
                logger.error(f"Ошибка отправки welcome photos в Telegram: {e}")
                # Попробуем отправить по одному
                for url in WELCOME_PHOTOS:
                    try:
                        await self.adapters[Platform.TELEGRAM].application.bot.send_photo(chat_id=user_id, photo=url)
                    except Exception as e2:
                        logger.error(f"Ошибка отправки фото {url}: {e2}")
        else:
            # VK: send text then upload photos and send as album (messages)
            await self.send_message(platform, user_id, WELCOME_MESSAGE, KeyboardManager.get_initial_keyboard(platform))
            await self.send_photos_vk(user_id, WELCOME_PHOTOS, "welcome")

    async def send_photos_vk(self, user_id: int, photo_urls: List[str], photo_type: str = "photos"):
        """Универсальная функция отправки фото в VK"""
        try:
            vk_adapter = self.adapters[Platform.VK]
            upload = VkUpload(vk_adapter.vk_session)
            photo_attachments = []
            
            for i, url in enumerate(photo_urls):
                try:
                    logger.info(f"VK: Загрузка {photo_type} фото {i+1}/{len(photo_urls)}: {url}")
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Загружаем фото в VK
                    photo = upload.photo_messages(photos=response.content)[0]
                    attachment = f"photo{photo['owner_id']}_{photo['id']}"
                    photo_attachments.append(attachment)
                    
                    # Небольшая задержка между загрузками чтобы не превысить лимиты VK
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки {photo_type} фото {url}: {e}")
                    continue
            
            if photo_attachments:
                # Отправляем фото одним сообщением (максимум 10 вложений)
                attachments_str = ','.join(photo_attachments)
                vk_adapter.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    attachment=attachments_str
                )
                logger.info(f"VK: Отправлено {len(photo_attachments)} {photo_type} фото")
            else:
                logger.warning(f"VK: Не удалось загрузить ни одного {photo_type} фото")
                
        except Exception as e:
            logger.error(f"Критическая ошибка отправки {photo_type} фото в VK: {e}")

    async def request_name(self, platform: Platform, user_id: int, message_id: int = None):
        text = "👤 Контактные данные\n\nПожалуйста, напишите ваше имя:"
        if message_id and platform == Platform.TELEGRAM:
            await self.edit_message(platform, user_id, message_id, text)
        else:
            await self.send_message(platform, user_id, text)
        self.get_user_data(user_id)["waiting_for"] = "name"

    async def handle_callback(self, platform: Platform, user_id: int, data: str, message_id: int = None):
        user_data_local = self.get_user_data(user_id)

        if data.startswith("назад_"):
            await self.handle_back_button(platform, user_id, data, message_id)
            return

        if data == "связаться_со_мной":
            user_data_local["category"] = "связаться_со_мной"
            await self.request_name(platform, user_id, message_id)
            return

        # Обработка материалов - отправка фото материалов
        if data.startswith("материал_"):
            # remember material selection
            if data == "материал_лдсп":
                user_data_local["material"] = "ЛДСП"
            elif data == "материал_агт":
                user_data_local["material"] = "АГТ"
            elif data == "материал_эмаль":
                user_data_local["material"] = "Эмаль"

            # send explanation + photos
            text = "Вот примеры материалов:"
            await self.send_message(platform, user_id, text)

            if platform == Platform.TELEGRAM:
                try:
                    media = [InputMediaPhoto(url) for url in MATERIALS_PHOTOS]
                    await self.adapters[Platform.TELEGRAM].application.bot.send_media_group(chat_id=user_id, media=media)
                    logger.info(f"Отправлено {len(MATERIALS_PHOTOS)} фото материалов в Telegram")
                except Exception as e:
                    logger.error(f"Ошибка отправки материалов в Telegram: {e}")
                    # Fallback - отправка по одному
                    for url in MATERIALS_PHOTOS:
                        try:
                            await self.adapters[Platform.TELEGRAM].application.bot.send_photo(chat_id=user_id, photo=url)
                        except Exception as e2:
                            logger.error(f"Ошибка отправки фото материала {url}: {e2}")
            else:
                await self.send_photos_vk(user_id, MATERIALS_PHOTOS, "materials")
            
            # После показа материалов продолжаем поток
            await self.send_message(platform, user_id, "Выберите фурнитуру:", KeyboardManager.get_hardware_keyboard(platform))
            return

        # Упрощенная обработка других callback для демонстрации
        if data in ["кухня", "шкаф", "гардеробная", "прихожая", "ванная", "другое"]:
            user_data_local["category"] = data
            if data == "кухня":
                await self.send_message(platform, user_id, "Выберите тип кухни:", KeyboardManager.get_kitchen_type_keyboard(platform))
            else:
                await self.send_message(platform, user_id, "Выберите бюджет:", KeyboardManager.get_budget_keyboard(platform))
        
        elif data.startswith("бюджет_"):
            user_data_local["budget"] = data.replace("бюджет_", "")
            await self.send_message(platform, user_id, "Выберите сроки:", KeyboardManager.get_deadline_keyboard(platform))
        
        elif data.startswith("срок_"):
            user_data_local["deadline"] = data.replace("срок_", "")
            await self.request_name(platform, user_id, message_id)

    async def send_or_edit_message(self, platform: Platform, user_id: int, message_id: int, text: str, keyboard=None):
        if message_id and platform == Platform.TELEGRAM:
            await self.edit_message(platform, user_id, message_id, text, keyboard)
        else:
            await self.send_message(platform, user_id, text, keyboard)

    async def handle_back_button(self, platform: Platform, user_id: int, data: str, message_id: int = None):
        if data == "назад_категории":
            await self.send_or_edit_message(platform, user_id, message_id, WELCOME_MESSAGE, KeyboardManager.get_initial_keyboard(platform))

    async def handle_text_message(self, platform: Platform, user_id: int, text: str):
        user_data_local = self.get_user_data(user_id)
        normalized_text = text.lower().strip()
        if normalized_text in ["/start", "start", "начать", "меню"]:
            await self.handle_start(platform, user_id)
            return

        if user_data_local.get("waiting_for") == "name":
            user_data_local["name"] = text
            user_data_local["waiting_for"] = "phone"
            await self.send_message(platform, user_id, f"Имя принято: {text}\nПожалуйста, отправьте телефон:", KeyboardManager.get_phone_keyboard(platform))
            return

        if user_data_local.get("waiting_for") == "phone":
            cleaned = ''.join(c for c in text if c.isdigit() or c == '+')
            if (cleaned.startswith('+7') and len(cleaned) == 12) or (cleaned.startswith('8') and len(cleaned) == 11) or (len(cleaned) == 10):
                user_data_local['phone'] = cleaned
                user_data_local['waiting_for'] = None
                await self.send_final_summary(platform, user_id)
            else:
                await self.send_message(platform, user_id, "Неверный формат номера. Попробуйте снова.")
            return

        # default reply
        await self.send_message(platform, user_id, "Пожалуйста, используйте кнопки или /start для начала.", KeyboardManager.get_initial_keyboard(platform))

    async def send_final_summary(self, platform: Platform, user_id: int):
        user_data_local = self.get_user_data(user_id)
        summary = "✅ Ваша заявка принята!\n\n"
        category = user_data_local.get('category', 'Не указано')
        summary += f"Категория: {category}\n"
        if 'kitchen_type' in user_data_local:
            summary += f"Тип кухни: {user_data_local.get('kitchen_type')}\n"
        summary += f"Бюджет: {user_data_local.get('budget', 'Не указано')}\n"
        summary += f"Сроки: {user_data_local.get('deadline', 'Не указано')}\n"
        summary += f"Имя: {user_data_local.get('name', 'Не указано')}\n"
        summary += f"Телефон: {user_data_local.get('phone', 'Не указано')}\n"

        await self.send_message(platform, user_id, summary, KeyboardManager.get_contact_final_keyboard(platform))

        # send to admin group
        try:
            # Функция отправки в админ-чат (нужно реализовать)
            await self.send_telegram_application(user_data_local)
        except Exception as e:
            logger.error(f"Не удалось отправить заявку в админ-чат: {e}")

        self.clear_user_data(user_id)

    async def send_telegram_application(self, user_data: Dict[str, Any]):
        """Отправка заявки в админ-чат Telegram"""
        try:
            summary = "📝 Новая заявка!\n\n"
            summary += f"Категория: {user_data.get('category', 'Не указано')}\n"
            if 'kitchen_type' in user_data:
                summary += f"Тип кухни: {user_data.get('kitchen_type')}\n"
            summary += f"Бюджет: {user_data.get('budget', 'Не указано')}\n"
            summary += f"Сроки: {user_data.get('deadline', 'Не указано')}\n"
            summary += f"Имя: {user_data.get('name', 'Не указано')}\n"
            summary += f"Телефон: {user_data.get('phone', 'Не указано')}\n"
            
            await self.adapters[Platform.TELEGRAM].application.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=summary
            )
        except Exception as e:
            logger.error(f"Ошибка отправки заявки в админ-чат: {e}")


# ----------------------- Telegram Adapter -----------------------
class TelegramAdapter:
    def __init__(self, token: str, bot_core: FurnitureBotCore):
        self.bot_core = bot_core
        self.application = ApplicationBuilder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.bot_core.handle_start(Platform.TELEGRAM, update.effective_user.id)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await self.bot_core.handle_callback(Platform.TELEGRAM, update.effective_user.id, query.data, query.message.message_id)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.bot_core.handle_text_message(Platform.TELEGRAM, update.effective_user.id, update.message.text)

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data_local = self.bot_core.get_user_data(user_id)
        if user_data_local.get('waiting_for') == 'phone':
            phone_number = update.message.contact.phone_number
            user_data_local['phone'] = phone_number
            user_data_local['waiting_for'] = None
            await self.bot_core.send_final_summary(Platform.TELEGRAM, user_id)

    async def send_message(self, user_id: int, text: str, keyboard=None):
        try:
            await self.application.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в Telegram: {e}")

    async def edit_message(self, user_id: int, message_id: int, text: str, keyboard=None):
        try:
            await self.application.bot.edit_message_text(chat_id=user_id, message_id=message_id, text=text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения в Telegram: {e}")

    def run(self):
        logger.info("Запуск Telegram бота...")
        self.application.run_polling()


# ----------------------- VK Adapter (with auto-reconnect) -----------------------
class VKAdapter:
    def __init__(self, token: str, group_id: str, bot_core: FurnitureBotCore):
        self.bot_core = bot_core
        self.token = token
        self.group_id = group_id
        self.vk_session = None
        self.vk = None

    def run(self):
        logger.info("Запуск VK бота через Long Poll (с автопереподключением)...")
        while True:
            try:
                self.vk_session = vk_api.VkApi(token=self.token)
                self.vk = self.vk_session.get_api()
                longpoll = VkBotLongPoll(self.vk_session, self.group_id)
                logger.info("✓ Long Poll подключен успешно!")

                for event in longpoll.listen():
                    try:
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            self.handle_message(event)
                        elif event.type == VkBotEventType.MESSAGE_EVENT:
                            self.handle_callback(event)
                    except Exception as e:
                        logger.error(f"Ошибка обработки события VK: {e}")
            except Exception as e:
                logger.error(f"VK loop error: {e}")
                logger.info("Переподключение к VK через 10 секунд...")
                time.sleep(10)

    def handle_message(self, event):
        try:
            user_id = event.obj.message['from_id']
            text = event.obj.message.get('text', '')
            logger.info(f"VK: Сообщение от {user_id}: '{text}'")
            asyncio.run(self.process_message(user_id, text))
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения VK: {e}")

    def handle_callback(self, event):
        try:
            user_id = event.obj.user_id
            payload = event.obj.payload
            if isinstance(payload, str):
                try:
                    payload_dict = json.loads(payload)
                    command = payload_dict.get('command', '')
                except Exception:
                    command = payload
            else:
                command = str(payload)

            # send UI response
            try:
                self.vk.messages.sendMessageEventAnswer(
                    event_id=event.obj.event_id,
                    user_id=user_id,
                    peer_id=event.obj.peer_id,
                    event_data=json.dumps({"type": "show_snackbar", "text": "Обрабатываю..."})
                )
            except Exception as e:
                logger.debug(f"Не удалось отправить event answer: {e}")

            asyncio.run(self.process_callback(user_id, command))
        except Exception as e:
            logger.error(f"Ошибка обработки callback VK: {e}")

    async def process_message(self, user_id: int, text: str):
        try:
            await self.bot_core.handle_text_message(Platform.VK, user_id, text)
        except Exception as e:
            logger.error(f"Ошибка process_message VK: {e}")

    async def process_callback(self, user_id: int, command: str):
        try:
            await self.bot_core.handle_callback(Platform.VK, user_id, command)
        except Exception as e:
            logger.error(f"Ошибка process_callback VK: {e}")

    async def send_message(self, user_id: int, text: str, keyboard=None):
        try:
            params = {
                'user_id': user_id,
                'message': text,
                'random_id': get_random_id(),
            }
            if keyboard:
                params['keyboard'] = keyboard

            result = self.vk.messages.send(**params)
            return result
        except Exception as e:
            logger.error(f"VK: Ошибка отправки сообщения: {e}")

    async def edit_message(self, user_id: int, message_id: int, text: str, keyboard=None):
        # VK longpoll can't edit messages: send new
        await self.send_message(user_id, text, keyboard)


# ----------------------- Main -----------------------

def main():
    logger.info("Запуск мультиплатформенного бота...")
    bot_core = FurnitureBotCore()

    telegram_adapter = TelegramAdapter(TELEGRAM_TOKEN, bot_core)
    vk_adapter = VKAdapter(VK_TOKEN, VK_GROUP_ID, bot_core)

    bot_core.register_adapter(Platform.TELEGRAM, telegram_adapter)
    bot_core.register_adapter(Platform.VK, vk_adapter)

    # Запускаем VK в отдельном потоке (будет автоматически переподключаться при ошибках)
    vk_thread = threading.Thread(target=vk_adapter.run, daemon=True)
    vk_thread.start()

    logger.info("VK: работает")
    logger.info("Telegram: запускается в главном потоке")

    # Запуск Telegram в главном потоке (async library)
    telegram_adapter.run()


if __name__ == '__main__':
    main()
