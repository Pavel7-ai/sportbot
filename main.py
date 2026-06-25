import telebot
from telebot import types
import sqlite3
import os
import re

# ==== ПОДКЛЮЧЕНИЕ К SQLite ====
DB_FILE = 'sport_bot.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            link TEXT,
            lat REAL,
            lon REAL
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_key TEXT,
            user_id INTEGER,
            rating INTEGER CHECK (rating >= 0 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(section_key, user_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            section_key TEXT UNIQUE NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print('✅ База данных SQLite инициализирована')

def add_default_sections():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM sections")
    count = cur.fetchone()[0]
    
    if count > 0:
        conn.close()
        return
    
    sections = [
        ('football_konoplev', 'Академия футбола им.Юрия Коноплёва', '📍 Советская, 23б', '+78482559115 +78482559116', 'https://vk.com/konoplev_academy', 53.4805, 49.3874),
        ('football_lada', 'Футбольная школа "Лада"', '📍 Юбилейная, 6б (комплекс Спутник)\n📍 Революционная, 80 (Стадион Торпедо)', '+78482371068 +78482580952', 'https://vk.com/public191471116', 53.5078, 49.4203),
        ('football_spartak', 'Футбольная школа "Спартак Юниор"', '📍 Южное шоссе, 2', '+78003010293 +79372123202', 'https://vk.com/fsspartak_tlt', 53.5142, 49.4251),
        ('football_galacticos', 'Футбольная школа "Галактикос"', '📍 Тополиная, 5\n📍 Автостроителей, 84 (Школа №66)\n📍 Бульвар Туполева, 12 (Школа №47)\n📍 Бульвар Королёва, 3 (Школа им. Королёва)\n📍 Степана Разина, 78 (Лицей №76)', '+79278922080 +78482341015', 'https://vk.com/fs_galacticos', 53.5200, 49.4000),
        ('football_impuls', 'Футбольная школа "Импульс"', '📍 Цветной бульвар, 13 (Школа №82)\n📍 Тополиная, 18 (Школа №90)\n📍 Бульвар Татищева, 19 (Школа №90)\n📍 Бульвар Космонавтов, 17 (Школа №79)\n📍 40 лет Победы, 74 (Школа №70)\n📍 40 лет Победы, 86 (Школа №70)', '+79608460989 +78482409350', 'https://vk.com/fc.impuls', 53.4900, 49.4100),
        ('football_athletic', 'Футбольная школа "Athletic football"', '📍 Бульвар Луначарского, 11 (Школа №71)\n📍 Свердлова, 23 (Школа №61)', '+79277851389 +78482326450', 'https://vk.com/athletic_football', 53.5000, 49.4300),
        ('hockey_flypro', 'Хоккейная школа "Fly pro"', '📍 40 лет Победы, 14', '+79276163714', 'https://vk.com/flyagin_school', 53.5100, 49.4400),
        ('hockey_lada', 'Хоккейная школа "Лада"', '📍 Ботаническая, 5', '+78482526840', 'https://vk.com/lada.arena', 53.5300, 49.3800),
        ('hockey_volgar', 'Хоккейная школа "Волгарь"', '📍 Приморский бульвар, 37\n📍 Баныкина, 9 (Стадион Кристалл)', '+78482347692', 'https://vk.com/volgar_tlt', 53.5400, 49.3600),
        ('basketball_redwings', 'Баскетбольная школа "Красные крылья"', '📍 Цветной бульвар, 18 (Школа №84)\n📍 40 лет Победы, 106 (Школа №81)', '+78482692388 +78482692377', 'https://vk.com/tltredwings', 53.5000, 49.4500),
        ('basketball_phoenix', 'Баскетбольная школа "Феникс"', '📍 Фрунзе, 2г (ТГУ)\n📍 Белорусская, 6а (ВУиТ)', '+79272110533', 'https://vk.com/basketboltlt', 53.4800, 49.4600),
        ('boxing_lotus', '"Lotusport\'s club r home"', '📍 Тополиная, 18 (Школа №90)', '+79277766212', 'https://vk.com/lsc63', 53.5200, 49.3900),
        ('boxing_vlasov', '"Школа бокса им. МСМК Игоря Власова"', '📍 Цветной бульвар, 18 (Школа №84)', '+79277887611 +79272185339', 'https://vk.com/vlasovboxing', 53.4900, 49.4200),
        ('boxing_gloves', '"Боевые перчатки"', '📍 Ворошилова, 21 (Школа №74)', '+78482429405', 'https://vk.com/public204222709', 53.5000, 49.4100),
        ('boxing_gaidarovets', '"Гайдаровец"', '📍 Фрунзе, 35', '+79272116655', 'https://vk.com/tolyattiboxing', 53.4700, 49.4300),
        ('boxing_pobeda', '"Победа-спорт"', '📍 Маршала Жукова, 26', '+78482417363 +78482290002', 'https://vk.com/ksepobeda', 53.4900, 49.4500),
        ('boxing_school', '"Школа бокса"', '📍 Юбилейная, 81 (Школа №73)\n📍 Приморский бульвар, 37 (Волгарь)', '+7848703455 +78482707450', 'https://vk.com/boxingschool163', 53.5000, 49.4600),
        ('boxing_albasport', '"Albasport"', '📍 Фермерская, 1а/1', '+78482580101', 'https://vk.com/albasport63', 53.5100, 49.4700),
        ('handball_lada', 'Гандбольный клуб "Лада"', '📍 Приморский бульвар, 49 (Олимп)\n📍 Бульвар Татищева, 19\n📍 40 лет Победы, 74\n📍 Ворошилова, 21', '+78482357963 +78482355394 +79277800042', 'https://vk.com/public157271429', 53.5300, 49.3500),
    ]
    
    for section in sections:
        cur.execute('''
            INSERT INTO sections (key, name, address, phone, link, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', section)
    
    conn.commit()
    conn.close()
    print(f'✅ Добавлено {len(sections)} секций')

def add_default_admin():
    conn = get_db_connection()
    cur = conn.cursor()
    
    admin_telegram_id = 647992946
    section_key = 'football_konoplev'
    
    cur.execute("SELECT COUNT(*) FROM admins WHERE telegram_id = ?", (admin_telegram_id,))
    exists = cur.fetchone()[0]
    
    if exists == 0:
        cur.execute(
            "INSERT INTO admins (telegram_id, section_key) VALUES (?, ?)",
            (admin_telegram_id, section_key)
        )
        conn.commit()
        print(f'✅ Админ добавлен (ID: {admin_telegram_id})')
    else:
        print('ℹ️ Админ уже существует')
    
    conn.close()

# ==== ИНИЦИАЛИЗАЦИЯ ====
init_db()
add_default_sections()
add_default_admin()

# ==== БОТ ====
TOKEN = os.getenv('TELEGRAM_TOKEN', '6059734363:AAEPa7yL052gvPAOQEA22EaNP-_2T2Yy7Yg')
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

# ==== НАСТРОЙКА МЕНЮ КОМАНД ====
bot.set_my_commands([
    types.BotCommand("start", "Начать пользование"),
    types.BotCommand("admin", "Панель администратора"),
])

# ==== ГЛОБАЛЬНЫЕ СЛОВАРИ ====
user_location_data = {}
user_review_state = {}
user_rating_state = {}

# ==== ФУНКЦИИ РАБОТЫ С БД ====

def get_section_data(section_key):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sections WHERE key = ?", (section_key,))
    result = cur.fetchone()
    conn.close()
    return result

def get_section_rating(section_key):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(AVG(rating), 0) as avg_rating, COUNT(*) as total_count FROM reviews WHERE section_key = ? AND rating > 0",
        (section_key,)
    )
    result = cur.fetchone()
    conn.close()
    return {'rating': result[0] if result and result[0] else 0, 'count': result[1] if result else 0}

def save_review_to_db(section_key, user_id, rating, comment):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM reviews WHERE section_key = ? AND user_id = ?", (section_key, user_id))
    existing = cur.fetchone()
    
    if existing:
        cur.execute(
            "UPDATE reviews SET rating = ?, comment = ? WHERE section_key = ? AND user_id = ?",
            (rating, comment, section_key, user_id)
        )
        conn.commit()
        conn.close()
        return 'updated'
    else:
        cur.execute(
            "INSERT INTO reviews (section_key, user_id, rating, comment) VALUES (?, ?, ?, ?)",
            (section_key, user_id, rating, comment)
        )
        conn.commit()
        conn.close()
        return 'created'

def get_reviews(section_key):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT rating, comment, user_id, created_at FROM reviews WHERE section_key = ? ORDER BY created_at DESC LIMIT 5",
        (section_key,)
    )
    results = cur.fetchall()
    conn.close()
    return results

def get_user(telegram_id, username=None, first_name=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        cur.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
            (telegram_id, username, first_name)
        )
        conn.commit()
        cur.execute("SELECT id, telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cur.fetchone()
    conn.close()
    return user

# ==== СЛОВАРЬ ДЛЯ ТЕКСТОВ СЕКЦИЙ ====
section_texts = {
    'football_konoplev': ('⚽️ Академия футбола им.Юрия Коноплёва', '📍 Советская, 23б\n📞 +78482559115 +78482559116\n🔗 https://vk.com/konoplev_academy'),
    'football_lada': ('⚽️ Футбольная школа "Лада"', '📍 Юбилейная, 6б (комплекс Спутник)\n📍 Революционная, 80 (Стадион Торпедо)\n📞 +78482371068 +78482580952\n🔗 https://vk.com/public191471116'),
    'football_spartak': ('⚽️ Футбольная школа "Спартак Юниор"', '📍 Южное шоссе, 2\n📞 +78003010293 +79372123202\n🔗 https://vk.com/fsspartak_tlt'),
    'football_galacticos': ('⚽️ Футбольная школа "Галактикос"', '📍 Тополиная, 5\n📍 Автостроителей, 84 (Школа №66)\n📍 Бульвар Туполева, 12 (Школа №47)\n📍 Бульвар Королёва, 3 (Школа им. Королёва)\n📍 Степана Разина, 78 (Лицей №76)\n📞 +79278922080 +78482341015\n🔗 https://vk.com/fs_galacticos'),
    'football_impuls': ('⚽️ Футбольная школа "Импульс"', '📍 Цветной бульвар, 13 (Школа №82)\n📍 Тополиная, 18 (Школа №90)\n📍 Бульвар Татищева, 19 (Школа №90)\n📍 Бульвар Космонавтов, 17 (Школа №79)\n📍 40 лет Победы, 74 (Школа №70)\n📍 40 лет Победы, 86 (Школа №70)\n📞 +79608460989 +78482409350\n🔗 https://vk.com/fc.impuls'),
    'football_athletic': ('⚽️ Футбольная школа "Athletic football"', '📍 Бульвар Луначарского, 11 (Школа №71)\n📍 Свердлова, 23 (Школа №61)\n📞 +79277851389 +78482326450\n🔗 https://vk.com/athletic_football'),
    'hockey_flypro': ('🏒 Хоккейная школа "Fly pro"', '📍 40 лет Победы, 14\n📞 +79276163714\n🔗 https://vk.com/flyagin_school'),
    'hockey_lada': ('🏒 Хоккейная школа "Лада"', '📍 Ботаническая, 5\n📞 +78482526840\n🔗 https://vk.com/lada.arena'),
    'hockey_volgar': ('🏒 Хоккейная школа "Волгарь"', '📍 Приморский бульвар, 37\n📍 Баныкина, 9 (Стадион Кристалл)\n📞 +78482347692\n🔗 https://vk.com/volgar_tlt'),
    'basketball_redwings': ('🏀 Баскетбольная школа "Красные крылья"', '📍 Цветной бульвар, 18 (Школа №84)\n📍 40 лет Победы, 106 (Школа №81)\n📞 +78482692388 +78482692377\n🔗 https://vk.com/tltredwings'),
    'basketball_phoenix': ('🏀 Баскетбольная школа "Феникс"', '📍 Фрунзе, 2г (ТГУ)\n📍 Белорусская, 6а (ВУиТ)\n📞 +79272110533\n🔗 https://vk.com/basketboltlt'),
    'boxing_lotus': ('🥊 "Lotusport\'s club r home"', '📍 Тополиная, 18 (Школа №90)\n📞 +79277766212\n🔗 https://vk.com/lsc63'),
    'boxing_vlasov': ('🥊 "Школа бокса им. МСМК Игоря Власова"', '📍 Цветной бульвар, 18 (Школа №84)\n📞 +79277887611 +79272185339\n🔗 https://vk.com/vlasovboxing'),
    'boxing_gloves': ('🥊 "Боевые перчатки"', '📍 Ворошилова, 21 (Школа №74)\n📞 +78482429405\n🔗 https://vk.com/public204222709'),
    'boxing_gaidarovets': ('🥊 "Гайдаровец"', '📍 Фрунзе, 35\n📞 +79272116655\n🔗 https://vk.com/tolyattiboxing'),
    'boxing_pobeda': ('🥊 "Победа-спорт"', '📍 Маршала Жукова, 26\n📞 +78482417363 +78482290002\n🔗 https://vk.com/ksepobeda'),
    'boxing_school': ('🥊 "Школа бокса"', '📍 Юбилейная, 81 (Школа №73)\n📍 Приморский бульвар, 37 (Волгарь)\n📞 +7848703455 +78482707450\n🔗 https://vk.com/boxingschool163'),
    'boxing_albasport': ('🥊 "Albasport"', '📍 Фермерская, 1а/1\n📞 +78482580101\n🔗 https://vk.com/albasport63'),
    'handball_lada': ('🤾 Гандбольный клуб "Лада"', '📍 Приморский бульвар, 49 (Олимп)\n📍 Бульвар Татищева, 19\n📍 40 лет Победы, 74\n📍 Ворошилова, 21\n📞 +78482357963 +78482355394 +79277800042\n🔗 https://vk.com/public157271429'),
}

def format_rating(section_key):
    data = get_section_rating(section_key)
    rating = data['rating']
    count = data['count']
    if count == 0:
        return '⭐ Нет оценок'
    stars = '⭐' * int(round(rating)) + '☆' * (5 - int(round(rating)))
    return f'{stars} {rating:.1f} ({count} оценок)'

def get_section_card_text(section_key):
    section = get_section_data(section_key)
    if not section:
        return '❌ Секция не найдена'
    
    sport_icons = {
        'football': '⚽️',
        'hockey': '🏒',
        'basketball': '🏀',
        'boxing': '🥊',
        'handball': '🤾'
    }
    sport = section_key.split('_')[0]
    icon = sport_icons.get(sport, '🏆')
    
    name = f"{icon} {section['name']}"
    info = section['address']
    # Добавляем телефон и ссылку отдельно (если есть)
    if section['phone']:
        info += f"\n📞 {section['phone']}"
    if section['link']:
        info += f"\n🔗 {section['link']}"
    rating_text = format_rating(section_key)
    return f'<b>{name}</b>\n\n{info}\n\n{rating_text}'

def section_keyboard(section_key):
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(text='📝 Оставить отзыв', callback_data=f'review_{section_key}')
    btn2 = types.InlineKeyboardButton(text='📖 Все отзывы', callback_data=f'view_reviews_{section_key}')
    btn3 = types.InlineKeyboardButton(text='🗺️ Показать на карте', callback_data=f'map_{section_key}')
    btn4 = types.InlineKeyboardButton(text='🔙 Назад к списку', callback_data=f'back_to_list_{section_key}')
    kb.add(btn1, btn2, btn3, btn4)
    return kb

def location_keyboard_with_back_to_card(section_key):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text='🔙 Назад к карточке', callback_data=f'back_to_card_{section_key}'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Футбол⚽️', callback_data='btn1')
    btn2 = types.InlineKeyboardButton(text='Хоккей🏒', callback_data='btn2')
    btn3 = types.InlineKeyboardButton(text='Баскетбол🏀', callback_data='btn3')
    btn4 = types.InlineKeyboardButton(text='Бокс🥊', callback_data='btn4')
    btn5 = types.InlineKeyboardButton(text='Гандбол🤾', callback_data='btn5')
    kb.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id, '<b>Добро пожаловать! Я предоставлю тебе всю информацию о спортивных секциях в Тольятти!</b>\n\n<i>Выбери, о какой хочешь узнать:</i>', parse_mode='html', reply_markup=kb)

# ==== ФУНКЦИИ ДЛЯ ПОКАЗА СПИСКОВ ШКОЛ ====

def show_football_list(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('⚽️ Академия Коноплёва', callback_data='btn1_konoplev'),
        types.InlineKeyboardButton('⚽️ ФШ Лада', callback_data='btn1_lada'),
        types.InlineKeyboardButton('⚽️ Спартак Юниор', callback_data='btn1_spartak'),
        types.InlineKeyboardButton('⚽️ Галактикос', callback_data='btn1_galacticos'),
        types.InlineKeyboardButton('⚽️ Импульс', callback_data='btn1_impuls'),
        types.InlineKeyboardButton('⚽️ Athletic football', callback_data='btn1_athletic'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    if message_id:
        bot.edit_message_text('⚽️ <b>Выбери футбольную школу:</b>', chat_id, message_id, parse_mode='html', reply_markup=kb)
    else:
        bot.send_message(chat_id, '⚽️ <b>Выбери футбольную школу:</b>', parse_mode='html', reply_markup=kb)

def show_hockey_list(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('🏒 Fly pro', callback_data='btn2_flypro'),
        types.InlineKeyboardButton('🏒 Лада', callback_data='btn2_lada'),
        types.InlineKeyboardButton('🏒 Волгарь', callback_data='btn2_volgar'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    if message_id:
        bot.edit_message_text('🏒 <b>Выбери хоккейную школу:</b>', chat_id, message_id, parse_mode='html', reply_markup=kb)
    else:
        bot.send_message(chat_id, '🏒 <b>Выбери хоккейную школу:</b>', parse_mode='html', reply_markup=kb)

def show_basketball_list(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('🏀 Красные крылья', callback_data='btn3_redwings'),
        types.InlineKeyboardButton('🏀 Феникс', callback_data='btn3_phoenix'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    if message_id:
        bot.edit_message_text('🏀 <b>Выбери баскетбольную школу:</b>', chat_id, message_id, parse_mode='html', reply_markup=kb)
    else:
        bot.send_message(chat_id, '🏀 <b>Выбери баскетбольную школу:</b>', parse_mode='html', reply_markup=kb)

def show_boxing_list(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('🥊 Lotusport', callback_data='btn4_lotus'),
        types.InlineKeyboardButton('🥊 Власова', callback_data='btn4_vlasov'),
        types.InlineKeyboardButton('🥊 Боевые перчатки', callback_data='btn4_gloves'),
        types.InlineKeyboardButton('🥊 Arsenal fighting', callback_data='btn4_arsenal'),
        types.InlineKeyboardButton('🥊 Гайдаровец', callback_data='btn4_gaidarovets'),
        types.InlineKeyboardButton('🥊 Победа-спорт', callback_data='btn4_pobeda'),
        types.InlineKeyboardButton('🥊 Школа бокса', callback_data='btn4_school'),
        types.InlineKeyboardButton('🥊 Albasport', callback_data='btn4_albasport'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    if message_id:
        bot.edit_message_text('🥊 <b>Выбери школу бокса:</b>', chat_id, message_id, parse_mode='html', reply_markup=kb)
    else:
        bot.send_message(chat_id, '🥊 <b>Выбери школу бокса:</b>', parse_mode='html', reply_markup=kb)

# ==================== ОБРАБОТЧИКИ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('map_'))
def send_location(call):
    chat_id = call.message.chat.id
    section_key = call.data.replace('map_', '')
    section = get_section_data(section_key)
    bot.delete_message(chat_id, call.message.message_id)
    if section and section['lat'] and section['lon']:
        location_msg = bot.send_location(chat_id, latitude=section['lat'], longitude=section['lon'])
        text_msg = bot.send_message(chat_id, '📍 <i>Нажми на точку, чтобы проложить маршрут</i>', parse_mode='html', reply_markup=location_keyboard_with_back_to_card(section_key))
        user_location_data[chat_id] = {'location_msg_id': location_msg.message_id, 'text_msg_id': text_msg.message_id}
    else:
        bot.send_message(chat_id, '❌ Координаты для этой секции пока не добавлены', reply_markup=location_keyboard_with_back_to_card(section_key))

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_card_'))
def back_to_card(call):
    section_key = call.data.replace('back_to_card_', '')
    chat_id = call.message.chat.id
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    if chat_id in user_location_data:
        try:
            bot.delete_message(chat_id, user_location_data[chat_id]['location_msg_id'])
        except:
            pass
        try:
            bot.delete_message(chat_id, user_location_data[chat_id]['text_msg_id'])
        except:
            pass
        del user_location_data[chat_id]
    text = get_section_card_text(section_key)
    bot.send_message(chat_id, text, parse_mode='html', reply_markup=section_keyboard(section_key))

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_list_'))
def back_to_list(call):
    chat_id = call.message.chat.id
    if chat_id in user_location_data:
        try:
            bot.delete_message(chat_id, user_location_data[chat_id]['location_msg_id'])
        except:
            pass
        try:
            bot.delete_message(chat_id, user_location_data[chat_id]['text_msg_id'])
        except:
            pass
        del user_location_data[chat_id]
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    section_key = call.data.split('_', 3)[3]
    if section_key.startswith('football'):
        show_football_list(chat_id)
    elif section_key.startswith('hockey'):
        show_hockey_list(chat_id)
    elif section_key.startswith('basketball'):
        show_basketball_list(chat_id)
    elif section_key.startswith('boxing'):
        show_boxing_list(chat_id)
    else:
        start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main(call):
    if call.message.chat.id in user_location_data:
        del user_location_data[call.message.chat.id]
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    get_user(call.from_user.id, call.from_user.username, call.from_user.first_name)
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Футбол⚽️', callback_data='btn1')
    btn2 = types.InlineKeyboardButton(text='Хоккей🏒', callback_data='btn2')
    btn3 = types.InlineKeyboardButton(text='Баскетбол🏀', callback_data='btn3')
    btn4 = types.InlineKeyboardButton(text='Бокс🥊', callback_data='btn4')
    btn5 = types.InlineKeyboardButton(text='Гандбол🤾', callback_data='btn5')
    kb.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(
        call.message.chat.id,
        '<b>Добро пожаловать! Я предоставлю тебе всю информацию о спортивных секциях в Тольятти!</b>\n\n<i>Выбери, о какой хочешь узнать:</i>',
        parse_mode='html',
        reply_markup=kb
    )

# ==================== ОТЗЫВ В ОДНОМ СООБЩЕНИИ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def ask_review(call):
    section_key = call.data.split('_', 1)[1]
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    user_review_state[call.message.chat.id] = section_key
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'cancel_review_{section_key}'))
    
    msg = bot.send_message(
        call.message.chat.id,
        f'📝 Напишите ваш отзыв и оценку (1-5) в одном сообщении.\n\n<b>Пример:</b> "Отличная секция! (5)"',
        parse_mode='html',
        reply_markup=kb
    )
    bot.register_next_step_handler(msg, save_review_with_rating, section_key)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_review_'))
def cancel_review(call):
    section_key = call.data.split('_', 2)[2]
    chat_id = call.message.chat.id
    
    bot.delete_message(chat_id, call.message.message_id)
    
    if chat_id in user_review_state:
        del user_review_state[chat_id]
    
    text = get_section_card_text(section_key)
    bot.send_message(chat_id, text, parse_mode='html', reply_markup=section_keyboard(section_key))

def save_review_with_rating(message, section_key):
    text = message.text
    
    # Парсим оценку из текста
    match = re.search(r'\((\d)\)', text)
    if match:
        rating = int(match.group(1))
        comment = text.replace(f'({rating})', '').strip()
    else:
        match2 = re.search(r'(\d)$', text)
        if match2 and int(match2.group(1)) in range(1, 6):
            rating = int(match2.group(1))
            comment = text.replace(str(rating), '').strip()
        else:
            bot.send_message(
                message.chat.id,
                '❌ Не удалось найти оценку (1-5). Напишите отзыв с оценкой, например:\n"Отличная секция! (5)"'
            )
            return
    
    # Удаляем сообщения
    try:
        bot.delete_message(message.chat.id, message.message_id - 1)
    except:
        pass
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    result = save_review_to_db(section_key, message.from_user.id, rating, comment)
    
    if message.chat.id in user_review_state:
        del user_review_state[message.chat.id]
    
    if result == 'updated':
        text = f'✅ Ваш отзыв обновлён! (⭐ {rating})\n\n{get_section_card_text(section_key)}'
    else:
        text = f'✅ Спасибо за ваш отзыв! (⭐ {rating})\n\n{get_section_card_text(section_key)}'
    
    bot.send_message(
        message.chat.id,
        text,
        parse_mode='html',
        reply_markup=section_keyboard(section_key)
    )

# ==================== ВСЕ ОТЗЫВЫ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_reviews_'))
def view_reviews(call):
    section_key = call.data.replace('view_reviews_', '')
    reviews = get_reviews(section_key)
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if not reviews:
        text = '📖 Пока нет отзывов. Будьте первым!'
    else:
        text = '📖 <b>Отзывы:</b>\n\n'
        for rev in reviews:
            text += f'⭐ {rev["rating"]} — {rev["comment"]}\n\n'
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text='🔙 Назад к карточке', callback_data=f'back_to_card_{section_key}'))
    bot.send_message(call.message.chat.id, text, parse_mode='html', reply_markup=kb)

# ==================== АДМИН-ПАНЕЛЬ ====================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT section_key FROM admins WHERE telegram_id = ?", (user_id,))
    admin = cur.fetchone()
    conn.close()
    
    if not admin:
        bot.send_message(message.chat.id, '❌ У вас нет прав администратора.')
        return
    
    section_key = admin[0]
    section = get_section_data(section_key)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('✏️ Редактировать название', callback_data=f'admin_edit_name_{section_key}'),
        types.InlineKeyboardButton('📍 Редактировать адрес', callback_data=f'admin_edit_address_{section_key}'),
        types.InlineKeyboardButton('📞 Редактировать телефон', callback_data=f'admin_edit_phone_{section_key}'),
        types.InlineKeyboardButton('🔗 Редактировать ссылку', callback_data=f'admin_edit_link_{section_key}'),
        types.InlineKeyboardButton('📊 Статистика секции', callback_data=f'admin_stats_{section_key}'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    
    bot.send_message(
        message.chat.id,
        f'👑 <b>Панель администратора</b>\n\n<i>Вы управляете секцией:</i>\n<b>{section["name"]}</b>',
        parse_mode='html',
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_edit_name_'))
def admin_edit_name(call):
    section_key = call.data.replace('admin_edit_name_', '')
    user_review_state[call.message.chat.id] = f'edit_name_{section_key}'
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'admin_back_{section_key}'))
    
    bot.edit_message_text(
        '📝 Введите новое название секции:',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_edit_address_'))
def admin_edit_address(call):
    section_key = call.data.replace('admin_edit_address_', '')
    user_review_state[call.message.chat.id] = f'edit_address_{section_key}'
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'admin_back_{section_key}'))
    
    bot.edit_message_text(
        '📍 Введите новый адрес секции:',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_edit_phone_'))
def admin_edit_phone(call):
    section_key = call.data.replace('admin_edit_phone_', '')
    user_review_state[call.message.chat.id] = f'edit_phone_{section_key}'
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'admin_back_{section_key}'))
    
    bot.edit_message_text(
        '📞 Введите новый телефон секции:',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_edit_link_'))
def admin_edit_link(call):
    section_key = call.data.replace('admin_edit_link_', '')
    user_review_state[call.message.chat.id] = f'edit_link_{section_key}'
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'admin_back_{section_key}'))
    
    bot.edit_message_text(
        '🔗 Введите новую ссылку секции:',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

@bot.message_handler(func=lambda message: message.chat.id in user_review_state)
def save_admin_edit(message):
    state = user_review_state[message.chat.id]
    parts = state.split('_', 2)
    action = parts[0] + '_' + parts[1]
    section_key = parts[2]
    
    new_value = message.text
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if action == 'edit_name':
        cur.execute("UPDATE sections SET name = ? WHERE key = ?", (new_value, section_key))
    elif action == 'edit_address':
        cur.execute("UPDATE sections SET address = ? WHERE key = ?", (new_value, section_key))
    elif action == 'edit_phone':
        cur.execute("UPDATE sections SET phone = ? WHERE key = ?", (new_value, section_key))
    elif action == 'edit_link':
        cur.execute("UPDATE sections SET link = ? WHERE key = ?", (new_value, section_key))
    
    conn.commit()
    conn.close()
    
    del user_review_state[message.chat.id]
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад в панель', callback_data=f'admin_back_{section_key}'))
    
    bot.send_message(
        message.chat.id,
        f'✅ Данные обновлены!\n\n{get_section_card_text(section_key)}',
        parse_mode='html',
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_stats_'))
def admin_stats(call):
    section_key = call.data.replace('admin_stats_', '')
    
    reviews = get_reviews(section_key)
    rating_data = get_section_rating(section_key)
    
    text = f'📊 <b>Статистика секции</b>\n\n'
    text += f'⭐ Средний рейтинг: {rating_data["rating"]:.1f}\n'
    text += f'📝 Всего отзывов: {rating_data["count"]}\n\n'
    text += f'📖 <b>Последние отзывы:</b>\n'
    
    if reviews:
        for rev in reviews[:3]:
            text += f'⭐ {rev["rating"]} — {rev["comment"]}\n'
    else:
        text += 'Пока нет отзывов.'
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔙 Назад в панель', callback_data=f'admin_back_{section_key}'))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='html',
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_back_'))
def admin_back(call):
    section_key = call.data.replace('admin_back_', '')
    
    section = get_section_data(section_key)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('✏️ Редактировать название', callback_data=f'admin_edit_name_{section_key}'),
        types.InlineKeyboardButton('📍 Редактировать адрес', callback_data=f'admin_edit_address_{section_key}'),
        types.InlineKeyboardButton('📞 Редактировать телефон', callback_data=f'admin_edit_phone_{section_key}'),
        types.InlineKeyboardButton('🔗 Редактировать ссылку', callback_data=f'admin_edit_link_{section_key}'),
        types.InlineKeyboardButton('📊 Статистика секции', callback_data=f'admin_stats_{section_key}'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    
    bot.edit_message_text(
        f'👑 <b>Панель администратора</b>\n\n<i>Вы управляете секцией:</i>\n<b>{section["name"]}</b>',
        call.message.chat.id,
        call.message.message_id,
        parse_mode='html',
        reply_markup=kb
    )

# ==================== ОСНОВНОЙ ОБРАБОТЧИК ====================

@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    if callback.message:
        if callback.data == 'btn1':
            show_football_list(callback.message.chat.id, callback.message.message_id)
        elif callback.data == 'btn1_konoplev':
            text = get_section_card_text('football_konoplev')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_konoplev'))
        elif callback.data == 'btn1_lada':
            text = get_section_card_text('football_lada')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_lada'))
        elif callback.data == 'btn1_spartak':
            text = get_section_card_text('football_spartak')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_spartak'))
        elif callback.data == 'btn1_galacticos':
            text = get_section_card_text('football_galacticos')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_galacticos'))
        elif callback.data == 'btn1_impuls':
            text = get_section_card_text('football_impuls')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_impuls'))
        elif callback.data == 'btn1_athletic':
            text = get_section_card_text('football_athletic')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_athletic'))
        elif callback.data == 'btn2':
            show_hockey_list(callback.message.chat.id, callback.message.message_id)
        elif callback.data == 'btn2_flypro':
            text = get_section_card_text('hockey_flypro')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('hockey_flypro'))
        elif callback.data == 'btn2_lada':
            text = get_section_card_text('hockey_lada')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('hockey_lada'))
        elif callback.data == 'btn2_volgar':
            text = get_section_card_text('hockey_volgar')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('hockey_volgar'))
        elif callback.data == 'btn3':
            show_basketball_list(callback.message.chat.id, callback.message.message_id)
        elif callback.data == 'btn3_redwings':
            text = get_section_card_text('basketball_redwings')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('basketball_redwings'))
        elif callback.data == 'btn3_phoenix':
            text = get_section_card_text('basketball_phoenix')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('basketball_phoenix'))
        elif callback.data == 'btn4':
            show_boxing_list(callback.message.chat.id, callback.message.message_id)
        elif callback.data == 'btn4_lotus':
            text = get_section_card_text('boxing_lotus')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('boxing_lotus'))
        elif callback.data == 'btn4_vlasov':
            text = get_section_card_text('boxing_vlasov')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('boxing_vlasov'))
        elif callback.data == 'btn4_gaidarovets':
            text = get_section_card_text('boxing_gaidarovets')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('boxing_gaidarovets'))
        elif callback.data == 'btn5':
            text = get_section_card_text('handball_lada')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('handball_lada'))

@bot.message_handler(content_types=['voice', 'photo', 'video'])
def handle_media(message):
    bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')

@bot.message_handler(func=lambda message: True)
def main(message):
    if message.text and message.text.lower() == "привет":
        bot.send_message(message.chat.id, 'Привет! Воспользуйся подсказкой в меню 👇')
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')

if __name__ == '__main__':
    print('🚀 Бот запущен!')
    bot.polling(none_stop=True)
