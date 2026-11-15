import asyncio
from datetime import date, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "9003328271:AAGkdnH3jVXe0WXJJhIv39bJVxQWemWliNA"
# =====================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_birthdays = {}

MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


class BirthdayForm(StatesGroup):
    choosing_day = State()
    choosing_month = State()
    choosing_year = State()


# ================= КЛАВИАТУРЫ =================

def days_keyboard():
    """Кнопки дней 1-31, по 7 в ряд"""
    buttons = []
    row = []
    for d in range(1, 32):
        row.append(InlineKeyboardButton(text=str(d), callback_data=f"day_{d}"))
        if len(row) == 7:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def months_keyboard():
    """Месяцы по 3 в ряд"""
    buttons = []
    row = []
    for num, name in MONTHS.items():
        row.append(InlineKeyboardButton(text=name, callback_data=f"month_{num}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def years_keyboard(page: int = 0):
    """Годы постранично — по 12 в ряд (4x3 = 12). page 0 = самые свежие"""
    current_year = date.today().year
    all_years = list(range(current_year, 1939, -1))  # от текущего вниз до 1940
    per_page = 12
    start = page * per_page
    chunk = all_years[start:start + per_page]

    buttons = []
    row = []
    for y in chunk:
        row.append(InlineKeyboardButton(text=str(y), callback_data=f"year_{y}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Навигация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Новее", callback_data=f"yearpage_{page-1}"))
    if start + per_page < len(all_years):
        nav.append(InlineKeyboardButton(text="Старше ➡️", callback_data=f"yearpage_{page+1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ================= ХЕНДЛЕРЫ =================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎂 Привет! Выбери **день** своего рождения:",
        reply_markup=days_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_day)


@dp.callback_query(BirthdayForm.choosing_day, F.data.startswith("day_"))
async def process_day(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split("_")[1])
    await state.update_data(day=day)
    await callback.message.edit_text(
        f"📅 День: **{day}**\n\nТеперь выбери **месяц**:",
        reply_markup=months_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_month)
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_month, F.data.startswith("month_"))
async def process_month(callback: CallbackQuery, state: FSMContext):
    month = int(callback.data.split("_")[1])
    await state.update_data(month=month)
    data = await state.get_data()
    await callback.message.edit_text(
        f"📅 Дата: **{data['day']} {MONTHS[month]}**\n\nТеперь выбери **год** рождения:",
        reply_markup=years_keyboard(page=0),
        parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_year)
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_year, F.data.startswith("yearpage_"))
async def process_year_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    await callback.message.edit_text(
        f"📅 Дата: **{data['day']} {MONTHS[data['month']]}**\n\nТеперь выбери **год** рождения:",
        reply_markup=years_keyboard(page=page),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(BirthdayForm.choosing_year, F.data.startswith("year_"))
async def process_year(callback: CallbackQuery, state: FSMContext):
    year = int(callback.data.split("_")[1])
    data = await state.get_data()
    day, month = data["day"], data["month"]

    # Проверка корректности (например, 31 февраля)
    try:
        birth = date(year, month, day)
    except ValueError:
        await callback.message.edit_text(
            "❌ Такой даты не существует (например, 31 февраля).\nДавай заново — выбери день:",
            reply_markup=days_keyboard()
        )
        await state.set_state(BirthdayForm.choosing_day)
        await callback.answer()
        return

    user_birthdays[callback.from_user.id] = birth
    await state.clear()

    await callback.message.edit_text(
        calculate_countdown(birth),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Изменить дату", callback_data="change")]
        ])
    )
    await callback.answer("Готово! 🎉")


@dp.callback_query(F.data == "change")
async def change_date(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎂 Выбери **день** своего рождения:",
        reply_markup=days_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BirthdayForm.choosing_day)
    await callback.answer()


# ================= РАСЧЁТ =================

def calculate_countdown(birth: date) -> str:
    today = date.today()

    try:
        next_bd = birth.replace(year=today.year)
    except ValueError:
        next_bd = date(today.year, 3, 1)  # 29 фев -> 1 марта

    if next_bd < today:
        try:
            next_bd = birth.replace(year=today.year + 1)
        except ValueError:
            next_bd = date(today.year + 1, 3, 1)

    days_left = (next_bd - today).days
    age = next_bd.year - birth.year
    age_now = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    delta = next_bd - today
    total_seconds = delta.total_seconds()
    hours_left = int(total_seconds // 3600) % 24
    minutes_left = int(total_seconds // 60) % 60

    date_str = next_bd.strftime("%d.%m.%Y")

    if days_left == 0:
        return (
            f"🎉🎂 **С ДНЁМ РОЖДЕНИЯ!** 🎂🎉\n\n"
            f"Сегодня твой день рождения! Тебе исполнилось **{age}**!\n"
            f"Желаю всего самого лучшего! 🥳"
        )

    return (
        f"🎂 **Твоя дата:** {birth.strftime('%d.%m.%Y')}\n"
        f"🎉 **Ближайший ДР:** {date_str} (исполнится {age} лет)\n"
        f"📊 **Сейчас тебе:** {age_now} лет\n\n"
        f"⏳ **До дня рождения осталось:**\n"
        f"• **{days_left}** дней\n"
        f"• ~{hours_left} ч\n"
        f"• ~{minutes_left} мин\n\n"
        f"Не забудь подготовить подарок! 🎁"
    )


@dp.message(F.text == "/my")
async def my_birthday(message: Message):
    birth = user_birthdays.get(message.from_user.id)
    if not birth:
        await message.answer("Ты ещё не указал дату рождения. Напиши /start")
        return
    await message.answer(calculate_countdown(birth), parse_mode="Markdown")


@dp.message(F.text == "/reset")
async def reset(message: Message, state: FSMContext):
    await state.clear()
    user_birthdays.pop(message.from_user.id, None)
    await message.answer("✅ Данные удалены. Напиши /start чтобы начать заново.")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())