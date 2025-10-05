import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State

API_TOKEN = '8364850506:AAFxKYwgrAfixORbkGlyfM_s0NhUVIQ59RU'
OWNER_CHAT_ID = 477634260

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🚗 Каталог авто"),
            KeyboardButton(text="💰 Калькулятор стоимости")
        ],
        [
            KeyboardButton(text="❓ FAQ"),
            KeyboardButton(text="📞 Связаться с нами")
        ],
        [
            KeyboardButton(text="✍️ Оставить заявку"),
            KeyboardButton(text="ℹ️ О компании"),
            KeyboardButton(text="⛔ Отмена")
        ]
    ],
    resize_keyboard=True
)

car_data = {
    "Toyota": {"Prius": list(range(2017, 2025))},
    "Honda": {"Vezel": list(range(2017, 2025))},
    "Mazda": {"CX-5": list(range(2017, 2025))},
    "Nissan": {"Note": list(range(2017, 2025))},
    "Subaru": {"Forester": list(range(2017, 2025))}
}

class CalcFSM(StatesGroup):
    brand = State()
    model = State()
    year = State()
    budget = State()

class RequestFSM(StatesGroup):
    name = State()
    phone = State()
    comment = State()

faq_list = [
    {"q": "Какой срок доставки автомобиля из Японии?", "a": "Обычно доставка занимает 35-50 дней с момента оплаты."},
    {"q": "Что включено в стоимость авто?", "a": "В стоимость входит цена на аукционе, доставка до Владивостока, пошлины и брокерские услуги."},
    {"q": "Можно ли оформить кредит или рассрочку?", "a": "Доступно оформление через банки-партнеры. Уточняйте детали у менеджера."},
    {"q": "Сколько составляет предоплата?", "a": "Предоплата — 15% для участия в аукционе и резервирования авто."},
    {"q": "Какие гарантии вы предоставляете?", "a": "Мы работаем официально с 2022 года, предоставляем все документы и сопровождаем авто до постановки на учет."}
]

def get_faq_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=item['q'], callback_data=f"faq_{i}")] for i, item in enumerate(faq_list)
        ]
    )

@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добро пожаловать в AutoSeller24!\n\nВыберите раздел в меню ниже.", reply_markup=main_menu)

@dp.message(F.text == "🚗 Каталог авто")
async def catalog_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("В разделе /Каталог реализован пошаговый калькулятор стоимости.", reply_markup=main_menu)

@dp.message(F.text == "💰 Калькулятор стоимости")
async def calculator_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CalcFSM.brand)
    brands = [InlineKeyboardButton(text=brand, callback_data=f"brand:{brand}") for brand in car_data]
    kb = InlineKeyboardMarkup(inline_keyboard=[[b] for b in brands])
    await message.answer("Выберите марку авто:", reply_markup=kb)

@dp.callback_query(F.data.startswith("brand:"))
async def calculator_choose_brand(callback: CallbackQuery, state: FSMContext):
    brand = callback.data.split(":", 1)[1]
    await state.update_data(brand=brand)
    models = [InlineKeyboardButton(text=model, callback_data=f"model:{model}") for model in car_data[brand]]
    kb = InlineKeyboardMarkup(inline_keyboard=[[m] for m in models])
    await callback.message.answer(f"Вы выбрали марку: <b>{brand}</b>\n\nТеперь выберите модель:", parse_mode="HTML", reply_markup=kb)
    await state.set_state(CalcFSM.model)
    await callback.answer()

@dp.callback_query(F.data.startswith("model:"))
async def calculator_choose_model(callback: CallbackQuery, state: FSMContext):
    model = callback.data.split(":", 1)[1]
    await state.update_data(model=model)
    data = await state.get_data()
    years = car_data[data['brand']][model]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=str(year), callback_data=f"year:{year}")] for year in years])
    await callback.message.answer(f"Вы выбрали модель: <b>{model}</b>\n\nТеперь выберите год выпуска:", parse_mode="HTML", reply_markup=kb)
    await state.set_state(CalcFSM.year)
    await callback.answer()

@dp.callback_query(F.data.startswith("year:"))
async def calculator_choose_year(callback: CallbackQuery, state: FSMContext):
    year = callback.data.split(":", 1)[1]
    await state.update_data(year=year)
    await callback.message.answer(f"Вы выбрали год: <b>{year}</b>\n\nВведите ваш бюджет в рублях (например, 1200000):", parse_mode="HTML")
    await state.set_state(CalcFSM.budget)
    await callback.answer()

@dp.message(StateFilter(CalcFSM.budget))
async def calculator_finish(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    data = await state.get_data()
    text = (f"🔎 <b>Ваши параметры:</b>\n"
            f"Марка: {data['brand']}\n"
            f"Модель: {data['model']}\n"
            f"Год: {data['year']}\n"
            f"Бюджет: {data['budget']} ₽\n\n"
            "Для расчета и заказа автомобиля заполните форму заявки 👇")
    await message.answer(text, parse_mode='HTML', reply_markup=main_menu)
    await message.answer("✍️ Хотите получить подбор и консультацию? Оставьте заявку!",
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✍️ Оставить заявку"), KeyboardButton(text="⛔ Отмена")]], resize_keyboard=True))
    await state.clear()

@dp.message(F.text == "✍️ Оставить заявку")
async def request_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RequestFSM.name)
    await message.answer("Пожалуйста, укажите ваше имя:")

@dp.message(StateFilter(RequestFSM.name))
async def request_name(message: Message, state: FSMContext):
    if message.text == "⛔ Отмена":
        await cancel_handler(message, state)
        return
    await state.update_data(name=message.text)
    await state.set_state(RequestFSM.phone)
    await message.answer("Введите номер телефона для связи:")

@dp.message(StateFilter(RequestFSM.phone))
async def request_phone(message: Message, state: FSMContext):
    if message.text == "⛔ Отмена":
        await cancel_handler(message, state)
        return
    await state.update_data(phone=message.text)
    await state.set_state(RequestFSM.comment)
    await message.answer("Добавьте комментарий к заявке (модель, год, бюджет или вопрос):")

@dp.message(StateFilter(RequestFSM.comment))
async def request_finish(message: Message, state: FSMContext):
    if message.text == "⛔ Отмена":
        await cancel_handler(message, state)
        return
    await state.update_data(comment=message.text)
    data = await state.get_data()
    notify = (f"📥 <b>Новая заявка AutoSeller24</b>\n"
              f"Имя: {data['name']}\nТелефон: {data['phone']}\nКомментарий: {data['comment']}\n"
              f"Telegram: @{message.from_user.username if message.from_user.username else '-'}")
    await bot.send_message(OWNER_CHAT_ID, notify, parse_mode="HTML")
    await message.answer("Спасибо! Ваша заявка принята. Наш менеджер свяжется с вами в ближайшее время.", reply_markup=main_menu)
    await state.clear()

@dp.message(F.text == "⛔ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено. Выберите раздел:", reply_markup=main_menu)

@dp.message(F.text == "❓ FAQ")
async def faq_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Часто задаваемые вопросы (выберите):", reply_markup=get_faq_keyboard())

@dp.callback_query(F.data.startswith("faq_"))
async def faq_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    idx = int(callback.data.split("_")[1])
    a = faq_list[idx]["a"]
    await callback.message.answer(f"ℹ️ {a}")
    await callback.answer()

@dp.message(F.text == "📞 Связаться с нами")
async def contact_handler(message: Message, state: FSMContext):
    await state.clear()
    text = ("<b>Контакты менеджера Сергея</b>\n\n"
            "📞 Телефон: +7 (391) 555-0123\n"
            "💬 Telegram: @autoseller24\n"
            "🟢 WhatsApp: +7 (391) 555-0123\n\n"
            "Вы можете звонить или писать в Telegram и WhatsApp по данному номеру.")
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "ℹ️ О компании")
async def about_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("AutoSeller24 — импорт автомобилей из Японии под заказ с 2022 года. Более 500 довольных клиентов.", reply_markup=main_menu)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
