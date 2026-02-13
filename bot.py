import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from config import BOT_TOKEN
from database import get_session
from models import User, Car

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Жестко прописываем правильный URL (без использования config)
BASE_URL = "https://gunter-bot-production.up.railway.app"

# ---------- СОСТОЯНИЯ ДЛЯ FSM ----------
class GarageStates(StatesGroup):
    tuning_valves = State()
    tuning_engine = State()
    tuning_wiring = State()
    buying_part = State()

# ---------- КОМАНДА СТАРТ ----------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.tg_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            session.add(user)
            await session.flush()
            
            car = Car(
                owner_id=user.id,
                engine_level=1,
                engine_power_multiplier=1.0
            )
            session.add(car)
            await session.commit()
    
    # Используем прямой URL
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Открыть Гараж", web_app=WebAppInfo(url=f"{BASE_URL}/garage"))],
        [InlineKeyboardButton(text="💰 Авито (Рынок)", web_app=WebAppInfo(url=f"{BASE_URL}/avito"))],
        [InlineKeyboardButton(text="📊 Мой Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🎁 Токены GUNTER", callback_data="tokens")]
    ])
    
    await message.answer(
        "🔰 <b>Добро пожаловать в GUNTER LIFE!</b>\n\n"
        "Тут пацаны собирают тачки, гоняют и бухают.\n"
        "У тебя уже есть стартовая Веста. Качай её, ставь турбину, настраивай клапана.\n\n"
        "👇 Жми кнопку, чтобы зайти в гараж!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ---------- ПРОФИЛЬ ----------
@dp.callback_query(lambda c: c.data == "profile")
async def show_profile(callback: CallbackQuery):
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.tg_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            await callback.answer()
            return
        
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        car_info = "🚗 <b>Нет машины</b>"
        if car:
            perf = car.calculate_performance()
            car_info = (
                f"🚗 <b>{car.name}</b>\n"
                f"⚡ Мощность: {perf['power']:.0f} л.с.\n"
                f"💨 Максималка: {perf['top_speed']:.0f} км/ч\n"
                f"🔄 Разгон: {perf['acceleration']:.1f} сек\n"
                f"🎚 Управление: {perf['handling']:.1f}"
            )
        
        text = (
            f"👤 <b>{user.first_name}</b>\n"
            f"🆔 @{user.username or 'нет юзернейма'}\n\n"
            f"💰 <b>Баланс:</b>\n"
            f"💵 Наличка: {user.balance_cash:.0f} $\n"
            f"🎮 Токены GUNTER: {user.balance_token:.2f}\n\n"
            f"🏆 <b>Статистика:</b>\n"
            f"🏁 Гонки: {user.races_won} побед / {user.races_lost} поражений\n"
            f"🤜 Драки: {user.fights_won} побед / {user.fights_lost} поражений\n"
            f"⭐ Репутация: {user.reputation}\n\n"
            f"{car_info}\n\n"
            f"🏢 Уровень гаража: {user.garage_level}"
        )
        
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()

# ---------- ТОКЕНЫ ----------
@dp.callback_query(lambda c: c.data == "tokens")
async def show_tokens(callback: CallbackQuery):
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.tg_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            await callback.answer()
            return
        
        text = (
            "🎮 <b>GUNTER TOKEN (GTR)</b>\n\n"
            f"Твой баланс: <b>{user.balance_token:.2f} GTR</b>\n"
            f"Всего заработано: {user.total_earned_tokens:.2f} GTR\n\n"
            "<b>Как получить токены:</b>\n"
            "• Победа в гонке — +5 GTR\n"
            "• Победа в драке — +3 GTR\n"
            "• Продажа машины на Авито — +10 GTR\n"
            "• Ежедневный бонус — +1 GTR\n"
            "• Донат — x2 GTR\n\n"
            "<b>Скоро:</b>\n"
            "🚀 Вывод токенов (Airdrop)\n"
            "💎 NFT тюнинг\n\n"
            "💰 <i>Токены готовятся к листингу!</i>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Купить токены (Донат)", callback_data="donate")]
        ])
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

# ---------- ДОНАТ ----------
@dp.callback_query(lambda c: c.data == "donate")
async def donate_tokens(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 100 GTR — 100 ₽", callback_data="donate_100")],
        [InlineKeyboardButton(text="⭐ 500 GTR — 450 ₽", callback_data="donate_500")],
        [InlineKeyboardButton(text="⭐ 1000 GTR — 800 ₽", callback_data="donate_1000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="tokens")]
    ])
    
    await callback.message.edit_text(
        "💎 <b>Магазин токенов GUNTER</b>\n\n"
        "Купи токены сейчас и получи x2 бонус!\n"
        "Токены будут начислены автоматически после оплаты.\n\n"
        "<i>Оплата через Telegram Stars</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("donate_"))
async def process_donate(callback: CallbackQuery):
    amount = int(callback.data.split("_")[1])
    
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.tg_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            await callback.answer()
            return
        
        token_amount = amount
        if amount == 100:
            token_amount = 100
        elif amount == 500:
            token_amount = 550
        elif amount == 1000:
            token_amount = 1200
        
        user.balance_token += token_amount
        user.total_earned_tokens += token_amount
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"Тебе начислено <b>{token_amount} GTR</b>!\n"
            f"Текущий баланс: {user.balance_token:.2f} GTR",
            parse_mode="HTML"
        )
        await callback.answer()
