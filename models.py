from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    
    # Экономика
    balance_cash = Column(Float, default=5000.0)  # Наличка (игровая валюта)
    balance_token = Column(Float, default=0.0)    # Токены GUNTER (для аирдропа)
    total_earned_tokens = Column(Float, default=0.0)  # Всего заработано
    
    # Гараж
    garage_level = Column(Integer, default=1)
    garage_slots = Column(Integer, default=2)  # Сколько машин можно иметь
    
    # Статистика
    races_won = Column(Integer, default=0)
    races_lost = Column(Integer, default=0)
    fights_won = Column(Integer, default=0)
    fights_lost = Column(Integer, default=0)
    reputation = Column(Integer, default=0)  # Репутация среди пацанов
    
    # Доступные запчасти в инвентаре (храним JSON)
    inventory = Column(JSON, default={
        'engines': [],  # [id двигателя, уровень]
        'turbos': [],
        'suspensions': [],
        'subwoofers': [],
        'body_kits': []
    })
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    cars = relationship("Car", back_populates="owner")
    listings = relationship("AvitoListing", back_populates="seller")

class Car(Base):
    __tablename__ = 'cars'
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, default="Тачка пацана")
    
    # ----- ОСНОВНЫЕ ХАРАКТЕРИСТИКИ (двигатель и тд) -----
    
    # Двигатель (уровень 1-10, базовая мощность * множитель)
    engine_level = Column(Integer, default=1)
    engine_power_multiplier = Column(Float, default=1.0)  # 1.0, 1.2, 1.5 и тд
    
    # Турбина (0-3 уровень, дает буст к мощности)
    turbo_level = Column(Integer, default=0)
    turbo_boost = Column(Float, default=0.0)  # % увеличения мощности
    
    # Подвеска (0-3, влияет на управление)
    suspension_level = Column(Integer, default=0)
    handling_bonus = Column(Float, default=1.0)  # Множитель управляемости
    
    # НАСТРОЙКА КЛАПАНОВ (БЕЗ МИНИ-ИГР, ПРОСТО КНОПКА)
    valves_tuned = Column(Boolean, default=False)
    valves_tune_quality = Column(Float, default=0.0)  # 0.0 - 1.0 качество настройки
    
    # НАСТРОЙКА ДВИГАТЕЛЯ (БЕЗ МИНИ-ИГР)
    engine_tuned = Column(Boolean, default=False)
    engine_tune_power = Column(Float, default=0.0)  # Доп. мощность от настройки
    
    # Проводка (0-2, влияет на надежность)
    wiring_quality = Column(Integer, default=0)  # 0-2
    reliability_bonus = Column(Float, default=1.0)
    
    # Аудиосистема (сабвуфер)
    subwoofer_level = Column(Integer, default=0)
    subwoofer_power = Column(Integer, default=0)  # Ватты
    subwoofer_brand = Column(String, default="none")  # Бренд саба
    music_genre = Column(String, default="none")  # Шансон, Реп, Русский рок
    
    # Тюнинг и косметика
    body_kit = Column(String, default="stock")
    tint_level = Column(Integer, default=0)  # 0-3 тонировка
    color = Column(String, default="#FF0000")
    
    # Состояние машины
    condition = Column(Float, default=100.0)  # 0-100%
    mileage = Column(Integer, default=0)  # Пробег
    
    # Гоночные параметры (расчетные)
    top_speed = Column(Float, default=180.0)
    acceleration = Column(Float, default=8.5)  # 0-100 км/ч
    handling = Column(Float, default=5.0)
    
    owner = relationship("User", back_populates="cars")

    def calculate_performance(self):
        """Пересчет характеристик машины на основе всех настроек"""
        
        # БАЗОВАЯ МОЩНОСТЬ ОТ ДВИГАТЕЛЯ
        base_power = 100 * self.engine_power_multiplier
        
        # ТУРБИНА
        turbo_power = 0
        if self.turbo_level == 1:
            turbo_power = base_power * 0.15  # +15%
        elif self.turbo_level == 2:
            turbo_power = base_power * 0.30  # +30%
        elif self.turbo_level == 3:
            turbo_power = base_power * 0.50  # +50%
        self.turbo_boost = turbo_power
        
        # НАСТРОЙКА КЛАПАНОВ (дает +10-30% мощности в зависимости от качества)
        valves_power = 0
        if self.valves_tuned:
            valves_power = base_power * (0.1 + self.valves_tune_quality * 0.2)
        
        # НАСТРОЙКА ДВИГАТЕЛЯ (индивидуальная калибровка)
        tune_power = base_power * self.engine_tune_power if self.engine_tuned else 0
        
        # ИТОГОВАЯ МОЩНОСТЬ
        total_power = base_power + turbo_power + valves_power + tune_power
        
        # УПРАВЛЯЕМОСТЬ (зависит от подвески + настройки)
        handling_base = 5.0
        if self.suspension_level == 1:
            handling_base += 1.5
        elif self.suspension_level == 2:
            handling_base += 3.0
        elif self.suspension_level == 3:
            handling_base += 5.0
        
        handling_base *= self.handling_bonus
        
        # РАЗГОН (зависит от мощности и веса)
        acceleration = 10.0 - (total_power / 200)
        
        # МАКСИМАЛКА
        top_speed = 150 + (total_power / 3)
        
        return {
            'power': total_power,
            'handling': handling_base,
            'acceleration': max(3.0, acceleration),
            'top_speed': top_speed
        }

class AvitoListing(Base):
    __tablename__ = 'avito_listings'
    
    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('users.id'))
    
    # Тип товара: 'car', 'engine', 'turbo', 'suspension', 'subwoofer', 'body_kit'
    item_type = Column(String)
    item_data = Column(JSON)  # Характеристики товара
    price = Column(Float)
    description = Column(String)
    
    is_sold = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    seller = relationship("User", back_populates="listings")

class RaceHistory(Base):
    __tablename__ = 'race_history'
    
    id = Column(Integer, primary_key=True)
    player1_id = Column(Integer, ForeignKey('users.id'))
    player2_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # NULL = гонка с ботом
    winner_id = Column(Integer, ForeignKey('users.id'))
    bet_amount = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class FightHistory(Base):
    __tablename__ = 'fight_history'
    
    id = Column(Integer, primary_key=True)
    attacker_id = Column(Integer, ForeignKey('users.id'))
    defender_id = Column(Integer, ForeignKey('users.id'))
    winner_id = Column(Integer, ForeignKey('users.id'))
    location = Column(String)  # 'лес', 'гараж', 'вечеринка'
    created_at = Column(DateTime, default=datetime.utcnow)