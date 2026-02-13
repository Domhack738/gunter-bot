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
from bot import dp, bot, BASE_URL  # Импортируем BASE_URL из bot.py
from config import WEBAPP_URL

# СОЗДАЕМ ОБЪЕКТ APP
app = FastAPI(title="Gunter Life API")

# Подключаем статические файлы (HTML, CSS, JS)
if os.path.exists("webapp"):
    app.mount("/static", StaticFiles(directory="webapp"), name="static")
    templates = Jinja2Templates(directory="webapp")