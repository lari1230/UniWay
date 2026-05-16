from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Мои предметы")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📝 Ежедневные задания")],
            [KeyboardButton(text="🎯 Практика по предметам")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_subjects_keyboard(selected_subjects):
    """Клавиатура выбора предметов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    subjects = {
        "math": "📐 Математика",
        "russian": "📖 Русский язык",
        "history": "🏛️ История"
    }
    
    for subject, name in subjects.items():
        status = "✅ " if selected_subjects.get(subject, False) else "❌ "
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{status}{name}",
                callback_data=f"tog_{subject}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="💾 Сохранить", callback_data="save_subj")
    ])
    
    return keyboard

def get_practice_subjects_keyboard():
    """Клавиатура выбора предмета для практики"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📐 Математика", callback_data="prac_math"),
            InlineKeyboardButton(text="📖 Русский язык", callback_data="prac_russian")
        ],
        [
            InlineKeyboardButton(text="🏛️ История", callback_data="prac_history"),
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")
        ]
    ])
    return keyboard

def get_topics_keyboard(subject, topics):
    """Клавиатура выбора темы"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Создаем кэш тем
    if not hasattr(get_topics_keyboard, 'topic_cache'):
        get_topics_keyboard.topic_cache = {}
    
    for i, topic in enumerate(topics):
        cache_key = f"{subject}_{i}"
        get_topics_keyboard.topic_cache[cache_key] = topic
        
        # Сокращаем длинные названия
        short_topic = topic[:25] + "..." if len(topic) > 25 else topic
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=short_topic,
                callback_data=f"topic_{subject}_{i}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🎲 Случайное задание", callback_data=f"rand_{subject}")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад к предметам", callback_data="back_to_practice")
    ])
    
    return keyboard

def get_task_navigation_keyboard(subject, task_id, is_daily=False):
    """Клавиатура навигации по заданию"""
    subject_short = {'math': 'm', 'russian': 'r', 'history': 'h'}.get(subject, 'm')
    daily_flag = 'd' if is_daily else 'p'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Ответить", 
                callback_data=f"ans_{task_id}_{subject_short}_{daily_flag}"
            )
        ]
    ])
    
    if is_daily:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад к ежедневным", callback_data="back_to_daily")
        ])
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад к темам", callback_data="back_to_practice")
        ])
    
    return keyboard

def get_answer_result_keyboard(task_id, subject, is_correct, is_daily=False):
    """Клавиатура после ответа"""
    subject_short = {'math': 'm', 'russian': 'r', 'history': 'h'}.get(subject, 'm')
    daily_flag = 'd' if is_daily else 'p'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if is_correct:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="➡️ Следующее задание", 
                callback_data=f"next_{subject_short}_{daily_flag}"
            )
        ])
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="📖 Показать решение", callback_data=f"sol_{task_id}")
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔄 Попробовать снова", 
                callback_data=f"retry_{task_id}_{subject_short}_{daily_flag}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="back_home")
    ])
    
    return keyboard

def get_topic_from_cache(subject, index):
    """Получить тему из кэша"""
    if hasattr(get_topics_keyboard, 'topic_cache'):
        cache_key = f"{subject}_{index}"
        return get_topics_keyboard.topic_cache.get(cache_key)
    return None