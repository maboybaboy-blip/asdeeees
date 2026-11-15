import asyncio
import os
from datetime import date, datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiosqlite
from zoneinfo import ZoneInfo

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9003328271:AAGkdnH3jVXe0WXJJhIv39bJVxQWemWliNA")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8795006636"))   # твой Telegram ID
DB_PATH = os.environ.get("DB_PATH", "birthdays.db")
NOTIFY_HOUR = 10
NOTIFY_MINUTE = 0
# =====================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone="UTC")

MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

# ============================================================
# ГОРОДА (все крупные города РФ по округам + другие страны)
# ============================================================
COUNTRIES = {
    "🇷🇺 Россия • Центральный ФО": [
        ("Москва", "Europe/Moscow", "🏛"),
        ("Белгород", "Europe/Moscow", "🏙"),
        ("Брянск", "Europe/Moscow", "🏙"),
        ("Владимир", "Europe/Moscow", "🏙"),
        ("Воронеж", "Europe/Moscow", "🏙"),
        ("Иваново", "Europe/Moscow", "🏙"),
        ("Калуга", "Europe/Moscow", "🏙"),
        ("Кострома", "Europe/Moscow", "🏙"),
        ("Курск", "Europe/Moscow", "🏙"),
        ("Липецк", "Europe/Moscow", "🏙"),
        ("Орёл", "Europe/Moscow", "🏙"),
        ("Рязань", "Europe/Moscow", "🏙"),
        ("Смоленск", "Europe/Moscow", "🏙"),
        ("Тамбов", "Europe/Moscow", "🏙"),
        ("Тверь", "Europe/Moscow", "🏙"),
        ("Тула", "Europe/Moscow", "🏙"),
        ("Ярославль", "Europe/Moscow", "🏙"),
    ],
    "🇷🇺 Россия • Северо-Западный ФО": [
        ("Санкт-Петербург", "Europe/Moscow", "🏛"),
        ("Архангельск", "Europe/Moscow", "🏙"),
        ("Вологда", "Europe/Moscow", "🏙"),
        ("Калининград", "Europe/Kaliningrad", "🏙"),
        ("Мурманск", "Europe/Moscow", "🏙"),
        ("Новгород", "Europe/Moscow", "🏙"),
        ("Петрозаводск", "Europe/Moscow", "🏙"),
        ("Псков", "Europe/Moscow", "🏙"),
        ("Сыктывкар", "Europe/Moscow", "🏙"),
    ],
    "🇷🇺 Россия • Южный ФО": [
        ("Ростов-на-Дону", "Europe/Moscow", "🏙"),
        ("Краснодар", "Europe/Moscow", "🏙"),
        ("Астрахань", "Europe/Volgograd", "🏙"),
        ("Волгоград", "Europe/Volgograd", "🏙"),
        ("Майкоп", "Europe/Moscow", "🏙"),
        ("Элиста", "Europe/Moscow", "🏙"),
        ("Сочи", "Europe/Moscow", "🌴"),
        ("Новороссийск", "Europe/Moscow", "🏙"),
    ],
    "🇷🇺 Россия • Северо-Кавказский ФО": [
        ("Махачкала", "Europe/Moscow", "🏙"),
        ("Владикавказ", "Europe/Moscow", "🏙"),
        ("Грозный", "Europe/Moscow", "🏙"),
        ("Нальчик", "Europe/Moscow", "🏙"),
        ("Ставрополь", "Europe/Moscow", "🏙"),
        ("Черкесск", "Europe/Moscow", "🏙"),
        ("Магас", "Europe/Moscow", "🏙"),
        ("Пятигорск", "Europe/Moscow", "🏙"),
    ],
    "🇷🇺 Россия • Приволжский ФО": [
        ("Нижний Новгород", "Europe/Moscow", "🏙"),
        ("Казань", "Europe/Moscow", "🕌"),
        ("Самара", "Europe/Samara", "🏙"),
        ("Уфа", "Asia/Yekaterinburg", "🏙"),
        ("Пермь", "Asia/Yekaterinburg", "🏙"),
        ("Саратов", "Europe/Saratov", "🏙"),
        ("Оренбург", "Asia/Yekaterinburg", "🏙"),
        ("Пенза", "Europe/Moscow", "🏙"),
        ("Ульяновск", "Europe/Ulyanovsk", "🏙"),
        ("Ижевск", "Europe/Samara", "🏙"),
        ("Йошкар-Ола", "Europe/Moscow", "🏙"),
        ("Саранск", "Europe/Moscow", "🏙"),
        ("Чебоксары", "Europe/Moscow", "🏙"),
        ("Киров", "Europe/Kirov", "🏙"),
    ],
    "🇷🇺 Россия • Уральский ФО": [
        ("Екатеринбург", "Asia/Yekaterinburg", "🏙"),
        ("Тюмень", "Asia/Yekaterinburg", "🏙"),
        ("Челябинск", "Asia/Yekaterinburg", "🏙"),
        ("Курган", "Asia/Yekaterinburg", "🏙"),
        ("Салехард", "Asia/Yekaterinburg", "🏙"),
        ("Ханты-Мансийск", "Asia/Yekaterinburg", "🏙"),
        ("Сургут", "Asia/Yekaterinburg", "🏙"),
        ("Нижневартовск", "Asia/Yekaterinburg", "🏙"),
    ],
    "🇷🇺 Россия • Сибирский ФО": [
        ("Новосибирск", "Asia/Novosibirsk", "🏙"),
        ("Омск", "Asia/Omsk", "🏙"),
        ("Красноярск", "Asia/Krasnoyarsk", "🏙"),
        ("Барнаул", "Asia/Barnaul", "🏙"),
        ("Кемерово", "Asia/Novokuznetsk", "🏙"),
        ("Новокузнецк", "Asia/Novokuznetsk", "🏙"),
        ("Томск", "Asia/Tomsk", "🏙"),
        ("Иркутск", "Asia/Irkutsk", "🏙"),
        ("Улан-Удэ", "Asia/Irkutsk", "🏙"),
        ("Абакан", "Asia/Krasnoyarsk", "🏙"),
        ("Кызыл", "Asia/Krasnoyarsk", "🏙"),
        ("Горно-Алтайск", "Asia/Barnaul", "🏙"),
    ],
    "🇷🇺 Россия • Дальневосточный ФО": [
        ("Владивосток", "Asia/Vladivostok", "🏙"),
        ("Хабаровск", "Asia/Vladivostok", "🏙"),
        ("Благовещенск", "Asia/Yakutsk", "🏙"),
        ("Якутск", "Asia/Yakutsk", "🏙"),
        ("Магадан", "Asia/Magadan", "🏙"),
        ("Петропавловск-Камчатский", "Asia/Kamchatka", "🌋"),
        ("Южно-Сахалинск", "Asia/Sakhalin", "🏙"),
        ("Биробиджан", "Asia/Vladivostok", "🏙"),
        ("Анадырь", "Asia/Anadyr", "🏙"),
        ("Чита", "Asia/Chita", "🏙"),
    ],
    "🇰🇿 Казахстан": [
        ("Алматы", "Asia/Almaty", "🏙"),
        ("Астана", "Asia/Almaty", "🏙"),
        ("Актобе", "Asia/Aqtobe", "🏙"),
        ("Атырау", "Asia/Atyrau", "🏙"),
    ],
    "🇧🇾 Беларусь": [("Минск", "Europe/Minsk", "🏙"), ("Гомель", "Europe/Minsk", "🏙")],
    "🇺🇦 Украина": [("Киев", "Europe/Kyiv", "🏙"), ("Харьков", "Europe/Kyiv", "🏙")],
    "🇩🇪 Германия": [("Берлин", "Europe/Berlin", "🏙"), ("Мюнхен", "Europe/Berlin", "🏙")],
    "🇺🇸 США": [
        ("Нью-Йорк", "America/New_York", "🗽"),
        ("Чикаго", "America/Chicago", "🏙"),
        ("Денвер", "America/Denver", "🏙"),
        ("Лос-Анджелес", "America/Los_Angeles", "🌴"),
    ],
    "🇬🇧 Великобритания": [("Лондон", "Europe/London", "🎡")],
    "🇹🇷 Турция": [("Стамбул", "Europe/Istanbul", "🕌")],
    "🇨🇳 Китай": [("Пекин", "Asia/Shanghai", "🏯")],
    "🇯🇵 Япония": [("Токио", "Asia/Tokyo", "🗾")],
    "🇦🇺 Австралия": [("Сидней", "Australia/Sydney", "🏄")],
    "🌐 UTC": [("UTC (универсальное)", "UTC", "🌐")],
}


# ================= БАЗА ДАННЫХ =================

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                timezone TEXT DEFAULT 'UTC',
                notifications INTEGER DEFAULT 1,
                last_notify_date TEXT DEFAULT NULL,
                is_banned INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sponsors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_title TEXT,
                invite_link TEXT NOT NULL
            )
        """)
        async with db.execute("PRAGMA table_info(users)") as cur:
            cols = [r[1] for r in await cur.fetchall()]
        for col, ddl in [
            ("timezone", "TEXT DEFAULT 'UTC'"),
            ("last_notify_date", "TEXT DEFAULT NULL"),
            ("is_banned", "INTEGER DEFAULT 0"),
        ]:
            if col not in cols:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
        await db.commit()


async def save_user(user_id: int, day: int, month: int, year: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, day, month, year, notifications)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                day=excluded.day, month=excluded.month, year=excluded.year
        """, (user_id, day, month, year))
        await db.commit()


async def set_timezone(user_id: int, tz: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET timezone=? WHERE user_id=?", (tz, user_id))
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT day, month, year, timezone, notifications, is_banned "
            "FROM users WHERE user_id=?", (user_id,)
        ) as cur:
            return await cur.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, day, month, year, timezone, notifications, "
            "last_notify_date, is_banned FROM users"
        ) as cur:
            return await cur.fetchall()


async def set_notifications(user_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET notifications=? WHERE user_id=?",
                         (1 if enabled else 0, user_id))
        await db.commit()


async def mark_notified(user_id: int, day_str: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_notify_date=? WHERE user_id=?",
                         (day_str, user_id))
        await db.commit()


async def delete_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        await db.commit()


# --- спонсоры ---
async def add_sponsor(channel_id: str, title: str, link: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO sponsors (channel_id, channel_title, invite_link) VALUES (?, ?, ?)",
            (channel_id, title, link)
        )
        await db.commit()


async def remove_sponsor(sponsor_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sponsors WHERE id=?", (sponsor_id,))
        await db.commit()


async def get_sponsors():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, channel_id, channel_title, invite_link FROM sponsors"
        ) as cur:
            return await cur.fetchall()


# ================= ПРОВЕРКА ПОДПИСКИ =================

async def check_subscriptions(user_id: int) -> list:
    sponsors = await get_sponsors()
    not_subscribed = []
    for sid, channel_id, title, link in sponsors:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append((sid, channel_id, title, link))
        except Exception as e:
            print(f"[subs] Ошибка проверки {channel_id}: {e}")
            not_subscribed.append((sid, channel_id, title, link))
    return not_subscribed


def sponsors_keyboard(not_subscribed):
    buttons = []
    for sid, channel_id, title, link in not_subscribed:
        buttons.append([InlineKeyboardButton(text=f"📢 {title}", url=link)])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался — проверить", callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def ensure_subscribed(event, state: FSMContext) -> bool:
    user_id = event.from_user.id
    not_sub = await check_subscriptions(user_id)
    if not not_sub:
        return True

    text = (
        "🔒 **Чтобы пользоваться ботом, подпишись на спонсоров:**\n\n"
        "После подписки нажми **«✅ Я подписался»**."
    )
    kb = sponsors_keyboard(not_sub)

    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            await event.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    return False


# ================= FSM =================

class BirthdayForm(StatesGroup):
    choosing_day = State()
    choosing_month = State()
    choosing_year = State()
    choosing_country = State()
    choosing_city = State()


class AdminForm(StatesGroup):
    waiting_broadcast = State()
    waiting_ban_id = State()
    waiting_unban_id = State()
    waiting_user_info = State()
    waiting_delete_id = State()
    waiting_sponsor_channel = State()
    waiting_sponsor_link = State()


# ================= КЛАВИАТУРЫ =================

def days_keyboard():
    buttons, row = [], []
    for d in range(1, 32):
        row.append(InlineKeyboardButton(text=str(d), callback_data=f"day_{d}"))
        if len(row) == 7:
            buttons.append(row); row = []
    if row: buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def months_keyboard():
    buttons, row = [], []
    for num, name in MONTHS.items():
        row.append(InlineKeyboardButton(text=name, callback_data=f"month_{num}"))
        if len(row) == 3:
            buttons.append(row); row = []
    if row: buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def years_keyboard(page: int = 0):
    current_year = date.today().year
    all_years = list(range(current_year, 1939, -1))
    per_page = 12
    start = page * per_page
    chunk = all_years[start:start + per_page]

    buttons, row = [], []
    for y in chunk:
        row.append(InlineKeyboardButton(text=str(y), callback_data=f"year_{y}"))
        if len(row) == 3:
            buttons.append(row); row = []
    if row: buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Новее", callback_data=f"yearpage_{page-1}"))
    if start + per_page < len(all_years):
        nav.append(InlineKeyboardButton(text="Старше ➡️", callback_data=f"yearpage_{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def countries_keyboard():
    buttons = []
    for idx, country in enumerate(COUNTRIES.keys()):
        buttons.append([InlineKeyboardButton(text=country, callback_data=f"country_{idx}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cities_keyboard(country: str):
    buttons = []
    for idx, (city, tz, emoji) in enumerate(COUNTRIES[country]):
        buttons.append([InlineKeyboardButton(text=f"{emoji} {city}", callback_data=f"city_{idx}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к странам", callback_data="back_countries")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu(notifications_on: bool):
    btn = "🔕 Выключить напоминания" if notifications_on else "🔔 Включить напоминания"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Изменить город/время", callback_data="change_tz")],
        [InlineKeyboardButton(text="🔄 Изменить дату", callback_data="change_date")],
        [InlineKeyboardButton(text=btn, callback_data="toggle_notify")],
    ])


def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="👤 Инфо о юзере", callback_data="adm_userinfo")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data="adm_ban")],
        [InlineKeyboardButton(text="✅ Разбанить", callback_data="adm_unban")],
        [InlineKeyboardButton(text="🗑 Удалить юзера", callback_data="adm_delete")],
        [InlineKeyboardButton(text="📢 Спонсоры", callback_data="adm_sponsors")],
    ])


def sponsors_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить канал", callback_data="sp_add")],
        [InlineKeyboardButton(text="📋 Список каналов", callback_data="sp_list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back")],
    ])


def is_admin(user_id: int) -> bool:
    return ADMIN_ID != 0 and user_id == ADMIN_ID


# ================= /start и проверка подписки =================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    if not await ensure_subscribed(message, state):
        return
    await message.answer(
        "🎂 Привет! Выбери **день** своего рождения:",
        reply_markup=days_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_day)


@dp.callback_query(F.data == "check_subs")
async def check_subs_handler(callback: CallbackQuery, state: FSMContext):
    not_sub = await check_subscriptions(callback.from_user.id)
    if not_sub:
        await callback.answer("❌ Ты ещё не подписан на всех спонсоров", show_alert=True)
        return
    await callback.message.edit_text(
        "✅ Спасибо за подписку!\n\n🎂 Выбери **день** своего рождения:",
        reply_markup=days_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_day)
    await callback.answer("✅ Подписка подтверждена")


# ================= ВЫБОР ДАТЫ =================

@dp.callback_query(BirthdayForm.choosing_day, F.data.startswith("day_"))
async def process_day(callback: CallbackQuery, state: FSMContext):
    if not await ensure_subscribed(callback, state):
        return
    day = int(callback.data.split("_")[1])
    await state.update_data(day=day)
    await callback.message.edit_text(
        f"📅 День: **{day}**\n\nТеперь выбери **месяц**:",
        reply_markup=months_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_month)
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_month, F.data.startswith("month_"))
async def process_month(callback: CallbackQuery, state: FSMContext):
    month = int(callback.data.split("_")[1])
    await state.update_data(month=month)
    data = await state.get_data()
    await callback.message.edit_text(
        f"📅 Дата: **{data['day']} {MONTHS[month]}**\n\nТеперь выбери **год**:",
        reply_markup=years_keyboard(0), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_year)
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_year, F.data.startswith("yearpage_"))
async def process_year_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    await callback.message.edit_text(
        f"📅 Дата: **{data['day']} {MONTHS[data['month']]}**\n\nТеперь выбери **год**:",
        reply_markup=years_keyboard(page), parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_year, F.data.startswith("year_"))
async def process_year(callback: CallbackQuery, state: FSMContext):
    year = int(callback.data.split("_")[1])
    data = await state.get_data()
    day, month = data["day"], data["month"]
    try:
        date(year, month, day)
    except ValueError:
        await callback.message.edit_text(
            "❌ Такой даты не существует. Заново — выбери день:",
            reply_markup=days_keyboard()
        )
        await state.set_state(BirthdayForm.choosing_day)
        await callback.answer()
        return

    await state.update_data(year=year)
    await callback.message.edit_text(
        "🌍 Теперь выбери **регион/страну**:",
        reply_markup=countries_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_country)
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_country, F.data.startswith("country_"))
async def process_country(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    country = list(COUNTRIES.keys())[idx]
    await state.update_data(country=country)
    await callback.message.edit_text(
        f"{country}\n\nВыбери **город**:",
        reply_markup=cities_keyboard(country), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_city)
    await callback.answer()


@dp.callback_query(F.data == "back_countries")
async def back_countries(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🌍 Выбери **регион/страну**:",
        reply_markup=countries_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_country)
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_city, F.data.startswith("city_"))
async def process_city(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    country = data.get("country")
    if not country or country not in COUNTRIES:
        await callback.answer("Ошибка, начни заново /start", show_alert=True); return
    city, tz, _ = COUNTRIES[country][idx]

    day, month, year = data["day"], data["month"], data["year"]
    await save_user(callback.from_user.id, day, month, year)
    await set_timezone(callback.from_user.id, tz)
    await state.clear()

    birth = date(year, month, day)
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        calculate_countdown(birth, tz)
        + f"\n\n🌍 Город: **{city}** (`{tz}`)"
        + f"\n🔔 Напоминания каждый день в **{NOTIFY_HOUR:02d}:{NOTIFY_MINUTE:02d}** по твоему времени!",
        parse_mode="Markdown",
        reply_markup=main_menu(bool(user[4]))
    )
    await callback.answer("Готово! 🎉")


# ================= СМЕНА ТАЙМЗОНЫ / ДАТЫ =================

@dp.callback_query(F.data == "change_tz")
async def change_tz(callback: CallbackQuery, state: FSMContext):
    if not await ensure_subscribed(callback, state):
        return
    await callback.message.edit_text(
        "🌍 Выбери **регион/страну**:",
        reply_markup=countries_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_country)
    await callback.answer()


@dp.callback_query(F.data == "change_date")
async def change_date(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎂 Выбери **день** своего рождения:",
        reply_markup=days_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_day)
    await callback.answer()


@dp.callback_query(F.data == "toggle_notify")
async def toggle_notify(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Сначала укажи дату рождения через /start", show_alert=True)
        return
    new_state = not bool(user[4])
    await set_notifications(callback.from_user.id, new_state)
    birth = date(user[2], user[1], user[0])
    tz = user[3]
    status = "🔔 Напоминания включены" if new_state else "🔕 Напоминания выключены"
    await callback.message.edit_text(
        calculate_countdown(birth, tz) + f"\n\n🌍 Часовой пояс: `{tz}`\n{status}",
        parse_mode="Markdown", reply_markup=main_menu(new_state)
    )
    await callback.answer(status)


# ================= РАСЧЁТ =================

def calc_next_bd(birth: date, tz: str):
    try:
        tzinfo = ZoneInfo(tz)
    except Exception:
        tzinfo = ZoneInfo("UTC")
    today = datetime.now(tzinfo).date()
    try:
        next_bd = birth.replace(year=today.year)
    except ValueError:
        next_bd = date(today.year, 3, 1)
    if next_bd < today:
        try:
            next_bd = birth.replace(year=today.year + 1)
        except ValueError:
            next_bd = date(today.year + 1, 3, 1)
    return next_bd, today


def calculate_countdown(birth: date, tz: str = "UTC") -> str:
    next_bd, today = calc_next_bd(birth, tz)
    days_left = (next_bd - today).days
    age = next_bd.year - birth.year
    age_now = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    if days_left == 0:
        return (
            f"🎉🎂 **С ДНЁМ РОЖДЕНИЯ!** 🎂🎉\n\n"
            f"Сегодня тебе исполнилось **{age}**!\n"
            f"Желаю всего самого лучшего! 🥳"
        )
    return (
        f"🎂 **Твоя дата:** {birth.strftime('%d.%m.%Y')}\n"
        f"🎉 **Ближайший ДР:** {next_bd.strftime('%d.%m.%Y')} (исполнится {age} лет)\n"
        f"📊 **Сейчас тебе:** {age_now} лет\n\n"
        f"⏳ **До дня рождения осталось:** **{days_left}** дней"
    )


# ================= ЕЖЕМИНУТНАЯ ПРОВЕРКА =================

async def check_notifications():
    users = await get_all_users()
    for row in users:
        user_id, day, month, year, tz, notifications, last_notify, is_banned = row
        if not notifications or is_banned:
            continue
        try:
            tzinfo = ZoneInfo(tz or "UTC")
        except Exception:
            tzinfo = ZoneInfo("UTC")
        now_local = datetime.now(tzinfo)
        if now_local.hour != NOTIFY_HOUR or now_local.minute != NOTIFY_MINUTE:
            continue
        today_str = now_local.date().isoformat()
        if last_notify == today_str:
            continue
        try:
            birth = date(year, month, day)
            next_bd, today = calc_next_bd(birth, tz)
            days_left = (next_bd - today).days
            age = next_bd.year - birth.year

            if days_left == 0:
                text = (
                    f"🎉🎂 **С ДНЁМ РОЖДЕНИЯ!** 🎂🎉\n\n"
                    f"Сегодня тебе исполнилось **{age}**!\n"
                    f"Желаю всего самого лучшего! 🥳"
                )
            elif days_left == 1:
                text = "🔥 **Завтра твой день рождения!**\n\nОстался **1 день** 🎂"
            else:
                text = (
                    f"⏳ До твоего дня рождения осталось **{days_left}** дней\n"
                    f"🎂 Ближайший ДР: {next_bd.strftime('%d.%m.%Y')} (исполнится {age})"
                )
            await bot.send_message(user_id, text, parse_mode="Markdown")
            await mark_notified(user_id, today_str)
            print(f"[notify] Отправлено {user_id} ({tz}, {days_left} дн.)")
        except Exception as e:
            print(f"[notify] Ошибка для {user_id}: {e}")


# ================= КОМАНДЫ =================

@dp.message(F.text == "/my")
async def my_birthday(message: Message, state: FSMContext):
    if not await ensure_subscribed(message, state):
        return
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Ты ещё не указал дату рождения. Напиши /start")
        return
    day, month, year, tz, notifications, is_banned = user
    birth = date(year, month, day)
    await message.answer(
        calculate_countdown(birth, tz) + f"\n\n🌍 Часовой пояс: `{tz}`",
        parse_mode="Markdown", reply_markup=main_menu(bool(notifications))
    )


@dp.message(F.text == "/notify")
async def notify_cmd(message: Message, state: FSMContext):
    if not await ensure_subscribed(message, state):
        return
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала укажи дату рождения через /start")
        return
    new_state = not bool(user[4])
    await set_notifications(message.from_user.id, new_state)
    await message.answer("🔔 Напоминания включены" if new_state else "🔕 Напоминания выключены")


@dp.message(F.text == "/tz")
async def tz_cmd(message: Message, state: FSMContext):
    if not await ensure_subscribed(message, state):
        return
    await message.answer(
        "🌍 Выбери **регион/страну**:",
        reply_markup=countries_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_country)


@dp.message(F.text == "/reset")
async def reset(message: Message, state: FSMContext):
    await state.clear()
    await delete_user(message.from_user.id)
    await message.answer("✅ Данные удалены. Напиши /start чтобы начать заново.")


@dp.message(F.text == "/help")
async def help_cmd(message: Message):
    await message.answer(
        "📖 **Команды:**\n"
        "/start — указать дату рождения и город\n"
        "/my — показать сколько осталось\n"
        "/tz — изменить город/часовой пояс\n"
        "/notify — вкл/выкл ежедневные напоминания\n"
        "/reset — удалить данные\n\n"
        f"🔔 Бот каждый день в **{NOTIFY_HOUR:02d}:{NOTIFY_MINUTE:02d}** "
        "по твоему часовому поясу присылает, сколько дней осталось до ДР, "
        "и поздравляет в сам день рождения!",
        parse_mode="Markdown"
    )


# ================= АДМИН-ПАНЕЛЬ =================

@dp.message(F.text == "/admin")
async def admin_cmd(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У тебя нет доступа.")
        return
    await state.clear()
    await message.answer(
        "🛠 **Админ-панель**\n\nВыбери действие:",
        reply_markup=admin_menu(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "adm_back")
async def adm_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "🛠 **Админ-панель**\n\nВыбери действие:",
        reply_markup=admin_menu(), parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "adm_stats")
async def adm_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE notifications=1") as cur:
            with_notify = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as cur:
            banned = (await cur.fetchone())[0]
    await callback.message.edit_text(
        f"📊 **Статистика**\n\n"
        f"👥 Всего юзеров: **{total}**\n"
        f"🔔 С напоминаниями: **{with_notify}**\n"
        f"🔕 Без напоминаний: **{total - with_notify}**\n"
        f"🚫 Забанено: **{banned}**",
        parse_mode="Markdown", reply_markup=admin_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await callback.message.edit_text(
        "📢 Введи текст для рассылки всем пользователям (можно Markdown):\n\n"
        "Отправь /cancel чтобы отменить."
    )
    await state.set_state(AdminForm.waiting_broadcast)
    await callback.answer()


@dp.message(AdminForm.waiting_broadcast, F.text == "/cancel")
async def adm_broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_broadcast)
async def adm_broadcast_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    text = message.text
    users = await get_all_users()
    ok, fail = 0, 0
    status = await message.answer(f"📤 Рассылаю {len(users)} юзерам...")
    for row in users:
        user_id = row[0]
        is_banned = row[7]
        if is_banned:
            continue
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
            ok += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fail += 1
            print(f"[broadcast] {user_id}: {e}")
    await status.edit_text(
        f"✅ Рассылка завершена\n\n"
        f"Отправлено: **{ok}**\n"
        f"Ошибок: **{fail}**",
        parse_mode="Markdown", reply_markup=admin_menu()
    )


@dp.callback_query(F.data == "adm_userinfo")
async def adm_userinfo_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await callback.message.edit_text(
        "👤 Введи **user_id** пользователя:\n\n/cancel — отмена"
    )
    await state.set_state(AdminForm.waiting_user_info)
    await callback.answer()


@dp.message(AdminForm.waiting_user_info, F.text == "/cancel")
async def adm_userinfo_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_user_info)
async def adm_userinfo_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз или /cancel"); return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT day, month, year, timezone, notifications, last_notify_date, is_banned "
            "FROM users WHERE user_id=?", (uid,)
        ) as cur:
            row = await cur.fetchone()
    await state.clear()
    if not row:
        await message.answer(f"❌ Юзер {uid} не найден", reply_markup=admin_menu()); return
    day, month, year, tz, notif, last, banned = row
    await message.answer(
        f"👤 **Юзер `{uid}`**\n\n"
        f"🎂 Дата: **{day:02d}.{month:02d}.{year}**\n"
        f"🌍 Таймзона: `{tz}`\n"
        f"🔔 Напоминания: {'вкл' if notif else 'выкл'}\n"
        f"🚫 Забанен: {'да' if banned else 'нет'}\n"
        f"📅 Последнее напоминание: `{last or '—'}`",
        parse_mode="Markdown", reply_markup=admin_menu()
    )


@dp.callback_query(F.data == "adm_ban")
async def adm_ban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await callback.message.edit_text("🚫 Введи user_id для бана:\n\n/cancel — отмена")
    await state.set_state(AdminForm.waiting_ban_id)
    await callback.answer()


@dp.message(AdminForm.waiting_ban_id, F.text == "/cancel")
async def adm_ban_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_ban_id)
async def adm_ban_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз или /cancel"); return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        await db.commit()
    await state.clear()
    await message.answer(f"🚫 Юзер `{uid}` забанен", parse_mode="Markdown", reply_markup=admin_menu())


@dp.callback_query(F.data == "adm_unban")
async def adm_unban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await callback.message.edit_text("✅ Введи user_id для разбана:\n\n/cancel — отмена")
    await state.set_state(AdminForm.waiting_unban_id)
    await callback.answer()


@dp.message(AdminForm.waiting_unban_id, F.text == "/cancel")
async def adm_unban_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_unban_id)
async def adm_unban_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз или /cancel"); return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        await db.commit()
    await state.clear()
    await message.answer(f"✅ Юзер `{uid}` разбанен", parse_mode="Markdown", reply_markup=admin_menu())


@dp.callback_query(F.data == "adm_delete")
async def adm_delete_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await callback.message.edit_text("🗑 Введи user_id для удаления:\n\n/cancel — отмена")
    await state.set_state(AdminForm.waiting_delete_id)
    await callback.answer()


@dp.message(AdminForm.waiting_delete_id, F.text == "/cancel")
async def adm_delete_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_delete_id)
async def adm_delete_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз или /cancel"); return
    await delete_user(uid)
    await state.clear()
    await message.answer(f"🗑 Юзер `{uid}` удалён", parse_mode="Markdown", reply_markup=admin_menu())


# ================= СПОНСОРЫ (админ) =================

@dp.callback_query(F.data == "adm_sponsors")
async def adm_sponsors(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await state.clear()
    await callback.message.edit_text(
        "📢 **Управление спонсорами**\n\n"
        "Бот должен быть **админом** в канале, чтобы проверять подписку!",
        reply_markup=sponsors_menu(), parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "sp_add")
async def sp_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    await callback.message.edit_text(
        "📢 Отправь **ID канала** (например `-1001234567890`) "
        "или **@username** (например `@my_channel`):\n\n"
        "Узнать ID: перешли сообщение из канала боту @userinfobot.\n\n"
        "/cancel — отмена"
    )
    await state.set_state(AdminForm.waiting_sponsor_channel)
    await callback.answer()


@dp.message(AdminForm.waiting_sponsor_channel, F.text == "/cancel")
async def sp_add_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_sponsor_channel)
async def sp_add_channel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    raw = message.text.strip()

    if raw.startswith("@"):
        try:
            chat = await bot.get_chat(raw)
            channel_id = chat.id
            title = chat.title or raw
            invite_link = f"https://t.me/{raw.lstrip('@')}"
        except Exception as e:
            await message.answer(f"❌ Не смог получить канал: {e}\nПроверь username или /cancel")
            return
    else:
        try:
            channel_id = int(raw)
        except ValueError:
            await message.answer("❌ Нужен ID (число) или @username. Попробуй ещё раз или /cancel")
            return
        try:
            chat = await bot.get_chat(channel_id)
            title = chat.title or str(channel_id)
            invite_link = chat.invite_link
            if not invite_link:
                username = chat.username
                if username:
                    invite_link = f"https://t.me/{username}"
                else:
                    await message.answer(
                        "❌ У приватного канала нет username. "
                        "Пришли ссылку на канал вручную (шаг 2)."
                    )
                    await state.update_data(pending_channel_id=channel_id, pending_title=title)
                    await state.set_state(AdminForm.waiting_sponsor_link)
                    return
        except Exception as e:
            await message.answer(f"❌ Не смог получить канал: {e}\nПроверь ID или /cancel")
            return

    await state.update_data(pending_channel_id=channel_id, pending_title=title)
    await message.answer(
        f"✅ Канал: **{title}** (`{channel_id}`)\n\n"
        f"Теперь пришли **ссылку**, которую увидит пользователь "
        f"(можно оставить предложенную: `{invite_link}`).\n\n"
        f"Просто отправь ссылку или /skip для использования предложенной.",
        parse_mode="Markdown"
    )
    await state.update_data(suggested_link=invite_link)
    await state.set_state(AdminForm.waiting_sponsor_link)


@dp.message(AdminForm.waiting_sponsor_link, F.text == "/cancel")
async def sp_link_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=admin_menu())


@dp.message(AdminForm.waiting_sponsor_link)
async def sp_add_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    channel_id = data.get("pending_channel_id")
    title = data.get("pending_title", "Канал")
    suggested = data.get("suggested_link")

    if message.text.strip() == "/skip" and suggested:
        link = suggested
    elif message.text.strip().startswith("http"):
        link = message.text.strip()
    else:
        await message.answer("❌ Пришли ссылку (http...) или /skip или /cancel")
        return

    await add_sponsor(str(channel_id), title, link)
    await state.clear()
    await message.answer(
        f"✅ Спонсор добавлен:\n**{title}** — `{link}`",
        parse_mode="Markdown", reply_markup=admin_menu()
    )


@dp.callback_query(F.data == "sp_list")
async def sp_list(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    sponsors = await get_sponsors()
    if not sponsors:
        await callback.message.edit_text(
            "📋 Спонсоров пока нет.",
            reply_markup=sponsors_menu()
        )
        await callback.answer()
        return

    buttons = []
    for sid, channel_id, title, link in sponsors:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {title}",
                callback_data=f"sp_del_{sid}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_sponsors")])
    await callback.message.edit_text(
        "📋 **Спонсоры** (нажми, чтобы удалить):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("sp_del_"))
async def sp_del(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True); return
    sid = int(callback.data.split("_")[2])
    await remove_sponsor(sid)
    sponsors = await get_sponsors()
    if not sponsors:
        await callback.message.edit_text("📋 Спонсоров больше нет.", reply_markup=sponsors_menu())
    else:
        buttons = []
        for s_id, channel_id, title, link in sponsors:
            buttons.append([InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"sp_del_{s_id}")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_sponsors")])
        await callback.message.edit_text(
            "📋 **Спонсоры** (нажми, чтобы удалить):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="Markdown"
        )
    await callback.answer("Удалено")


# ================= ЗАПУСК =================

async def main():
    await init_db()
    scheduler.add_job(check_notifications, "cron", minute="*", id="notify_check")
    scheduler.start()
    print(f"Бот запущен. Напоминания в {NOTIFY_HOUR:02d}:{NOTIFY_MINUTE:02d} по локальному времени каждого пользователя")
    if ADMIN_ID == 0:
        print("⚠️ ADMIN_ID не задан — админ-панель отключена. Укажи ADMIN_ID в настройках.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
