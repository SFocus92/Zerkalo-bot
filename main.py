from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from config import BOT_TOKEN, OWNER_CHAT_ID, ADMIN_PASSWORD
from database import init_db, add_appointment, is_slot_taken, cancel_appointment, get_all_appointments
from datetime import datetime, timedelta
import re
import calendar

# Валидация номера телефона
def validate_phone(phone):
    pattern = r'^(\+7|8)\d{10}$'
    return re.match(pattern, phone) is not None

# Словарь для перевода дней недели на русский
WEEKDAY_RU = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}

# Словарь для русских названий месяцев
MONTH_RU = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
    7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}

# Список мастеров
MASTERS = ['Наташа', 'Ваня']

# Стартовое сообщение
def start(update: Update, context: CallbackContext):
    try:
        init_db()
    except Exception as e:
        update.message.reply_text(f"Ошибка подключения к базе данных: {e}")
        return
    
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
        show_masters(update, context)
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
            client_name, master = result
            update.message.reply_text(f"Запись для {client_name} (мастер: {master}) успешно отменена.")
            context.bot.send_message(
                OWNER_CHAT_ID, 
                f"Клиент {client_name} ({phone}) отменил запись у мастера {master}."
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
        master = context.user_data["master"]
        add_appointment(context.user_data["name"], text, appointment_time, master)
        update.message.reply_text(
            f"Запись успешно создана!\nИмя: {context.user_data['name']}\nТелефон: {text}\nМастер: {master}\nВремя: {appointment_time.strftime('%Y-%m-%d %H:%M')}"
        )
        context.bot.send_message(
            OWNER_CHAT_ID,
            f"Новая запись:\nИмя: {context.user_data['name']}\nТелефон: {text}\nМастер: {master}\nВремя: {appointment_time.strftime('%Y-%m-%d %H:%M')}"
        )
        context.user_data.clear()

# Показ мастеров
def show_masters(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton(master, callback_data=f"master_{master}")] for master in MASTERS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите мастера:", reply_markup=reply_markup)

# Показ месяцев
def show_months(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    master = query.data.split("_")[1] if query.data.startswith("master_") else context.user_data.get("master")
    context.user_data["master"] = master
    today = datetime.now()
    keyboard = []
    for i in range(12):  # 12 месяцев вперед
        month_date = today + timedelta(days=30*i)
        year = month_date.year
        month = month_date.month
        month_name = MONTH_RU.get(month, f"Месяц {month}")
        button_text = f"{month_name} {year}"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"month_{year}-{month:02d}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("Выберите месяц:", reply_markup=reply_markup)

# Показ дней в месяце
def show_days_in_month(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    year, month = map(int, query.data.split("_")[1].split("-"))
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    _, last_day = calendar.monthrange(year, month)
    keyboard = []
    
    for day in range(1, last_day + 1):
        date = datetime(year, month, day)
        if date < today:
            continue
        weekday_en = date.strftime("%A")
        weekday_ru = WEEKDAY_RU.get(weekday_en, weekday_en)
        button_text = f"{date.strftime('%Y-%m-%d')} ({weekday_ru})"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"day_{date.strftime('%Y-%m-%d')}"
        )])
    
    if not keyboard:
        query.message.reply_text("Нет доступных дней в этом месяце. Выберите другой месяц.")
        show_months(update, context)
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(f"Выберите день в {MONTH_RU.get(month, f'Месяц {month}')} {year}:", reply_markup=reply_markup)

# Выбор времени
def show_times(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    day_str = query.data.split("_")[1]
    selected_day = datetime.strptime(day_str, "%Y-%m-%d")
    master = context.user_data["master"]
    keyboard = []
    current_time = datetime.now()
    
    for hour in range(9, 21):
        slot_time = selected_day.replace(hour=hour, minute=0)
        if slot_time > current_time and not is_slot_taken(slot_time, master):
            keyboard.append([InlineKeyboardButton(
                f"{hour}:00", 
                callback_data=f"time_{slot_time.strftime('%Y-%m-%d %H:%M')}"
            )])
    
    if not keyboard:
        query.message.reply_text("Нет доступных слотов на этот день. Выберите другой день.")
        show_days_in_month(update, context)
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(f"Выберите время для мастера {master}:", reply_markup=reply_markup)

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
    for name, phone, time, master in appointments:
        response += f"Имя: {name}, Телефон: {phone}, Мастер: {master}, Время: {time.strftime('%Y-%m-%d %H:%M')}\n"
    update.message.reply_text(response)

# Обработка inline-кнопок
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data.startswith("master_"):
        show_months(update, context)
    elif query.data.startswith("month_"):
        show_days_in_month(update, context)
    elif query.data.startswith("day_"):
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