from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Токен вашего бота от BotFather
TOKEN = "8406823713:AAHlcszbNdT2-DrxFMa4EC5CCBAAcY-FIFM"

# Приветственное сообщение
WELCOME_MESSAGE = """
Приветствую вас!
Наша компания занимается производством качественной мебели уже более 10 лет.
Мы предлагаем широкий ассортимент продукции для любого интерьера.
Выберите категорию интересующей вас мебели:
"""


# Создание инлайн-клавиатуры с категориями мебели
def get_categories_keyboard():
    keyboard = [
        [InlineKeyboardButton("Кухня", callback_data="кухня")],
        [InlineKeyboardButton("Шкаф", callback_data="шкаф")],
        [InlineKeyboardButton("Гардеробная", callback_data="гардеробная")],
        [InlineKeyboardButton("Другая мебель", callback_data="другое")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Создание реплай-клавиатуры для нижней панели
def get_actions_keyboard():
    keyboard = [
        [KeyboardButton("Консультация"), KeyboardButton("Написать в ТГ")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие...")


# Клавиатура для блока связи в конце
def get_contact_final_keyboard():
    keyboard = [
        [KeyboardButton("📞 По телефону"), KeyboardButton("💬 Сообщение в Telegram")],
        [KeyboardButton("🔄 Начать заново")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите способ связи...")


# Клавиатура для отправки номера телефона
def get_phone_keyboard():
    keyboard = [
        [KeyboardButton("📱 Отправить номер", request_contact=True)],
        [KeyboardButton("Ввести вручную")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


# Клавиатуры для разных этапов с кнопкой "Назад"
def get_kitchen_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("Угловая", callback_data="кухня_угловая")],
        [InlineKeyboardButton("Прямая", callback_data="кухня_прямая")],
        [InlineKeyboardButton("П-образная", callback_data="кухня_п_образная")],
        [InlineKeyboardButton("С островом", callback_data="кухня_остров")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_size_keyboard():
    keyboard = [
        [InlineKeyboardButton("Точные", callback_data="размер_точные")],
        [InlineKeyboardButton("Приблизительные", callback_data="размер_приблизительные")],
        [InlineKeyboardButton("Не знаю", callback_data="размер_не_знаю")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_тип")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_material_keyboard():
    keyboard = [
        [InlineKeyboardButton("ЛДСП", callback_data="материал_лдсп")],
        [InlineKeyboardButton("АГТ", callback_data="материал_агт")],
        [InlineKeyboardButton("Эмаль", callback_data="материал_эмаль")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_размер")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_hardware_keyboard():
    keyboard = [
        [InlineKeyboardButton("Эконом", callback_data="фурнитура_эконом")],
        [InlineKeyboardButton("Стандарт", callback_data="фурнитура_стандарт")],
        [InlineKeyboardButton("Премиум", callback_data="фурнитура_премиум")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_материал")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_budget_keyboard():
    keyboard = [
        [InlineKeyboardButton("Эконом", callback_data="бюджет_эконом")],
        [InlineKeyboardButton("Стандарт", callback_data="бюджет_стандарт")],
        [InlineKeyboardButton("Премиум", callback_data="бюджет_премиум")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_предыдущий")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_deadline_keyboard():
    keyboard = [
        [InlineKeyboardButton("Этот месяц", callback_data="срок_месяц")],
        [InlineKeyboardButton("1-2 месяца", callback_data="срок_1_2")],
        [InlineKeyboardButton("3 месяца", callback_data="срок_3")],
        [InlineKeyboardButton("Присматриваюсь", callback_data="срок_присмотр")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_бюджет")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cabinet_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("Распашной", callback_data="шкаф_распашной")],
        [InlineKeyboardButton("Купе", callback_data="шкаф_купе")],
        [InlineKeyboardButton("↩️ Назад", callback_data="назад_категории")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Хранилище данных пользователя
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=get_categories_keyboard())


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # Инициализация данных пользователя
    if user_id not in user_data:
        user_data[user_id] = {}

    # Обработка кнопки "Назад"
    if query.data.startswith("назад_"):
        await handle_back_button(query, user_id)
        return

    # Обработка выбора категории
    if query.data == "кухня":
        user_data[user_id]['category'] = 'кухня'
        user_data[user_id]['current_step'] = 'kitchen_type'
        await query.edit_message_text(
            "🏠 **Кухня**\n\nВыберите тип кухни:",
            reply_markup=get_kitchen_type_keyboard()
        )

    elif query.data == "шкаф":
        user_data[user_id]['category'] = 'шкаф'
        user_data[user_id]['current_step'] = 'cabinet_type'
        await query.edit_message_text(
            "🚪 **Шкаф**\n\nВыберите тип шкафа:",
            reply_markup=get_cabinet_type_keyboard()
        )

    elif query.data == "гардеробная":
        user_data[user_id]['category'] = 'гардеробная'
        user_data[user_id]['current_step'] = 'size'
        await query.edit_message_text(
            "👔 **Гардеробная**\n\nКакие у вас размеры?",
            reply_markup=get_size_keyboard()
        )

    elif query.data == "другое":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🛋 **Другая мебель**\n\nУточните, какая мебель вас интересует?",
            reply_markup=get_actions_keyboard()
        )

    # Обработка сценария КУХНЯ
    elif query.data.startswith("кухня_"):
        if query.data == "кухня_угловая":
            user_data[user_id]['kitchen_type'] = 'Угловая'
        elif query.data == "кухня_прямая":
            user_data[user_id]['kitchen_type'] = 'Прямая'
        elif query.data == "кухня_п_образная":
            user_data[user_id]['kitchen_type'] = 'П-образная'
        elif query.data == "кухня_остров":
            user_data[user_id]['kitchen_type'] = 'С островом'

        user_data[user_id]['current_step'] = 'size'
        await query.edit_message_text(
            "📏 **Размеры**\n\nКакие у вас размеры?",
            reply_markup=get_size_keyboard()
        )

    # Обработка размеров (общее для Кухни и Гардеробной)
    elif query.data.startswith("размер_"):
        if query.data == "размер_точные":
            user_data[user_id]['size'] = 'Точные'
        elif query.data == "размер_приблизительные":
            user_data[user_id]['size'] = 'Приблизительные'
        elif query.data == "размер_не_знаю":
            user_data[user_id]['size'] = 'Не знаю'

        # Определяем следующий шаг в зависимости от категории
        category = user_data[user_id].get('category', '')
        
        if category == 'кухня':
            user_data[user_id]['current_step'] = 'material'
            await query.edit_message_text(
                "🎨 **Материал фасадов**\n\nВыберите материал:",
                reply_markup=get_material_keyboard()
            )
        elif category == 'гардеробная':
            user_data[user_id]['current_step'] = 'budget'
            await query.edit_message_text(
                "💰 **Бюджет**\n\nВыберите бюджет:",
                reply_markup=get_budget_keyboard()
            )

    elif query.data.startswith("материал_"):
        if query.data == "материал_лдсп":
            user_data[user_id]['material'] = 'ЛДСП'
        elif query.data == "материал_агт":
            user_data[user_id]['material'] = 'АГТ'
        elif query.data == "материал_эмаль":
            user_data[user_id]['material'] = 'Эмаль'

        user_data[user_id]['current_step'] = 'hardware'
        await query.edit_message_text(
            "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
            reply_markup=get_hardware_keyboard()
        )

    elif query.data.startswith("фурнитура_"):
        if query.data == "фурнитура_эконом":
            user_data[user_id]['hardware'] = 'Эконом'
        elif query.data == "фурнитура_стандарт":
            user_data[user_id]['hardware'] = 'Стандарт'
        elif query.data == "фурнитура_премиум":
            user_data[user_id]['hardware'] = 'Премиум'

        user_data[user_id]['current_step'] = 'budget'
        await query.edit_message_text(
            "💰 **Бюджет**\n\nВыберите бюджет:",
            reply_markup=get_budget_keyboard()
        )

    elif query.data.startswith("бюджет_"):
        if query.data == "бюджет_эконом":
            user_data[user_id]['budget'] = 'Эконом'
        elif query.data == "бюджет_стандарт":
            user_data[user_id]['budget'] = 'Стандарт'
        elif query.data == "бюджет_премиум":
            user_data[user_id]['budget'] = 'Премиум'

        user_data[user_id]['current_step'] = 'deadline'
        await query.edit_message_text(
            "📅 **Сроки заказа**\n\nВыберите сроки:",
            reply_markup=get_deadline_keyboard()
        )

    # Обработка сценария ШКАФ
    elif query.data.startswith("шкаф_"):
        if query.data == "шкаф_распашной":
            user_data[user_id]['cabinet_type'] = 'Распашной'
        elif query.data == "шкаф_купе":
            user_data[user_id]['cabinet_type'] = 'Купе'

        user_data[user_id]['current_step'] = 'budget'
        await query.edit_message_text(
            "💰 **Бюджет**\n\nВыберите бюджет:",
            reply_markup=get_budget_keyboard()
        )

    # Обработка сроков заказа (переходим к запросу контактных данных)
    elif query.data.startswith("срок_"):
        if query.data == "срок_месяц":
            user_data[user_id]['deadline'] = 'Этот месяц'
        elif query.data == "срок_1_2":
            user_data[user_id]['deadline'] = '1-2 месяца'
        elif query.data == "срок_3":
            user_data[user_id]['deadline'] = '3 месяца'
        elif query.data == "срок_присмотр":
            user_data[user_id]['deadline'] = 'Присматриваюсь'

        # Запрашиваем имя
        await query.edit_message_text(
            "👤 **Контактные данные**\n\nПожалуйста, напишите ваше имя:",
        )
        user_data[user_id]['waiting_for'] = 'name'
        user_data[user_id]['current_step'] = 'name'


# Обработчик кнопки "Назад"
async def handle_back_button(query, user_id):
    back_step = query.data.replace("назад_", "")
    
    if back_step == "категории":
        await query.edit_message_text(
            WELCOME_MESSAGE,
            reply_markup=get_categories_keyboard()
        )
        # Очищаем данные при возврате к выбору категории
        if user_id in user_data:
            del user_data[user_id]
    
    elif back_step == "тип":
        category = user_data[user_id].get('category', '')
        if category == 'кухня':
            await query.edit_message_text(
                "🏠 **Кухня**\n\nВыберите тип кухни:",
                reply_markup=get_kitchen_type_keyboard()
            )
        elif category == 'шкаф':
            await query.edit_message_text(
                "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                reply_markup=get_cabinet_type_keyboard()
            )
    
    elif back_step == "размер":
        await query.edit_message_text(
            "📏 **Размеры**\n\nКакие у вас размеры?",
            reply_markup=get_size_keyboard()
        )
    
    elif back_step == "материал":
        await query.edit_message_text(
            "🎨 **Материал фасадов**\n\nВыберите материал:",
            reply_markup=get_material_keyboard()
        )
    
    elif back_step == "предыдущий":
        # Определяем предыдущий шаг на основе категории
        category = user_data[user_id].get('category', '')
        if category == 'кухня':
            await query.edit_message_text(
                "🔧 **Фурнитура**\n\nВыберите класс фурнитуры:",
                reply_markup=get_hardware_keyboard()
            )
        elif category in ['шкаф', 'гардеробная']:
            if category == 'шкаф':
                await query.edit_message_text(
                    "🚪 **Шкаф**\n\nВыберите тип шкафа:",
                    reply_markup=get_cabinet_type_keyboard()
                )
            else:
                await query.edit_message_text(
                    "👔 **Гардеробная**\n\nКакие у вас размеры?",
                    reply_markup=get_size_keyboard()
                )
    
    elif back_step == "бюджет":
        await query.edit_message_text(
            "💰 **Бюджет**\n\nВыберите бюджет:",
            reply_markup=get_budget_keyboard()
        )


# Обработчик текстовых сообщений (для имени и телефона)
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        user_data[user_id] = {}

    # Если ожидаем имя
    if user_data[user_id].get('waiting_for') == 'name':
        user_data[user_id]['name'] = text
        user_data[user_id]['waiting_for'] = 'phone'
        
        await update.message.reply_text(
            f"👤 **Имя принято:** {text}\n\n"
            "📱 **Телефон**\n\nПожалуйста, отправьте ваш номер телефона:",
            reply_markup=get_phone_keyboard()
        )

    # Если ожидаем телефон и пользователь ввел вручную
    elif user_data[user_id].get('waiting_for') == 'phone':
        if text == "Ввести вручную":
            await update.message.reply_text(
                "📱 **Введите номер телефона вручную:**\n\n"
                "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("↩️ Назад")]], resize_keyboard=True)
            )
        elif text == "↩️ Назад":
            user_data[user_id]['waiting_for'] = 'name'
            await update.message.reply_text(
                "👤 **Введите ваше имя еще раз:**",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            # Проверяем формат номера телефона
            if validate_phone(text):
                user_data[user_id]['phone'] = text
                await send_final_summary(update, context, user_id)
            else:
                await update.message.reply_text(
                    "❌ **Неверный формат номера**\n\n"
                    "Пожалуйста, введите номер в формате:\n"
                    "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
                    "Или нажмите кнопку '📱 Отправить номер'",
                    reply_markup=get_phone_keyboard()
                )


# Обработчик контактов (когда пользователь отправляет номер через кнопку)
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in user_data and user_data[user_id].get('waiting_for') == 'phone':
        phone_number = update.message.contact.phone_number
        user_data[user_id]['phone'] = phone_number
        await send_final_summary(update, context, user_id)


# Функция проверки номера телефона
def validate_phone(phone):
    # Упрощенная проверка номера телефона
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if phone.startswith('+7') and len(phone) == 12:
        return True
    elif phone.startswith('8') and len(phone) == 11:
        return True
    elif phone.startswith('7') and len(phone) == 11:
        return True
    return False


# Функция отправки финальной сводки
async def send_final_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    # Формируем итоговое сообщение с собранными данными
    category = user_data[user_id].get('category', '')
    summary = "✅ **Заявка оформлена!**\n\n"
    summary += f"👤 **Контактные данные:**\n"
    summary += f"• Имя: {user_data[user_id].get('name', '')}\n"
    summary += f"• Телефон: {user_data[user_id].get('phone', '')}\n\n"

    if category == 'кухня':
        summary += f"🏠 **Кухня**\n"
        summary += f"• Тип: {user_data[user_id].get('kitchen_type', '')}\n"
        summary += f"• Размеры: {user_data[user_id].get('size', '')}\n"
        summary += f"• Материал: {user_data[user_id].get('material', '')}\n"
        summary += f"• Фурнитура: {user_data[user_id].get('hardware', '')}\n"
        summary += f"• Бюджет: {user_data[user_id].get('budget', '')}\n"
        summary += f"• Сроки: {user_data[user_id].get('deadline', '')}\n"

    elif category == 'шкаф':
        summary += f"🚪 **Шкаф**\n"
        summary += f"• Тип: {user_data[user_id].get('cabinet_type', '')}\n"
        summary += f"• Бюджет: {user_data[user_id].get('budget', '')}\n"
        summary += f"• Сроки: {user_data[user_id].get('deadline', '')}\n"

    elif category == 'гардеробная':
        summary += f"👔 **Гардеробная**\n"
        summary += f"• Размеры: {user_data[user_id].get('size', '')}\n"
        summary += f"• Бюджет: {user_data[user_id].get('budget', '')}\n"
        summary += f"• Сроки: {user_data[user_id].get('deadline', '')}\n"

    summary += "\nСпасибо за заявку!"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=summary
    )

    # Добавляем блок связи
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📞 **Как с вами связаться?**\n\nВыберите удобный способ связи:",
        reply_markup=get_contact_final_keyboard()
    )

    # Очищаем данные пользователя после завершения
    if user_id in user_data:
        del user_data[user_id]


# Обработчик для кнопок в нижней панели
async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Обработка кнопок основного меню
    if text == "Консультация":
        await update.message.reply_text(
            "📞 **Консультация**\n\nДля консультации свяжитесь с нами:\n\n"
            "💬 Телеграм: @max_lap555\n"
            "📱 WhatsApp: +79063405556",
            reply_markup=get_actions_keyboard()
        )
    elif text == "Написать в ТГ":
        await update.message.reply_text(
            "💬 **Написать в Telegram**\n\n"
            "Перейдите в Telegram: @max_lap555\n"
            "Или напишите на номер: +79063405556",
            reply_markup=get_actions_keyboard()
        )

    # Обработка кнопок финального блока связи
    elif text == "📞 По телефону":
        await update.message.reply_text(
            "📞 **Связь по телефону**\n\n"
            "Позвоните нам по номеру:\n"
            "📱 +79063405556\n\n"
            "Мы доступны:\n"
            "• Пн-Пт: 9:00-18:00\n"
            "• Сб: 10:00-16:00",
            reply_markup=get_contact_final_keyboard()
        )
    elif text == "💬 Сообщение в Telegram":
        await update.message.reply_text(
            "💬 **Сообщение в Telegram**\n\n"
            "Напишите нам в Telegram:\n"
            "👤 @max_lap555\n\n"
            "Или перейдите по ссылке:\n"
            "https://t.me/max_lap555",
            reply_markup=get_contact_final_keyboard()
        )
    elif text == "🔄 Начать заново":
        # Очищаем данные и начинаем заново
        user_id = update.effective_user.id
        if user_id in user_data:
            del user_data[user_id]
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=get_categories_keyboard()
        )


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_buttons))

    application.run_polling()


if __name__ == '__main__':
    main()
