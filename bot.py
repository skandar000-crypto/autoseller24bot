import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State

# --- 1. НАСТРОЙКИ ---
API_TOKEN = "8364850506:AAFxKYwgrAfixORbkGlyfM_s0NhUVIQ59RU"
OWNER_IDS = [477634260, 5103316031]  # <-- Впиши сюда ID получателей

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- 2. ДАННЫЕ ДЛЯ FAQ ---
faq_data = [
    {
        "question": "Сколько времени занимает доставка?",
        "answer": "В среднем, доставка с момента покупки на аукционе до прибытия во Владивосток занимает 3–5 недель. Срок может меняться в зависимости от удалённости аукциона, погоды и загруженности таможни."
    },
    {
        "question": "Как доставляют автомобили?",
        "answer": "Основной способ — на специальных судах типа Ro-Ro. Машины сами заезжают в трюм, где их надёжно закрепляют. Это самый безопасный метод, защищающий от повреждений и морской воды."
    },
    {
        "question": "Из чего складывается конечная цена?",
        "answer": "Финальная стоимость — это не только цена на аукционе. К ней добавляются: аукционный сбор, доставка по Японии до порта, морской фрахт, комиссия за услуги банка, таможенная пошлина, утилизационный сбор, стоимость автовоза и наша комиссия."
    },
    {
        "question": "Стоимость услуг компании AutoSeller24?",
        "answer": "Стоимость оказания наших услуг составляет 30 000  -40 000 руб."
    },
    {
        "question": "Есть ли риски при заказе автомобиля из Японии?",
        "answer": "Да, риски есть всегда, в  основном это риски связанные с транспортировкой автомобиля."
    },
    {
        "question": "Другой вопрос",
        "answer": "Вы можете связаться с нами через раздел Контакты, наши менеджеры ответят на интересующий Вас вопрос."
    }
    ]

# --- 3. КЛАВИАТУРЫ ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✍️ Оставить заявку")],
        [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="🛒 Схема покупки")]
    ],
    resize_keyboard=True
)

cancel_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⛔ Отмена")]],
    resize_keyboard=True
)

# --- 4. МАШИНА СОСТОЯНИЙ (FSM) ---
class RequestFSM(StatesGroup):
    name = State()
    phone = State()
    comment = State()

# --- 5. ОБРАБОТЧИКИ ---

@dp.message(Command("start"), StateFilter('*'))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте! Я бот-помощник компании AutoSeller24.\n\nНажмите 'Оставить заявку', чтобы мы подобрали для вас автомобиль из Японии.",
        reply_markup=main_menu
    )

@dp.message(F.text == "⛔ Отмена", StateFilter('*'))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu)

@dp.message(F.text == "✍️ Оставить заявку", StateFilter(None))
async def request_start(message: Message, state: FSMContext):
    await state.set_state(RequestFSM.name)
    await message.answer("Пожалуйста, укажите ваше имя:", reply_markup=cancel_menu)

@dp.message(StateFilter(RequestFSM.name))
async def request_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RequestFSM.phone)
    await message.answer("Введите номер телефона для связи:")

@dp.message(StateFilter(RequestFSM.phone))
async def request_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(RequestFSM.comment)
    await message.answer("Добавьте комментарий к заявке (модель, год, бюджет или вопрос):")

@dp.message(StateFilter(RequestFSM.comment))
async def request_finish(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    data = await state.get_data()

    notify = (f"📥 <b>Новая заявка AutoSeller24</b>\n"
              f"Имя: {data['name']}\nТелефон: {data['phone']}\nКомментарий: {data['comment']}\n"
              f"Telegram: @{message.from_user.username if message.from_user.username else '-'}")

    # --- УЛУЧШЕННАЯ ОТПРАВКА ---
    tasks = [bot.send_message(owner_id, notify, parse_mode="HTML") for owner_id in OWNER_IDS]
    await asyncio.gather(*tasks, return_exceptions=True)
    # --------------------------

    # --- ГАРАНТИРОВАННАЯ ОТПРАВКА ПОЛЬЗОВАТЕЛЮ ---
    try:
        await message.answer(
            "Спасибо! Ваша заявка принята. Наш менеджер свяжется с вами в ближайшее время.",
            reply_markup=main_menu
        )
    except Exception as e:
        print(f"!!! ОШИБКА: Не удалось отправить подтверждение пользователю {message.from_user.id}: {e}")
    # ---------------------------------------------

    await state.clear()

@dp.message(F.text == "❓ FAQ", StateFilter('*'))
async def faq_handler(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=item["question"], callback_data=f"faq_{i}")]
            for i, item in enumerate(faq_data)
        ]
    )
    await message.answer("Выберите интересующий вас вопрос:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("faq_"))
async def faq_answer_handler(callback: CallbackQuery):
    question_index = int(callback.data.split("_")[1])
    answer = faq_data[question_index]["answer"]
    await callback.message.answer(text=answer, parse_mode="HTML")
    await callback.answer()

@dp.message(F.text == "📞 Контакты", StateFilter('*'))
async def contact_handler(message: Message, state: FSMContext):
    await state.clear()
    text = ("<b>Контакты</b>\n\n"
            "📞 Телефон: +7-(391)-2-949-666\n"
            "💬 Telegram: @autoseller24\n"
            "🟢 WhatsApp: +7-(902)-924-96-66\n\n"
            "Вы можете звонить или писать в Telegram и WhatsApp по данному номеру.")
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu)

@dp.message(F.text == "🛒 Схема покупки", StateFilter('*'))
async def purchase_flow_handler(message: Message, state: FSMContext):
    await state.clear()

    part1 = (
        "🚗 Пошаговая схема покупки авто из Японии 🇯🇵\n\n"
        "1️⃣ <b>Встреча и договор</b>\n"
        "Приезжаете к нам в офис или встречаемся в удобном месте.\n"
        "Заключаем договор (форма ответственности — ИП).\n"
        "💰 Наша комиссия — 30 000 руб.\n\n"
        "2️⃣ <b>Выбор автомобиля</b>\n"
        "Можно выбрать машину сразу или заранее получать варианты перед торгами.\n"
        "Каждый день вечером отправляем подборку авто под ваш запрос.\n"
        "В день торгов формируется группа до 5 автомобилей, из которых покупается один.\n\n"
        "3️⃣ <b>Фиксация курса валюты (по желанию)</b>\n"
        "Рекомендуем открыть счёт в Азиатско-Тихоокеанском банке и купить японские йены —\n"
        "так вы застрахуетесь от роста курса 💹.\n"
    )

    part2 = (
        "4️⃣ <b>Торги и покупка</b>\n"
        "Ставки делаем по очереди в назначенное время.\n"
        "После выигрыша остальных отменяем.\n"
        "Получаете инвойс-лист с указанием стоимости авто и расходов по Японии\n"
        "(услуги аукциона, фрахт до Владивостока 🚢).\n\n"
        "5️⃣ <b>Оплата и документы</b>\n"
        "Оплата инвойса — в течение 3 дней.\n"
        "Делаем нотариально заверенные копии паспорта + цветные сканы:\n"
        "ИНН, СНИЛС, заявление на перевод, паспорт.\n"
        "Все отправляете нам в WhatsApp.\n\n"
        "6️⃣ <b>Регистрация ЭПТС</b>\n"
        "Проходите регистрацию через <a href=\"https://dp.elpts.ru/#/auth/person\">Госуслуги</a>.\n"
        "После оплаты пошлины и лаборатории ЭПТС придет на почту (3–10 дней).\n"
    )

    part3 = (
        "7️⃣ <b>Ожидание отправки во Владивосток</b>\n"
        "Средний срок — 10–30 дней.\n"
        "Предоставляем фотоотчеты с ярда и разгрузки.\n\n"
        "8️⃣ <b>Временная прописка во Владивостоке</b>\n"
        "Оформляется через Госуслуги на 1 месяц.\n"
        "⚠️ Важно: данные профиля должны совпадать с паспортом\n"
        "(слово в слово, точка в точку!).\n"
        "Инструкцию выдаем в день регистрации.\n\n"
        "9️⃣ <b>Таможенные процедуры и финальная оплата</b>\n"
        "Брокеры оформляют всё за ~10 дней.\n"
        "Оплачиваете расходы по РФ: таможня, ЭПТС, лаборатория, СБКТС и т.д.\n"
        "💳 Оплата возможна в Сбербанке, у нас в офисе или во Владивостоке.\n\n"
        "📞 Подробности по телефону:\n"
        "+7 (391) 2‑949‑666"
    )

    await message.answer(part1, parse_mode="HTML", reply_markup=main_menu)
    await message.answer(part2, parse_mode="HTML")
    await message.answer(part3, parse_mode="HTML")

# --- 6. ЗАПУСК БОТА ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(main())

