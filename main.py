import telebot
from telebot import types
import os
import psycopg2
import psycopg2.extras
import time

# ==== ПОДКЛЮЧЕНИЕ К БД (SUPABASE) ====
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print('❌ Ошибка: DATABASE_URL не задан!')
    exit(1)

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    except Exception as e:
        print(f'❌ Ошибка подключения к БД: {e}')
        return None

def init_db():
    print('🔄 Инициализация базы данных...')
    conn = get_db_connection()
    if not conn:
        print('❌ Не удалось подключиться к БД')
        return
    
    cur = conn.cursor()
    
    try:
        # Таблица секций
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sections (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                link TEXT,
                lat REAL,
                lon REAL
            )
        ''')
        
        # Таблица пользователей
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица отзывов
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                section_key TEXT REFERENCES sections(key) ON DELETE CASCADE,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                rating INTEGER CHECK (rating >= 0 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(section_key, user_id)
            )
        ''')
        
        # Таблица администраторов
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                section_key TEXT UNIQUE NOT NULL REFERENCES sections(key) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        print('✅ База данных инициализирована!')
        
        # Добавляем секции, если их нет
        add_default_sections()
        
    except Exception as e:
        print(f'❌ Ошибка при создании таблиц: {e}')
        conn.close()

def add_default_sections():
    conn = get_db_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    
    # Проверяем, есть ли уже секции
    cur.execute("SELECT COUNT(*) FROM sections")
    count = cur.fetchone()['count']
    
    if count > 0:
        conn.close()
        return
    
    # Добавляем секции
    sections = [
        ('football_konoplev', 'Академия футбола им.Юрия Коноплёва', 'Советская, 23б', '+78482559115 +78482559116', 'https://vk.com/konoplev_academy', 53.4805, 49.3874),
        ('football_lada', 'Футбольная школа "Лада"', 'Юбилейная, 6б (комплекс Спутник)\nРеволюционная, 80 (Стадион Торпедо)', '+78482371068 +78482580952', 'https://vk.com/public191471116', 53.5078, 49.4203),
        ('football_spartak', 'Футбольная школа "Спартак Юниор"', 'Южное шоссе, 2', '+78003010293 +79372123202', 'https://vk.com/fsspartak_tlt', 53.5142, 49.4251),
        ('football_galacticos', 'Футбольная школа "Галактикос"', 'Тополиная, 5\nАвтостроителей, 84 (Школа №66)\nБульвар Туполева, 12 (Школа №47)\nБульвар Королёва, 3 (Школа им. Королёва)\nСтепана Разина, 78 (Лицей №76)', '+79278922080 +78482341015', 'https://vk.com/fs_galacticos', 53.5200, 49.4000),
        ('football_impuls', 'Футбольная школа "Импульс"', 'Цветной бульвар, 13 (Школа №82)\nТополиная, 18 (Школа №90)\nБульвар Татищева, 19 (Школа №90)\nБульвар Космонавтов, 17 (Школа №79)\n40 лет Победы, 74 (Школа №70)\n40 лет Победы, 86 (Школа №70)', '+79608460989 +78482409350', 'https://vk.com/fc.impuls', 53.4900, 49.4100),
        ('football_athletic', 'Футбольная школа "Athletic football"', 'Бульвар Луначарского, 11 (Школа №71)\nСвердлова, 23 (Школа №61)', '+79277851389 +78482326450', 'https://vk.com/athletic_football', 53.5000, 49.4300),
        ('hockey_flypro', 'Хоккейная школа "Fly pro"', '40 лет Победы, 14', '+79276163714', 'https://vk.com/flyagin_school', 53.5100, 49.4400),
        ('hockey_lada', 'Хоккейная школа "Лада"', 'Ботаническая, 5', '+78482526840', 'https://vk.com/lada.arena', 53.5300, 49.3800),
        ('hockey_volgar', 'Хоккейная школа "Волгарь"', 'Приморский бульвар, 37\nБаныкина, 9 (Стадион Кристалл)', '+78482347692', 'https://vk.com/volgar_tlt', 53.5400, 49.3600),
        ('basketball_redwings', 'Баскетбольная школа "Красные крылья"', 'Цветной бульвар, 18 (Школа №84)\n40 лет Победы, 106 (Школа №81)', '+78482692388 +78482692377', 'https://vk.com/tltredwings', 53.5000, 49.4500),
        ('basketball_phoenix', 'Баскетбольная школа "Феникс"', 'Фрунзе, 2г (ТГУ)\nБелорусская, 6а (ВУиТ)', '+79272110533', 'https://vk.com/basketboltlt', 53.4800, 49.4600),
        ('boxing_lotus', '"Lotusport\'s club r home"', 'Тополиная, 18 (Школа №90)', '+79277766212', 'https://vk.com/lsc63', 53.5200, 49.3900),
        ('boxing_vlasov', '"Школа бокса им. МСМК Игоря Власова"', 'Цветной бульвар, 18 (Школа №84)', '+79277887611 +79272185339', 'https://vk.com/vlasovboxing', 53.4900, 49.4200),
        ('boxing_gloves', '"Боевые перчатки"', 'Ворошилова, 21 (Школа №74)', '+78482429405', 'https://vk.com/public204222709', 53.5000, 49.4100),
        ('boxing_gaidarovets', '"Гайдаровец"', 'Фрунзе, 35', '+79272116655', 'https://vk.com/tolyattiboxing', 53.4700, 49.4300),
        ('boxing_pobeda', '"Победа-спорт"', 'Маршала Жукова, 26', '+78482417363 +78482290002', 'https://vk.com/ksepobeda', 53.4900, 49.4500),
        ('boxing_school', '"Школа бокса"', 'Юбилейная, 81 (Школа №73)\nПриморский бульвар, 37 (Волгарь)', '+7848703455 +78482707450', 'https://vk.com/boxingschool163', 53.5000, 49.4600),
        ('boxing_albasport', '"Albasport"', 'Фермерская, 1а/1', '+78482580101', 'https://vk.com/albasport63', 53.5100, 49.4700),
        ('handball_lada', 'Гандбольный клуб "Лада"', 'Приморский бульвар, 49 (Олимп)\nБульвар Татищева, 19\n40 лет Победы, 74\nВорошилова, 21', '+78482357963 +78482355394 +79277800042', 'https://vk.com/public157271429', 53.5300, 49.3500),
    ]
    
    for section in sections:
        cur.execute('''
            INSERT INTO sections (key, name, address, phone, link, lat, lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', section)
    
    conn.commit()
    conn.close()
    print(f'✅ Добавлено {len(sections)} секций в базу данных')

# ==== ИНИЦИАЛИЗАЦИЯ ПРИ ЗАПУСКЕ ====
init_db()

# ==== БОТ ====
TOKEN = os.getenv('TELEGRAM_TOKEN', '6059734363:AAEPa7yL052gvPAOQEA22EaNP-_2T2Yy7Yg')
bot = telebot.TeleBot(TOKEN)

# ==== ГЛОБАЛЬНЫЕ СЛОВАРИ ====
user_location_data = {}
user_review_state = {}
user_rating_state = {}

# ==== ФУНКЦИИ РАБОТЫ С БД ====

def get_section_data(section_key):
    conn = get_db_connection()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute("SELECT * FROM sections WHERE key = %s", (section_key,))
    result = cur.fetchone()
    conn.close()
    return result

def get_section_rating(section_key):
    conn = get_db_connection()
    if not conn:
        return {'rating': 0, 'count': 0}
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(AVG(rating), 0) as avg_rating, COUNT(*) as total_count FROM reviews WHERE section_key = %s AND rating > 0",
        (section_key,)
    )
    result = cur.fetchone()
    conn.close()
    return {'rating': result['avg_rating'] if result else 0, 'count': result['total_count'] if result else 0}

def save_review_to_db(section_key, user_id, rating, comment):
    conn = get_db_connection()
    if not conn:
        return False
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM reviews WHERE section_key = %s AND user_id = %s", (section_key, user_id))
    existing = cur.fetchone()
    if existing:
        conn.close()
        return 'duplicate'
    
    cur.execute(
        "INSERT INTO reviews (section_key, user_id, rating, comment) VALUES (%s, %s, %s, %s)",
        (section_key, user_id, rating, comment)
    )
    conn.commit()
    conn.close()
    return True

def get_reviews(section_key):
    conn = get_db_connection()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute(
        "SELECT rating, comment, user_id, created_at FROM reviews WHERE section_key = %s ORDER BY created_at DESC LIMIT 5",
        (section_key,)
    )
    results = cur.fetchall()
    conn.close()
    return results

def get_user(telegram_id, username=None, first_name=None):
    conn = get_db_connection()
    if not conn:
        return None
    cur = conn.cursor()
    cur.execute("SELECT id, telegram_id FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    if not user:
        cur.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (%s, %s, %s)",
            (telegram_id, username, first_name)
        )
        conn.commit()
        cur.execute("SELECT id, telegram_id FROM users WHERE telegram_id = %s", (telegram_id,))
        user = cur.fetchone()
    conn.close()
    return user

# ==== СЛОВАРЬ С ТЕКСТАМИ СЕКЦИЙ ====
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
    info = f"📍 {section['address']}\n📞 {section['phone']}\n🔗 {section['link']}"
    rating_text = format_rating(section_key)
    return f'<b>{name}</b>\n\n{info}\n\n{rating_text}'

def section_keyboard(section_key):
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(text='⭐ Оценить (1-5)', callback_data=f'rate_{section_key}')
    btn2 = types.InlineKeyboardButton(text='📝 Оставить отзыв', callback_data=f'review_{section_key}')
    btn3 = types.InlineKeyboardButton(text='📖 Все отзывы', callback_data=f'view_reviews_{section_key}')
    btn4 = types.InlineKeyboardButton(text='🗺️ Показать на карте', callback_data=f'map_{section_key}')
    btn5 = types.InlineKeyboardButton(text='🔙 Назад к списку', callback_data=f'back_to_list_{section_key}')
    kb.add(btn1, btn2, btn3, btn4, btn5)
    return kb

def location_keyboard_with_back_to_card(section_key):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text='🔙 Назад к карточке', callback_data=f'back_to_card_{section_key}'))
    return kb

@bot.message_handler(commands=['start', 'back'])
def start(message):
    get_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Футбол⚽️', callback_data='btn1')
    btn2 = types.InlineKeyboardButton(text='Хоккей🏒', callback_data='btn2')
    btn3 = types.InlineKeyboardButton(text='Баскетбол🏀', callback_data='btn3')
    btn4 = types.InlineKeyboardButton(text='Бокс🥊', callback_data='btn4')
    btn5 = types.InlineKeyboardButton(text='Гандбол🤾', callback_data='btn5')
    kb.add(btn1, btn2, btn3, btn4, btn5)

    try:
        bot.edit_message_text(
            '<b>Добро пожаловать! Я предоставлю тебе всю информацию о спортивных секциях в Тольятти!</b>\n\n<i>Выбери, о какой хочешь узнать:</i>',
            message.chat.id,
            message.message_id,
            parse_mode='html',
            reply_markup=kb
        )
    except:
        bot.send_message(
            message.chat.id,
            '<b>Добро пожаловать! Я предоставлю тебе всю информацию о спортивных секциях в Тольятти!</b>\n\n<i>Выбери, о какой хочешь узнать:</i>',
            parse_mode='html',
            reply_markup=kb
        )

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

@bot.callback_query_handler(func=lambda call: call.data.startswith('map_'))
def send_location(call):
    chat_id = call.message.chat.id
    section_key = call.data.replace('map_', '')
    section = get_section_data(section_key)
    
    bot.delete_message(chat_id, call.message.message_id)
    
    if section and section['lat'] and section['lon']:
        location_msg = bot.send_location(chat_id, latitude=section['lat'], longitude=section['lon'])
        text_msg = bot.send_message(
            chat_id,
            '📍 <i>Нажми на точку, чтобы проложить маршрут</i>',
            parse_mode='html',
            reply_markup=location_keyboard_with_back_to_card(section_key)
        )
        user_location_data[chat_id] = {
            'location_msg_id': location_msg.message_id,
            'text_msg_id': text_msg.message_id
        }
    else:
        bot.send_message(
            chat_id,
            '❌ Координаты для этой секции пока не добавлены',
            reply_markup=location_keyboard_with_back_to_card(section_key)
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_card_'))
def back_to_card(call):
    section_key = call.data.replace('back_to_card_', '')
    chat_id = call.message.chat.id

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

    if chat_id in user_location_data:
        data = user_location_data[chat_id]
        try:
            bot.delete_message(chat_id, data['location_msg_id'])
        except:
            pass
        try:
            bot.delete_message(chat_id, data['text_msg_id'])
        except:
            pass
        del user_location_data[chat_id]

    text = get_section_card_text(section_key)
    bot.send_message(chat_id, text, parse_mode='html', reply_markup=section_keyboard(section_key))

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_list_'))
def back_to_list(call):
    chat_id = call.message.chat.id

    if chat_id in user_location_data:
        data = user_location_data[chat_id]
        try:
            bot.delete_message(chat_id, data['location_msg_id'])
        except:
            pass
        try:
            bot.delete_message(chat_id, data['text_msg_id'])
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
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def handle_rating(call):
    section_key = call.data.split('_', 1)[1]
    user_rating_state[call.message.chat.id] = section_key
    
    kb = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(str(i), callback_data=f'setrate_{section_key}_{i}') for i in range(1, 6)]
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton('❌ Отмена', callback_data='cancel_rate'))
    bot.edit_message_text('⭐ Оцените секцию (1-5):', call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setrate_'))
def set_rating(call):
    parts = call.data.split('_')
    section_key = '_'.join(parts[1:-1])
    rating = int(parts[-1])
    
    result = save_review_to_db(section_key, call.from_user.id, rating, '')
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if result == 'duplicate':
        text = f'⚠️ Вы уже оценили эту секцию!\n\n{get_section_card_text(section_key)}'
    else:
        text = f'✅ Спасибо за оценку {rating}⭐!\n\n{get_section_card_text(section_key)}'
    
    bot.send_message(call.message.chat.id, text, parse_mode='html', reply_markup=section_keyboard(section_key))

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_rate')
def cancel_rate(call):
    chat_id = call.message.chat.id
    if chat_id in user_rating_state:
        section_key = user_rating_state[chat_id]
        del user_rating_state[chat_id]
        text = get_section_card_text(section_key)
        bot.send_message(chat_id, text, parse_mode='html', reply_markup=section_keyboard(section_key))
    else:
        start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def ask_review(call):
    section_key = call.data.split('_', 1)[1]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_review_state[call.message.chat.id] = section_key
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙 Назад', callback_data=f'cancel_review_{section_key}'))
    bot.send_message(call.message.chat.id, '📝 Напишите ваш отзыв о секции:', reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_review_'))
def cancel_review(call):
    section_key = call.data.split('_', 2)[2]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.message.chat.id in user_review_state:
        del user_review_state[call.message.chat.id]
    text = get_section_card_text(section_key)
    bot.send_message(call.message.chat.id, text, parse_mode='html', reply_markup=section_keyboard(section_key))

@bot.message_handler(func=lambda message: message.chat.id in user_review_state)
def handle_review_text(message):
    section_key = user_review_state[message.chat.id]
    review_text = message.text
    
    try:
        bot.delete_message(message.chat.id, message.message_id - 1)
    except:
        pass
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    result = save_review_to_db(section_key, message.from_user.id, 0, review_text)
    
    if message.chat.id in user_review_state:
        del user_review_state[message.chat.id]
    
    if result == 'duplicate':
        text = f'⚠️ Вы уже оставляли отзыв на эту секцию!\n\n{get_section_card_text(section_key)}'
    else:
        text = f'✅ Спасибо за отзыв!\n\n{get_section_card_text(section_key)}'
    
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=section_keyboard(section_key))

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

@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    if callback.message:
        if callback.data == 'btn1':
            show_football_list(callback.message.chat.id, callback.message.message_id)
            return
        elif callback.data == 'btn1_konoplev':
            text = get_section_card_text('football_konoplev')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_konoplev'))
            return
        elif callback.data == 'btn1_lada':
            text = get_section_card_text('football_lada')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_lada'))
            return
        elif callback.data == 'btn1_spartak':
            text = get_section_card_text('football_spartak')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_spartak'))
            return
        elif callback.data == 'btn1_galacticos':
            text = get_section_card_text('football_galacticos')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_galacticos'))
            return
        elif callback.data == 'btn1_impuls':
            text = get_section_card_text('football_impuls')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_impuls'))
            return
        elif callback.data == 'btn1_athletic':
            text = get_section_card_text('football_athletic')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('football_athletic'))
            return
        elif callback.data == 'btn2':
            show_hockey_list(callback.message.chat.id, callback.message.message_id)
            return
        elif callback.data == 'btn2_flypro':
            text = get_section_card_text('hockey_flypro')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('hockey_flypro'))
            return
        elif callback.data == 'btn2_lada':
            text = get_section_card_text('hockey_lada')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('hockey_lada'))
            return
        elif callback.data == 'btn2_volgar':
            text = get_section_card_text('hockey_volgar')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('hockey_volgar'))
            return
        elif callback.data == 'btn3':
            show_basketball_list(callback.message.chat.id, callback.message.message_id)
            return
        elif callback.data == 'btn3_redwings':
            text = get_section_card_text('basketball_redwings')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('basketball_redwings'))
            return
        elif callback.data == 'btn3_phoenix':
            text = get_section_card_text('basketball_phoenix')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('basketball_phoenix'))
            return
        elif callback.data == 'btn4':
            show_boxing_list(callback.message.chat.id, callback.message.message_id)
            return
        elif callback.data == 'btn4_lotus':
            text = get_section_card_text('boxing_lotus')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('boxing_lotus'))
            return
        elif callback.data == 'btn4_vlasov':
            text = get_section_card_text('boxing_vlasov')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('boxing_vlasov'))
            return
        elif callback.data == 'btn4_gaidarovets':
            text = get_section_card_text('boxing_gaidarovets')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('boxing_gaidarovets'))
            return
        elif callback.data == 'btn5':
            text = get_section_card_text('handball_lada')
            bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, parse_mode='html', reply_markup=section_keyboard('handball_lada'))
            return

@bot.message_handler(content_types=['voice', 'photo', 'video'])
def handle_media(message):
    bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')

@bot.message_handler(func=lambda message: True)
def main(message):
    if message.text and message.text.lower() == "привет":
        bot.send_message(message.chat.id, 'Привет! Воспользуйся подсказкой в меню 👇')
    elif message.text and message.text.startswith('/'):
        pass
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')

if __name__ == '__main__':
    print('🚀 Бот запущен!')
    bot.delete_webhook()
    bot.polling(none_stop=True)
