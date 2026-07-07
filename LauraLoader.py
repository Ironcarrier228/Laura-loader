import sys
import subprocess
import os
import time
import requests
import zipfile
import hashlib
import json
import webbrowser
from tqdm import tqdm
from keyauth import api
import psutil

# ======================== НАСТРОЙКИ ========================
loader_version = "1.0.8"  # Фикс user_data
cheat_version = "1.5.0"
VERSION_FILE_LOADER = "loader.version"
CLIENT_DIR = r"C:\LauraClient"
CLIENT_URL = "https://www.dropbox.com/scl/fi/800hclzzujbdj6hh44nt2/client.zip?rlkey=xvfy101lmuw1oafwqks4kre3i&st=ippl2vzk&dl=1"
CONFIG_FILE = "loader_config.json"
DEFAULT_JAVA_EXE = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.15.6-hotspot\bin\java.exe"

# ======================== GITHUB ===========================
GITHUB_USER = "Ironcarrier228"
GITHUB_REPO = "Laura-Client"
GITHUB_BRANCH = "master"
GITHUB_JAR_PATH = "client.jar"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?path={GITHUB_JAR_PATH}&sha={GITHUB_BRANCH}&per_page=1"
GITHUB_DOWNLOAD = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_JAR_PATH}"
VERSION_FILE = os.path.join(CLIENT_DIR, ".jar_version")
LOADER_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/loader_version.txt"
LOADER_DOWNLOAD_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/LauraLoader.exe"

# ======================== CONFIG ===========================
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"java_path": DEFAULT_JAVA_EXE}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

config = load_config()
JAVA_EXE = config.get("java_path", DEFAULT_JAVA_EXE)

# ======================== KEYAUTH ==========================
def getchecksum():
    md5 = hashlib.md5()
    with open(sys.argv[0], "rb") as f:
        md5.update(f.read())
    return md5.hexdigest()

keyauthapp = api(
    name="Elhan",
    ownerid="AtwJqdx5tK",
    version="1.0",
    hash_to_check=getchecksum()
)

# ======================== TIME SYNC ========================
def sync_windows_time():
    print("[Время] Синхронизация времени Windows...")
    try:
        result = subprocess.run(["w32tm", "/resync", "/force"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[Время] Синхронизация успешна ✓")
            time.sleep(2)
            return True
        else:
            print(f"[Время] Ошибка: {result.stderr}")
            return False
    except Exception as e:
        print(f"[Время] Ошибка: {e}")
        return False

def check_system_time():
    try:
        import ntplib
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org', version=3, timeout=5)
        from datetime import datetime
        server_time = datetime.fromtimestamp(response.tx_time)
        local_time = datetime.now()
        time_diff = abs(response.offset)
        print(f"[Время] Сервер NTP: {server_time.strftime('%H:%M:%S')}")
        print(f"[Время] Локальное:  {local_time.strftime('%H:%M:%S')}")
        print(f"[Время] Разница:    {time_diff:.2f} сек")
        if time_diff > 5:
            print("\n[Предупреждение] Время сильно отличается!")
            return False
        return True
    except Exception as e:
        print(f"[Время] Не удалось проверить NTP: {e}")
        return False

def force_time_sync():
    print("\n[Время] Проверка синхронизации...")
    if check_system_time():
        print("[Время] Время синхронизировано ✓\n")
        return True
    print("\n[Время] Попытка автоматической синхронизации...")
    if sync_windows_time():
        print("[Время] Повторная проверка...")
        time.sleep(2)
        if check_system_time():
            print("[Время] Время успешно синхронизировано ✓\n")
            return True
    print("\n[Предупреждение] Не удалось синхронизировать время автоматически")
    print("\nДля ручного исправления:")
    print("  1. Откройте командную строку ОТ АДМИНИСТРАТОРА")
    print("  2. Введите: w32tm /resync /force")
    print("  3. Запустите лоадер снова")
    print()
    choice = input("Продолжить без синхронизации? (y/n): ").lower()
    return choice == 'y'

# ======================== LOADER UPDATE ====================
def get_loader_version():
    if os.path.exists(VERSION_FILE_LOADER):
        try:
            with open(VERSION_FILE_LOADER, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return loader_version

def save_loader_version(version):
    with open(VERSION_FILE_LOADER, "w", encoding="utf-8") as f:
        f.write(version)

def check_loader_update():
    try:
        print("[Лоадер] Проверка обновлений...")
        r = requests.get(LOADER_VERSION_URL, timeout=5)
        if r.status_code != 200:
            print("[Лоадер] Не удалось проверить обновления")
            return
        github_version = r.text.strip()
        current_version = get_loader_version()
        if github_version == current_version:
            print(f"[Лоадер] Версия актуальна ({current_version}) ✓")
            return
        print(f"\n{'='*50}")
        print(f"[Лоадер] Найдено обновление!")
        print(f"  Текущая версия: {current_version}")
        print(f"  Новая версия:   {github_version}")
        print(f"{'='*50}\n")
        choice = input("Обновить лоадер? (y/n): ").lower()
        if choice != 'y':
            print("[Лоадер] Обновление отменено")
            return
        update_loader(github_version)
    except Exception as e:
        print(f"[Лоадер] Ошибка проверки обновлений: {e}")

def update_loader(github_version):
    try:
        print("[Лоадер] Скачивание обновления...")
        r = requests.get(LOADER_DOWNLOAD_URL, stream=True, timeout=30)
        if r.status_code != 200:
            print(f"[Лоадер] Ошибка скачивания (код {r.status_code})")
            return
        total = int(r.headers.get("content-length", 0))
        bar = tqdm(total=total, unit="B", unit_scale=True, desc="LauraLoader.exe")
        new_exe = "LauraLoader_new.exe"
        with open(new_exe, "wb") as f:
            for chunk in r.iter_content(8192):
                bar.update(len(chunk))
                f.write(chunk)
        bar.close()
        print("[Лоадер] Создание скрипта обновления...")
        updater_script = f"""@echo off
echo Обновление лоадера...
timeout /t 2 /nobreak >nul
taskkill /F /IM "LauraLoader.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
del "LauraLoader.exe" >nul 2>&1
ren "LauraLoader_new.exe" "LauraLoader.exe"
echo {github_version} > loader.version
echo Обновление завершено! Версия: {github_version}
timeout /t 1 /nobreak >nul
cd /d "%~dp0"
start "" "LauraLoader.exe"
timeout /t 2 /nobreak >nul
del "%~f0"
"""
        with open("updater.bat", "w", encoding="utf-8") as f:
            f.write(updater_script)
        print("[Лоадер] Запуск обновления...")
        subprocess.Popen(["updater.bat"], shell=True)
        time.sleep(3)
        sys.exit(0)
    except Exception as e:
        print(f"[Лоадер] Ошибка обновления: {e}")
        if os.path.exists("LauraLoader_new.exe"):
            os.remove("LauraLoader_new.exe")

# ======================== AUTH =============================
def auth():
    current_version = get_loader_version()
    print(f"\n{'='*50}")
    print(f"Laura Client Loader v{current_version}")
    print(f"{'='*50}\n")
    check_loader_update()
    if not force_time_sync():
        print("\n[Ошибка] Требуется синхронизация времени для авторизации")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    print("[Сеть] Проверка подключения...")
    try:
        requests.get("https://keyauth.com", timeout=5)
        print("[Сеть] Подключение есть ✓\n")
    except:
        print("[Ошибка] Нет подключения к интернету!")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            key = input(f"Введите ключ (попытка {attempt + 1}/{max_retries}): ")
            print("[Авторизация] Проверка ключа...")
            keyauthapp.license(key)
            if keyauthapp.sessionid:
                print(f"\n[Успех] Авторизация прошла успешно!")
                try:
                    print(f"  Пользователь: {keyauthapp.user_data.username}")
                    print(f"  Срок действия: {keyauthapp.user_data.expiry}")
                except:
                    pass
                print()
                return
            else:
                print(f"[Ошибка] Не удалось авторизоваться")
        except Exception as e:
            error_msg = str(e)
            print(f"\n[Ошибка KeyAuth] {type(e).__name__}: {error_msg}")
            if "Timestamp" in error_msg or "timestamp" in error_msg.lower():
                print("\n[Ошибка] Проблема со временем!")
                print("Запуск повторной синхронизации...")
                sync_windows_time()
                print("Попробуйте ввести ключ снова")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                print("\n[Ошибка] Проблема с подключением к интернету")
            elif "invalid" in error_msg.lower() or "key" in error_msg.lower():
                print("\n[Ошибка] Неверный или истёкший ключ")
            else:
                print(f"\n[Ошибка] Неизвестная ошибка: {error_msg}")
            if attempt < max_retries - 1:
                print(f"\n[Попытка] Повтор через 3 секунды...\n")
                time.sleep(3)
            else:
                print("\n[Ошибка] Превышено количество попыток")
                input("Нажмите Enter для выхода...")
                sys.exit(1)

# ======================== DOWNLOAD =========================
def download_and_extract():
    if not os.path.exists(CLIENT_DIR):
        os.makedirs(CLIENT_DIR)
    for root, _, files in os.walk(CLIENT_DIR):
        for f in files:
            if f.lower() == "client.jar":
                print("[Инфо] Клиент уже загружен.")
                return
    zip_path = os.path.join(CLIENT_DIR, "client.zip")
    print("[Загрузка] Скачивание клиента...")
    r = requests.get(CLIENT_URL, stream=True)
    total = int(r.headers.get("content-length", 0))
    bar = tqdm(total=total, unit="B", unit_scale=True)
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(1024):
            bar.update(len(chunk))
            f.write(chunk)
    bar.close()
    print("[Распаковка] Извлечение...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(CLIENT_DIR)
    os.remove(zip_path)

# ======================== FIND FILES =======================
def find_client_jar():
    for root, _, files in os.walk(CLIENT_DIR):
        for f in files:
            if f.lower() == "client.jar":
                return os.path.join(root, f)
    return None

# ======================== AUTO UPDATE ======================
def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return None

def save_local_version(commit_sha):
    os.makedirs(CLIENT_DIR, exist_ok=True)
    with open(VERSION_FILE, "w") as f:
        f.write(commit_sha)

def get_github_latest_commit():
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        r = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                return data[0]["sha"]
        elif r.status_code == 403:
            print("[Обновление] Превышен лимит запросов GitHub API.")
        else:
            print(f"[Обновление] GitHub недоступен (код {r.status_code})")
    except requests.exceptions.ConnectionError:
        print("[Обновление] Нет подключения к интернету.")
    except Exception as e:
        print(f"[Обновление] Ошибка: {e}")
    return None

def download_jar_update(jar_path):
    try:
        print("[Обновление] Скачивание нового client.jar...")
        r = requests.get(GITHUB_DOWNLOAD, stream=True, timeout=30)
        if r.status_code != 200:
            print(f"[Обновление] Ошибка скачивания (код {r.status_code})")
            return False
        total = int(r.headers.get("content-length", 0))
        bar = tqdm(total=total, unit="B", unit_scale=True, desc="client.jar")
        tmp_path = jar_path + ".tmp"
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(8192):
                bar.update(len(chunk))
                f.write(chunk)
        bar.close()
        if os.path.exists(jar_path):
            os.remove(jar_path)
        os.rename(tmp_path, jar_path)
        return True
    except Exception as e:
        print(f"[Обновление] Ошибка при скачивании: {e}")
        if os.path.exists(jar_path + ".tmp"):
            os.remove(jar_path + ".tmp")
        return False

def check_for_updates():
    print("[Обновление] Проверка обновлений client.jar...")
    latest_commit = get_github_latest_commit()
    if not latest_commit:
        print("[Обновление] Не удалось проверить обновления, продолжаем...")
        return
    local_version = get_local_version()
    if local_version == latest_commit:
        print("[Обновление] client.jar актуален ✓")
        return
    if local_version is None:
        print("[Обновление] Первый запуск, скачиваем client.jar...")
    else:
        print(f"[Обновление] Найдено обновление!")
        print(f"  Текущая версия: {local_version[:7]}")
        print(f"  Новая версия:   {latest_commit[:7]}")
    jar_path = find_client_jar()
    if not jar_path:
        print("[Обновление] client.jar не найден, установка через Dropbox...")
        return
    if download_jar_update(jar_path):
        save_local_version(latest_commit)
        print(f"[Обновление] client.jar успешно обновлён до {latest_commit[:7]} ✓")
    else:
        print("[Обновление] Не удалось обновить, запускаем старую версию...")

# ======================== JAVA =============================
def find_java_by_version(major_version):
    for java_path in find_java_installations():
        version = check_java_version(java_path)
        if version:
            if major_version == 17 and version.startswith("17"):
                return java_path
            if major_version == 21 and version.startswith("21"):
                return java_path
    return None

def get_java_for_version(mc_version):
    if mc_version.startswith("1.20.5") or mc_version.startswith("1.21"):
        return 21
    elif mc_version.startswith("1.17") or mc_version.startswith("1.18") or \
         mc_version.startswith("1.19") or mc_version.startswith("1.20"):
        return 17
    else:
        return 17

def detect_minecraft_version(client_jar_path):
    try:
        import zipfile
        with zipfile.ZipFile(client_jar_path, 'r') as z:
            if 'version.json' in z.namelist():
                with z.open('version.json') as f:
                    data = json.load(f)
                    return data.get('id', '1.16.5')
    except:
        pass
    return '1.16.5'

def setup_java_path():
    global JAVA_EXE, config
    print("\n=== Настройка пути к Java ===")
    print(f"Текущий путь: {JAVA_EXE}")
    print(f"Текущая версия: {check_java_version(JAVA_EXE) or 'не определена'}")
    print()
    print("[Поиск] Попытка найти Java автоматически...")
    found_java = find_java_installations()
    if found_java:
        print("\nНайденные установки Java:")
        for i, java_path in enumerate(found_java, 1):
            version = check_java_version(java_path)
            print(f"  {i}. {java_path}")
            if version:
                print(f"     Версия: {version}")
        print()
        choice = input("Выберите номер (Enter - ввести путь вручную): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(found_java):
            new_path = found_java[int(choice) - 1]
            if verify_java_path(new_path):
                JAVA_EXE = new_path
                config["java_path"] = new_path
                save_config(config)
                print(f"\n[Успех] Путь к Java обновлён: {new_path}")
                return
    print("\nВведите путь к java.exe (или Enter для отмены):")
    new_path = input("> ").strip().strip('"')
    if not new_path:
        print("[Отмена] Путь не изменён.")
        return
    if verify_java_path(new_path):
        JAVA_EXE = new_path
        config["java_path"] = new_path
        save_config(config)
        print(f"\n[Успех] Путь к Java обновлён: {new_path}")
    else:
        print("\n[Ошибка] Некорректный путь или Java не найдена.")

def verify_java_path(path):
    if not os.path.exists(path):
        return False
    if not os.path.isfile(path):
        return False
    if not (path.endswith("java.exe") or path.endswith("java")):
        return False
    try:
        result = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=5)
        output = result.stderr + result.stdout
        if "version" in output.lower():
            if any(v in output for v in ["17.", "18.", "19.", "20.", "21.", "22.", "23."]):
                return True
            else:
                print("[Предупреждение] Найдена Java, но рекомендуется Java 17+")
                return True
    except:
        pass
    return False

def find_java_installations():
    java_paths = []
    if sys.platform == "win32":
        search_dirs = [
            r"C:\Program Files\Java",
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\Program Files\Eclipse Foundation",
            r"C:\Program Files (x86)\Java",
            r"C:\Program Files\Microsoft\jdk-17",
            r"C:\Program Files\Microsoft\jdk-21",
            r"C:\Program Files\Zulu\zulu-17",
            r"C:\Program Files\Zulu\zulu-21",
            r"C:\Program Files\Amazon Corretto\jdk17",
            r"C:\Program Files\Amazon Corretto\jdk21"
        ]
        for base_dir in search_dirs:
            if os.path.exists(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    if "java.exe" in files:
                        java_path = os.path.join(root, "java.exe")
                        if verify_java_path(java_path):
                            java_paths.append(java_path)
    elif sys.platform == "darwin":
        search_dirs = ["/Library/Java/JavaVirtualMachines", "/System/Library/Java/JavaVirtualMachines"]
        for base_dir in search_dirs:
            if os.path.exists(base_dir):
                for jdk in os.listdir(base_dir):
                    java_path = os.path.join(base_dir, jdk, "Contents/Home/bin/java")
                    if os.path.exists(java_path) and verify_java_path(java_path):
                        java_paths.append(java_path)
    else:
        search_dirs = ["/usr/lib/jvm", "/usr/java", "/opt/java"]
        for base_dir in search_dirs:
            if os.path.exists(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    if "java" in files and "bin" in root:
                        java_path = os.path.join(root, "java")
                        if verify_java_path(java_path):
                            java_paths.append(java_path)
    return java_paths

def check_java_version(java_path):
    try:
        result = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=5)
        output = result.stderr + result.stdout
        import re
        match = re.search(r'version "?(\d+\.?\d*)', output)
        if match:
            return match.group(1)
    except:
        pass
    return None

# ======================== RUN ==============================
def run_cheat():
    print("[Чит] Подготовка...")
    download_and_extract()
    check_for_updates()
    client_jar = find_client_jar()
    if not client_jar:
        print("[Ошибка] client.jar не найден.")
        return
    mc_version = detect_minecraft_version(client_jar)
    print(f"[Инфо] Версия Minecraft: {mc_version}")
    required_java = get_java_for_version(mc_version)
    print(f"[Инфо] Требуется Java {required_java}")
    java_path = find_java_by_version(required_java)
    if not java_path:
        java_path = JAVA_EXE
        print(f"[Предупреждение] Java {required_java} не найдена, используем настроенную")
    java_version = check_java_version(java_path)
    if java_version:
        actual_version = int(java_version.split('.')[0]) if '.' in java_version else int(java_version)
        if required_java == 21 and actual_version < 21:
            print(f"[Ошибка] Для Minecraft {mc_version} нужна Java 21, а найдена Java {java_version}")
            return
        if required_java == 17 and actual_version < 17:
            print(f"[Ошибка] Для Minecraft {mc_version} нужна Java 17+, а найдена Java {java_version}")
            return
    libs_dir = os.path.join(CLIENT_DIR, "libraries")
    libs = []
    if os.path.exists(libs_dir):
        for root, _, files in os.walk(libs_dir):
            for f in files:
                if f.endswith(".jar"):
                    libs.append(os.path.join(root, f))
    separator = ";" if sys.platform == "win32" else ":"
    classpath = separator.join([client_jar] + libs)
    total_ram = int(psutil.virtual_memory().total / (1024 ** 3))
    while True:
        try:
            mem = int(input(f"Введите RAM (1–{total_ram - 1} ГБ): "))
            if 1 <= mem < total_ram:
                break
            print("Недопустимое значение.")
        except ValueError:
            print("Введите число.")
    print(f"[Java] Используется: {java_path}")
    if java_version:
        print(f"[Java] Версия: {java_version}")
    print("[Запуск] Клиент запускается...\n")
    jvm_args = [f"-Xmx{mem}G"]
    if java_version and java_version.startswith("21"):
        jvm_args.extend([
            "--add-opens", "java.base/java.lang=ALL-UNNAMED",
            "--add-opens", "java.base/java.util=ALL-UNNAMED",
            "--add-opens", "java.base/java.lang.reflect=ALL-UNNAMED",
            "--add-opens", "java.base/java.text=ALL-UNNAMED",
            "--add-opens", "java.desktop/java.awt.font=ALL-UNNAMED",
            "--add-opens", "java.base/java.io=ALL-UNNAMED",
            "--add-opens", "java.base/java.net=ALL-UNNAMED",
            "--add-opens", "java.base/java.nio=ALL-UNNAMED",
            "--add-opens", "java.base/java.util.concurrent=ALL-UNNAMED",
            "-Djava.awt.headless=false"
        ])
    jvm_args.extend(["-cp", classpath, "Start"])
    subprocess.Popen([java_path] + jvm_args, cwd=os.path.dirname(client_jar))
    print("[Успех] Клиент запущен!")

# ======================== MENU =============================
def menu():
    while True:
        print(f"\n{'='*50}")
        print("=== Главное меню ===")
        print(f"{'='*50}")
        print("1. Версия лоадера")
        print("2. Версия чита")
        print("3. Запустить чит")
        print("4. Выход")
        print("5. Настроить путь к Java")
        print("6. Проверить обновления client.jar")
        print("7. Открыть GitHub репозиторий")
        print("8. Обновить лоадер")
        print("9. Синхронизировать время")
        c = input("Выбор: ")
        if c == "1":
            print(f"\nВерсия лоадера: {get_loader_version()}")
        elif c == "2":
            print(f"\nВерсия чита: {cheat_version}")
        elif c == "3":
            run_cheat()
        elif c == "4":
            print("\nВыход...")
            break
        elif c == "5":
            setup_java_path()
        elif c == "6":
            check_for_updates()
        elif c == "7":
            github_url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
            print(f"\n[GitHub] Открываю {github_url}")
            webbrowser.open(github_url)
            print("[GitHub] Репозиторий открыт в браузере ✓")
        elif c == "8":
            check_loader_update()
        elif c == "9":
            sync_windows_time()
            check_system_time()
        else:
            print("Неверный выбор.")

# ======================== START ===========================
if __name__ == "__main__":
    auth()
    menu()
