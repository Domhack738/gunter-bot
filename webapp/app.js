// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Глобальные переменные
let tg_id = tg.initDataUnsafe?.user?.id;
let userData = null;
let carData = null;

// ---------- ЗАГРУЗКА ДАННЫХ ПРИ СТАРТЕ ----------
async function loadUserData() {
    try {
        const response = await fetch(`/api/user/${tg_id}`);
        const data = await response.json();
        
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        userData = data;
        carData = data.car;
        
        // Обновляем UI
        updateUI();
    } catch (error) {
        console.error('Error loading user data:', error);
        showNotification('Ошибка загрузки данных', 'error');
    }
}

// ---------- ОБНОВЛЕНИЕ ИНТЕРФЕЙСА ----------
function updateUI() {
    if (!userData) return;
    
    // Баланс
    document.getElementById('cashBalance').textContent = Math.floor(userData.balance_cash);
    document.getElementById('tokenBalance').textContent = userData.balance_token.toFixed(2);
    document.getElementById('garageLevel').textContent = userData.garage_level;
    
    if (carData) {
        // Основная инфа
        document.getElementById('carName').textContent = carData.name || 'Тачка пацана';
        document.getElementById('carCondition').textContent = `${carData.condition || 100}%`;
        
        // Характеристики
        const perf = carData.performance;
        document.getElementById('powerValue').textContent = Math.round(perf.power);
        document.getElementById('accelerationValue').textContent = perf.acceleration.toFixed(1);
        document.getElementById('handlingValue').textContent = perf.handling.toFixed(1);
        document.getElementById('topSpeed').textContent = Math.round(perf.top_speed);
        
        // Спидометр
        const speedPercent = Math.min(perf.top_speed / 300, 1);
        const needle = document.getElementById('speedNeedle');
        needle.style.transform = `rotate(${speedPercent * 90 - 45}deg)`;
        
        // Двигатель и турбина
        document.getElementById('engineLevel').textContent = carData.engine_level;
        document.getElementById('engineMultiplier').textContent = carData.engine_power;
        document.getElementById('turboLevel').textContent = carData.turbo_level;
        
        let turboPercent = {0:0, 1:15, 2:30, 3:50};
        document.getElementById('turboBoost').textContent = turboPercent[carData.turbo_level] || 0;
        
        // Подвеска
        document.getElementById('suspensionLevel').textContent = carData.suspension_level;
        let handlingBonus = {0:0, 1:20, 2:40, 3:70};
        document.getElementById('handlingBonus').textContent = handlingBonus[carData.suspension_level] || 0;
        
        // Сабвуфер
        if (carData.subwoofer_level > 0) {
            document.getElementById('subwooferInfo').innerHTML = `
                ${carData.subwoofer_brand} ${carData.subwoofer_power}Вт<br>
                🎵 ${carData.music_genre}
            `;
        }
        
        // Статусы настройки
        // Клапана
        const valvesStatus = document.getElementById('valvesStatus');
        const valvesQuality = document.getElementById('valvesQuality');
        
        if (carData.valves_tuned) {
            valvesStatus.innerHTML = '✅ Клапана настроены';
            valvesStatus.style.color = 'var(--success)';
            valvesQuality.textContent = `${Math.round(carData.valves_quality * 100)}%`;
        } else {
            valvesStatus.innerHTML = '⏹️ Не настроены';
            valvesStatus.style.color = 'var(--text-dim)';
            valvesQuality.textContent = '0%';
        }
        
        // Двигатель
        const engineTuneStatus = document.getElementById('engineTuneStatus');
        const engineTuneBonus = document.getElementById('engineTuneBonus');
        
        if (carData.engine_tuned) {
            engineTuneStatus.innerHTML = '✅ Двигатель настроен';
            engineTuneStatus.style.color = 'var(--success)';
            engineTuneBonus.textContent = Math.round(carData.engine_tune_power * 100);
        } else {
            engineTuneStatus.innerHTML = '⏹️ Не настроен';
            engineTuneStatus.style.color = 'var(--text-dim)';
            engineTuneBonus.textContent = '0';
        }
    }
}

// ---------- НАСТРОЙКА КЛАПАНОВ (БЕЗ МИНИ-ИГР) ----------
async function tuneValves() {
    try {
        const response = await fetch(`/api/tune/valves/${tg_id}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.error) {
            showNotification(result.error, 'error');
        } else {
            showNotification(result.message, result.success ? 'success' : 'error');
            
            // Обновляем данные
            await loadUserData();
        }
    } catch (error) {
        showNotification('Ошибка настройки', 'error');
    }
}

// ---------- НАСТРОЙКА ДВИГАТЕЛЯ ----------
async function tuneEngine() {
    try {
        const response = await fetch(`/api/tune/engine/${tg_id}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.error) {
            showNotification(result.error, 'error');
        } else {
            showNotification(result.message, 'success');
            await loadUserData();
        }
    } catch (error) {
        showNotification('Ошибка настройки', 'error');
    }
}

// ---------- УЛУЧШЕНИЕ ТУРБИНЫ ----------
async function upgradeTurbo() {
    const select = document.getElementById('turboSelect');
    const level = parseInt(select.value);
    
    try {
        const response = await fetch(`/api/upgrade/turbo/${tg_id}?level=${level}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.error) {
            showNotification(result.error, 'error');
        } else {
            showNotification(result.message, 'success');
            await loadUserData();
        }
    } catch (error) {
        showNotification('Ошибка покупки', 'error');
    }
}

// ---------- УЛУЧШЕНИЕ ПОДВЕСКИ ----------
async function upgradeSuspension() {
    const select = document.getElementById('suspensionSelect');
    const level = parseInt(select.value);
    
    try {
        const response = await fetch(`/api/upgrade/suspension/${tg_id}?level=${level}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.error) {
            showNotification(result.error, 'error');
        } else {
            showNotification(result.message, 'success');
            await loadUserData();
        }
    } catch (error) {
        showNotification('Ошибка покупки', 'error');
    }
}

// ---------- УСТАНОВКА САБВУФЕРА ----------
async function upgradeSubwoofer() {
    const level = parseInt(document.getElementById('subLevel').value);
    const brand = document.getElementById('subBrand').value;
    const genre = document.getElementById('musicGenre').value;
    
    try {
        const response = await fetch(`/api/upgrade/subwoofer/${tg_id}?level=${level}&brand=${brand}&genre=${genre}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.error) {
            showNotification(result.error, 'error');
        } else {
            showNotification(result.message, 'success');
            await loadUserData();
        }
    } catch (error) {
        showNotification('Ошибка установки', 'error');
    }
}

// ---------- ПОКУПКА ДВИГАТЕЛЯ (ЗАГЛУШКА - НУЖНО ДОРАБОТАТЬ) ----------
async function upgradeEngine() {
    showNotification('Функция в разработке', 'error');
}

// ---------- ГОНКА С БОТОМ ----------
async function raceWithBot() {
    try {
        const response = await fetch(`/api/race/bot/${tg_id}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.error) {
            showNotification(result.error, 'error');
        } else {
            showNotification(result.message, result.is_winner ? 'success' : 'error');
            await loadUserData();
        }
    } catch (error) {
        showNotification('Ошибка гонки', 'error');
    }
}

// ---------- УЛУЧШЕНИЕ ПРОВОДКИ (ЗАГЛУШКА) ----------
function upgradeWiring() {
    showNotification('Проводка будет доступна в следующем обновлении', 'error');
}

// ---------- ПОКАЗ УВЕДОМЛЕНИЙ ----------
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.remove('hidden', 'success', 'error');
    notification.classList.add(type);
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

// ---------- ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ----------
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Убираем активный класс у всех кнопок
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Прячем все вкладки
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        
        // Показываем нужную
        const tabId = btn.dataset.tab;
        document.getElementById(`tab-${tabId}`).classList.add('active');
    });
});

// ---------- ЗАГРУЗКА ПРИ СТАРТЕ ----------
if (tg_id) {
    loadUserData();
} else {
    showNotification('Ошибка: не удалось получить ID пользователя', 'error');
}