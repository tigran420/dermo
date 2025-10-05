import asyncio
import json
import logging
import threading
import time
from enum import Enum
from typing import Dict, Any

# VK imports
import vk_api
# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Platform(Enum):
    TELEGRAM = "telegram"
    VK = "vk"


# КОНФИГУРАЦИЯ
TELEGRAM_TOKEN = "8295931339:AAEP07XBDZ7FBIGSZg7SOZ8g7Sc_hsml8h0"
VK_TOKEN = "vk1.a.Do3IzROgiVPPGSjBVw3nFEg2eIAsy7673mBTpwakOxj_qNTtCxEXx8Pa9NS_q7FbDZqVlfecQgofYCYotRguILuXWAYu7DL2gkQocsu7zcRvk3M9R_0jCzzjErAJRLcy_Zx4jEZR87zCFUJvKIvkU_hLmJbfozuPkamZbBaElI1yZ8U3RpRNqMdjkdwm5SdFFS1HqCp7xxLu0EnF4JyVqA"
VK_GROUP_ID = "233089872"

# Приветственное сообщение
WELCOME_MESSAGE = """
Приветствую вас!
Наша компания занимается производством качественной мебели уже более 10 лет.
Мы предлагаем широкий ассортимент продукции для любого интерьера.
Выберите категорию интересующей вас мебели:
"""

# Хранилище данных пользователя
user_data = {}


# Класс для управления клавиатурами
class KeyboardManager:
    @staticmethod
    def get_categories_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Кухня", callback_data="кухня")],
                [InlineKeyboardButton("Шкаф", callback_data="шкаф")],
                [InlineKeyboardButton("Гардеробная", callback_data="гардеробная")],
                [InlineKeyboardButton("Другая мебель", callback_data="другое")],
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🍳 Кухня",
                            "payload": "{\"command\": \"кухня\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🚪 Шкаф",
                            "payload": "{\"command\": \"шкаф\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "👔 Гардеробная",
                            "payload": "{\"command\": \"гардеробная\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🛋 Другая мебель",
                            "payload": "{\"command\": \"другое\"}"
                        },
                        "color": "secondary"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_actions_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [KeyboardButton("Консультация"), KeyboardButton("Написать в ТГ")]
            ]
            return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие...")
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📞 Консультация",
                            "payload": "{\"command\": \"консультация\"}"
                        },
                        "color": "positive"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "💬 Написать в ТГ",
                            "payload": "{\"command\": \"написать_тг\"}"
                        },
                        "color": "primary"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_contact_final_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [KeyboardButton("📞 По телефону"), KeyboardButton("💬 Сообщение в Telegram")],
                [KeyboardButton("🔄 Начать заново")]
            ]
            return ReplyKeyboardMarkup(keyboard, resize_keyboard=True,
                                       input_field_placeholder="Выберите способ связи...")
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📞 По телефону",
                            "payload": "{\"command\": \"по_телефону\"}"
                        },
                        "color": "positive"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "💬 Сообщение в Telegram",
                            "payload": "{\"command\": \"сообщение_тг\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔄 Начать заново",
                            "payload": "{\"command\": \"начать_заново\"}"
                        },
                        "color": "secondary"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_phone_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [KeyboardButton("📱 Отправить номер", request_contact=True)],
                [KeyboardButton("Ввести вручную")]
            ]
            return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📞 Ввести телефон",
                            "payload": "{\"command\": \"ввести_телефон\"}"
                        },
                        "color": "positive"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_kitchen_type_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Угловая", callback_data="кухня_угловая")],
                [InlineKeyboardButton("Прямая", callback_data="кухня_прямая")],
                [InlineKeyboardButton("П-образная", callback_data="кухня_п_образная")],
                [InlineKeyboardButton("С островом", callback_data="кухня_остров")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📐 Угловая",
                            "payload": "{\"command\": \"кухня_угловая\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📏 Прямая",
                            "payload": "{\"command\": \"кухня_прямая\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔄 П-образная",
                            "payload": "{\"command\": \"кухня_п_образная\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🏝 С островом",
                            "payload": "{\"command\": \"кухня_остров\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_категории\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_size_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Точные", callback_data="размер_точные")],
                [InlineKeyboardButton("Приблизительные", callback_data="размер_приблизительные")],
                [InlineKeyboardButton("Не знаю", callback_data="размер_не_знаю")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_тип")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📏 Точные размеры",
                            "payload": "{\"command\": \"размер_точные\"}"
                        },
                        "color": "positive"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📐 Приблизительные",
                            "payload": "{\"command\": \"размер_приблизительные\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "❓ Не знаю",
                            "payload": "{\"command\": \"размер_не_знаю\"}"
                        },
                        "color": "secondary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_тип\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_material_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("ЛДСП", callback_data="материал_лдсп")],
                [InlineKeyboardButton("АГТ", callback_data="материал_агт")],
                [InlineKeyboardButton("Эмаль", callback_data="материал_эмаль")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_размер")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🌳 ЛДСП",
                            "payload": "{\"command\": \"материал_лдсп\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "✨ АГТ",
                            "payload": "{\"command\": \"материал_агт\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🎨 Эмаль",
                            "payload": "{\"command\": \"материал_эмаль\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_размер\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_hardware_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Эконом", callback_data="фурнитура_эконом")],
                [InlineKeyboardButton("Стандарт", callback_data="фурнитура_стандарт")],
                [InlineKeyboardButton("Премиум", callback_data="фурнитура_премиум")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_материал")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "💰 Эконом",
                            "payload": "{\"command\": \"фурнитура_эконом\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "💎 Стандарт",
                            "payload": "{\"command\": \"фурнитура_стандарт\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "👑 Премиум",
                            "payload": "{\"command\": \"фурнитура_премиум\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_материал\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_budget_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Эконом", callback_data="бюджет_эконом")],
                [InlineKeyboardButton("Стандарт", callback_data="бюджет_стандарт")],
                [InlineKeyboardButton("Премиум", callback_data="бюджет_премиум")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_предыдущий")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "💰 Эконом",
                            "payload": "{\"command\": \"бюджет_эконом\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "💎 Стандарт",
                            "payload": "{\"command\": \"бюджет_стандарт\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "👑 Премиум",
                            "payload": "{\"command\": \"бюджет_премиум\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_предыдущий\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_deadline_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Этот месяц", callback_data="срок_месяц")],
                [InlineKeyboardButton("1-2 месяца", callback_data="срок_1_2")],
                [InlineKeyboardButton("3 месяца", callback_data="срок_3")],
                [InlineKeyboardButton("Присматриваюсь", callback_data="срок_присмотр")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_бюджет")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📅 Этот месяц",
                            "payload": "{\"command\": \"срок_месяц\"}"
                        },
                        "color": "positive"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "📆 1-2 месяца",
                            "payload": "{\"command\": \"срок_1_2\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🗓 3 месяца",
                            "payload": "{\"command\": \"срок_3\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "👀 Присматриваюсь",
                            "payload": "{\"command\": \"срок_присмотр\"}"
                        },
                        "color": "secondary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_бюджет\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_cabinet_type_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Распашной", callback_data="шкаф_распашной")],
                [InlineKeyboardButton("Купе", callback_data="шкаф_купе")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🚪 Распашной",
                            "payload": "{\"command\": \"шкаф_распашной\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🚶 Купе",
                            "payload": "{\"command\": \"шкаф_купе\"}"
                        },
                        "color": "primary"
                    }],
                    [{
                        "action": {
                            "type": "callback",
                            "label": "🔙 Назад",
                            "payload": "{\"command\": \"назад_категории\"}"
                        },
                        "color": "negative"
                    }]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)


# Ядро бота с общей логикой
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
        await self.send_message(
            platform, user_id, WELCOME_MESSAGE,
            KeyboardManager.get_categories_keyboard(platform)
        )

    async def request_name(self, platform: Platform, user_id: int, message_id: int = None):
        text = "👤 **Контактные данные**\n\nПожалуйста, напишите ваше имя:"
        if message_id:
            await self.edit_message(platform, user_id, message_id, text)
        else:
            await self.send_message(platform, user_id, text)
        self.get_user_data(user_id)['waiting_for'] = 'name'

    async def handle_callback(self, platform: Platform, user_id: int, data: str, message_id: int = None):
        user_data = self.get_user_data(user_id)

        # Обработка кнопки "Назад"
        if data.startswith("назад_"):
            await self.handle_back_button(platform, user_id, data, message_id)
            return

        # Обработка выбора категории
        if data == "кухня":
            user_data['category'] = 'кухня'
            user_data['current_step'] = 'kitchen_type'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🏠 **Кухня**\n\nВыберите тип кухни:",
                KeyboardManager.get_kitchen_type_keyboard(platform)
            )

        elif data == "шкаф":
            user_data['category'] = 'шкаф'
            user_data['current_step'] = 'cabinet_type'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                KeyboardManager.get_cabinet_type_keyboard(platform)
            )

        elif data == "гардеробная":
            user_data['category'] = 'гардеробная'
            user_data['current_step'] = 'size'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "👔 **Гардеробная**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform)
            )

        elif data == "другое":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🛋 **Другая мебель**\n\nУточните, какая мебель вас интересует?",
                KeyboardManager.get_actions_keyboard(platform)
            )

        # Обработка сценария КУХНЯ
        elif data.startswith("кухня_"):
            if data == "кухня_угловая":
                user_data['kitchen_type'] = 'Угловая'
            elif data == "кухня_прямая":
                user_data['kitchen_type'] = 'Прямая'
            elif data == "кухня_п_образная":
                user_data['kitchen_type'] = 'П-образная'
            elif data == "кухня_остров":
                user_data['kitchen_type'] = 'С островом'

            user_data['current_step'] = 'size'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📏 **Размеры**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform)
            )

        # Обработка размеров (общее для Кухни и Гардеробной)
        elif data.startswith("размер_"):
            if data == "размер_точные":
                user_data['size'] = 'Точные'
            elif data == "размер_приблизительные":
                user_data['size'] = 'Приблизительные'
            elif data == "размер_не_знаю":
                user_data['size'] = 'Не знаю'

            # Определяем следующий шаг в зависимости от категории
            category = user_data.get('category', '')

            if category == 'кухня':
                user_data['current_step'] = 'material'
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🎨 **Материал фасадов**\n\nВыберите материал:",
                    KeyboardManager.get_material_keyboard(platform)
                )
            elif category == 'гардеробная':
                user_data['current_step'] = 'budget'
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "💰 **Бюджет**\n\nВыберите бюджет:",
                    KeyboardManager.get_budget_keyboard(platform)
                )

        elif data.startswith("материал_"):
            if data == "материал_лдсп":
                user_data['material'] = 'ЛДСП'
            elif data == "материал_агт":
                user_data['material'] = 'АГТ'
            elif data == "материал_эмаль":
                user_data['material'] = 'Эмаль'

            user_data['current_step'] = 'hardware'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
                KeyboardManager.get_hardware_keyboard(platform)
            )

        elif data.startswith("фурнитура_"):
            if data == "фурнитура_эконом":
                user_data['hardware'] = 'Эконом'
            elif data == "фурнитура_стандарт":
                user_data['hardware'] = 'Стандарт'
            elif data == "фурнитура_премиум":
                user_data['hardware'] = 'Премиум'

            user_data['current_step'] = 'budget'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💰 **Бюджет**\n\nВыберите бюджет:",
                KeyboardManager.get_budget_keyboard(platform)
            )

        elif data.startswith("бюджет_"):
            if data == "бюджет_эконом":
                user_data['budget'] = 'Эконом'
            elif data == "бюджет_стандарт":
                user_data['budget'] = 'Стандарт'
            elif data == "бюджет_премиум":
                user_data['budget'] = 'Премиум'

            user_data['current_step'] = 'deadline'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📅 **Сроки заказа**\n\nВыберите сроки:",
                KeyboardManager.get_deadline_keyboard(platform)
            )

        # Обработка сценария ШКАФ
        elif data.startswith("шкаф_"):
            if data == "шкаф_распашной":
                user_data['cabinet_type'] = 'Распашной'
            elif data == "шкаф_купе":
                user_data['cabinet_type'] = 'Купе'

            user_data['current_step'] = 'budget'
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💰 **Бюджет**\n\nВыберите бюджет:",
                KeyboardManager.get_budget_keyboard(platform)
            )

        # Обработка сроков заказа (переходим к запросу контактных данных)
        elif data.startswith("срок_"):
            if data == "срок_месяц":
                user_data['deadline'] = 'Этот месяц'
            elif data == "срок_1_2":
                user_data['deadline'] = '1-2 месяца'
            elif data == "срок_3":
                user_data['deadline'] = '3 месяца'
            elif data == "срок_присмотр":
                user_data['deadline'] = 'Присматриваюсь'

            # Запрашиваем имя
            await self.request_name(platform, user_id, message_id)

        # Обработка дополнительных кнопок для VK
        elif data == "ввести_телефон":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📱 **Введите номер телефона:**\n\nФормат: +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
            user_data['waiting_for'] = 'phone'

        elif data == "консультация":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📞 **Консультация**\n\nДля консультации свяжитесь с нами:\n\n"
                "💬 Телеграм: @max_lap555\n"
                "📱 WhatsApp: +79063405556",
                KeyboardManager.get_actions_keyboard(platform)
            )

        elif data == "написать_тг":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💬 **Написать в Telegram**\n\n"
                "Перейдите в Telegram: @max_lap555\n"
                "Или напишите на номер: +79063405556",
                KeyboardManager.get_actions_keyboard(platform)
            )

        elif data == "по_телефону":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📞 **Связь по телефону**\n\n"
                "Позвоните нам по номеру:\n"
                "📱 +79063405556\n\n"
                "Мы доступны:\n"
                "• Пн-Пт: 9:00-18:00\n"
                "• Сб: 10:00-16:00",
                KeyboardManager.get_contact_final_keyboard(platform)
            )

        elif data == "сообщение_тг":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💬 **Сообщение в Telegram**\n\n"
                "Напишите нам в Telegram:\n"
                "👤 @max_lap555\n\n"
                "Или перейдите по ссылке:\n"
                "https://t.me/max_lap555",
                KeyboardManager.get_contact_final_keyboard(platform)
            )

        elif data == "начать_заново":
            self.clear_user_data(user_id)
            await self.handle_start(platform, user_id)

    async def send_or_edit_message(self, platform: Platform, user_id: int, message_id: int, text: str, keyboard=None):
        if message_id:
            await self.edit_message(platform, user_id, message_id, text, keyboard)
        else:
            await self.send_message(platform, user_id, text, keyboard)

    async def handle_back_button(self, platform: Platform, user_id: int, data: str, message_id: int = None):
        back_step = data.replace("назад_", "")

        if back_step == "категории":
            self.clear_user_data(user_id)
            await self.send_or_edit_message(
                platform, user_id, message_id,
                WELCOME_MESSAGE,
                KeyboardManager.get_categories_keyboard(platform)
            )

        elif back_step == "тип":
            category = self.get_user_data(user_id).get('category', '')
            if category == 'кухня':
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🏠 **Кухня**\n\nВыберите тип кухни:",
                    KeyboardManager.get_kitchen_type_keyboard(platform)
                )
            elif category == 'шкаф':
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                    KeyboardManager.get_cabinet_type_keyboard(platform)
                )

        elif back_step == "размер":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📏 **Размеры**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform)
            )

        elif back_step == "материал":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🎨 **Материал фасадов**\n\nВыберите материал:",
                KeyboardManager.get_material_keyboard(platform)
            )

        elif back_step == "предыдущий":
            # Определяем предыдущий шаг на основе категории
            category = self.get_user_data(user_id).get('category', '')
            if category == 'кухня':
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
                    KeyboardManager.get_hardware_keyboard(platform)
                )
            elif category in ['шкаф', 'гардеробная']:
                if category == 'шкаф':
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                        KeyboardManager.get_cabinet_type_keyboard(platform)
                    )
                else:
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "👔 **Гардеробная**\n\nКакие у вас размеры?",
                        KeyboardManager.get_size_keyboard(platform)
                    )

        elif back_step == "бюджет":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💰 **Бюджет**\n\nВыберите бюджет:",
                KeyboardManager.get_budget_keyboard(platform)
            )

    async def handle_text_message(self, platform: Platform, user_id: int, text: str):
        user_data = self.get_user_data(user_id)

        # Нормализуем текст команды
        normalized_text = text.lower().strip()

        # Команды для запуска бота
        start_commands = ['/start', 'start', 'начать', 'старт', 'go', 'меню']

        if normalized_text in start_commands:
            await self.handle_start(platform, user_id)
            return

        # Если ожидаем имя
        if user_data.get('waiting_for') == 'name':
            user_data['name'] = text
            user_data['waiting_for'] = 'phone'

            await self.send_message(
                platform, user_id,
                f"👤 **Имя принято:** {text}\n\n"
                "📱 **Телефон**\n\nПожалуйста, отправьте ваш номер телефона:",
                KeyboardManager.get_phone_keyboard(platform)
            )

        # Если ожидаем телефон и пользователь ввел вручную
        elif user_data.get('waiting_for') == 'phone':
            # Если пользователь нажал "Ввести вручную" в Telegram
            if text == "Ввести вручную":
                # Для Telegram используем специальную клавиатуру без кнопок
                if platform == Platform.TELEGRAM:
                    from telegram import ReplyKeyboardRemove
                    await self.send_message(
                        platform, user_id,
                        "📱 **Введите номер телефона вручную:**\n\n"
                        "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX",
                        ReplyKeyboardRemove()
                    )
                else:
                    await self.send_message(
                        platform, user_id,
                        "📱 **Введите номер телефона вручную:**\n\n"
                        "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
                    )
                return

            # Простая валидация номера телефона
            phone = text.strip()
            # Убираем все нецифровые символы кроме +
            cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')

            # Проверяем различные форматы номеров
            is_valid = False
            if cleaned_phone.startswith('+7') and len(cleaned_phone) == 12:
                is_valid = True
            elif cleaned_phone.startswith('8') and len(cleaned_phone) == 11:
                is_valid = True
                cleaned_phone = '+7' + cleaned_phone[1:]  # Конвертируем в международный формат
            elif cleaned_phone.startswith('7') and len(cleaned_phone) == 11:
                is_valid = True
                cleaned_phone = '+7' + cleaned_phone[1:]

            if is_valid:
                user_data['phone'] = cleaned_phone
                user_data['waiting_for'] = None

                # Формируем итоговое сообщение с данными
                await self.send_final_summary(platform, user_id)

            else:
                await self.send_message(
                    platform, user_id,
                    "❌ **Неверный формат номера**\n\n"
                    "Пожалуйста, введите номер в формате:\n"
                    "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
                    "Примеры:\n"
                    "+79123456789\n"
                    "89123456789\n"
                    "9123456789",
                    KeyboardManager.get_phone_keyboard(platform)
                )

        # Обработка текстовых команд для дополнительных действий
        elif normalized_text == "консультация":
            await self.send_message(
                platform, user_id,
                "📞 **Консультация**\n\nДля консультации свяжитесь с нами:\n\n"
                "💬 Телеграм: @max_lap555\n"
                "📱 WhatsApp: +79063405556",
                KeyboardManager.get_actions_keyboard(platform)
            )

        elif normalized_text == "написать в тг":
            await self.send_message(
                platform, user_id,
                "💬 **Написать в Telegram**\n\n"
                "Перейдите в Telegram: @max_lap555\n"
                "Или напишите на номер: +79063405556",
                KeyboardManager.get_actions_keyboard(platform)
            )
        else:
            # Если непонятное сообщение - отправляем приветствие
            await self.handle_start(platform, user_id)

    async def send_final_summary(self, platform: Platform, user_id: int):
        user_data = self.get_user_data(user_id)

        # Формируем итоговое сообщение БЕЗ Markdown разметки
        summary = "✅ Заявка принята!\n\n"
        summary += "📋 Данные заявки:\n"

        category = user_data.get('category', 'Не указано')
        summary += f"• Категория: {category}\n"

        if category == 'кухня':
            summary += f"• Тип кухни: {user_data.get('kitchen_type', 'Не указано')}\n"
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"
            summary += f"• Материал: {user_data.get('material', 'Не указано')}\n"
            summary += f"• Фурнитура: {user_data.get('hardware', 'Не указано')}\n"
        elif category == 'шкаф':
            summary += f"• Тип шкафа: {user_data.get('cabinet_type', 'Не указано')}\n"
        elif category == 'гардеробная':
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"

        summary += f"• Бюджет: {user_data.get('budget', 'Не указано')}\n"
        summary += f"• Сроки: {user_data.get('deadline', 'Не указано')}\n"
        summary += f"• Имя: {user_data.get('name', 'Не указано')}\n"
        summary += f"• Телефон: {user_data.get('phone', 'Не указано')}\n\n"

        summary += "📞 Свяжитесь с нами:\n"
        summary += "💬 Телеграм: @max_lap555\n"
        summary += "📱 WhatsApp: +79063405556\n\n"
        summary += "Спасибо за вашу заявку! Мы свяжемся с вами в ближайшее время."

        await self.send_message(
            platform, user_id, summary,
            KeyboardManager.get_contact_final_keyboard(platform)
        )

        # Очищаем данные пользователя после отправки сводки
        self.clear_user_data(user_id)


# Адаптер для Telegram
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
        await self.bot_core.handle_callback(
            Platform.TELEGRAM,
            update.effective_user.id,
            query.data,
            query.message.message_id
        )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.bot_core.handle_text_message(
            Platform.TELEGRAM,
            update.effective_user.id,
            update.message.text
        )

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = self.bot_core.get_user_data(user_id)

        if user_data.get('waiting_for') == 'phone':
            phone_number = update.message.contact.phone_number
            user_data['phone'] = phone_number
            user_data['waiting_for'] = None
            await self.bot_core.send_final_summary(Platform.TELEGRAM, user_id)

    async def send_message(self, user_id: int, text: str, keyboard=None):
        # Убираем parse_mode чтобы избежать ошибок с Markdown
        await self.application.bot.send_message(
            chat_id=user_id, text=text, reply_markup=keyboard
        )

    async def edit_message(self, user_id: int, message_id: int, text: str, keyboard=None):
        await self.application.bot.edit_message_text(
            chat_id=user_id, message_id=message_id, text=text, reply_markup=keyboard
        )

    def run(self):
        logger.info("Запуск Telegram бота...")
        self.application.run_polling()


# Адаптер для VK
class VKAdapter:
    def __init__(self, token: str, group_id: str, bot_core: FurnitureBotCore):
        self.bot_core = bot_core
        self.vk_session = vk_api.VkApi(token=token)
        self.vk = self.vk_session.get_api()
        self.group_id = group_id

    def run(self):
        logger.info("Запуск VK бота через Long Poll...")
        try:
            longpoll = VkBotLongPoll(self.vk_session, self.group_id)
            logger.info("✓ Long Poll подключен успешно!")

            logger.info("VK бот готов! Напишите любое сообщение в группу")

            for event in longpoll.listen():
                logger.info(f"VK: Получено событие типа: {event.type}")

                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.handle_message(event)
                elif event.type == VkBotEventType.MESSAGE_EVENT:
                    self.handle_callback(event)
                else:
                    logger.info(f"VK: Необработанный тип события: {event.type}")

        except Exception as e:
            logger.error(f"Ошибка VK бота: {e}")
            import traceback
            logger.error(f"Детали: {traceback.format_exc()}")

    def handle_message(self, event):
        """Обработка текстовых сообщений"""
        try:
            user_id = event.obj.message['from_id']
            text = event.obj.message['text']

            logger.info(f"VK: Сообщение от {user_id}: '{text}'")

            # Запускаем обработку в отдельном потоке
            threading.Thread(
                target=lambda: asyncio.run(
                    self.process_message(user_id, text)
                )
            ).start()

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")

    def handle_callback(self, event):
        """Обработка нажатий на кнопки"""
        try:
            logger.info(f"VK: Callback событие получено!")
            logger.info(f"VK: Event object: {event.obj}")

            user_id = event.obj.user_id
            payload = event.obj.payload

            logger.info(f"VK: Callback от пользователя {user_id}")
            logger.info(f"VK: Payload: {payload}")

            # Извлекаем команду из payload
            if isinstance(payload, dict):
                command = payload.get('command', '')
            elif isinstance(payload, str):
                # Пытаемся распарсить JSON строку
                try:
                    payload_dict = json.loads(payload)
                    command = payload_dict.get('command', '')
                except:
                    command = payload
            else:
                command = str(payload)

            logger.info(f"VK: Извлеченная команда: '{command}'")

            # Отправляем ответ на callback (ВАЖНО!) - используем глобальный json
            self.vk.messages.sendMessageEventAnswer(
                event_id=event.obj.event_id,
                user_id=user_id,
                peer_id=event.obj.peer_id,
                event_data=json.dumps({"type": "show_snackbar", "text": "Обрабатываю..."})
            )

            logger.info("VK: Ответ на callback отправлен")

            # Запускаем обработку команды
            threading.Thread(
                target=lambda: asyncio.run(
                    self.process_callback(user_id, command)
                )
            ).start()

        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            import traceback
            logger.error(f"Детали: {traceback.format_exc()}")

    async def process_message(self, user_id: int, text: str):
        """Обработка текстового сообщения"""
        try:
            normalized_text = text.lower().strip()

            if normalized_text in ['/start', 'start', 'начать', 'меню']:
                await self.bot_core.handle_start(Platform.VK, user_id)
            else:
                await self.bot_core.handle_text_message(Platform.VK, user_id, text)

        except Exception as e:
            logger.error(f"Ошибка process_message: {e}")

    async def process_callback(self, user_id: int, command: str):
        """Обработка callback команды"""
        try:
            logger.info(f"VK: Обработка callback команды: '{command}'")
            # Передаем только 3 аргумента, message_id не нужен для VK
            await self.bot_core.handle_callback(Platform.VK, user_id, command)
        except Exception as e:
            logger.error(f"Ошибка process_callback: {e}")
            import traceback
            logger.error(f"Детали: {traceback.format_exc()}")

    async def send_message(self, user_id: int, text: str, keyboard=None):
        """Отправка сообщения с улучшенным логированием"""
        try:
            logger.info(f"VK: Отправка сообщения пользователю {user_id}")
            logger.info(f"VK: Текст: {text}")

            params = {
                'user_id': user_id,
                'message': text,
                'random_id': get_random_id(),
                'dont_parse_links': 1
            }

            if keyboard:
                logger.info("VK: Добавляю клавиатуру")
                params['keyboard'] = keyboard

                # Логируем клавиатуру для отладки
                try:
                    if isinstance(keyboard, str):
                        keyboard_obj = json.loads(keyboard)
                    else:
                        keyboard_obj = keyboard
                    logger.info(
                        f"VK: Кнопки: {[btn['action']['label'] for row in keyboard_obj['buttons'] for btn in row]}")
                except Exception as e:
                    logger.error(f"VK: Ошибка логирования клавиатуры: {e}")

            result = self.vk.messages.send(**params)
            logger.info(f"VK: Сообщение отправлено! ID: {result}")
            return result

        except Exception as e:
            logger.error(f"VK: Ошибка отправки: {e}")
            import traceback
            logger.error(f"VK: Детали: {traceback.format_exc()}")

    async def edit_message(self, user_id: int, message_id: int, text: str, keyboard=None):
        """В VK через Long Poll нельзя редактировать, отправляем новое"""
        await self.send_message(user_id, text, keyboard)


# Главная функция
def main():
    logger.info("Запуск мультиплатформенного бота...")

    bot_core = FurnitureBotCore()

    # Инициализация адаптеров
    telegram_adapter = TelegramAdapter(TELEGRAM_TOKEN, bot_core)
    vk_adapter = VKAdapter(VK_TOKEN, VK_GROUP_ID, bot_core)

    bot_core.register_adapter(Platform.TELEGRAM, telegram_adapter)
    bot_core.register_adapter(Platform.VK, vk_adapter)

    # Запускаем VK в отдельном потоке
    def run_vk():
        vk_adapter.run()

    vk_thread = threading.Thread(target=run_vk, daemon=True)
    vk_thread.start()

    logger.info("VK: работает")
    logger.info("Telegram: запускается в главном потоке")

    # Запуск Telegram в главном потоке
    telegram_adapter.run()

    logger.info("Оба бота запущены! Нажми Ctrl+C для остановки")


    try:
        # Держим основной поток активным
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nОстановка ботов...")


if __name__ == '__main__':
    main()
