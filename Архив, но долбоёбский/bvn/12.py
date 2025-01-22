import struct
import requests
import asyncio
import websockets
import json
import time
import random
import tkinter as tk
import threading
from PIL import Image, ImageTk
from movement import right_click  # Импорт функции движения по правому клику

# Глобальные переменные для размеров холста и карты
CANVAS_WIDTH = 750
CANVAS_HEIGHT = 750
MAP_SIZE = 15000  # Размер игровой карты в юнитах
SCALING_FACTOR = CANVAS_WIDTH / MAP_SIZE  # Коэффициент масштабирования для перевода юнитов карты в пиксели холста

# Словарь для отслеживания сущностей
tracked_entities = {}
textures = {
    13: 'ghoul.png',  # Путь к специальной текстуре игрока
    0: 'player.png',  # Путь к текстуре игрока
    2: 'block.png', 3: 'block.png', 4: 'box.png', 5: 'block.png',
    6: 'floor.png', 7: 'block.png', 8: 'wood.png', 9: 'orange.png',
    10: 'stone.png', 11: 'wood.png', 12: 'block.png', 1: 'wood.png'
}

# Глобальный словарь для хранения измененных изображений, чтобы избежать их сборки мусора
image_cache = {}

# Глобальные переменные для управления зумом и камерой
zoom_level = 1.0
camera_offset_x = 0
camera_offset_y = 0
is_dragging = False
drag_start_x = 0
drag_start_y = 0

# Функция для изменения размера изображения с использованием PIL
def resize_image(texture_path, size):
    try:
        if (texture_path, size) not in image_cache:
            image = Image.open(texture_path)  # Открыть файл изображения
            resized_image = image.resize((size, size), Image.LANCZOS)  # Изменить размер изображения с использованием LANCZOS
            image_cache[(texture_path, size)] = ImageTk.PhotoImage(resized_image)  # Преобразовать в PhotoImage и кешировать
        return image_cache[(texture_path, size)]
    except Exception as e:
        print(f"Ошибка при изменении размера изображения: {e}")
        return None

# Функция для отрисовки сущности на холсте с удалением прошлой позиции
def draw_entity(canvas, entity_type, x, y, entity_id=None):
    try:
        # Масштабирование координат
        global camera_offset_x, camera_offset_y, zoom_level
        scaled_x = (x * SCALING_FACTOR + camera_offset_x) * zoom_level
        scaled_y = (y * SCALING_FACTOR + camera_offset_y) * zoom_level

        # Определение размера в зависимости от типа сущности
        size = 15 if entity_type in [1, 13] else 8 if entity_type in textures else 10
        size = int(size * zoom_level)

        # Если сущность уже существует, удалим её предыдущую позицию
        if entity_id in tracked_entities:
            if 'canvas_id' in tracked_entities[entity_id]:
                canvas.delete(tracked_entities[entity_id]['canvas_id'])  # Удаление предыдущего объекта

        # Отрисовка сущности на основе текстуры
        if entity_type in textures:
            texture_path = textures[entity_type]
            image = resize_image(texture_path, size)
            if image is None:
                return
            entity_image = canvas.create_image(scaled_x, scaled_y, image=image, anchor=tk.CENTER)
            tracked_entities[entity_id] = {'type': 'image', 'canvas_id': entity_image, 'image': image}
        else:
            # Отрисовка игрока или блока
            if entity_type in [1, 13]:
                radius = 5
                player = canvas.create_oval(scaled_x - radius, scaled_y - radius, scaled_x + radius, scaled_y + radius, fill='blue', outline='black')
                tracked_entities[entity_id] = {'type': 'oval', 'canvas_id': player}
            else:
                size = 10
                block = canvas.create_rectangle(scaled_x, scaled_y, scaled_x + size, scaled_y + size, fill='green', outline='black')
                tracked_entities[entity_id] = {'type': 'rectangle', 'canvas_id': block}

    except Exception as e:
        print(f"Ошибка при отрисовке сущности: {e}")

# Функция для обработки данных
def process_data(data, canvas):
    try:
        if len(data) < 2:
            return

        ui8 = data
        ui16 = struct.unpack('<' + 'H' * (len(ui8) // 2), ui8)
        length = (len(ui8) - 2) // 18

        for i in range(length):
            isRef8 = 2 + i * 18
            isRef16 = 1 + i * 9

            if isRef8 + 18 > len(ui8) or isRef16 + 9 > len(ui16):
                continue

            pid = ui8[isRef8]
            uid = ui8[isRef8 + 1]
            type_ = ui8[isRef8 + 3]
            state = ui16[isRef16 + 2]
            id_ = ui16[isRef16 + 3]
            x = ui16[isRef16 + 4]
            y = ui16[isRef16 + 5]
            extra = ui16[isRef16 + 8]

            # Проверка наличия данных
            if pid is None or uid is None or type_ is None or id_ is None:
                print("Отсутствуют данные сущности")
                continue

            # Проверка на существующую сущность
            existing_entity = None
            for entity_id, entity_data in tracked_entities.items():
                if entity_data.get('pid') == pid and entity_data.get('uid') == uid:
                    existing_entity = entity_id
                    break

            # Обновление или удаление сущности
            if existing_entity:
                if entity_data.get('x') != x or entity_data.get('y') != y:
                    canvas.delete(tracked_entities[existing_entity]['canvas_id'])
                    del tracked_entities[existing_entity]
                else:
                    draw_entity(canvas, type_, x, y, existing_entity)  # Обновление позиции сущности
            else:
                if state != 0:
                    draw_entity(canvas, type_, x, y, id_)  # Новая сущность
                    tracked_entities[id_] = {'pid': pid, 'uid': uid}
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")

# Функции для отправки запросов и инициализации соединения
def send_options(base_url):
    headers = {'Content-Type': 'application/json', 'Origin': 'https://devast.io'}
    try:
        return requests.options(base_url, headers=headers)
    except Exception as e:
        print(f"Ошибка при отправке OPTIONS-запроса: {e}")
        return None

def send_post(base_url):
    headers = {'Content-Type': 'application/json', 'Origin': 'https://devast.io'}
    payload = {"lobby_id": "2acd2dbf-2238-444b-9c0b-291b8a1ea1b1"}
    try:
        response = requests.post(base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при отправке POST-запроса: {e}")
        return None

def initialize_connection(base_url):
    options_response = send_options(base_url)
    if options_response is None:
        return None, None

    post_response = send_post(base_url)
    if post_response is None:
        return None, None

    try:
        token = post_response['player']['token']
        host = post_response['ports']['default']['hostname']
        return token, host
    except Exception as e:
        print(f"Ошибка при инициализации соединения: {e}")
        return None, None

# Вебсокет-соединение
async def connect_websocket(base_url, canvas):
    for _ in range(4):
        token, host = initialize_connection(base_url)
        if token is None or host is None:
            await asyncio.sleep(5)
            continue

        websocket_url = f"wss://{host}/?token={token}"
        try:
            async with websockets.connect(websocket_url) as ws:
                random_value = random.randint(0, 100000)
                message = [30, "DEVASTCHEAT", random_value, 81, 0, "Perf", 0, 0, 0]
                await ws.send(json.dumps(message))

                while True:
                    response = await ws.recv()

                    if isinstance(response, str):
                        try:
                            data = json.loads(response)
                            if isinstance(data, list) and all(isinstance(i, (int, float)) for i in data):
                                process_data(bytes(data), canvas)
                        except Exception as e:
                            print(f"Ошибка при обработке данных вебсокета: {e}")
                    elif isinstance(response, bytes):
                        process_data(response, canvas)
        except Exception as e:
            print(f"Ошибка подключения к вебсокету: {e}")
            await asyncio.sleep(5)

# Обработчик события нажатия на колесо мыши (для перемещения камеры)
def on_middle_button_press(event):
    global is_dragging, drag_start_x, drag_start_y
    is_dragging = True
    drag_start_x = event.x
    drag_start_y = event.y

# Обработчик события отпускания средней кнопки мыши
def on_middle_button_release(event):
    global is_dragging
    is_dragging = False

# Функция для обновления позиции всех объектов на холсте
def update_canvas_objects(canvas):
    global tracked_entities, camera_offset_x, camera_offset_y, zoom_level
    for entity_id, entity_data in tracked_entities.items():
        if entity_data['type'] == 'oval':
            # Получение координат для oval (игрок)
            canvas_coords = canvas.coords(entity_data['canvas_id'])
            new_x = canvas_coords[0] + camera_offset_x * zoom_level
            new_y = canvas_coords[1] + camera_offset_y * zoom_level
            canvas.move(entity_data['canvas_id'], new_x - canvas_coords[0], new_y - canvas_coords[1])
        elif entity_data['type'] == 'rectangle':
            # Получение координат для rectangle (блок)
            canvas_coords = canvas.coords(entity_data['canvas_id'])
            new_x = canvas_coords[0] + camera_offset_x * zoom_level
            new_y = canvas_coords[1] + camera_offset_y * zoom_level
            canvas.move(entity_data['canvas_id'], new_x - canvas_coords[0], new_y - canvas_coords[1])
        elif entity_data['type'] == 'image':
            # Получение координат для image (текстура)
            canvas_coords = canvas.coords(entity_data['canvas_id'])
            new_x = canvas_coords[0] + camera_offset_x * zoom_level
            new_y = canvas_coords[1] + camera_offset_y * zoom_level
            canvas.move(entity_data['canvas_id'], new_x - canvas_coords[0], new_y - canvas_coords[1])

# Обработчик события движения мыши (для перемещения камеры)
def on_mouse_motion(event):
    global is_dragging, camera_offset_x, camera_offset_y, drag_start_x, drag_start_y
    if is_dragging:
        delta_x = event.x - drag_start_x
        delta_y = event.y - drag_start_y
        camera_offset_x += delta_x / zoom_level
        camera_offset_y += delta_y / zoom_level
        drag_start_x = event.x
        drag_start_y = event.y
        update_canvas_objects(canvas)  # Обновляем позиции всех объектов



# Функция для изменения уровня зума
def zoom(event, canvas):
    global zoom_level
    if event.char == '+':
        zoom_level = min(zoom_level * 1.1, 5.0)  # Максимальный зум 5x
    elif event.char == '-':
        zoom_level = max(zoom_level / 1.1, 0.5)  # Минимальный зум 0.5x
    canvas.delete("all")  # Перерисовка карты

# Главная функция с инициализацией GUI и вебсокета
def main():
    global canvas
    window = tk.Tk()
    window.title("Game Map")
    window.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}")
    canvas = tk.Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
    canvas.pack()

    # Привязка событий для управления камерой
    canvas.bind("<Button-2>", on_middle_button_press)  # Нажатие средней кнопки мыши
    canvas.bind("<ButtonRelease-2>", on_middle_button_release)  # Отпускание средней кнопки мыши
    canvas.bind("<Motion>", on_mouse_motion)  # Движение мыши
    canvas.bind("<Button-3>", right_click)  # Движение мыши
    window.bind("<KeyPress>", lambda event: zoom(event, canvas))  # Управление зумом

    base_url = "https://api.eg.rivet.gg/matchmaker/lobbies/join"
    threading.Thread(target=lambda: asyncio.run(connect_websocket(base_url, canvas))).start()

    window.mainloop()

if __name__ == "__main__":
    main()
