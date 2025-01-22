from PIL import Image
import numpy as np

# Словарь для сопоставления цветов с ID блоков
color_to_id = {
    (0, 0, 0): 71,         # Черный цвет - ID блока 71
    (255, 255, 255): 84,   # Белый цвет - ID блока 84
    (255, 0, 0): 155,      # Красный цвет - ID блока 155
    (0, 255, 0): 67,       # Зеленый цвет - ID блока 67
    (0, 0, 255): 86,       # Синий цвет - ID блока 86
    (255, 255, 0): 42,     # Желтый цвет - ID блока 42
    (0, 255, 255): 43,     # Голубой цвет - ID блока 43
    (192, 192, 192): 10    # Серый цвет - ID блока 10
}

def closest_color(pixel):
    min_distance = float('inf')
    closest_id = None
    for color, block_id in color_to_id.items():
        distance = np.sqrt(sum((px - cx) ** 2 for px, cx in zip(pixel, color)))
        if distance < min_distance:
            min_distance = distance
            closest_id = block_id
    return closest_id

def image_to_block_commands(image_path):
    # Открываем изображение
    image = Image.open(image_path)
    # Преобразуем изображение в размер 150x150 пикселей
    image = image.resize((150, 150), Image.LANCZOS)
    # Преобразуем изображение в массив numpy
    image_array = np.array(image)
    
    commands = []
    
    # Идентифицируем каждый цвет и формируем команды
    for y in range(image_array.shape[0]):
        for x in range(image_array.shape[1]):
            pixel = tuple(image_array[y, x][:3])  # Игнорируем альфа-канал, если он есть
            block_id = closest_color(pixel)
            command = f"!b={block_id}:{y}:{x}:0"
            commands.append(command)

    return commands

# Пример использования
image_path = '1.webp'  # Укажите путь к изображению
commands = image_to_block_commands(image_path)

# Объединяем все команды в одну строку
output = ''.join(commands)

# Выводим результат
print(output)
