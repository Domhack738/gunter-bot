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
from bot import dp, bot  # Эти импорты должны быть
from config import WEBAPP_URL  # Добавляем импорт конфига