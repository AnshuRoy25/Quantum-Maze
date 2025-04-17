import pygame
import random
import time
import subprocess
import sqlite3
import sys
import os
import cv2  # Added OpenCV for video handling


# Initialize Pygame
pygame.init()

# Screen settings - Increased from 600x600 to 800x800
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 21
CELL_SIZE = WIDTH // GRID_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quantum Maze Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)  
GREEN = (0, 255, 0)  
RED = (255, 0, 0)  
WHITE_DOOR = (255, 255, 255)  
PURPLE = (128, 0, 128)  
YELLOW = (255, 255, 0)  
BUTTON_COLOR = (200, 200, 200)
BUTTON_HOVER = (150, 150, 150)

# Game constants
SUPERPOSITION_DURATION = 5  # Seconds before doors return to superposition
TELEPORT_COOLDOWN = 15      # Seconds between forced teleports

# Database setup
db_file = "quantum_maze_data.db"

def init_db():
    """Initialize the database and create the tables if they don't exist"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS level_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            level INTEGER,
            completion_time INTEGER,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS total_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            total_time INTEGER,
            completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    """)
    
    conn.commit()
    conn.close()

def save_completion_time(level, completion_time):
    """Save completion time to database."""
    # Get username from shared file
    try:
        with open("current_player.txt", "r") as f:
            username = f.read().strip()
    except:
        username = "Player"  # Default if file not found
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Insert or ignore the player
    cursor.execute("INSERT OR IGNORE INTO players (username) VALUES (?)", (username,))
    conn.commit()
    
    # Get player ID
    cursor.execute("SELECT id FROM players WHERE username = ?", (username,))
    player_id = cursor.fetchone()[0]
    
    # Check if time for this level and player already exists
    cursor.execute(
        "SELECT id FROM level_times WHERE player_id = ? AND level = ?", 
        (player_id, level)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Update existing time
        cursor.execute(
            "UPDATE level_times SET completion_time = ? WHERE id = ?", 
            (completion_time, existing[0])
        )
    else:
        # Insert new time
        cursor.execute(
            "INSERT INTO level_times (player_id, level, completion_time) VALUES (?, ?, ?)",
            (player_id, level, completion_time)
        )
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 32)  # Font for the button

def show_start_screen():
    screen.fill(WHITE)
    small_font = pygame.font.Font(None, 34)  # Reduced font size
    text = small_font.render("Level 3: Tunneling", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.update()
    time.sleep(2)

# Function to show tutorial video with OpenCV
def show_tutorial_video():
    # Create a start button
    button_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 40)
    
    video_path = "3.mp4"  # Changed to 3.mp4 for Level 3
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return False  # Skip video and start the game
    
    try:
        # Open the video file with OpenCV
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error opening video file")
            return False
        
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate scaling to fit video on screen
        max_video_height = HEIGHT - 150  # Leave more space for title and button
        scale = min(WIDTH / frame_width, max_video_height / frame_height)
        display_width = int(frame_width * scale)
        display_height = int(frame_height * scale)
        
        # Calculate position to center video - move it down to leave space for title
        video_x = (WIDTH - display_width) // 2
        video_y = (HEIGHT - display_height - 100) // 2 + 30  # Add offset to push video down
        
        # Position for the tutorial text - ensure it's higher than the video
        tutorial_text_y = video_y - 30
        
        # For controlling video timing
        clock = pygame.time.Clock()
        last_frame_time = time.time() * 1000  # Current time in milliseconds
        frame_time = 1000 / fps if fps > 0 else 33  # milliseconds per frame
        
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        running = False  # Start the game
            
            # Strictly control frame timing to ensure constant playback speed
            current_time = time.time() * 1000
            if current_time - last_frame_time >= frame_time:
                # Read the next frame
                ret, frame = cap.read()
                
                # If the video ended, loop back to beginning
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Rewind to beginning
                    ret, frame = cap.read()
                    if not ret:  # If still can't read, there's a problem
                        break
                
                # Apply rotation (90 degrees clockwise) and vertical flip transformations
                # 1. Rotate 90 degrees clockwise
                # Apply rotation (90 degrees counterclockwise two times)
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)  # First rotation
                # Second rotation

                # 2. Flip vertically (up/down)
                frame = cv2.flip(frame, 0)
                
                # Convert OpenCV BGR to RGB for Pygame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize for display
                frame = cv2.resize(frame, (display_width, display_height))
                
                # Convert to Pygame surface
                video_surf = pygame.Surface((display_width, display_height))
                pygame.surfarray.blit_array(video_surf, frame)
                
                # Clear screen
                screen.fill(BLACK)
                
                # Add "Tutorial - Level 3" text - draw this BEFORE the video
                tutorial_text = font.render("Tutorial - Level 3", True, WHITE)  # Changed to Level 3
                tutorial_text_rect = tutorial_text.get_rect(center=(WIDTH // 2, tutorial_text_y))
                screen.blit(tutorial_text, tutorial_text_rect)
                
                # Display video frame
                screen.blit(video_surf, (video_x, video_y))
                
                # Draw start button
                mouse_pos = pygame.mouse.get_pos()
                button_color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
                pygame.draw.rect(screen, button_color, button_rect)
                button_text = button_font.render("Start", True, BLACK)
                text_rect = button_text.get_rect(center=button_rect.center)
                screen.blit(button_text, text_rect)
                
                pygame.display.update()
                
                # Update the last frame time
                last_frame_time = current_time
            
            # Only tick at a high rate to handle events responsively,
            # but actual frame display is controlled by our manual timing
            clock.tick(60)
        
        # Clean up
        cap.release()
        return True
        
    except Exception as e:
        print(f"Error playing video: {e}")
        return False  # Skip video and start the game

def show_end_screen(completion_time):
    # Save to database
    save_completion_time(3, completion_time)
    
    screen.fill(WHITE)
    
    # Create text surfaces
    text_font = pygame.font.Font(None, 36)
    line1 = text_font.render(f"Level 3 Completed in {completion_time} Seconds!", True, BLACK)
    line2 = text_font.render("Tunneling Successful! No wall could stop you!", True, BLACK)
    
    # Position text
    line1_rect = line1.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    line2_rect = line2.get_rect(center=(WIDTH//2, HEIGHT//2))
    
    # Create button
    button_rect = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 50, 240, 50)
    
    running = True
    while running:
        screen.fill(WHITE)
        
        # Draw text
        screen.blit(line1, line1_rect)
        screen.blit(line2, line2_rect)
        
        # Get mouse position for hover effect
        mouse_pos = pygame.mouse.get_pos()
        button_color = (50, 50, 50) if button_rect.collidepoint(mouse_pos) else BLACK
        
        # Draw button with rounded corners
        pygame.draw.rect(screen, button_color, button_rect, border_radius=10)
        button_text = text_font.render("Continue to Level 4", True, WHITE)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    pygame.quit()
                    subprocess.run(["python", "enemy_Level4.py"])
                    exit()

# Show start screen before the game begins
show_start_screen()

# Show tutorial video
if show_tutorial_video():
    # Reset start_time after the tutorial video
    start_time = time.time()

# Tunneling variables
tunneling_probability = 20  
tunnel_cooldown_time = 10  
last_tunnel_time = 0  

def generate_maze():
    maze = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    stack = [(random.randint(0, GRID_SIZE // 2) * 2, random.randint(0, GRID_SIZE // 2) * 2)]
    visited = set(stack)
    
    directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
    while stack:
        x, y = stack[-1]
        random.shuffle(directions)
        found = False
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in visited:
                maze[y][x] = 1  
                maze[ny][nx] = 1  
                maze[y + dy // 2][x + dx // 2] = 1  
                stack.append((nx, ny))
                visited.add((nx, ny))
                found = True
                break
        if not found:
            stack.pop()
    
    maze[0][0] = 1  
    maze[GRID_SIZE - 1][GRID_SIZE - 1] = 3  

    door_states = {}
    door_positions = []
    door_pair_timers = {}

    # Find valid door positions
    for row in range(1, GRID_SIZE - 1):
        for col in range(1, GRID_SIZE - 1):
            if maze[row][col] == 1:  
                wall_neighbors = sum(
                    maze[row + dr][col + dc] == 0
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                )
                if wall_neighbors == 2:  
                    door_positions.append((col, row))

    random.shuffle(door_positions)
    entangled_pairs = []
    
    # Limit to exactly 3 pairs
    max_pairs = 3  
    for i in range(0, max_pairs * 2, 2):  
        door1, door2 = door_positions[i], door_positions[i + 1]
        maze[door1[1]][door1[0]] = 2  
        maze[door2[1]][door2[0]] = 2  
        door_states[door1] = None  # Start in superposition
        door_states[door2] = None  # Start in superposition
        entangled_pairs.append((door1, door2))

    # Add tunneling power-ups (yellow cells)
    for _ in range(3):  
        while True:
            ex, ey = random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2)
            if maze[ey][ex] == 1:
                maze[ey][ex] = 4  
                break

    return maze, door_states, entangled_pairs, door_pair_timers

player_x, player_y = 0, 0
maze, door_states, entangled_pairs, door_pair_timers = generate_maze()
start_time = time.time()
last_teleport_time = time.time()
blinking = False
keys_enabled = True
blink_position = None
keys_pressed = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}
blink_disabled_until = 0  # Time until which keys should be disabled (2 seconds after blinking starts)

def draw_maze():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if maze[row][col] == 1:
                color = WHITE if not blinking else random.choice([WHITE, PURPLE])
            elif maze[row][col] == 3:
                color = GREEN
            elif maze[row][col] == 2:
                door_pos = (col, row)
                state = door_states.get(door_pos, None)
                if state is None:  # Superposition
                    color = random.choice([RED, WHITE_DOOR])
                elif state:  # Passable
                    color = WHITE_DOOR
                else:  # Impassable
                    color = RED
            elif maze[row][col] == 4:
                color = YELLOW
            else:
                color = BLACK
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    if not blinking:
        pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, (255, 0, 0))
    prob_text = font.render(f"Tunnel %: {tunneling_probability}%", True, YELLOW)
    tunnel_cd_text = font.render(f"Tunnel CD: {max(0, tunnel_cooldown_time - int(time.time() - last_tunnel_time))}s", True, RED)
    
    screen.blit(timer_text, (10, 10))
    screen.blit(prob_text, (10, 40))
    screen.blit(tunnel_cd_text, (10, 70))

def move_player(dx, dy):
    global player_x, player_y, tunneling_probability
    if not keys_enabled:
        return
    
    new_x, new_y = player_x + dx, player_y + dy
    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
        if maze[new_y][new_x] == 2:
            if door_states.get((new_x, new_y)) is True:  # Only pass through open doors
                player_x, player_y = new_x, new_y
        elif maze[new_y][new_x] in [1, 3, 4]:
            if maze[new_y][new_x] == 4:  # Tunneling power-up
                tunneling_probability = min(100, tunneling_probability + 10)
                maze[new_y][new_x] = 1  # Convert to normal path after collecting
            player_x, player_y = new_x, new_y
        
        if maze[new_y][new_x] == 3:
            completion_time = int(time.time() - start_time)
            show_end_screen(completion_time)

def teleport_player():
    global player_x, player_y, keys_enabled, blinking, last_teleport_time
    valid_positions = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if maze[y][x] == 1]
    if valid_positions:
        player_x, player_y = random.choice(valid_positions)
    keys_enabled = True
    blinking = False
    last_teleport_time = time.time()

def is_adjacent_to_door():
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        adj_x, adj_y = player_x + dx, player_y + dy
        if 0 <= adj_x < GRID_SIZE and 0 <= adj_y < GRID_SIZE and maze[adj_y][adj_x] == 2:
            return (adj_x, adj_y)
    return None

def has_red_neighbor(door):
    x, y = door
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            if maze[ny][nx] == 2 and door_states.get((nx, ny)) == False:
                return True
    return False

def toggle_door():
    global door_pair_timers
    adjacent_door = is_adjacent_to_door()
    if adjacent_door:
        for pair in entangled_pairs:
            if adjacent_door in pair:
                if any(door_states.get(d) is None for d in pair):
                    # If adjacent to a red door, make both passable
                    if has_red_neighbor(pair[0]) or has_red_neighbor(pair[1]):
                        door_states[pair[0]] = True
                        door_states[pair[1]] = True
                    else:
                        # Otherwise random but opposite states
                        new_state = random.choice([True, False])
                        door_states[pair[0]] = new_state
                        door_states[pair[1]] = not new_state
                    door_pair_timers[pair] = time.time()
                break

def check_door_superposition():
    current_time = time.time()
    pairs_to_reset = []
    
    for pair, measure_time in door_pair_timers.items():
        if current_time - measure_time >= SUPERPOSITION_DURATION:
            pairs_to_reset.append(pair)
    
    for pair in pairs_to_reset:
        door_states[pair[0]] = None
        door_states[pair[1]] = None
        del door_pair_timers[pair]

def attempt_tunneling(dx, dy):
    global player_x, player_y, last_tunnel_time

    if time.time() - last_tunnel_time < tunnel_cooldown_time:
        return  

    last_tunnel_time = time.time()  

    if random.randint(1, 100) <= tunneling_probability:
        new_x, new_y = player_x + dx, player_y + dy
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            player_x, player_y = new_x, new_y  

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)
    check_door_superposition()
    draw_maze()
    pygame.display.update()
    
    current_time = time.time()
    # Changed from 10 to 15 seconds for blinking interval
    if current_time - last_teleport_time >= TELEPORT_COOLDOWN and not blinking:
        blinking = True
        keys_enabled = False
        blink_disabled_until = current_time + 2  # Disable keys for 2 seconds after blinking starts
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if current_time < blink_disabled_until:
                continue  # Skip key presses for 2 seconds after blinking starts
            
            if blinking:
                teleport_player()
            elif keys_enabled:
                if event.key in keys_pressed:
                    keys_pressed[event.key] = True
                elif event.key == pygame.K_f:
                    toggle_door()
                elif event.key == pygame.K_SPACE:
                    keys = pygame.key.get_pressed()
                    dx = (keys[pygame.K_d] - keys[pygame.K_a])
                    dy = (keys[pygame.K_s] - keys[pygame.K_w]) 
                    attempt_tunneling(dx, dy)
        elif event.type == pygame.KEYUP:
            if event.key in keys_pressed:
                keys_pressed[event.key] = False
    
    if keys_enabled:
        if keys_pressed[pygame.K_w]: move_player(0, -1)
        if keys_pressed[pygame.K_s]: move_player(0, 1)
        if keys_pressed[pygame.K_a]: move_player(-1, 0)
        if keys_pressed[pygame.K_d]: move_player(1, 0)
    
    clock.tick(10)

pygame.quit()