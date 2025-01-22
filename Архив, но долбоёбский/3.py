import json
import os
import aiohttp
import asyncio
import time

# Путь до JSON файла с правилами
json_file_path = 'input.json'

# Папка для сохранения загруженных изображений
output_folder = 'img'

# Создаем папку, если она не существует
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Функция для загрузки изображения по URL
async def download_image(session, url, folder, semaphore):
    async with semaphore:  # Ограничиваем количество одновременно выполняемых задач
        try:
            async with session.get(url) as response:
                response.raise_for_status()  # Проверяем наличие ошибок при запросе
                # Извлекаем имя файла из URL
                filename = os.path.join(folder, url.split('/')[-1])
                with open(filename, 'wb') as file:
                    file.write(await response.read())
                print(f"Загружено: {filename}")
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}")

# Основная асинхронная функция
async def main():
    # Читаем JSON файл
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Создаем сессию aiohttp и семафор для ограничения количества параллельных запросов
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(5)  # Ограничиваем до 15 одновременных запросов
        tasks = []
        # Ищем match в данных и загружаем изображения
        for item in data.get('data', []):
            for rule in item.get('rules', []):
                if rule.get('on') and rule.get('type') == 'normalOverride':
                    match_url = rule['replace']
                    tasks.append(download_image(session, match_url, output_folder, semaphore))
        
        # Запускаем все задачи параллельно, но контролируем количество одновременно выполняемых запросов
        while tasks:
            current_tasks = tasks[:5]  # Берем до 15 задач
            await asyncio.gather(*current_tasks)  # Запускаем задачи
            tasks = tasks[5:]  # Удаляем выполненные задачи
            await asyncio.sleep(1)  # Ждем 1 секунду перед следующей пачкой

# Запускаем асинхронный код
if __name__ == '__main__':
    asyncio.run(main())
    print("Загрузка изображений завершена.")
