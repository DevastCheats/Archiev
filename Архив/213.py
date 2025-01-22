from PIL import Image, ImageTk
import tkinter as tk
import imageio
import numpy as np
import random

# Глобальные переменные
scale = 1
center_x = -0.5
center_y = 0
max_iter = 100
width, height = 1200, 1000
fps = 20
mode = None  # Текущий режим: 'zoom' для приближения, 'record' для записи видео
recording = False  # Флаг записи
frames = []  # Список для хранения кадров

def generate_mandelbrot():
    global width, height, scale, center_x, center_y, max_iter
    
    # Генерация случайного смещения для разнообразия
    random_offset_x = (random.random() - 0.5) * 0.5
    random_offset_y = (random.random() - 0.5) * 0.5
    
    x = np.linspace(center_x - scale / 2 + random_offset_x, center_x + scale / 2 + random_offset_x, width)
    y = np.linspace(center_y - scale / 2 + random_offset_y, center_y + scale / 2 + random_offset_y, height)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.zeros_like(C)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    for i in range(max_iter):
        mask = np.abs(Z) < 2
        img[mask] = np.array([
            0,  # Черный для непринадлежащих к множеству
            0,  # Черный для непринадлежащих к множеству
            255 * i // max_iter  # Синий для значений, которые сходятся
        ])
        Z[mask] = Z[mask] * Z[mask] + C[mask]
    
    img[np.abs(Z) >= 2] = [0, 0, 0]  # Черный для значений, которые не сходятся
    return Image.fromarray(img)

def update_image(img):
    tk_img = ImageTk.PhotoImage(img)
    label.config(image=tk_img)
    label.image = tk_img

def zoom_in(event):
    global scale, center_x, center_y
    
    cx = center_x + (event.x - width / 2) * scale / width
    cy = center_y + (event.y - height / 2) * scale / height
    
    scale /= 2
    center_x = cx
    center_y = cy
    
    img = generate_mandelbrot()
    update_image(img)

def start_recording(event):
    global recording, frames
    if not recording:
        recording = True
        frames = []  # Сброс списка кадров
        zoom_in(event)  # Начинаем с первого кадра
        print("Запись видео начата")

def stop_recording():
    global recording
    if recording:
        recording = False
        with imageio.get_writer('mandelbrot_zoom.mp4', fps=fps) as writer:
            for frame in frames:
                writer.append_data(frame)
        print("Видео сохранено как 'mandelbrot_zoom.mp4'")

def on_click(event):
    global mode, recording
    if mode == 'zoom':
        zoom_in(event)
    elif mode == 'record':
        if not recording:
            start_recording(event)
        else:
            stop_recording()

def set_mode(new_mode):
    global mode
    mode = new_mode
    print(f"Режим установлен на: {mode}")

def setup_gui():
    global label, root
    
    root = tk.Tk()
    root.title("Фрактал Мандельброта")
    
    # Кнопка приближения
    zoom_button = tk.Button(root, text="Приближение", command=lambda: set_mode('zoom'))
    zoom_button.pack(side=tk.LEFT)
    
    # Кнопка записи видео
    record_button = tk.Button(root, text="Записать видео", command=lambda: set_mode('record'))
    record_button.pack(side=tk.LEFT)
    
    # Кнопка остановки записи
    stop_button = tk.Button(root, text="Остановить видео", command=stop_recording)
    stop_button.pack(side=tk.LEFT)
    
    # Создаем начальное изображение
    img = generate_mandelbrot()
    tk_img = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=tk_img)
    label.pack()
    
    # Обработка клика мыши
    root.bind("<Button-1>", on_click)  # Левой кнопкой мыши

    root.mainloop()

if __name__ == "__main__":
    setup_gui()
