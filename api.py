cat > api.py << 'EOF'
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import random
from datetime import datetime
import os
from typing import Optional

from database import get_session
from models import User, Car, AvitoListing
from sqlalchemy import select, update

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

# ---------- ВЕБХУК ДЛЯ ТЕЛЕГРАМ ----------
@app.post("/webhook")
async def webhook(request: Request):
    """Эндпоинт для вебхуков от Telegram"""
    try:
        update = await request.json()
        # Здесь будет обработка обновлений
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}
EOF