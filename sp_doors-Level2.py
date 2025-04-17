import pygame
import random
import time
import subprocess
import sqlite3  # Added for database storage
import sys
import os
import cv2  # Added OpenCV for video handling

# Initialize Pygame
pygame.init()

# Screen settings
# Screen settings - Increased from 600x600 to 800x800
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 21
CELL_SIZE = WIDTH // GRID_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quantum Maze Game - Level 2: Entanglement")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)  
GREEN = (0, 255, 0)  
RED = (255, 0, 0)  
WHITE_DOOR = (255, 255, 255)  
PURPLE = (128, 0, 128)  
GRAY = (150, 150, 150)  # Added for button
BUTTON_COLOR = (200, 200, 200)
BUTTON_HOVER = (150, 150, 150)

# Game constants
SUPERPOSITION_DURATION = 5  # Seconds before doors return to superposition
TELEPORT_COOLDOWN = 10      # Seconds between forced teleports

font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 32)  # Font for the button

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

def show_start_screen():
    screen.fill(WHITE)
    small_font = pygame.font.Font(None, 34)  # Reduced font size
    text = small_font.render("Level 2: Entanglement", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.update()
    time.sleep(2)

# Function to show tutorial video with OpenCV
def show_tutorial_video():
    # Create a start button
    button_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 40)
    
    video_path = "2.mp4"  # Changed to 2.mp4 for Level 2
    
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
                
                # Add "Tutorial - Level 2" text - draw this BEFORE the video
                tutorial_text = font.render("Tutorial - Level 2", True, WHITE)  # Changed to Level 2
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

def show_completion_screen():
    elapsed_time = int(time.time() - start_time)
    save_completion_time(2, elapsed_time)  # Save to level_times table
    
    screen.fill(WHITE)

    # Text
    text1 = font.render(f"Level 2 Completed in {elapsed_time} Seconds!", True, BLACK)
    text2 = font.render("You have mastered the unseen link!", True, BLACK)

    # Button
    button_width, button_height = 280, 60
    button_x, button_y = WIDTH // 2 - button_width // 2, HEIGHT // 2 + 50
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    text1_rect = text1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    text2_rect = text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))

    screen.blit(text1, text1_rect)
    screen.blit(text2, text2_rect)

    # Main loop to handle button hover effect
    waiting = True
    while waiting:
        screen.fill(WHITE)
        screen.blit(text1, text1_rect)
        screen.blit(text2, text2_rect)

        # Get mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Change button color on hover
        button_color = (50, 50, 50) if button_rect.collidepoint((mouse_x, mouse_y)) else GRAY
        pygame.draw.rect(screen, button_color, button_rect, border_radius=10)  # Rounded corners

        button_text = font.render("Continue to Level 3", True, WHITE)
        screen.blit(button_text, button_text.get_rect(center=button_rect.center))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                pygame.quit()
                subprocess.run(["python", "sp_door_tunnel-Level3.py"])  # Open Level 3
                exit()
                
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

    # Find valid door positions (adjacent to exactly 2 walls)
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
    
    # Create exactly 3 entangled pairs with minimum distance
    max_pairs = 3
    for i in range(0, max_pairs * 2, 2):
        if i + 1 >= len(door_positions):
            break
        
        # Ensure doors aren't adjacent to each other
        door1, door2 = door_positions[i], door_positions[i + 1]
        x1, y1 = door1
        x2, y2 = door2
        
        # Check if doors are adjacent
        if abs(x1 - x2) + abs(y1 - y2) == 1:
            continue  # Skip this pair if adjacent
            
        maze[y1][x1] = 2
        maze[y2][x2] = 2
        door_states[door1] = None  # Start in superposition
        door_states[door2] = None  # Start in superposition
        entangled_pairs.append((door1, door2))

    return maze, door_states, entangled_pairs, door_pair_timers

# Initialize database
init_db()

# Initialize game
show_start_screen()

# Show tutorial video
if show_tutorial_video():
    # Reset start_time after the tutorial video
    start_time = time.time()
else:
    start_time = time.time()

player_x, player_y = 0, 0
maze, door_states, entangled_pairs, door_pair_timers = generate_maze()
last_teleport_time = time.time()
blinking = False
keys_enabled = True
blink_disabled_until = 0
keys_pressed = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}

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
            else:
                color = BLACK
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    if not blinking:
        pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, RED)
    screen.blit(timer_text, (10, 10))

def move_player(dx, dy):
    global player_x, player_y, running
    if not keys_enabled:
        return
    
    new_x, new_y = player_x + dx, player_y + dy
    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
        if maze[new_y][new_x] == 2:
            if door_states.get((new_x, new_y)) is True:
                player_x, player_y = new_x, new_y
        elif maze[new_y][new_x] in [1, 3]:
            player_x, player_y = new_x, new_y
        
        if maze[new_y][new_x] == 3:
            completion_time = int(time.time() - start_time)
            print(f"You reached the exit in {completion_time} seconds!")
            show_completion_screen()
            running = False

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
                    if has_red_neighbor(pair[0]) or has_red_neighbor(pair[1]):
                        door_states[pair[0]] = True
                        door_states[pair[1]] = True
                    else:
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

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)
    check_door_superposition()
    
    current_time = time.time()
    if current_time - last_teleport_time >= TELEPORT_COOLDOWN and not blinking:
        blinking = True
        keys_enabled = False
        blink_disabled_until = current_time + 2
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if current_time < blink_disabled_until:
                continue
            
            if blinking:
                teleport_player()
            elif keys_enabled:
                if event.key in keys_pressed:
                    keys_pressed[event.key] = True
                elif event.key == pygame.K_f:
                    toggle_door()
        elif event.type == pygame.KEYUP:
            if event.key in keys_pressed:
                keys_pressed[event.key] = False
    
    if keys_enabled:
        if keys_pressed[pygame.K_w]: move_player(0, -1)
        if keys_pressed[pygame.K_s]: move_player(0, 1)
        if keys_pressed[pygame.K_a]: move_player(-1, 0)
        if keys_pressed[pygame.K_d]: move_player(1, 0)
    
    draw_maze()
    pygame.display.update()
    clock.tick(10)

pygame.quit()