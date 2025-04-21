from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from config import BOT_TOKEN, OWNER_CHAT_ID, ADMIN_PASSWORD
from database import init_db, add_appointment, is_slot_taken, cancel_appointment, get_all_appointments
from datetime import datetime, timedelta
import re

# Валидация номера телефона
def validate_phone(phone):
    pattern = r'^(\+7|8)\d{10}$'
    return re.match(pattern, phone) is not None

# Стартовое сообщение
def start(update: Update, context: CallbackContext):
    # Инициализация базы данных при первом вызове
    # try:
    #     init_db()
    # except Exception as e:
    #     update.message.reply_text(f"Ошибка подключения к базе данных: {e}")
    #     return
    
    keyboard = [
        ["Записаться"],
        ["Отменить запись"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "Добро пожаловать в бот парикмахерской! Выберите действие:", 
        reply_markup=reply_markup
    )

# Обработка выбора действия
def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "Записаться":
        show_days(update, context)
    elif text == "Отменить запись":
        context.user_data["action"] = "cancel"
        update.message.reply_text("Введите ваш номер телефона (например, +79991234567):")
    elif context.user_data.get("action") == "cancel":
        phone = text
        if not validate_phone(phone):
            update.message.reply_text("Некорректный номер телефона. Попробуйте снова (например, +79991234567):")
            return
        result = cancel_appointment(phone)
        if result:
            update.message.reply_text(f"Запись для {result[0]} успешно отменена.")
            context.bot.send_message(
                OWNER_CHAT_ID, 
                f"Клиент {result[0]} ({phone}) отменил запись."
            )
        else:
            update.message.reply_text("Запись с таким номером не найдена.")
        context.user_data.clear()
    elif context.user_data.get("action") == "admin":
        if text == ADMIN_PASSWORD:
            show_admin_menu(update, context)
        else:
            update.message.reply_text("Неверный пароль.")
        context.user_data.clear()
    elif context.user_data.get("action") == "name":
        context.user_data["name"] = text
        context.user_data["action"] = "phone"
        update.message.reply_text("Введите ваш номер телефона (например, +79991234567):")
    elif context.user_data.get("action") == "phone":
        if not validate_phone(text):
            update.message.reply_text("Некорректный номер телефона. Попробуйте снова (например, +79991234567):")
            return
        context.user_data["phone"] = text
        appointment_time = context.user_data["appointment_time"]
        add_appointment(context.user_data["name"], text, appointment_time)
        update.message.reply_text(
            f"Запись успешно создана!\nИмя: {context.user_data['name']}\nТелефон: {text}\nВремя: {appointment_time.strftime('%Y-%m-%d %H:%M')}"
        )
        context.bot.send_message(
            OWNER_CHAT_ID,
            f"Новая запись:\nИмя: {context.user_data['name']}\nТелефон: {text}\nВремя: {appointment_time.strftime('%Y-%m-%d %H:%M')}"
        )
        context.user_data.clear()

# Выбор дня
def show_days(update: Update, context: CallbackContext):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    keyboard = []
    for i in range(7):
        day = today + timedelta(days=i)
        keyboard.append([InlineKeyboardButton(
            day.strftime("%Y-%m-%d (%A)"), 
            callback_data=f"day_{day.strftime('%Y-%m-%d')}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите день:", reply_markup=reply_markup)

# Выбор времени
def show_times(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    day_str = query.data.split("_")[1]
    selected_day = datetime.strptime(day_str, "%Y-%m-%d")
    keyboard = []
    current_time = datetime.now()
    
    for hour in range(9, 21):
        slot_time = selected_day.replace(hour=hour, minute=0)
        if slot_time > current_time and not is_slot_taken(slot_time):
            keyboard.append([InlineKeyboardButton(
                f"{hour}:00", 
                callback_data=f"time_{slot_time.strftime('%Y-%m-%d %H:%M')}"
            )])
    
    if not keyboard:
        query.message.reply_text("Нет доступных слотов на этот день. Выберите другой день.")
        show_days(query, context)
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("Выберите время:", reply_markup=reply_markup)

# Подтверждение времени и ввод имени
def confirm_time(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    time_str = query.data.split("_")[1]
    context.user_data["appointment_time"] = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    context.user_data["action"] = "name"
    query.message.reply_text("Введите ваше имя:")

# Админ-панель
def admin(update: Update, context: CallbackContext):
    context.user_data["action"] = "admin"
    update.message.reply_text("Введите пароль админа:")

def show_admin_menu(update: Update, context: CallbackContext):
    appointments = get_all_appointments()
    if not appointments:
        update.message.reply_text("Записей нет.")
        return
    
    response = "Список записей:\n"
    for name, phone, time in appointments:
        response += f"Имя: {name}, Телефон: {phone}, Время: {time.strftime('%Y-%m-%d %H:%M')}\n"
    update.message.reply_text(response)

# Обработка inline-кнопок
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data.startswith("day_"):
        show_times(update, context)
    elif query.data.startswith("time_"):
        confirm_time(update, context)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()