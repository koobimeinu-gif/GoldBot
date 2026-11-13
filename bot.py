import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9192813629:AAFWptpskYcSq22gMz-ePYONsuaN3YLsTN0"
ADMIN_ID = 7472588058 
CARD_NUMBER = "2200396125086054" 
PRICE_PER_100 = 80 
SUPPORT_LINK = "@Goldix_Shopp" 
# ============================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class OrderState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment = State()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Купить Gold")],
        [KeyboardButton(text="📜 Правила"), KeyboardButton(text="ℹ️ Информация")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🆘 Поддержка")]
    ], resize_keyboard=True)
    await message.answer("Добро пожаловать в Goldix! 💙\nВыбирай нужный раздел в меню.", reply_markup=kb)

@dp.message(F.text == "🛒 Купить Gold")
async def buy_gold(message: types.Message, state: FSMContext):
    await message.answer("Напиши, сколько G хочешь купить (например '100'):")
    await state.set_state(OrderState.waiting_for_amount)

@dp.message(OrderState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 100:
            await message.answer("Минимальная покупка — 100 G. Введи другое число.")
            return
        
        total_price = (amount / 100) * PRICE_PER_100
        await state.update_data(amount=amount, price=total_price)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
        
        text = (f"💳 Реквизиты для оплаты:\n\n"
                f"Карта Т-Банк: `{CARD_NUMBER}`\n"
                f"Сумма: **{total_price:.0f} ₽**\n\n"
                f"Переведи точную сумму и нажми кнопку ниже 👇")
        
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
        await state.set_state(OrderState.waiting_for_payment)
    except ValueError:
        await message.answer("Пожалуйста, введи число (например: 500)")

@dp.callback_query(F.data == "paid")
async def payment_sent(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount')
    price = data.get('price')
    
    await callback.message.edit_text("⏳ Проверяем оплату, ожидай...")
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_{callback.from_user.id}_{amount}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{callback.from_user.id}")]
    ])
    
    await bot.send_message(ADMIN_ID, 
        f"🔔 **Новая заявка!**\nПользователь: {callback.from_user.full_name} (@{callback.from_user.username})\nКол-во: {amount} G\nСумма: {price:.0f} ₽\n\nПроверь перевод в приложении Т-Банк!", 
        reply_markup=admin_kb, parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_order(callback: CallbackQuery):
    _, user_id, amount = callback.data.split("_")
    user_id = int(user_id)
    
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛒 Купить Gold")]], resize_keyboard=True)
    await bot.send_message(user_id, 
        f"✅ Оплата подтверждена! Твои {amount} G готовы к выдаче.\n\n"
        f"⚠️ **Инструкция:** Выставь на рынке Standoff 2 любой скин по цене **{amount} G** и напиши в поддержку, чтобы мы его выкупили.", 
        reply_markup=kb, parse_mode="Markdown")
    
    await callback.message.edit_text("✅ Заказ подтвержден, пользователю выдана инструкция.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery):
    _, user_id = callback.data.split("_")
    user_id = int(user_id)
    await bot.send_message(user_id, "❌ Оплата не найдена. Если произошла ошибка, напиши в поддержку.")
    await callback.message.edit_text("❌ Заказ отклонен.")

@dp.callback_query(F.data == "cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Покупка отменена.")

@dp.message(F.text == "📜 Правила")
async def rules(message: types.Message):
    text = (
        "📜 **Правила магазина Goldix:**\n\n"
        "1. Минимальная покупка — 100 G.\n"
        "2. Оплата производится строго на указанную карту Т-Банк.\n"
        "3. После перевода обязательно нажмите кнопку «Я оплатил».\n"
        "4. Выдача Gold происходит через выставление скина на рынке Standoff 2.\n"
        "5. Администрация не несет ответственности за блокировку аккаунта игровыми властями.\n"
        "6. По любым вопросам пишите в поддержку."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🆘 Поддержка")
async def support(message: types.Message):
    await message.answer(f"По всем вопросам пишите нашему менеджеру: {SUPPORT_LINK}\n\nОтветим в течение 15 минут.")

@dp.message(F.text == "ℹ️ Информация")
async def info(message: types.Message):
    await message.answer("🤖 Магазин: Goldix\nВывод: до 15 минут после подтверждения оплаты.")

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    await message.answer(f"👤 Никнейм: {message.from_user.full_name}\n🆔 ID: `{message.from_user.id}`\n💰 Баланс: 0 G", parse_mode="Markdown")

async def main():
    print("Бот Goldix запущен! Иди в Telegram и пиши /start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())