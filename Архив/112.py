import pygame
import random
import time

# Инициализация Pygame
pygame.init()

# Параметры экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Arkanoid Game")

ball_speed_x = 1
ball_speed_y = 1

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Параметры ракетки
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10
paddle_speed = 6

# Параметры шариков
BALL_SIZE = 10
ball_speed = 4

# Параметры кубиков
BRICK_WIDTH = 60
BRICK_HEIGHT = 20
bricks = []

# Параметры улучшений
POWERUP_SIZE = 20
powerups = []
powerup_chance = 0.1  # Шанс выпадения улучшения

# Параметры FPS
fps = 60

# Типы улучшений
POWERUP_TYPES = {
    'WIDE_PADDLE': (GREEN, 'W'),
    'MULTIPLE_BALLS': (YELLOW, 'M'),
    'SLOW_BALL': (PURPLE, 'S'),
}

class Brick:
    def __init__(self, rect):
        self.rect = rect
        self.color = WHITE
        self.alpha = 255
        self.falling_speed = 0
        self.is_destroyed = False
        self.destroy_start_time = None
        self.destroy_duration = 0.5  # Время анимации разрушения в секундах
        self.hit_count = 0  # Счётчик ударов по блоку

    def draw(self):
        if self.alpha > 0:
            surface = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT), pygame.SRCALPHA)
            surface.fill((*self.color, self.alpha))
            screen.blit(surface, self.rect.topleft)

    def update(self):
        if self.is_destroyed:
            current_time = time.time()
            if self.destroy_start_time is None:
                self.destroy_start_time = current_time

            elapsed_time = current_time - self.destroy_start_time
            progress = min(elapsed_time / self.destroy_duration, 1)

            # Уменьшаем прозрачность и увеличиваем скорость падения
            self.alpha = int(255 * (1 - progress))
            self.rect.y += self.falling_speed * progress
            self.falling_speed += 0.2

            # Если анимация завершена, блок должен быть удален
            if progress >= 1:
                return True  # Return True if the brick should be removed
        return False

    def hit(self):
        self.hit_count += 1
        if self.hit_count >= 1:  # Ломаем блок сразу после первого удара
            self.is_destroyed = True

def create_bricks():
    global bricks
    bricks = []
    for row in range(5):
        for col in range(10):
            brick = Brick(
                pygame.Rect(col * (BRICK_WIDTH + 10) + 35, row * (BRICK_HEIGHT + 10) + 50, BRICK_WIDTH, BRICK_HEIGHT)
            )
            bricks.append(brick)

def check_ball_collisions():
    global balls, powerups, bricks
    
    for ball in balls[:]:
        ball_rect = ball['rect']
        ball_speed_x = ball['speed_x']
        ball_speed_y = ball['speed_y']
        
        # Проверка столкновений с краями экрана
        if ball_rect.left <= 0 or ball_rect.right >= SCREEN_WIDTH:
            ball['speed_x'] = -ball['speed_x']
        if ball_rect.top <= 0:
            ball['speed_y'] = -ball['speed_y']
        if ball_rect.bottom >= SCREEN_HEIGHT:
            balls.remove(ball)  # Удаление мяча, если он улетает за экран
            continue
        
        # Проверка столкновений с ракеткой
        if ball_rect.colliderect(paddle):
            ball['speed_y'] = -ball['speed_y']
        
        # Проверка столкновений с блоками
        for brick in bricks[:]:
            if brick.update():
                bricks.remove(brick)
                continue
            if ball_rect.colliderect(brick.rect):
                # Определение типа столкновения и направление отскока
                if abs(ball_rect.bottom - brick.rect.top) < BALL_SIZE:
                    ball['speed_y'] = -ball['speed_y']
                elif abs(ball_rect.top - brick.rect.bottom) < BALL_SIZE:
                    ball['speed_y'] = -ball['speed_y']
                elif abs(ball_rect.right - brick.rect.left) < BALL_SIZE:
                    ball['speed_x'] = -ball['speed_x']
                elif abs(ball_rect.left - brick.rect.right) < BALL_SIZE:
                    ball['speed_x'] = -ball['speed_x']
                    
                brick.hit()
                if brick.is_destroyed:
                    if random.random() < powerup_chance:
                        powerup_type = random.choice(list(POWERUP_TYPES.keys()))
                        powerup = pygame.Rect(brick.rect.x, brick.rect.y, POWERUP_SIZE, POWERUP_SIZE)
                        powerups.append((powerup, powerup_type))
                break

def reset_game(level_data=None):
    global paddle, balls, powerups
    
    # Начальные скорости
    ball_speed_x = 4
    ball_speed_y = -4
    
    # Инициализация ракетки
    paddle = pygame.Rect(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2, SCREEN_HEIGHT - 30, PADDLE_WIDTH, PADDLE_HEIGHT)
    
    # Инициализация шариков
    balls = [{'rect': pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE), 'speed_x': ball_speed_x, 'speed_y': ball_speed_y}]
    
    # Сброс улучшений
    powerups = []
    
    # Создание уровня
    create_level(level_data)

def draw_powerup(powerup):
    color, _ = POWERUP_TYPES.get(powerup[1], (GREEN, 'W'))
    pygame.draw.rect(screen, color, powerup[0])

def update_powerups():
    global powerups, paddle
    
    for powerup in powerups[:]:
        powerup_rect, powerup_type = powerup
        powerup_rect.y += 5
        if powerup_rect.colliderect(paddle):
            apply_powerup(powerup_type)
            powerups.remove(powerup)
        elif powerup_rect.top > SCREEN_HEIGHT:
            powerups.remove(powerup)

def apply_powerup(powerup_type):
    global balls, paddle, ball_speed_x, ball_speed_y
    
    if powerup_type == 'WIDE_PADDLE':
        paddle.width += 20
    elif powerup_type == 'MULTIPLE_BALLS':
        new_balls = []
        for ball in balls:
            x, y = ball['rect'].x, ball['rect'].y
            new_balls.append({'rect': pygame.Rect(x, y, BALL_SIZE, BALL_SIZE), 'speed_x': ball_speed_x, 'speed_y': ball_speed_y})
            new_balls.append({'rect': pygame.Rect(x, y, BALL_SIZE, BALL_SIZE), 'speed_x': ball_speed_x * 0.7, 'speed_y': ball_speed_y * 0.7})
            new_balls.append({'rect': pygame.Rect(x, y, BALL_SIZE, BALL_SIZE), 'speed_x': ball_speed_x * -0.7, 'speed_y': ball_speed_y * 0.7})
        balls = new_balls
    elif powerup_type == 'SLOW_BALL':
        if ball_speed_x > 2 and ball_speed_y > 2:  # Применяем замедление только если оно неактивно
            ball_speed_x *= 0.8
            ball_speed_y *= 0.8

def create_level(level_data=None):
    global bricks
    
    # Если данные уровня не переданы, используем стандартные данные
    if level_data is None:
        level_data = [['1'] * 10 for _ in range(5)]  # Пример уровня, заполненного кирпичами
    
    bricks = []
    for row in range(len(level_data)):
        for col in range(len(level_data[row])):
            if level_data[row][col] == '1':
                brick = Brick(
                    pygame.Rect(col * (BRICK_WIDTH + 10) + 35, row * (BRICK_HEIGHT + 10) + 50, BRICK_WIDTH, BRICK_HEIGHT)
                )
                bricks.append(brick)

def load_next_level():
    global current_level
    level_filename = f'level_{current_level}.txt'
    try:
        level_data = load_level(level_filename)
        create_level(level_data)
        current_level += 1
    except FileNotFoundError:
        print("No more levels available")
        # Логика завершения игры или перехода на первый уровень
        reset_game()
        current_level = 1

def show_start_menu():
    menu_font = pygame.font.Font(None, 74)
    start_text = menu_font.render("Press SPACE to Start", True, WHITE)
    start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.fill(BLACK)
    screen.blit(start_text, start_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False

def show_pause_menu():
    menu_font = pygame.font.Font(None, 74)
    pause_text = menu_font.render("Paused", True, WHITE)
    pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.fill(BLACK)
    screen.blit(pause_text, pause_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False

# Главный игровой цикл
running = True
clock = pygame.time.Clock()
paused = False

show_start_menu()
reset_game()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
                if paused:
                    show_pause_menu()
            if event.key == pygame.K_r:
                reset_game()
    
    if not paused:
        # Управление ракеткой
        mouse_x, _ = pygame.mouse.get_pos()
        paddle.x = mouse_x - PADDLE_WIDTH // 2
        if paddle.left < 0:
            paddle.left = 0
        if paddle.right > SCREEN_WIDTH:
            paddle.right = SCREEN_WIDTH
        
        # Обновление шариков и их столкновений
        for ball in balls:
            ball['rect'].x += ball['speed_x']
            ball['rect'].y += ball['speed_y']
        
        check_ball_collisions()
        
        # Обновление улучшений
        update_powerups()
        
        # Проверка проигрыша
        ball_out_of_bounds = any(ball['rect'].top >= SCREEN_HEIGHT for ball in balls)
        if ball_out_of_bounds:
            reset_game()
        
        # Отображение экрана
        screen.fill(BLACK)
        for brick in bricks:
            brick.draw()
        pygame.draw.rect(screen, WHITE, paddle)
        for ball in balls:
            pygame.draw.ellipse(screen, WHITE, ball['rect'])
        for powerup in powerups:
            draw_powerup(powerup)
        
        pygame.display.flip()
        clock.tick(fps)

pygame.quit()
