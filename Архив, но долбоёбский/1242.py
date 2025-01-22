import os
import platform
import json
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

window_size_file = os.path.join(os.getcwd(), "window_size.json")

def hide_console():
    if platform.system() == "Windows":
        subprocess.Popen("pythonw", creationflags=subprocess.CREATE_NEW_CONSOLE)

def save_window_size(driver):
    size = driver.get_window_size()
    is_fullscreen = driver.get_window_rect()['width'] == driver.execute_script("return window.screen.width") and driver.get_window_rect()['height'] == driver.execute_script("return window.screen.height")
    data = {"size": size, "fullscreen": is_fullscreen}
    with open(window_size_file, 'w') as f:
        json.dump(data, f)

def load_window_size():
    if os.path.exists(window_size_file):
        with open(window_size_file, 'r') as f:
            return json.load(f)
    return {"width": 1200, "height": 800, "fullscreen": False}

temp_profile_dir = os.path.join(os.getcwd(), "chrome_temp_profile")

if not os.path.exists(temp_profile_dir):
    os.makedirs(temp_profile_dir)

options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={temp_profile_dir}")
options.add_argument("--disable-bluetooth")
options.add_argument("--disable-gpu")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_argument("--no-default-browser-check")
options.add_argument("--no-first-run")
options.add_argument("--disable-extensions")
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

# Настройка User-Agent, чтобы запрос выглядел как от реального пользователя
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
options.add_argument(f"user-agent={user_agent}")

# Добавление расширения Vencord
extension_path = r'C:\Vencord.crx'
if os.path.exists(extension_path):
    options.add_extension(extension_path)

window_size = load_window_size()
options.add_argument(f"--window-size={window_size['width']},{window_size['height']}")

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://f.skytime.fun/threads/43208/")
    
    # Имитируем небольшую задержку, как будто пользователь изучает страницу
    time.sleep(5)
    
    # Скроллинг страницы вниз и обратно вверх, имитируя действия пользователя
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    
    # Имитируем движение мыши и клики на элементы (если требуется)
    actions = ActionChains(driver)
    actions.move_by_offset(100, 100).perform()  # Переместить мышь
    time.sleep(2)  # Задержка перед следующей симуляцией
    
    # Цикл с логированием размера окна
    try:
        while True:
            current_size = driver.get_window_size()
            with open("window_log.txt", "a") as log_file:
                log_file.write(f"{current_size['width']}x{current_size['height']}\n")
            time.sleep(5)  # Сделать запросы реже
    except KeyboardInterrupt:
        save_window_size(driver)
except Exception as e:
    with open("error_log.txt", "w") as error_file:
        error_file.write(str(e))
finally:
    driver.quit()
