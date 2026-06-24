import telebot
from telebot import types
import requests
import os

# ==== УБИРАЕМ ПРОКСИ ====
os.environ['NO_PROXY'] = 'api.telegram.org'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

# ==== СОЗДАЁМ БОТА ====
bot = telebot.TeleBot('6059734363:AAEPa7yL052gvPAOQEA22EaNP-_2T2Yy7Yg')

# ==== ЧИСТИМ СЕССИЮ ОТ ПРОКСИ ====
session = requests.Session()
session.proxies = {}
session.verify = True
bot.session = session

# ДАЛЬШЕ ВЕСЬ ОСТАЛЬНОЙ КОД...

# Глобальные словари
user_location_data = {}
user_review_state = {}
user_rating_state = {}

# ==== ВРЕМЕННОЕ ХРАНИЛИЩЕ (ПОКА БЕЗ БД) ====
reviews_db = {
    'football_konoplev': {'rating': 4.5, 'count': 12, 'reviews': ['Отличная академия!', 'Тренеры супер!']},
    'football_lada': {'rating': 4.2, 'count': 8, 'reviews': ['Хорошая школа', 'Ребёнок доволен']},
    'football_spartak': {'rating': 3.8, 'count': 5, 'reviews': ['Неплохо, но есть нюансы']},
    'football_galacticos': {'rating': 4.0, 'count': 6, 'reviews': ['Очень круто!']},
    'football_impuls': {'rating': 4.7, 'count': 15, 'reviews': ['Лучшая школа в городе!']},
    'football_athletic': {'rating': 3.5, 'count': 3, 'reviews': ['Хороший коллектив']},
    'hockey_flypro': {'rating': 4.3, 'count': 7, 'reviews': ['Отличная школа!']},
    'hockey_lada': {'rating': 4.8, 'count': 20, 'reviews': ['Супер!']},
    'hockey_volgar': {'rating': 4.0, 'count': 4, 'reviews': ['Хорошая школа']},
    'basketball_redwings': {'rating': 4.1, 'count': 9, 'reviews': ['Крутые тренеры']},
    'basketball_phoenix': {'rating': 3.9, 'count': 6, 'reviews': ['Неплохо']},
    'boxing_lotus': {'rating': 4.6, 'count': 11, 'reviews': ['Отличный зал!']},
    'boxing_vlasov': {'rating': 4.4, 'count': 8, 'reviews': ['Тренер профи!']},
    'boxing_gaidarovets': {'rating': 4.2, 'count': 5, 'reviews': ['Хорошая атмосфера']},
    'handball_lada': {'rating': 4.9, 'count': 25, 'reviews': ['Чемпионская школа!']},
}

# ==================== КООРДИНАТЫ ДЛЯ ГЕОЛОКАЦИИ ====================
locations = {
    'football_konoplev': (53.4805, 49.3874),
    'football_lada': (53.5078, 49.4203),
    'football_spartak': (53.5142, 49.4251),
    'football_galacticos': (53.5200, 49.4000),
    'football_impuls': (53.4900, 49.4100),
    'football_athletic': (53.5000, 49.4300),
    'hockey_flypro': (53.5100, 49.4400),
    'hockey_lada': (53.5300, 49.3800),
    'hockey_volgar': (53.5400, 49.3600),
    'basketball_redwings': (53.5000, 49.4500),
    'basketball_phoenix': (53.4800, 49.4600),
    'boxing_lotus': (53.5200, 49.3900),
    'boxing_vlasov': (53.4900, 49.4200),
    'boxing_gaidarovets': (53.4700, 49.4300),
    'handball_lada': (53.5300, 49.3500),
}

# ==================== СЛОВАРЬ С ТЕКСТАМИ СЕКЦИЙ ====================
section_texts = {
    'football_konoplev': ('⚽️ Академия футбола им.Юрия Коноплёва',
                          '📍 Советская, 23б\n📞 +78482559115 +78482559116\n🔗 https://vk.com/konoplev_academy'),
    'football_lada': ('⚽️ Футбольная школа "Лада"',
                      '📍 Юбилейная, 6б (комплекс Спутник)\n📍 Революционная, 80 (Стадион Торпедо)\n📞 +78482371068 +78482580952\n🔗 https://vk.com/public191471116'),
    'football_spartak': ('⚽️ Футбольная школа "Спартак Юниор"',
                         '📍 Южное шоссе, 2\n📞 +78003010293 +79372123202\n🔗 https://vk.com/fsspartak_tlt'),
    'football_galacticos': ('⚽️ Футбольная школа "Галактикос"',
                            '📍 Тополиная, 5\n📍 Автостроителей, 84 (Школа №66)\n📍 Бульвар Туполева, 12 (Школа №47)\n📍 Бульвар Королёва, 3 (Школа им. Королёва)\n📍 Степана Разина, 78 (Лицей №76)\n📞 +79278922080 +78482341015\n🔗 https://vk.com/fs_galacticos'),
    'football_impuls': ('⚽️ Футбольная школа "Импульс"',
                        '📍 Цветной бульвар, 13 (Школа №82)\n📍 Тополиная, 18 (Школа №90)\n📍 Бульвар Татищева, 19 (Школа №90)\n📍 Бульвар Космонавтов, 17 (Школа №79)\n📍 40 лет Победы, 74 (Школа №70)\n📍 40 лет Победы, 86 (Школа №70)\n📞 +79608460989 +78482409350\n🔗 https://vk.com/fc.impuls'),
    'football_athletic': ('⚽️ Футбольная школа "Athletic football"',
                          '📍 Бульвар Луначарского, 11 (Школа №71)\n📍 Свердлова, 23 (Школа №61)\n📞 +79277851389 +78482326450\n🔗 https://vk.com/athletic_football'),

    'hockey_flypro': (
    '🏒 Хоккейная школа "Fly pro"', '📍 40 лет Победы, 14\n📞 +79276163714\n🔗 https://vk.com/flyagin_school'),
    'hockey_lada': ('🏒 Хоккейная школа "Лада"', '📍 Ботаническая, 5\n📞 +78482526840\n🔗 https://vk.com/lada.arena'),
    'hockey_volgar': ('🏒 Хоккейная школа "Волгарь"',
                      '📍 Приморский бульвар, 37\n📍 Баныкина, 9 (Стадион Кристалл)\n📞 +78482347692\n🔗 https://vk.com/volgar_tlt'),

    'basketball_redwings': ('🏀 Баскетбольная школа "Красные крылья"',
                            '📍 Цветной бульвар, 18 (Школа №84)\n📍 40 лет Победы, 106 (Школа №81)\n📞 +78482692388 +78482692377\n🔗 https://vk.com/tltredwings'),
    'basketball_phoenix': ('🏀 Баскетбольная школа "Феникс"',
                           '📍 Фрунзе, 2г (ТГУ)\n📍 Белорусская, 6а (ВУиТ)\n📞 +79272110533\n🔗 https://vk.com/basketboltlt'),

    'boxing_lotus': (
    '🥊 "Lotusport\'s club r home"', '📍 Тополиная, 18 (Школа №90)\n📞 +79277766212\n🔗 https://vk.com/lsc63'),
    'boxing_vlasov': ('🥊 "Школа бокса им. МСМК Игоря Власова"',
                      '📍 Цветной бульвар, 18 (Школа №84)\n📞 +79277887611 +79272185339\n🔗 https://vk.com/vlasovboxing'),
    'boxing_gloves': (
    '🥊 "Боевые перчатки"', '📍 Ворошилова, 21 (Школа №74)\n📞 +78482429405\n🔗 https://vk.com/public204222709'),
    'boxing_arsenal': (
    '🥊 "Arsenal fighting"', '📍 Бульвар Кулибина, 15\n📞 +79277855553\n🔗 https://vk.com/arsenalfighting'),
    'boxing_gaidarovets': ('🥊 "Гайдаровец"', '📍 Фрунзе, 35\n📞 +79272116655\n🔗 https://vk.com/tolyattiboxing'),
    'boxing_pobeda': (
    '🥊 "Победа-спорт"', '📍 Маршала Жукова, 26\n📞 +78482417363 +78482290002\n🔗 https://vk.com/ksepobeda'),
    'boxing_school': ('🥊 "Школа бокса"',
                      '📍 Юбилейная, 81 (Школа №73)\n📍 Приморский бульвар, 37 (Волгарь)\n📞 +7848703455 +78482707450\n🔗 https://vk.com/boxingschool163'),
    'boxing_albasport': ('🥊 "Albasport"', '📍 Фермерская, 1а/1\n📞 +78482580101\n🔗 https://vk.com/albasport63'),

    'handball_lada': ('🤾 Гандбольный клуб "Лада"',
                      '📍 Приморский бульвар, 49 (Олимп)\n📍 Бульвар Татищева, 19\n📍 40 лет Победы, 74\n📍 Ворошилова, 21\n📞 +78482357963 +78482355394 +79277800042\n🔗 https://vk.com/public157271429'),
}


def format_rating(section_key):
    data = reviews_db.get(section_key, {'rating': 0, 'count': 0})
    rating = data['rating']
    count = data['count']
    if count == 0:
        return '⭐ Нет оценок'
    stars = '⭐' * int(round(rating)) + '☆' * (5 - int(round(rating)))
    return f'{stars} {rating:.1f} ({count} оценок)'


# ==================== НОВАЯ ФУНКЦИЯ ДЛЯ КАРТОЧКИ ====================
def get_section_card_text(section_key):
    """Возвращает полный текст карточки секции с рейтингом внизу"""
    name, info = section_texts.get(section_key, ('Секция', ''))
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


# ==================== ФУНКЦИИ ДЛЯ ПОКАЗА СПИСКОВ ШКОЛ ====================

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
        bot.edit_message_text(
            '⚽️ <b>Выбери футбольную школу:</b>',
            chat_id,
            message_id,
            parse_mode='html',
            reply_markup=kb
        )
    else:
        bot.send_message(
            chat_id,
            '⚽️ <b>Выбери футбольную школу:</b>',
            parse_mode='html',
            reply_markup=kb
        )


def show_hockey_list(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('🏒 Fly pro', callback_data='btn2_flypro'),
        types.InlineKeyboardButton('🏒 Лада', callback_data='btn2_lada'),
        types.InlineKeyboardButton('🏒 Волгарь', callback_data='btn2_volgar'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    if message_id:
        bot.edit_message_text(
            '🏒 <b>Выбери хоккейную школу:</b>',
            chat_id,
            message_id,
            parse_mode='html',
            reply_markup=kb
        )
    else:
        bot.send_message(
            chat_id,
            '🏒 <b>Выбери хоккейную школу:</b>',
            parse_mode='html',
            reply_markup=kb
        )


def show_basketball_list(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('🏀 Красные крылья', callback_data='btn3_redwings'),
        types.InlineKeyboardButton('🏀 Феникс', callback_data='btn3_phoenix'),
        types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
    )
    if message_id:
        bot.edit_message_text(
            '🏀 <b>Выбери баскетбольную школу:</b>',
            chat_id,
            message_id,
            parse_mode='html',
            reply_markup=kb
        )
    else:
        bot.send_message(
            chat_id,
            '🏀 <b>Выбери баскетбольную школу:</b>',
            parse_mode='html',
            reply_markup=kb
        )


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
        bot.edit_message_text(
            '🥊 <b>Выбери школу бокса:</b>',
            chat_id,
            message_id,
            parse_mode='html',
            reply_markup=kb
        )
    else:
        bot.send_message(
            chat_id,
            '🥊 <b>Выбери школу бокса:</b>',
            parse_mode='html',
            reply_markup=kb
        )


# ==================== ОБРАБОТЧИК ГЕОЛОКАЦИИ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('map_'))
def send_location(call):
    chat_id = call.message.chat.id
    section_key = call.data.replace('map_', '')

    bot.delete_message(chat_id, call.message.message_id)

    if section_key in locations:
        lat, lon = locations[section_key]
        location_msg = bot.send_location(chat_id, latitude=lat, longitude=lon)
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


# ==================== ОБРАБОТЧИК ВОЗВРАТА К КАРТОЧКЕ ====================

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

    if section_key not in section_texts:
        bot.send_message(chat_id, '❌ Секция не найдена')
        start(call.message)
        return

    text = get_section_card_text(section_key)
    bot.send_message(
        chat_id,
        text,
        parse_mode='html',
        reply_markup=section_keyboard(section_key)
    )


# ==================== ОБРАБОТЧИК КНОПКИ "НАЗАД К СПИСКУ" ====================

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


# ==================== ОБРАБОТЧИК КНОПКИ "НАЗАД В ГЛАВНОЕ МЕНЮ" ====================

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main(call):
    if call.message.chat.id in user_location_data:
        del user_location_data[call.message.chat.id]
    start(call.message)


# ==================== ОБРАБОТЧИКИ РЕЙТИНГА ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def handle_rating(call):
    section_key = call.data.split('_', 1)[1]

    user_rating_state[call.message.chat.id] = section_key

    kb = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(str(i), callback_data=f'setrate_{section_key}_{i}') for i in range(1, 6)]
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton('❌ Отмена', callback_data='cancel_rate'))

    bot.edit_message_text(
        f'⭐ Оцените секцию (1-5):',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('setrate_'))
def set_rating(call):
    parts = call.data.split('_')
    section_key = '_'.join(parts[1:-1])
    rating = int(parts[-1])

    data = reviews_db.get(section_key, {'rating': 0, 'count': 0, 'reviews': []})
    total = data['rating'] * data['count'] + rating
    data['count'] += 1
    data['rating'] = round(total / data['count'], 1)
    reviews_db[section_key] = data

    bot.delete_message(call.message.chat.id, call.message.message_id)

    text = f'✅ Спасибо за оценку {rating}⭐!\n\n{get_section_card_text(section_key)}'

    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode='html',
        reply_markup=section_keyboard(section_key)
    )


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_rate')
def cancel_rate(call):
    chat_id = call.message.chat.id

    bot.delete_message(chat_id, call.message.message_id)

    if chat_id in user_rating_state:
        section_key = user_rating_state[chat_id]
        del user_rating_state[chat_id]

        text = get_section_card_text(section_key)
        bot.send_message(
            chat_id,
            text,
            parse_mode='html',
            reply_markup=section_keyboard(section_key)
        )
    else:
        start(call.message)


# ==================== ОБРАБОТЧИКИ ОТЗЫВОВ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def ask_review(call):
    section_key = call.data.split('_', 1)[1]

    bot.delete_message(call.message.chat.id, call.message.message_id)

    user_review_state[call.message.chat.id] = section_key

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙 Назад', callback_data=f'cancel_review_{section_key}'))

    bot.send_message(
        call.message.chat.id,
        f'📝 Напишите ваш отзыв о секции:',
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_review_'))
def cancel_review(call):
    section_key = call.data.split('_', 2)[2]

    bot.delete_message(call.message.chat.id, call.message.message_id)

    if call.message.chat.id in user_review_state:
        del user_review_state[call.message.chat.id]

    text = get_section_card_text(section_key)
    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode='html',
        reply_markup=section_keyboard(section_key)
    )


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

    data = reviews_db.get(section_key, {'rating': 0, 'count': 0, 'reviews': []})
    data['reviews'].append(review_text)
    reviews_db[section_key] = data

    if message.chat.id in user_review_state:
        del user_review_state[message.chat.id]

    text = f'✅ Спасибо за отзыв! ({len(data["reviews"])} всего)\n\n{get_section_card_text(section_key)}'

    bot.send_message(
        message.chat.id,
        text,
        parse_mode='html',
        reply_markup=section_keyboard(section_key)
    )


# ==================== ОБРАБОТЧИК ВСЕХ ОТЗЫВОВ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_reviews_'))
def view_reviews(call):
    section_key = call.data.replace('view_reviews_', '')

    data = reviews_db.get(section_key, {'reviews': []})
    reviews = data['reviews']

    bot.delete_message(call.message.chat.id, call.message.message_id)

    if not reviews:
        text = '📖 Пока нет отзывов. Будьте первым!'
    else:
        text = '📖 <b>Отзывы:</b>\n\n'
        for i, rev in enumerate(reviews[-5:], 1):
            text += f'{i}. {rev}\n\n'

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text='🔙 Назад к карточке', callback_data=f'back_to_card_{section_key}'))

    bot.send_message(
        call.message.chat.id,
        text,
        parse_mode='html',
        reply_markup=kb
    )


# ==================== ОСНОВНОЙ ОБРАБОТЧИК КНОПОК ====================

@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    if callback.message:
        # ==================== ФУТБОЛ ====================
        if callback.data == 'btn1':
            show_football_list(callback.message.chat.id, callback.message.message_id)
            return

        elif callback.data == 'btn1_konoplev':
            text = get_section_card_text('football_konoplev')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('football_konoplev')
            )
            return

        elif callback.data == 'btn1_lada':
            text = get_section_card_text('football_lada')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('football_lada')
            )
            return

        elif callback.data == 'btn1_spartak':
            text = get_section_card_text('football_spartak')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('football_spartak')
            )
            return

        elif callback.data == 'btn1_galacticos':
            text = get_section_card_text('football_galacticos')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('football_galacticos')
            )
            return

        elif callback.data == 'btn1_impuls':
            text = get_section_card_text('football_impuls')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('football_impuls')
            )
            return

        elif callback.data == 'btn1_athletic':
            text = get_section_card_text('football_athletic')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('football_athletic')
            )
            return

        # ==================== ХОККЕЙ ====================
        elif callback.data == 'btn2':
            show_hockey_list(callback.message.chat.id, callback.message.message_id)
            return

        elif callback.data == 'btn2_flypro':
            text = get_section_card_text('hockey_flypro')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('hockey_flypro')
            )
            return

        elif callback.data == 'btn2_lada':
            text = get_section_card_text('hockey_lada')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('hockey_lada')
            )
            return

        elif callback.data == 'btn2_volgar':
            text = get_section_card_text('hockey_volgar')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('hockey_volgar')
            )
            return

        # ==================== БАСКЕТБОЛ ====================
        elif callback.data == 'btn3':
            show_basketball_list(callback.message.chat.id, callback.message.message_id)
            return

        elif callback.data == 'btn3_redwings':
            text = get_section_card_text('basketball_redwings')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('basketball_redwings')
            )
            return

        elif callback.data == 'btn3_phoenix':
            text = get_section_card_text('basketball_phoenix')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('basketball_phoenix')
            )
            return

        # ==================== БОКС ====================
        elif callback.data == 'btn4':
            show_boxing_list(callback.message.chat.id, callback.message.message_id)
            return

        elif callback.data == 'btn4_lotus':
            text = get_section_card_text('boxing_lotus')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('boxing_lotus')
            )
            return

        elif callback.data == 'btn4_vlasov':
            text = get_section_card_text('boxing_vlasov')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('boxing_vlasov')
            )
            return

        elif callback.data == 'btn4_gaidarovets':
            text = get_section_card_text('boxing_gaidarovets')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('boxing_gaidarovets')
            )
            return

        # ==================== ГАНДБОЛ ====================
        elif callback.data == 'btn5':
            text = get_section_card_text('handball_lada')
            bot.edit_message_text(
                text,
                callback.message.chat.id,
                callback.message.message_id,
                parse_mode='html',
                reply_markup=section_keyboard('handball_lada')
            )
            return


# ==================== ОБРАБОТЧИКИ МЕДИА И ТЕКСТА ====================

@bot.message_handler(content_types=['voice'])
def voice(message):
    bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')


@bot.message_handler(content_types=['photo'])
def photo(message):
    bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')


@bot.message_handler(content_types=['video'])
def video(message):
    bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')


@bot.message_handler(func=lambda message: True)
def main(message):
    if message.text and message.text.lower() == "привет":
        bot.send_message(message.chat.id, 'Привет! Воспользуйся подсказкой в меню 👇')
    elif message.text and message.text.startswith('/'):
        pass
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю, воспользуйся подсказкой в меню 👇')


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('🚀 Бот запущен!')
    bot.polling(none_stop=True, timeout=120)