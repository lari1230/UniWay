import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database import Database
from models import Task  # Добавьте эту строку если нужно

from config import BOT_TOKEN, SUBJECTS
from database import Database
from keyboards import *

# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('aiogram.event').setLevel(logging.ERROR)
logging.getLogger('aiogram.dispatcher').setLevel(logging.WARNING)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

# Проверяем подключение к SQL Server
if not db.check_connection():
    print("❌ Не удалось подключиться к SQL Server")
    print("Проверьте настройки в .env файле")
    exit(1)
else:
    print("✅ Подключение к SQL Server установлено")

# Состояния
class AnswerState(StatesGroup):
    waiting_for_answer = State()

# Хранилища
user_temp_subjects = {}
user_current_tasks = {}
user_message_ids = {}

# Вспомогательные функции
async def edit_or_send_message(user_id, text, reply_markup=None, parse_mode=None):
    try:
        if user_id in user_message_ids:
            try:
                await bot.edit_message_text(
                    text=text,
                    chat_id=user_id,
                    message_id=user_message_ids[user_id],
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return user_message_ids[user_id]
            except:
                if user_id in user_message_ids:
                    del user_message_ids[user_id]
        
        msg = await bot.send_message(user_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        user_message_ids[user_id] = msg.message_id
        return msg.message_id
    except Exception as e:
        logging.error(f"Ошибка в edit_or_send_message: {e}")
        return None

async def delete_user_message(user_id, message_id):
    try:
        await bot.delete_message(chat_id=user_id, message_id=message_id)
    except:
        pass

# Кэш для тем
topic_cache = {}

# ==================== ГЛАВНЫЕ ОБРАБОТЧИКИ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        user = db.add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        await edit_or_send_message(
            message.from_user.id,
            f"🎓 Добро пожаловать в UniWay, {message.from_user.first_name}!\n\n"
            "Я помогу тебе подготовиться к ЕГЭ по математике, русскому языку и истории.\n\n"
            "📌 Выбери предметы для подготовки\n"
            "📊 Отслеживай прогресс\n"
            "🎯 Решай задания\n\n"
            "Начни с выбора предметов:",
            reply_markup=get_main_keyboard()
        )
        
        await show_subjects_selection(message.from_user.id)
        await delete_user_message(message.from_user.id, message.message_id)
    except Exception as e:
        logging.error(f"Ошибка в cmd_start: {e}")

async def show_subjects_selection(user_id):
    try:
        user = db.get_user(user_id)
        if user:
            selected = {
                "math": user.math_selected,
                "russian": user.russian_selected,
                "history": user.history_selected
            }
            user_temp_subjects[user_id] = selected.copy()
            
            await edit_or_send_message(
                user_id,
                "📚 Выбери предметы для подготовки:",
                reply_markup=get_subjects_keyboard(selected)
            )
    except Exception as e:
        logging.error(f"Ошибка в show_subjects_selection: {e}")

# ==================== МЕНЮ ====================

@dp.message(F.text == "📚 Мои предметы")
async def show_my_subjects(message: Message):
    try:
        await delete_user_message(message.from_user.id, message.message_id)
        
        user = db.get_user(message.from_user.id)
        if user:
            selected = []
            if user.math_selected:
                selected.append("📐 Математика")
            if user.russian_selected:
                selected.append("📖 Русский язык")
            if user.history_selected:
                selected.append("🏛️ История")
            
            if selected:
                text = "✅ Твои выбранные предметы:\n" + "\n".join(f"• {s}" for s in selected)
            else:
                text = "⚠️ Ты еще не выбрал ни одного предмета."
            
            text += "\n\nХочешь изменить выбор?"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Изменить предметы", callback_data="edit_subjects")],
                [InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_home")]
            ])
            
            await edit_or_send_message(message.from_user.id, text, reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка в show_my_subjects: {e}")

@dp.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    try:
        await delete_user_message(message.from_user.id, message.message_id)
        
        user = db.get_user(message.from_user.id)
        if user:
            stats = db.get_user_statistics(user.id)
            
            text = "📊 *Твоя статистика:*\n\n"
            
            for subject_key, subject_data in SUBJECTS.items():
                if subject_key in stats:
                    s = stats[subject_key]
                    text += f"{subject_data['emoji']} {subject_data['name']}:\n"
                    text += f"   ✅ Правильно: {s['correct']}\n"
                    text += f"   📝 Всего: {s['total']}\n"
                    text += f"   📈 Процент: {s['percentage']}%\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_home")]
            ])
            
            await edit_or_send_message(message.from_user.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка в show_statistics: {e}")

@dp.message(F.text == "📝 Ежедневные задания")
async def show_daily_tasks(message: Message):
    try:
        await delete_user_message(message.from_user.id, message.message_id)
        
        user = db.get_user(message.from_user.id)
        
        if not user:
            await edit_or_send_message(message.from_user.id, "❌ Пользователь не найден")
            return
        
        selected_subjects = []
        if user.math_selected:
            selected_subjects.append("math")
        if user.russian_selected:
            selected_subjects.append("russian")
        if user.history_selected:
            selected_subjects.append("history")
        
        if not selected_subjects:
            await edit_or_send_message(
                message.from_user.id,
                "⚠️ Сначала выбери предметы в разделе 'Мои предметы'",
                reply_markup=get_main_keyboard()
            )
            return
        
        tasks = db.create_daily_tasks(user.id, selected_subjects)
        
        if tasks:
            text = "📝 *Ежедневные задания на сегодня:*\n\n"
            for subject_key, task in tasks:
                subject_name = SUBJECTS[subject_key]['name']
                text += f"• {subject_name}\n"
            
            text += "\nВыбери предмет:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            for subject_key in selected_subjects:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=SUBJECTS[subject_key]['name'],
                        callback_data=f"daily_{subject_key}"
                    )
                ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_home")
            ])
            
            await edit_or_send_message(message.from_user.id, text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await edit_or_send_message(
                message.from_user.id,
                "✅ Ты уже выполнил все ежедневные задания!",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logging.error(f"Ошибка в show_daily_tasks: {e}")

@dp.message(F.text == "🎯 Практика по предметам")
async def show_practice_menu(message: Message):
    try:
        await delete_user_message(message.from_user.id, message.message_id)
        
        await edit_or_send_message(
            message.from_user.id,
            "🎯 *Выбери предмет для практики:*",
            reply_markup=get_practice_subjects_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка в show_practice_menu: {e}")

# ==================== КНОПКИ НАЗАД ====================

@dp.callback_query(F.data == "back_home")
async def back_to_home(callback: CallbackQuery):
    try:
        await edit_or_send_message(
            callback.from_user.id,
            "🏠 *Главное меню*\n\nВыбери действие:",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в back_to_home: {e}")

@dp.callback_query(F.data == "back_to_practice")
async def back_to_practice(callback: CallbackQuery):
    try:
        await edit_or_send_message(
            callback.from_user.id,
            "🎯 *Выбери предмет для практики:*",
            reply_markup=get_practice_subjects_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в back_to_practice: {e}")

@dp.callback_query(F.data == "back_to_daily")
async def back_to_daily(callback: CallbackQuery):
    try:
        user = db.get_user(callback.from_user.id)
        if user:
            selected_subjects = []
            if user.math_selected:
                selected_subjects.append("math")
            if user.russian_selected:
                selected_subjects.append("russian")
            if user.history_selected:
                selected_subjects.append("history")
            
            if not selected_subjects:
                await edit_or_send_message(
                    callback.from_user.id,
                    "⚠️ Сначала выбери предметы в разделе 'Мои предметы'",
                    reply_markup=get_main_keyboard()
                )
                await callback.answer()
                return
            
            tasks = db.create_daily_tasks(user.id, selected_subjects)
            
            if tasks:
                text = "📝 *Ежедневные задания на сегодня:*\n\n"
                for subject_key, task in tasks:
                    subject_name = SUBJECTS[subject_key]['name']
                    text += f"• {subject_name}\n"
                
                text += "\nВыбери предмет:"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                for subject_key in selected_subjects:
                    keyboard.inline_keyboard.append([
                        InlineKeyboardButton(
                            text=SUBJECTS[subject_key]['name'],
                            callback_data=f"daily_{subject_key}"
                        )
                    ])
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_home")
                ])
                
                await edit_or_send_message(callback.from_user.id, text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await edit_or_send_message(
                    callback.from_user.id,
                    "✅ Ты уже выполнил все ежедневные задания!",
                    reply_markup=get_main_keyboard()
                )
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в back_to_daily: {e}")

# ==================== ВЫБОР ПРЕДМЕТОВ ====================

@dp.callback_query(F.data == "edit_subjects")
async def edit_subjects(callback: CallbackQuery):
    try:
        await show_subjects_selection(callback.from_user.id)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в edit_subjects: {e}")

@dp.callback_query(F.data.startswith("tog_"))
async def toggle_subject(callback: CallbackQuery):
    try:
        subject = callback.data.split("_")[1]
        user_id = callback.from_user.id
        
        if user_id in user_temp_subjects:
            user_temp_subjects[user_id][subject] = not user_temp_subjects[user_id][subject]
            
            if user_id in user_message_ids:
                try:
                    await bot.edit_message_reply_markup(
                        chat_id=user_id,
                        message_id=user_message_ids[user_id],
                        reply_markup=get_subjects_keyboard(user_temp_subjects[user_id])
                    )
                except:
                    pass
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в toggle_subject: {e}")

@dp.callback_query(F.data == "save_subj")
async def save_subjects(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        if user_id in user_temp_subjects:
            db.update_user_subjects(user_id, user_temp_subjects[user_id])
            
            await edit_or_send_message(
                user_id,
                "✅ *Предметы сохранены!* Теперь я буду присылать тебе ежедневные задания.",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в save_subjects: {e}")

# ==================== ПРАКТИКА ====================

@dp.callback_query(F.data.startswith("prac_"))
async def practice_subject(callback: CallbackQuery):
    try:
        subject = callback.data.split("_")[1]
        topics = db.get_topics_by_subject(subject)
        
        if not topics:
            await edit_or_send_message(
                callback.from_user.id,
                "⚠️ Пока нет заданий по этому предмету.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return
        
        global topic_cache
        for i, topic in enumerate(topics):
            topic_cache[f"{subject}_{i}"] = topic
        
        await edit_or_send_message(
            callback.from_user.id,
            f"📚 *{SUBJECTS[subject]['name']}*\n\nВыбери тему:",
            reply_markup=get_topics_keyboard(subject, topics),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в practice_subject: {e}")

@dp.callback_query(F.data.startswith("topic_"))
async def practice_by_topic(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        subject = parts[1]
        topic_index = int(parts[2])
        
        topic = topic_cache.get(f"{subject}_{topic_index}")
        
        if not topic:
            await edit_or_send_message(
                callback.from_user.id,
                "⚠️ Тема не найдена",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return
        
        tasks = db.get_tasks_by_subject_topic(subject, topic)
        
        if tasks:
            user_current_tasks[callback.from_user.id] = {
                'tasks': tasks,
                'current_index': 0,
                'subject': subject,
                'is_daily': False
            }
            
            await show_task(callback.from_user.id)
        else:
            await edit_or_send_message(
                callback.from_user.id,
                "⚠️ Нет заданий по этой теме.",
                reply_markup=get_main_keyboard()
            )
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в practice_by_topic: {e}")

@dp.callback_query(F.data.startswith("rand_"))
async def random_task(callback: CallbackQuery):
    try:
        subject = callback.data.split("_")[1]
        tasks = db.get_tasks_by_subject_topic(subject)
        
        if tasks:
            random_task = random.choice(tasks)
            user_current_tasks[callback.from_user.id] = {
                'current_task': random_task,
                'subject': subject,
                'is_daily': False,
                'single_task': True
            }
            
            await show_single_task(callback.from_user.id, random_task, subject, False)
        else:
            await edit_or_send_message(
                callback.from_user.id,
                "⚠️ Нет заданий по этому предмету.",
                reply_markup=get_main_keyboard()
            )
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в random_task: {e}")

# ==================== ЕЖЕДНЕВНЫЕ ЗАДАНИЯ ====================

@dp.callback_query(F.data.startswith("daily_"))
async def daily_task_handler(callback: CallbackQuery):
    try:
        subject = callback.data.split("_")[1]
        user = db.get_user(callback.from_user.id)
        
        if user:
            task = db.get_daily_task(user.id, subject)
            if task:
                user_current_tasks[callback.from_user.id] = {
                    'current_task': task,
                    'subject': subject,
                    'is_daily': True
                }
                await show_single_task(callback.from_user.id, task, subject, True)
            else:
                await edit_or_send_message(
                    callback.from_user.id,
                    "✅ Ты уже выполнил это задание сегодня!",
                    reply_markup=get_main_keyboard()
                )
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в daily_task_handler: {e}")

# ==================== ЗАДАНИЯ ====================

async def show_task(user_id):
    try:
        data = user_current_tasks.get(user_id)
        if data and 'tasks' in data:
            tasks = data['tasks']
            index = data['current_index']
            
            if index < len(tasks):
                task = tasks[index]
                await show_single_task(user_id, task, data['subject'], data['is_daily'])
            else:
                await edit_or_send_message(
                    user_id,
                    "🎉 *Поздравляю!* Ты выполнил все задания по этой теме!",
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown"
                )
                del user_current_tasks[user_id]
    except Exception as e:
        logging.error(f"Ошибка в show_task: {e}")

async def show_single_task(user_id, task, subject, is_daily):
    try:
        text = f"📝 *Задание*\n\n{task.text}\n\n"
        text += f"📚 Предмет: {SUBJECTS[subject]['name']}\n"
        text += f"🏷️ Тема: {task.topic}\n"
        text += f"⭐ Сложность: {'🟢' if task.difficulty == 1 else '🟡' if task.difficulty == 2 else '🔴'}"
        
        if user_id not in user_current_tasks:
            user_current_tasks[user_id] = {}
        user_current_tasks[user_id]['current_task'] = task
        user_current_tasks[user_id]['subject'] = subject
        user_current_tasks[user_id]['is_daily'] = is_daily
        
        await edit_or_send_message(
            user_id,
            text,
            reply_markup=get_task_navigation_keyboard(subject, task.id, is_daily),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка в show_single_task: {e}")

@dp.callback_query(F.data.startswith("ans_"))
async def ask_for_answer(callback: CallbackQuery, state: FSMContext):
    """Запросить ответ"""
    try:
        parts = callback.data.split("_")
        task_id = int(parts[1])
        subject_short = parts[2]
        flag = parts[3]
        
        subject_map = {'m': 'math', 'r': 'russian', 'h': 'history'}
        subject = subject_map.get(subject_short, 'math')
        is_daily = (flag == 'd')
        
        await state.set_state(AnswerState.waiting_for_answer)
        await state.update_data(
            task_id=task_id,
            subject=subject,
            is_daily=is_daily,
            message_id=callback.message.message_id  # Сохраняем ID сообщения с заданием
        )
        
        # Отправляем запрос ответа
        msg = await bot.send_message(
            callback.from_user.id,
            "✏️ *Введи свой ответ:*\n(Твое сообщение будет удалено после ответа)",
            parse_mode="Markdown"
        )
        
        await state.update_data(prompt_message_id=msg.message_id)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в ask_for_answer: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@dp.message(StateFilter(AnswerState.waiting_for_answer))
async def process_answer(message: Message, state: FSMContext):
    """Обработать ответ"""
    try:
        # Удаляем сообщение пользователя с ответом
        await delete_user_message(message.from_user.id, message.message_id)
        
        data = await state.get_data()
        task_id = data.get('task_id')
        subject = data.get('subject')
        is_daily = data.get('is_daily')
        user_answer = message.text
        original_message_id = data.get('message_id')
        
        # Удаляем сообщение с запросом ответа
        if 'prompt_message_id' in data:
            try:
                await bot.delete_message(
                    chat_id=message.from_user.id,
                    message_id=data['prompt_message_id']
                )
            except:
                pass
        
        user = db.get_user(message.from_user.id)
        
        if is_daily:
            task, is_correct, solution = db.check_daily_task_answer(user.id, subject, user_answer)
            
            if task:
                # Формируем текст результата
                if is_correct:
                    text = f"✅ *ПРАВИЛЬНО!*\n\n📝 *Правильный ответ:* {task.answer}\n\n✨ Отличная работа! Ты справился с заданием."
                else:
                    text = f"❌ *НЕПРАВИЛЬНО!*\n\n📝 *Правильный ответ:* {task.answer}\n\n"
                    # if solution:
                    #     text += f"📖 *Решение:*\n{solution}\n\n"
                    text += "🔄 Ты можешь попробовать еще раз или перейти к следующему заданию."
                
                # Создаем клавиатуру для результата
                if is_correct:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📝 К ежедневным заданиям", callback_data="back_to_daily")],
                        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                    ])
                else:
                    subject_short = {'math': 'm', 'russian': 'r', 'history': 'h'}.get(subject, 'm')
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📖 Показать решение", callback_data=f"sol_{task.id}")],
                        # [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"retry_{task.id}_{subject_short}_d")],
                        [InlineKeyboardButton(text="📝 К ежедневным", callback_data="back_to_daily")],
                        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                    ])
                
                # Отправляем НОВОЕ сообщение с результатом (не редактируем)
                await bot.send_message(
                    message.from_user.id,
                    text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
                # Очищаем текущее задание
                if message.from_user.id in user_current_tasks:
                    del user_current_tasks[message.from_user.id]
            else:
                await bot.send_message(
                    message.from_user.id,
                    "❌ Задание не найдено или уже выполнено.",
                    reply_markup=get_main_keyboard()
                )
        else:
            # Обычная практика
            task = db.get_task_by_id(task_id)
            if task:
                is_correct = task.answer.lower().strip() == user_answer.lower().strip()
                db.complete_practice_task(user.id, task_id, subject, is_correct)
                
                # Формируем текст результата
                if is_correct:
                    text = f"✅ *ПРАВИЛЬНО!*\n\n📝 *Правильный ответ:* {task.answer}\n\n🎉 Молодец!"
                else:
                    text = f"❌ *НЕПРАВИЛЬНО!*\n\n📝 *Правильный ответ:* {task.answer}\n\n"
                    if task.solution:
                        text += f"📖 *Решение:*\n{task.solution}\n\n"
                if is_correct:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                    ])
                else:
                    subject_short = {'math': 'm', 'russian': 'r', 'history': 'h'}.get(subject, 'm')
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        # [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"retry_{task.id}_{subject_short}_d")],
                        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                    ])
                
                # Отправляем результат
                await bot.send_message(
                    message.from_user.id,
                    text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
                # Показываем следующее задание
                user_data = user_current_tasks.get(message.from_user.id, {})
                if 'tasks' in user_data:
                    # Если есть список заданий
                    user_data['current_index'] += 1
                    if user_data['current_index'] < len(user_data['tasks']):
                        # Показываем следующее задание
                        next_task = user_data['tasks'][user_data['current_index']]
                        await show_single_task(message.from_user.id, next_task, subject, False)
                    else:
                        # Все задания выполнены
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🎯 К практике", callback_data="back_to_practice")],
                            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                        ])
                        await bot.send_message(
                            message.from_user.id,
                            "🎉 *Поздравляю!* Ты выполнил все задания по этой теме!",
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                        del user_current_tasks[message.from_user.id]
                elif 'single_task' in user_data:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎯 К практике", callback_data="back_to_practice")],
                        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                    ])
                    await bot.send_message(
                        message.from_user.id,
                        "Хочешь продолжить практику?",
                        reply_markup=keyboard
                    )
                    del user_current_tasks[message.from_user.id]
                else:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎯 К практике", callback_data="back_to_practice")],
                        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_home")]
                    ])
                    await bot.send_message(
                        message.from_user.id,
                        "Хочешь продолжить практику?",
                        reply_markup=keyboard
                    )
        
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в process_answer: {e}")
        await bot.send_message(
            message.from_user.id,
            f"⚠️ Произошла ошибка: {str(e)}\nПопробуй еще раз.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

@dp.callback_query(F.data.startswith("sol_"))
async def show_solution(callback: CallbackQuery):
    """Показать решение (отправляет новым сообщением, не удаляет)"""
    try:
        task_id = int(callback.data.split("_")[1])
        task = db.get_task_by_id(task_id)
        
        if task and task.solution:
            # Отправляем решение как новое сообщение
            await bot.send_message(
                callback.from_user.id,
                f"📖 *Решение задания:*\n\n{task.solution}",
                parse_mode="Markdown"
            )
        else:
            await bot.send_message(
                callback.from_user.id,
                "Решение недоступно для этого задания."
            )
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в show_solution: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@dp.callback_query(F.data.startswith("retry_"))
async def retry_task(callback: CallbackQuery):
    """Повторить задание (показывает задание заново)"""
    try:
        parts = callback.data.split("_")
        task_id = int(parts[1])
        subject_short = parts[2]
        flag = parts[3]
        
        subject_map = {'m': 'math', 'r': 'russian', 'h': 'history'}
        subject = subject_map.get(subject_short, 'math')
        is_daily = (flag == 'd')
        
        task = db.get_task_by_id(task_id)
        
        if task:
            # Показываем задание заново
            await show_single_task(callback.from_user.id, task, subject, is_daily)
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в retry_task: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@dp.callback_query(F.data.startswith("next_"))
async def next_task(callback: CallbackQuery):
    """Следующее задание"""
    try:
        parts = callback.data.split("_")
        subject_short = parts[1]
        flag = parts[2]
        
        is_daily = (flag == 'd')
        
        if is_daily:
            await back_to_daily(callback)
        else:
            await back_to_practice(callback)
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в next_task: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@dp.callback_query(F.data.startswith("retry_daily_"))
async def retry_daily_task(callback: CallbackQuery):
    """Повторить ежедневное задание"""
    try:
        subject = callback.data.split("_")[2]
        user = db.get_user(callback.from_user.id)
        
        if user:
            task = db.get_daily_task(user.id, subject)
            if task:
                await show_single_task(callback.from_user.id, task, subject, True)
        
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в retry_daily_task: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

# ==================== ЗАПУСК ====================

async def main():
    try:
        # Проверяем подключение к БД
        if not db.check_connection():
            print("❌ Не удалось подключиться к базе данных")
            return
        
        # Проверяем, есть ли задания в БД (не добавляем автоматически)
        session = db.get_session()
        tasks_count = session.query(Task).count()
        session.close()
        
        print(f"📊 В базе данных: {tasks_count} заданий")
        
        if tasks_count == 0:
            print("⚠️ ВНИМАНИЕ: База данных пуста!")
            print("Пожалуйста, выполните SQL скрипт init_database.sql для заполнения БД")
        
        me = await bot.get_me()
        print(f"🤖 Бот {me.username} успешно запущен!")
        print("📱 Начинаю polling...")
        
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        await asyncio.sleep(5)
        await main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")