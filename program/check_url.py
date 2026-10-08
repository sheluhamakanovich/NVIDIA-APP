#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПРОВЕРКА КАКОЙ URL ИСПОЛЬЗУЕТ MAIN.PY

Показывает какой URL будет использовать main.py при подключении к боту.
Это помогает понять почему testconnect.py может не работать.
"""

import os
import sys

def read_config_ini():
    """Читает config.ini"""
    try:
        import configparser
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        if not os.path.exists(config_path):
            return None, "config.ini не найден"
        
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        if 'SERVER' in config:
            url = config['SERVER'].get('url', '').strip()
            if url and (url.startswith('http://') or url.startswith('https://')):
                return url, "config.ini"
        
        return None, "URL не задан в config.ini"
    except Exception as e:
        return None, f"Ошибка чтения config.ini: {e}"

def read_bot_url_txt():
    """Читает bot_url.txt"""
    try:
        here = os.path.dirname(__file__)
        cfg = os.path.join(here, 'bot_url.txt')
        
        if not os.path.exists(cfg):
            return None, "bot_url.txt не найден"
        
        with open(cfg, 'r', encoding='utf-8') as f:
            line = (f.read() or '').strip()
            if line.startswith('http://') or line.startswith('https://'):
                return line, "bot_url.txt"
            else:
                return None, f"Неверный URL в bot_url.txt: {line}"
    except Exception as e:
        return None, f"Ошибка чтения bot_url.txt: {e}"

def main():
    print("=" * 70)
    print("  🔍 ПРОВЕРКА КОНФИГУРАЦИИ ПОДКЛЮЧЕНИЯ")
    print("=" * 70)
    print()
    print("Эта программа показывает какой URL будет использовать main.py")
    print()
    
    # 1. Проверяем config.ini (приоритет)
    print("[1/3] 🔍 Проверка config.ini (ПРИОРИТЕТ для интернет)...")
    url1, status1 = read_config_ini()
    if url1:
        print(f"      ✅ НАЙДЕН: {url1}")
        print(f"      📝 Источник: {status1}")
    else:
        print(f"      ℹ️  {status1}")
    print()
    
    # 2. Проверяем UDP broadcast (не можем проверить, но упоминаем)
    print("[2/3] 🔍 UDP broadcast (для локальной сети)...")
    print("      ℹ️  Автоматическое обнаружение в локальной сети")
    print("      ℹ️  Работает только если config.ini не задан")
    print("      ℹ️  Не работает через интернет!")
    print()
    
    # 3. Проверяем bot_url.txt (старый метод)
    print("[3/3] 🔍 Проверка bot_url.txt (legacy)...")
    url3, status3 = read_bot_url_txt()
    if url3:
        print(f"      ✅ НАЙДЕН: {url3}")
        print(f"      📝 Источник: {status3}")
    else:
        print(f"      ℹ️  {status3}")
    print()
    
    # Определяем финальный URL
    print("=" * 70)
    print("  📊 РЕЗУЛЬТАТ")
    print("=" * 70)
    print()
    
    final_url = None
    final_source = None
    
    if url1:
        final_url = url1
        final_source = "config.ini (ПРИОРИТЕТ)"
    elif url3:
        final_url = url3
        final_source = "bot_url.txt (legacy)"
    else:
        print("❌ URL НЕ НАЙДЕН в конфигурации!")
        print()
        print("🔧 main.py будет использовать:")
        print("   1. UDP broadcast (если в локальной сети)")
        print("   2. localhost (http://127.0.0.1:8765) как fallback")
        print()
        print("💡 РЕКОМЕНДАЦИЯ:")
        print("   Создайте config.ini с нужным URL:")
        print("   [SERVER]")
        print("   url = http://192.168.1.100:8765")
        return
    
    print(f"✅ main.py БУДЕТ ИСПОЛЬЗОВАТЬ:")
    print(f"   URL: {final_url}")
    print(f"   Источник: {final_source}")
    print()
    
    # Анализ URL
    if 'localhost' in final_url or '127.0.0.1' in final_url:
        print("🏠 ТИП: LOCALHOST (локальное подключение)")
        print()
        print("   ✅ Работает: на этом же ПК")
        print("   ❌ НЕ работает: с другого ПК через интернет/сеть")
        print()
        print("   💡 Для подключения с других ПК:")
        print("      1. Узнайте IP этого ПК: ipconfig")
        print("      2. Измените config.ini:")
        print("         url = http://ВАШ_IP:8765")
    else:
        print("🌐 ТИП: REMOTE (сетевое/интернет подключение)")
        print()
        print("   ✅ Работает: с других ПК в сети/интернете")
        print("   ℹ️  Требуется: открытый порт 8765, нет firewall блокировки")
    
    print()
    print("🧪 ДЛЯ ПРОВЕРКИ ПОДКЛЮЧЕНИЯ:")
    print(f"   python testconnect.py {final_url}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
