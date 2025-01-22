import struct
import time
import threading

# WebSocket message formats for different movements
move_right = [2, 2]  # Move right
move_left = [2, 1]   # Move left
move_down = [2, 4]   # Move down
move_up = [2, 8]     # Move up
stop_movement = [2, 0]  # Stop movement

# Function to handle right-click movement
def right_click(event, canvas, websocket):
    # Get the canvas coordinates where the right-click happened
    click_x, click_y = event.x, event.y

    # Convert canvas coordinates to map coordinates
    map_x = click_x / canvas.winfo_width() * 15000  # Adjust according to your map size
    map_y = click_y / canvas.winfo_height() * 15000

    print(f"Right-click detected at map coordinates: X={map_x}, Y={map_y}")

    # Depending on the position, send the WebSocket message to move in the direction
    if map_x > 7500:  # If clicked on the right side of the map, move right
        send_websocket_message(websocket, move_right)
    elif map_x < 7500:  # If clicked on the left side of the map, move left
        send_websocket_message(websocket, move_left)
    elif map_y > 7500:  # If clicked on the lower side of the map, move down
        send_websocket_message(websocket, move_down)
    elif map_y < 7500:  # If clicked on the upper side of the map, move up
        send_websocket_message(websocket, move_up)

    # Start a new thread that waits before sending the stop message
    stop_thread = threading.Thread(target=delayed_stop, args=(websocket,))
    stop_thread.start()

# Function to send a stop message after a delay
def delayed_stop(websocket):
    time.sleep(2)  # Wait for 2 seconds before stopping (adjust the delay as necessary)
    send_websocket_message(websocket, stop_movement)

# Function to send a WebSocket message
def send_websocket_message(websocket, message):
    try:
        if websocket.open:  # Check if WebSocket is still open
            websocket.send(json.dumps(message))  # Send the message in JSON format
            print(f"Sending WebSocket message: {message}")
        else:
            print("WebSocket is closed. Unable to send message.")
    except Exception as e:
        print(f"Error sending WebSocket message: {e}")
