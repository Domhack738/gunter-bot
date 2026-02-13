from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram.types import Update
import json
import random
from datetime import datetime
import os
from typing import Optional

from database import get_session
from models import User, Car, AvitoListing
from sqlalchemy import select, update
from bot import dp, bot
from config import WEBAPP_URL

# СОЗДАЕМ ОБЪЕКТ APP - ЭТО САМОЕ ВАЖНОЕ!
app = FastAPI(title="Gunter Life API")

# Подключаем статические файлы (HTML, CSS, JS)
if os.path.exists("webapp"):
    app.mount("/static", StaticFiles(directory="webapp"), name="static")
    templates = Jinja2Templates(directory="webapp")

# ---------- ГЛАВНАЯ СТРАНИЦА ----------
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Gunter Life Simulator API is running",
        "version": "1.0.0"
    }

# ---------- HEALTH CHECK ----------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------- ВЕБХУК ДЛЯ ТЕЛЕГРАМ БОТА ----------
@app.post("/webhook")
async def webhook(request: Request):
    """Эндпоинт для вебхуков от Telegram"""
    try:
        update_data = await request.json()
        print(f"Received update: {update_data.get('update_id')}")
        
        # Создаем объект Update и передаем его диспетчеру
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ---------- ГЛАВНАЯ СТРАНИЦА ГАРАЖА ----------
@app.get("/garage", response_class=HTMLResponse)
async def garage_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------- СТРАНИЦА АВИТО ----------
@app.get("/avito", response_class=HTMLResponse)
async def avito_page(request: Request):
    return templates.TemplateResponse("avito.html", {"request": request})

# ---------- API: ПОЛУЧИТЬ ДАННЫЕ ИГРОКА ----------
@app.get("/api/user/{tg_id}")
async def get_user(tg_id: int):
    async for session in get_session():
        # Ищем пользователя
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        # Ищем машину
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        car_data = None
        if car:
            try:
                perf = car.calculate_performance()
                car_data = {
                    "id": car.id,
                    "name": car.name,
                    "engine_level": car.engine_level,
                    "engine_power": car.engine_power_multiplier,
                    "turbo_level": car.turbo_level,
                    "suspension_level": car.suspension_level,
                    "valves_tuned": car.valves_tuned,
                    "valves_quality": car.valves_tune_quality,
                    "engine_tuned": car.engine_tuned,
                    "engine_tune_power": car.engine_tune_power,
                    "wiring_quality": car.wiring_quality,
                    "subwoofer_level": car.subwoofer_level,
                    "subwoofer_brand": car.subwoofer_brand,
                    "music_genre": car.music_genre,
                    "body_kit": car.body_kit,
                    "tint_level": car.tint_level,
                    "condition": car.condition,
                    "performance": perf
                }
            except Exception as e:
                print(f"Error calculating performance: {e}")
                car_data = {"error": "Could not calculate performance"}
        
        return {
            "id": user.id,
            "tg_id": user.tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "balance_cash": user.balance_cash,
            "balance_token": user.balance_token,
            "garage_level": user.garage_level,
            "reputation": user.reputation,
            "races_won": user.races_won,
            "inventory": user.inventory,
            "car": car_data
        }

# ---------- API: НАСТРОЙКА КЛАПАНОВ ----------
@app.post("/api/tune/valves/{tg_id}")
async def tune_valves(tg_id: int):
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        if not car:
            return JSONResponse({"error": "No car found"}, status_code=404)
        
        if user.balance_cash < 500:
            return JSONResponse({"error": "Недостаточно средств! Нужно 500$"}, status_code=400)
        
        user.balance_cash -= 500
        
        base_chance = 0.5 + (user.garage_level * 0.1)
        success = random.random() < base_chance
        
        if success:
            quality = 0.6 + (user.garage_level * 0.1) + random.random() * 0.2
            car.valves_tuned = True
            car.valves_tune_quality = min(quality, 1.0)
            message = "✅ Клапана настроены идеально! Машина поёт!"
        else:
            car.valves_tuned = False
            car.valves_tune_quality = 0.0
            message = "❌ Неудачная настройка! Клапана стучат, нужно переделывать."
        
        await session.commit()
        perf = car.calculate_performance()
        
        return {
            "success": success,
            "message": message,
            "valves_tuned": car.valves_tuned,
            "valves_quality": car.valves_tune_quality,
            "new_power": perf['power'],
            "balance": user.balance_cash
        }

# ---------- API: НАСТРОЙКА ДВИГАТЕЛЯ ----------
@app.post("/api/tune/engine/{tg_id}")
async def tune_engine(tg_id: int):
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
            
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        if not car:
            return JSONResponse({"error": "No car found"}, status_code=404)
        
        if user.balance_cash < 1000:
            return JSONResponse({"error": "Недостаточно средств! Нужно 1000$"}, status_code=400)
        
        user.balance_cash -= 1000
        tune_power = 0.05 + (user.garage_level * 0.03) + random.random() * 0.08
        
        car.engine_tuned = True
        car.engine_tune_power = min(tune_power, 0.25)
        
        await session.commit()
        perf = car.calculate_performance()
        
        return {
            "success": True,
            "message": f"🔧 Двигатель настроен! +{car.engine_tune_power*100:.0f}% к мощности",
            "engine_tune_power": car.engine_tune_power,
            "new_power": perf['power'],
            "balance": user.balance_cash
        }

# ---------- API: УСТАНОВКА ТУРБИНЫ ----------
@app.post("/api/upgrade/turbo/{tg_id}")
async def upgrade_turbo(tg_id: int, level: int):
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
            
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        if not car:
            return JSONResponse({"error": "No car found"}, status_code=404)
        
        turbo_prices = {1: 2000, 2: 5000, 3: 10000}
        
        if level not in turbo_prices:
            return JSONResponse({"error": "Invalid turbo level"}, status_code=400)
        
        price = turbo_prices[level]
        
        if user.balance_cash < price:
            return JSONResponse({"error": "Недостаточно средств!"}, status_code=400)
        
        user.balance_cash -= price
        car.turbo_level = level
        
        await session.commit()
        perf = car.calculate_performance()
        
        boost_percent = {1: 15, 2: 30, 3: 50}
        
        return {
            "success": True,
            "message": f"💨 Установлена турбина {level} уровня! +{boost_percent[level]}% мощности",
            "turbo_level": car.turbo_level,
            "new_power": perf['power'],
            "balance": user.balance_cash
        }

# ---------- API: УСТАНОВКА ПОДВЕСКИ ----------
@app.post("/api/upgrade/suspension/{tg_id}")
async def upgrade_suspension(tg_id: int, level: int):
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
            
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        if not car:
            return JSONResponse({"error": "No car found"}, status_code=404)
        
        suspension_prices = {1: 1500, 2: 3500, 3: 7000}
        
        if level not in suspension_prices:
            return JSONResponse({"error": "Invalid suspension level"}, status_code=400)
        
        price = suspension_prices[level]
        
        if user.balance_cash < price:
            return JSONResponse({"error": "Недостаточно средств!"}, status_code=400)
        
        user.balance_cash -= price
        car.suspension_level = level
        
        if level == 1:
            car.handling_bonus = 1.2
        elif level == 2:
            car.handling_bonus = 1.4
        elif level == 3:
            car.handling_bonus = 1.7
        
        await session.commit()
        perf = car.calculate_performance()
        
        return {
            "success": True,
            "message": f"🔩 Установлена подвеска {level} уровня! Управляемость улучшена",
            "suspension_level": car.suspension_level,
            "handling": perf['handling'],
            "balance": user.balance_cash
        }

# ---------- API: УСТАНОВКА САБВУФЕРА ----------
@app.post("/api/upgrade/subwoofer/{tg_id}")
async def upgrade_subwoofer(tg_id: int, level: int, brand: str, genre: str):
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
            
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        if not car:
            return JSONResponse({"error": "No car found"}, status_code=404)
        
        sub_prices = {1: 1000, 2: 3000, 3: 6000}
        
        if level not in sub_prices:
            return JSONResponse({"error": "Invalid subwoofer level"}, status_code=400)
        
        price = sub_prices[level]
        
        if user.balance_cash < price:
            return JSONResponse({"error": "Недостаточно средств!"}, status_code=400)
        
        user.balance_cash -= price
        car.subwoofer_level = level
        car.subwoofer_brand = brand
        car.music_genre = genre
        car.subwoofer_power = level * 500
        
        await session.commit()
        
        return {
            "success": True,
            "message": f"🔊 Установлен сабвуфер {brand}! {car.subwoofer_power}Вт, играет {genre}",
            "subwoofer_level": car.subwoofer_level,
            "subwoofer_power": car.subwoofer_power,
            "music_genre": car.music_genre,
            "balance": user.balance_cash
        }

# ---------- API: АВИТО - ПОЛУЧИТЬ ВСЕ ОБЪЯВЛЕНИЯ ----------
@app.get("/api/avito/listings")
async def get_listings():
    async for session in get_session():
        result = await session.execute(
            select(AvitoListing).where(AvitoListing.is_sold == False)
        )
        listings = result.scalars().all()
        
        result_data = []
        for listing in listings:
            seller_result = await session.execute(
                select(User).where(User.id == listing.seller_id)
            )
            seller = seller_result.scalar_one()
            
            result_data.append({
                "id": listing.id,
                "seller_username": seller.username,
                "seller_tg_id": seller.tg_id,
                "item_type": listing.item_type,
                "item_data": listing.item_data,
                "price": listing.price,
                "description": listing.description,
                "created_at": listing.created_at.isoformat() if listing.created_at else None
            })
        
        return result_data

# ---------- API: АВИТО - ВЫСТАВИТЬ ТОВАР ----------
@app.post("/api/avito/create/{tg_id}")
async def create_listing(tg_id: int, request: Request):
    data = await request.json()
    
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        listing = AvitoListing(
            seller_id=user.id,
            item_type=data['item_type'],
            item_data=data['item_data'],
            price=data['price'],
            description=data.get('description', '')
        )
        
        session.add(listing)
        await session.commit()
        
        return {"success": True, "listing_id": listing.id}

# ---------- API: АВИТО - КУПИТЬ ТОВАР ----------
@app.post("/api/avito/buy/{tg_id}/{listing_id}")
async def buy_listing(tg_id: int, listing_id: int):
    async for session in get_session():
        buyer_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        buyer = buyer_result.scalar_one_or_none()
        
        if not buyer:
            return JSONResponse({"error": "Buyer not found"}, status_code=404)
        
        listing_result = await session.execute(
            select(AvitoListing).where(AvitoListing.id == listing_id)
        )
        listing = listing_result.scalar_one_or_none()
        
        if not listing or listing.is_sold:
            return JSONResponse({"error": "Товар уже продан"}, status_code=400)
        
        seller_result = await session.execute(
            select(User).where(User.id == listing.seller_id)
        )
        seller = seller_result.scalar_one()
        
        if buyer.id == seller.id:
            return JSONResponse({"error": "Нельзя купить свой товар"}, status_code=400)
        
        if buyer.balance_cash < listing.price:
            return JSONResponse({"error": "Недостаточно средств"}, status_code=400)
        
        buyer.balance_cash -= listing.price
        seller.balance_cash += listing.price
        
        if listing.item_type not in buyer.inventory:
            buyer.inventory[listing.item_type] = []
        
        buyer.inventory[listing.item_type].append(listing.item_data)
        listing.is_sold = True
        
        await session.commit()
        
        return {
            "success": True,
            "message": f"✅ Товар куплен у @{seller.username}!",
            "balance": buyer.balance_cash
        }

# ---------- API: ГОНКА С БОТОМ ----------
@app.post("/api/race/bot/{tg_id}")
async def race_with_bot(tg_id: int):
    async for session in get_session():
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
            
        car_result = await session.execute(
            select(Car).where(Car.owner_id == user.id)
        )
        car = car_result.scalar_one_or_none()
        
        if not car:
            return JSONResponse({"error": "No car"}, status_code=400)
        
        player_perf = car.calculate_performance()
        player_score = (
            player_perf['power'] * 0.5 +
            player_perf['handling'] * 0.3 +
            player_perf['acceleration'] * 20
        )
        
        bot_power = 120 + user.garage_level * 20
        bot_score = bot_power * 0.5 + 5 * 0.3 + 12 * 20
        
        player_score *= random.uniform(0.9, 1.1)
        bot_score *= random.uniform(0.9, 1.1)
        
        is_winner = player_score > bot_score
        
        if is_winner:
            user.balance_cash += 500
            user.balance_token += 5
            user.total_earned_tokens += 5
            user.races_won += 1
            user.reputation += 1
            result_text = "🏆 Ты выиграл гонку! +500$, +5 GTR"
        else:
            user.balance_cash -= 200
            user.races_lost += 1
            user.reputation -= 1
            result_text = "💔 Ты проиграл... -200$"
        
        await session.commit()
        
        return {
            "success": True,
            "is_winner": is_winner,
            "message": result_text,
            "balance": user.balance_cash,
            "tokens": user.balance_token
        }
