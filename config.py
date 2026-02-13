import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8227351959:AAHSpdM_xT7azDYk3vcNcTsGK82hSGi3gsk')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///gunter.db')
ADMIN_ID = int(os.getenv('ADMIN_ID', 1776341320))
# WEBAPP_URL больше не используется в bot.py, но оставим для совместимости
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://gunter-bot-production.up.railway.app')
