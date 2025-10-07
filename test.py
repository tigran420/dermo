
import asyncio
import json
import logging
import threading
import time
from enum import Enum
from typing import Dict, Any

# VK imports
import vk_api  # type: ignore
# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    InputMediaPhoto  # type: ignore
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, \
    filters  # type: ignore
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType  # type: ignore
import requests  # type: ignore

TELEGRAM_TOKEN = "7912680613:AAH_7SLbjywJk2fqLIes9JTfrv940kHGnCE"
VK_TOKEN = "vk1.a.Zpg9wzHaNYM4K0-F3KvYs2ValUpkHXkkU0ClznSTRt_9C5Lbvi36nYiaPz41e7eVyndY0fSbvYDPfZbvp1P_VYC4PlrBrnfGQ1IAJdb4aJhZMB8odobM4BZQgOqfZUybdJR-g_FWg2tLJBkpq4YKchVevXgcU90-9SZxqVmufumLmnZB-RNe3eoiifZNRPqba_cUa76fk-3d0fy1zj3daA"
VK_GROUP_ID = "233147090"
# URL изображений
WELCOME_PHOTOS = [
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(2).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(3).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(4).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(5).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(6).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58%20(7).jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-58.jpg",
    "https://raw.githubusercontent.com/tigran420/dermo/5be79081c7a6fa620a49671bf22703d98c6d9020/photo_2025-10-05_16-08-59.jpg",
    # user provided 9th maybe duplicate; keep it if exists
]
MATERIAL_PHOTOS = {
    "лдсп": "https://raw.githubusercontent.com/tigran420/dermo/refs/heads/main/photo_2025-10-06_15-58-59%20(2).jpg",
    "агт": "https://raw.githubusercontent.com/tigran420/dermo/refs/heads/main/photo_2025-10-06_15-58-59.jpg",
    "эмаль": "https://raw.githubusercontent.com/tigran420/dermo/refs/heads/main/photo_2025-10-06_15-58-59%20(3).jpg"
}


# В функции send_telegram_application используйте TELEGRAM_TOKEN вместо TELEGRAM_BOT_TOKEN
def send_telegram_application(application_data):
    if not TELEGRAM_TOKEN:
        logging.warning("Telegram bot token or chat ID not configured. Skipping sending application to Telegram group.")
        return

    message_text = "Новая заявка:\n\n"
    for key, value in application_data.items():
        message_text += f"{key}: {value}\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "text": message_text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Application successfully sent to Telegram group: {response.json()}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send application to Telegram group: {e}")


from vk_api.utils import get_random_id  # type: ignore

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Platform(Enum):
    TELEGRAM = "telegram"
    VK = "vk"


# Приветственное сообщение
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

# Хранилище данных пользователя
user_data = {}


# Класс для управления клавиатурами
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
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🍳 Кухня",
                                "payload": "{\"command\": \"кухня\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🚪 Шкаф",
                                "payload": "{\"command\": \"шкаф\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "👔 Гардеробная",
                                "payload": "{\"command\": \"гардеробная\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🛋 Прихожая",
                                "payload": "{\"command\": \"прихожая\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🛁 Мебель для ванной",
                                "payload": "{\"command\": \"ванная\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🛋 Другая мебель",
                                "payload": "{\"command\": \"другое\"}"
                            },
                            "color": "secondary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📞 Свяжитесь со мной",
                                "payload": "{\"command\": \"связаться_со_мной\"}"
                            },
                            "color": "positive"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_categories_keyboard(platform: Platform):
        # This method is now redundant, get_initial_keyboard will be used for categories
        return KeyboardManager.get_initial_keyboard(platform)

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
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📞 Консультация",
                                "payload": "{\"command\": \"консультация\"}"
                            },
                            "color": "positive"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "💬 Написать в ТГ",
                                "payload": "{\"command\": \"написать_тг\"}"
                            },
                            "color": "primary"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_contact_final_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [KeyboardButton(""), KeyboardButton("")],
                [KeyboardButton("🔄 Начать заново"), ]
            ]
            return ReplyKeyboardMarkup(keyboard, resize_keyboard=True,
                                       input_field_placeholder="Выберите способ связи...")
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📞 По телефону",
                                "payload": "{\"command\": \"по_телефону\"}"
                            },
                            "color": "positive"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "💬 Сообщение в Telegram",
                                "payload": "{\"command\": \"сообщение_тг\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔄 Начать заново",
                                "payload": "{\"command\": \"начать_заново\"}"
                            },
                            "color": "secondary"
                        }
                    ]
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
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📐 Угловая",
                                "payload": "{\"command\": \"кухня_угловая\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "📏 Прямая",
                                "payload": "{\"command\": \"кухня_прямая\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔄 П-образная",
                                "payload": "{\"command\": \"кухня_п_образная\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🏝 С островом",
                                "payload": "{\"command\": \"кухня_остров\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": "{\"command\": \"назад_категории\"}"
                            },
                            "color": "negative"
                        }
                    ]
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
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🚪 Распашной",
                                "payload": "{\"command\": \"шкаф_распашной\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🚶 Купе",
                                "payload": "{\"command\": \"шкаф_купе\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": "{\"command\": \"назад_категории\"}"
                            },
                            "color": "negative"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_hallway_type_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Прямая", callback_data="прихожая_прямая")],
                [InlineKeyboardButton("Угловая", callback_data="прихожая_угловая")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📏 Прямая",
                                "payload": "{\"command\": \"прихожая_прямая\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "📐 Угловая",
                                "payload": "{\"command\": \"прихожая_угловая\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": "{\"command\": \"назад_категории\"}"
                            },
                            "color": "negative"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_bathroom_type_keyboard(platform: Platform):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Тумба под раковину", callback_data="ванная_тумба")],
                [InlineKeyboardButton("Шкаф-пенал", callback_data="ванная_пенал")],
                [InlineKeyboardButton("Зеркало с подсветкой", callback_data="ванная_зеркало")],
                [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🚰 Тумба под раковину",
                                "payload": "{\"command\": \"ванная_тумба\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🧺 Шкаф-пенал",
                                "payload": "{\"command\": \"ванная_пенал\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "💡 Зеркало с подсветкой",
                                "payload": "{\"command\": \"ванная_зеркало\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": "{\"command\": \"назад_категории\"}"
                            },
                            "color": "negative"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_size_keyboard(platform: Platform, back_callback: str = "назад_тип"):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Точные", callback_data="размер_точные")],
                [InlineKeyboardButton("Приблизительные", callback_data="размер_приблизительные")],
                [InlineKeyboardButton("Не знаю", callback_data="размер_не_знаю")],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📏 Точные размеры",
                                "payload": "{\"command\": \"размер_точные\"}"
                            },
                            "color": "positive"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "📐 Приблизительные",
                                "payload": "{\"command\": \"размер_приблизительные\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "❓ Не знаю",
                                "payload": "{\"command\": \"размер_не_знаю\"}"
                            },
                            "color": "secondary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": f"{{\"command\": \"{back_callback}\"}}"
                            },
                            "color": "negative"
                        }
                    ]
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
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🌳 ЛДСП",
                                "payload": "{\"command\": \"материал_лдсп\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "✨ АГТ",
                                "payload": "{\"command\": \"материал_агт\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🎨 Эмаль",
                                "payload": "{\"command\": \"материал_эмаль\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": "{\"command\": \"назад_размер\"}"
                            },
                            "color": "negative"
                        }
                    ]
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
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "💰 Эконом",
                                "payload": "{\"command\": \"фурнитура_эконом\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "💎 Стандарт",
                                "payload": "{\"command\": \"фурнитура_стандарт\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "👑 Премиум",
                                "payload": "{\"command\": \"фурнитура_премиум\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": "{\"command\": \"назад_материал\"}"
                            },
                            "color": "negative"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_budget_keyboard(platform: Platform, back_callback: str = "назад_предыдущий"):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Эконом - (до 150 тыс руб)", callback_data="бюджет_эконом")],
                [InlineKeyboardButton("Стандарт - (150-300 тыс руб)", callback_data="бюджет_стандарт")],
                [InlineKeyboardButton("Премиум - (от 300 тыс руб)", callback_data="бюджет_премиум")],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "💰 Эконом - (до 150 тыс руб)",
                                "payload": "{\"command\": \"бюджет_эконом\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "💎 Стандарт - (150-300 тыс руб)",
                                "payload": "{\"command\": \"бюджет_стандарт\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "👑 Премиум - (от 300 тыс руб)",
                                "payload": "{\"command\": \"бюджет_премиум\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": f"{{\"command\": \"{back_callback}\"}}"
                            },
                            "color": "negative"
                        }
                    ]
                ]
            }
            return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def get_deadline_keyboard(platform: Platform, back_callback: str = "назад_бюджет"):
        if platform == Platform.TELEGRAM:
            keyboard = [
                [InlineKeyboardButton("Этот месяц", callback_data="срок_месяц")],
                [InlineKeyboardButton("1-2 месяца", callback_data="срок_1_2")],
                [InlineKeyboardButton("3 месяца", callback_data="срок_3")],
                [InlineKeyboardButton("Присматриваюсь", callback_data="срок_присмотр")],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
            ]
            return InlineKeyboardMarkup(keyboard)
        else:  # VK
            keyboard = {
                "inline": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🗓 Этот месяц",
                                "payload": "{\"command\": \"срок_месяц\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "⏳ 1-2 месяца",
                                "payload": "{\"command\": \"срок_1_2\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "📅 3 месяца",
                                "payload": "{\"command\": \"срок_3\"}"
                            },
                            "color": "primary"
                        },
                        {
                            "action": {
                                "type": "callback",
                                "label": "👀 Присматриваюсь",
                                "payload": "{\"command\": \"срок_присмотр\"}"
                            },
                            "color": "primary"
                        }
                    ],
                    [
                        {
                            "action": {
                                "type": "callback",
                                "label": "🔙 Назад",
                                "payload": f"{{\"command\": \"{back_callback}\"}}"
                            },
                            "color": "negative"
                        }
                    ]
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

        await self.send_photo_album(
            platform, user_id,
            WELCOME_PHOTOS,
            WELCOME_MESSAGE,
            KeyboardManager.get_initial_keyboard(platform)
        )

    async def request_name(self, platform: Platform, user_id: int, message_id: int = None):
        text = "👤 **Контактные данные**\n\nПожалуйста, напишите ваше имя:"
        if message_id and platform == Platform.TELEGRAM:
            await self.edit_message(platform, user_id, message_id, text)
        else:
            await self.send_message(platform, user_id, text)
        self.get_user_data(user_id)["waiting_for"] = "name"

    async def handle_callback(self, platform: Platform, user_id: int, data: str, message_id: int = None):
        user_data = self.get_user_data(user_id)

        # Обработка кнопки "Назад"
        if data.startswith("назад_"):
            await self.handle_back_button(platform, user_id, data, message_id)
            return

        # Обработка кнопки "Свяжитесь со мной"
        if data == "связаться_со_мной":
            user_data["category"] = "связаться_со_мной"
            await self.request_name(platform, user_id, message_id)
            return

        # Обработка выбора категории
        if data == "кухня":
            user_data["category"] = "кухня"
            user_data["current_step"] = "kitchen_type"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🏠 **Кухня**\n\nВыберите тип кухни:",
                KeyboardManager.get_kitchen_type_keyboard(platform)
            )

        elif data == "шкаф":
            user_data["category"] = "шкаф"
            user_data["current_step"] = "cabinet_type"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                KeyboardManager.get_cabinet_type_keyboard(platform)
            )

        elif data == "гардеробная":
            user_data["category"] = "гардеробная"
            user_data["current_step"] = "size"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "👔 **Гардеробная**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform, back_callback="назад_категории")
            )

        elif data == "прихожая":
            user_data["category"] = "прихожая"
            user_data["current_step"] = "hallway_type"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🛋 **Прихожая**\n\nВыберите тип прихожей:",
                KeyboardManager.get_hallway_type_keyboard(platform)
            )

        elif data == "ванная":
            user_data["category"] = "ванная"
            user_data["current_step"] = "bathroom_type"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🛁 **Мебель для ванной**\n\nВыберите тип мебели для ванной:",
                KeyboardManager.get_bathroom_type_keyboard(platform)
            )

        elif data == "другое":
            user_data["category"] = "другое"
            user_data["current_step"] = "other_furniture_text"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🛋 **Другая мебель**\n\nПожалуйста, опишите, какая мебель вас интересует:"
            )
            user_data["waiting_for"] = "other_furniture_description"

        # Обработка сценария КУХНЯ
        elif data.startswith("кухня_"):
            if data == "кухня_угловая":
                user_data["kitchen_type"] = "Угловая"
            elif data == "кухня_прямая":
                user_data["kitchen_type"] = "Прямая"
            elif data == "кухня_п_образная":
                user_data["kitchen_type"] = "П-образная"
            elif data == "кухня_остров":
                user_data["kitchen_type"] = "С островом"

            user_data["current_step"] = "size"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📏 **Размеры**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform, back_callback="назад_тип")
            )

        # Обработка сценария ПРИХОЖАЯ
        elif data.startswith("прихожая_"):
            if data == "прихожая_прямая":
                user_data["hallway_type"] = "Прямая"
            elif data == "прихожая_угловая":
                user_data["hallway_type"] = "Угловая"

            user_data["current_step"] = "size"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📏 **Размеры**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform, back_callback="назад_тип")
            )

        # Обработка сценария ВАННАЯ
        elif data.startswith("ванная_"):
            if data == "ванная_тумба":
                user_data["bathroom_type"] = "Тумба под раковину"
            elif data == "ванная_пенал":
                user_data["bathroom_type"] = "Шкаф-пенал"
            elif data == "ванная_зеркало":
                user_data["bathroom_type"] = "Зеркало с подсветкой"

            user_data["current_step"] = "size"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📏 **Размеры**\n\nКакие у вас размеры?",
                KeyboardManager.get_size_keyboard(platform, back_callback="назад_тип")
            )

        # Обработка размеров (общее для Кухни, Гардеробной, Прихожей, Ванной)
        elif data.startswith("размер_"):
            if data == "размер_точные":
                user_data["size"] = "Точные"
            elif data == "размер_приблизительные":
                user_data["size"] = "Приблизительные"
            elif data == "размер_не_знаю":
                user_data["size"] = "Не знаю"

            # Определяем следующий шаг в зависимости от категории
            category = user_data.get("category", "")

            if category == "кухня":
                user_data["current_step"] = "material"
                await self.send_material_options(platform, user_id, message_id)
            elif category in ["гардеробная", "прихожая", "ванная", "шкаф", "другое"]:
                user_data["current_step"] = "budget"
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "💰 **Бюджет**\n\nВыберите бюджет:",
                    KeyboardManager.get_budget_keyboard(platform, back_callback="назад_размер")
                )

        elif data.startswith("материал_"):
            if data == "материал_лдсп":
                user_data["material"] = "ЛДСП"
            elif data == "материал_агт":
                user_data["material"] = "АГТ"
            elif data == "материал_эмаль":
                user_data["material"] = "Эмаль"

            # Отправляем фото выбранного материала
            material_key = data.replace("материал_", "")
            photo_url = MATERIAL_PHOTOS.get(material_key)
            if photo_url:
                await self.send_photo_album(platform, user_id, [photo_url], f"📸 Материал: {user_data['material']}")

            user_data["current_step"] = "hardware"
            await self.send_message(
                platform, user_id,
                "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
                KeyboardManager.get_hardware_keyboard(platform)
            )

        elif data.startswith("фурнитура_"):
            if data == "фурнитура_эконом":
                user_data["hardware"] = "Эконом"
            elif data == "фурнитура_стандарт":
                user_data["hardware"] = "Стандарт"
            elif data == "фурнитура_премиум":
                user_data["hardware"] = "Премиум"

            user_data["current_step"] = "budget"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💰 **Бюджет**\n\nВыберите бюджет:",
                KeyboardManager.get_budget_keyboard(platform, back_callback="назад_фурнитура")
            )

        elif data.startswith("бюджет_"):
            if data == "бюджет_эконом":
                user_data["budget"] = "Эконом"
            elif data == "бюджет_стандарт":
                user_data["budget"] = "Стандарт"
            elif data == "бюджет_премиум":
                user_data["budget"] = "Премиум"

            user_data["current_step"] = "deadline"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📅 **Сроки заказа**\n\nВыберите сроки:",
                KeyboardManager.get_deadline_keyboard(platform, back_callback="назад_бюджет")
            )

        # Обработка сценария ШКАФ
        elif data.startswith("шкаф_"):
            if data == "шкаф_распашной":
                user_data["cabinet_type"] = "Распашной"
            elif data == "шкаф_купе":
                user_data["cabinet_type"] = "Купе"

            user_data["current_step"] = "budget"
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "💰 **Бюджет**\n\nВыберите бюджет:",
                KeyboardManager.get_budget_keyboard(platform, back_callback="назад_тип")
            )

        # Обработка сроков заказа (переходим к запросу контактных данных)
        elif data.startswith("срок_"):
            if data == "срок_месяц":
                user_data["deadline"] = "Этот месяц"
            elif data == "срок_1_2":
                user_data["deadline"] = "1-2 месяца"
            elif data == "срок_3":
                user_data["deadline"] = "3 месяца"
            elif data == "срок_присмотр":
                user_data["deadline"] = "Присматриваюсь"

            # Запрашиваем имя
            await self.request_name(platform, user_id, message_id)

        # Обработка дополнительных кнопок для VK
        elif data == "ввести_телефон":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "📱 **Введите номер телефона:**\n\nФормат: +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
            user_data["waiting_for"] = "phone"

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

    async def send_material_options(self, platform: Platform, user_id: int, message_id: int = None):
        """Отправка фото материалов и клавиатуры выбора материалов"""
        # Сначала отправляем сообщение с клавиатурой
        await self.send_or_edit_message(
            platform, user_id, message_id,
            "🎨 **Материал фасадов**\n\nВыберите материал:",
            KeyboardManager.get_material_keyboard(platform)
        )

        # Затем отправляем все фото материалов отдельными сообщениями
        for material_name, photo_url in MATERIAL_PHOTOS.items():
            material_display_name = material_name.upper()
            await self.send_photo_album(
                platform, user_id,
                [photo_url],
                f"📸 Материал: {material_display_name}"
            )

    async def send_or_edit_message(self, platform: Platform, user_id: int, message_id: int, text: str, keyboard=None):
        if message_id and platform == Platform.TELEGRAM:  # Only edit message for Telegram
            await self.edit_message(platform, user_id, message_id, text, keyboard)
        else:
            await self.send_message(platform, user_id, text, keyboard)

    async def send_photo_album(self, platform: Platform, user_id: int, photo_urls: list, text: str, keyboard=None):
        """Отправка альбома фото с текстом одним сообщением"""
        if platform in self.adapters:
            await self.adapters[platform].send_photo_album(user_id, photo_urls, text, keyboard)

    async def handle_back_button(self, platform: Platform, user_id: int, data: str, message_id: int = None):
        back_step = data.replace("назад_", "")
        user_data = self.get_user_data(user_id)

        if back_step == "категории":
            self.clear_user_data(user_id)
            await self.send_or_edit_message(
                platform, user_id, message_id,
                WELCOME_MESSAGE,
                KeyboardManager.get_initial_keyboard(platform)
            )

        elif back_step == "тип":  # For kitchen, wardrobe, hallway, bathroom
            category = user_data.get("category", "")
            if category == "кухня":
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🏠 **Кухня**\n\nВыберите тип кухни:",
                    KeyboardManager.get_kitchen_type_keyboard(platform)
                )
            elif category == "шкаф":
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                    KeyboardManager.get_cabinet_type_keyboard(platform)
                )
            elif category == "прихожая":
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🛋 **Прихожая**\n\nВыберите тип прихожей:",
                    KeyboardManager.get_hallway_type_keyboard(platform)
                )
            elif category == "ванная":
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🛁 **Мебель для ванной**\n\nВыберите тип мебели для ванной:",
                    KeyboardManager.get_bathroom_type_keyboard(platform)
                )

        elif back_step == "размер":
            category = user_data.get("category", "")
            if category == "кухня":
                user_data["current_step"] = "kitchen_type"
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🏠 **Кухня**\n\nВыберите тип кухни:",
                    KeyboardManager.get_kitchen_type_keyboard(platform)
                )
            elif category == "гардеробная":
                user_data["current_step"] = "size"
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "👔 **Гардеробная**\n\nКакие у вас размеры?",
                    KeyboardManager.get_size_keyboard(platform, back_callback="назад_категории")
                )
            elif category == "прихожая":
                user_data["current_step"] = "hallway_type"
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🛋 **Прихожая**\n\nВыберите тип прихожей:",
                    KeyboardManager.get_hallway_type_keyboard(platform)
                )
            elif category == "ванная":
                user_data["current_step"] = "bathroom_type"
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🛁 **Мебель для ванной**\n\nВыберите тип мебели для ванной:",
                    KeyboardManager.get_bathroom_type_keyboard(platform)
                )
            elif category == "шкаф":
                user_data["current_step"] = "cabinet_type"
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                    KeyboardManager.get_cabinet_type_keyboard(platform)
                )

        elif back_step == "материал":
            await self.send_material_options(platform, user_id, message_id)

        elif back_step == "фурнитура":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
                KeyboardManager.get_hardware_keyboard(platform)
            )

        elif back_step == "бюджет":
            category = user_data.get("category", "")
            if category == "кухня":
                await self.send_or_edit_message(
                    platform, user_id, message_id,
                    "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
                    KeyboardManager.get_hardware_keyboard(platform)
                )
            elif category in ["шкаф", "гардеробная", "прихожая", "ванная", "другое"]:
                if category == "шкаф":
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                        KeyboardManager.get_cabinet_type_keyboard(platform)
                    )
                elif category == "гардеробная":
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "👔 **Гардеробная**\n\nКакие у вас размеры?",
                        KeyboardManager.get_size_keyboard(platform, back_callback="назад_категории")
                    )
                elif category == "прихожая":
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "🛋 **Прихожая**\n\nВыберите тип прихожей:",
                        KeyboardManager.get_hallway_type_keyboard(platform)
                    )
                elif category == "ванная":
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "🛁 **Мебель для ванной**\n\nВыберите тип мебели для ванной:",
                        KeyboardManager.get_bathroom_type_keyboard(platform)
                    )
                elif category == "другое":
                    await self.send_or_edit_message(
                        platform, user_id, message_id,
                        "🛋 **Другая мебель**\n\nПожалуйста, опишите, какая мебель вас интересует:"
                    )
                    user_data["waiting_for"] = "other_furniture_description"

        elif back_step == "другое":
            await self.send_or_edit_message(
                platform, user_id, message_id,
                WELCOME_MESSAGE,
                KeyboardManager.get_initial_keyboard(platform)
            )

    async def handle_text_message(self, platform: Platform, user_id: int, text: str):
        user_data = self.get_user_data(user_id)

        # Нормализуем текст команды
        normalized_text = text.lower().strip()

        # Команды для запуска бота
        start_commands = ["/start", "start", "начать", "старт", "go", "меню"]

        if normalized_text in start_commands:
            await self.handle_start(platform, user_id)
            return

        # Если ожидаем имя
        if user_data.get("waiting_for") == "name":
            user_data["name"] = text
            user_data["waiting_for"] = "phone"

            await self.send_message(
                platform, user_id,
                f"👤 **Имя принято:** {text}\n\n"
                "📱 **Телефон**\n\nПожалуйста, отправьте ваш номер телефона:",
                KeyboardManager.get_phone_keyboard(platform)
            )
            return

        # Если ожидаем телефон
        if user_data.get("waiting_for") == "phone":
            # Простая валидация номера телефона
            if len(text) >= 10 and all(char.isdigit() or char in ["+", "(", ")", "-", " "] for char in text):
                user_data["phone"] = text
                user_data["waiting_for"] = None
                await self.send_final_summary(platform, user_id)
            else:
                await self.send_message(
                    platform, user_id,
                    "❌ Некорректный формат номера. Пожалуйста, введите номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX:"
                )
            return

        # Если ожидаем описание другой мебели
        if user_data.get("waiting_for") == "other_furniture_description":
            user_data["other_furniture_description"] = text
            user_data["waiting_for"] = None
            user_data["current_step"] = "budget"
            await self.send_or_edit_message(
                platform, user_id, None,
                "💰 **Бюджет**\n\nВыберите бюджет:",
                KeyboardManager.get_budget_keyboard(platform, back_callback="назад_другое")
            )
            return

        # Если сообщение не является командой и не ожидается ввод
        await self.send_message(
            platform, user_id,
            "Извините, я не понял ваше сообщение. Пожалуйста, используйте кнопки или начните заново /start.",
            KeyboardManager.get_initial_keyboard(platform)  # Возвращаем к начальной клавиатуре
        )

    async def send_final_summary(self, platform: Platform, user_id: int):
        user_data = self.get_user_data(user_id)
        summary = "✅ **Ваша заявка принята!**\n\n"

        category = user_data.get("category", "Не указано")

        if category == "связаться_со_мной":
            summary += "Мы свяжемся с вами в ближайшее время.\n\n"
        else:
            summary += f"**Детали заказа {category.capitalize()}:**\n"

        if category == "кухня":
            summary += f"• Тип кухни: {user_data.get('kitchen_type', 'Не указано')}\n"
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"
            summary += f"• Материал: {user_data.get('material', 'Не указано')}\n"
            summary += f"• Фурнитура: {user_data.get('hardware', 'Не указано')}\n"
        elif category == "шкаф":
            summary += f"• Тип шкафа: {user_data.get('cabinet_type', 'Не указано')}\n"
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"
        elif category == "гардеробная":
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"
        elif category == "прихожая":
            summary += f"• Тип прихожей: {user_data.get('hallway_type', 'Не указано')}\n"
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"
        elif category == "ванная":
            summary += f"• Тип мебели для ванной: {user_data.get('bathroom_type', 'Не указано')}\n"
            summary += f"• Размеры: {user_data.get('size', 'Не указано')}\n"
        elif category == "другое":
            summary += f"• Описание мебели: {user_data.get('other_furniture_description', 'Не указано')}\n"

        if category != "связаться_со_мной":
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

        # Отправляем заявку в Telegram группу
        send_telegram_application(user_data)

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

    async def send_photo_album(self, user_id: int, photo_urls: list, text: str, keyboard=None):
        try:
            # Создаем медиагруппу (максимум 10 фото в одном сообщении)
            media_group = []

            for i, photo_url in enumerate(photo_urls[:10]):  # Ограничение Telegram
                if i == 0:
                    # Первое фото с подписью (текстом)
                    media_group.append(InputMediaPhoto(
                        media=photo_url,
                        caption=text,
                        parse_mode=None
                    ))
                else:
                    # Остальные фото без подписи
                    media_group.append(InputMediaPhoto(
                        media=photo_url
                    ))

            # Отправляем альбом
            await self.application.bot.send_media_group(
                chat_id=user_id,
                media=media_group
            )

            # Отправляем клавиатуру отдельным сообщением
            if keyboard:
                await self.send_message(user_id, "Выберите категорию:", keyboard)

        except Exception as e:
            logger.error(f"Ошибка отправки фотоальбома в Telegram: {e}")
            # Fallback - отправляем текстовое сообщение
            await self.send_message(user_id, text, keyboard)

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = self.bot_core.get_user_data(user_id)

        if user_data.get("waiting_for") == "phone":
            phone_number = update.message.contact.phone_number
            user_data["phone"] = phone_number
            user_data["waiting_for"] = None
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
            user_id = event.obj.message["from_id"]
            text = event.obj.message["text"]

            logger.info(f"VK: Сообщение от {user_id}: \'{text}\'")

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
                command = payload.get("command", "")
            elif isinstance(payload, str):
                # Пытаемся распарсить JSON строку
                try:
                    payload_dict = json.loads(payload)
                    command = payload_dict.get("command", "")
                except:
                    command = payload
            else:
                command = str(payload)

            logger.info(f"VK: Извлеченная команда: \'{command}\'")

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

            if normalized_text in ["/start", "start", "начать", "меню"]:
                await self.bot_core.handle_start(Platform.VK, user_id)
            else:
                await self.bot_core.handle_text_message(Platform.VK, user_id, text)

        except Exception as e:
            logger.error(f"Ошибка process_message: {e}")

    async def send_photo_album(self, user_id: int, photo_urls: list, text: str, keyboard=None):
        try:
            attachments = []

            # Загружаем все фото (VK ограничение - 10 вложений)
            for photo_url in photo_urls[:10]:
                attachment = await self.upload_photo(photo_url)
                if attachment:
                    attachments.append(attachment)

            params = {
                "user_id": user_id,
                "message": text,
                "random_id": get_random_id(),
                "dont_parse_links": 1
            }

            if attachments:
                params["attachment"] = ",".join(attachments)
                logger.info(f"VK: Добавлены {len(attachments)} фото в альбом")

            if keyboard:
                params["keyboard"] = keyboard

            result = self.vk.messages.send(**params)
            logger.info(f"VK: Фотоальбом отправлен одним сообщением! ID: {result}")
            return result

        except Exception as e:
            logger.error(f"VK: Ошибка отправки фотоальбома: {e}")
            await self.send_message(user_id, text, keyboard)

    async def upload_photo(self, photo_url: str):
        """Загружает фото по URL и возвращает attachment строку для VK"""
        try:
            logger.info(f"VK: Загрузка фото из URL: {photo_url}")

            # Скачиваем фото
            response = requests.get(photo_url, timeout=10)
            response.raise_for_status()

            # Получаем URL для загрузки
            upload_url = self.vk.photos.getMessagesUploadServer()['upload_url']

            # Загружаем фото на сервер VK
            files = {'photo': ('photo.jpg', response.content, 'image/jpeg')}
            upload_response = requests.post(upload_url, files=files, timeout=10)
            upload_response.raise_for_status()
            upload_data = upload_response.json()

            # Сохраняем фото
            save_response = self.vk.photos.saveMessagesPhoto(
                server=upload_data['server'],
                photo=upload_data['photo'],
                hash=upload_data['hash']
            )

            if save_response:
                photo = save_response[0]
                attachment = f"photo{photo['owner_id']}_{photo['id']}"
                logger.info(f"VK: Фото успешно загружено: {attachment}")
                return attachment
            else:
                logger.error("VK: Ошибка сохранения фото")
                return None

        except Exception as e:
            logger.error(f"VK: Ошибка загрузки фото: {e}")
            return None

    async def process_callback(self, user_id: int, command: str):
        """Обработка callback команды"""
        try:
            logger.info(f"VK: Обработка callback команды: \'{command}\'")
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
                "user_id": user_id,
                "message": text,
                "random_id": get_random_id(),
                "dont_parse_links": 1
            }

            if keyboard:
                logger.info("VK: Добавляю клавиатуру")
                params["keyboard"] = keyboard

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
