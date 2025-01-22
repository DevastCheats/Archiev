# movement.py

def find_nearest_player(players, bot_position):
    nearest_player = None
    min_distance = float('inf')
    
    for player in players:
        # Вычисление расстояния до игрока
        distance = ((bot_position['x'] - player['x']) ** 2 + (bot_position['y'] - player['y']) ** 2) ** 0.5
        
        if distance < min_distance:
            min_distance = distance
            nearest_player = player
    
    return nearest_player

def send_movement_command(ws, direction):
    commands = {
        'right': [2, 2],
        'left': [2, 1],
        'down': [2, 4],
        'up': [2, 8],
        'stop': [2, 0]
    }
    if direction in commands:
        ws.send(json.dumps(commands[direction]))

def move_towards_nearest_player(ws, bot_position, players):
    nearest_player = find_nearest_player(players, bot_position)
    if nearest_player:
        # Определите направление движения
        dx = nearest_player['x'] - bot_position['x']
        dy = nearest_player['y'] - bot_position['y']
        
        if abs(dx) > abs(dy):
            if dx > 0:
                send_movement_command(ws, 'right')
            else:
                send_movement_command(ws, 'left')
        else:
            if dy > 0:
                send_movement_command(ws, 'down')
            else:
                send_movement_command(ws, 'up')
    else:
        send_movement_command(ws, 'stop')
