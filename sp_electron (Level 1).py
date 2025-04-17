import pygame
import random
import time
import os
import sqlite3
import cv2  # Added OpenCV for video handling
import sys
import subprocess

# Initialize Pygame
pygame.init()

# Screen settings
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
PURPLE = (128, 0, 128)
GRAY = (150, 150, 150)
BUTTON_COLOR = (200, 200, 200)
BUTTON_HOVER = (150, 150, 150)

font = pygame.font.Font(None, 36)
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

init_db()

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

def show_level_screen():
    screen.fill(WHITE)
    text = font.render("LEVEL 1: SUPERPOSITION", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.update()
    time.sleep(2)

# Function to show tutorial video with OpenCV
def show_tutorial_video():
    # Create a start button
    button_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 40)
    
    video_path = "1.mp4"  # Changed to 1.mp4 for Level 1
    
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
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)  # First rotation
                frame = cv2.flip(frame, 0)  # Flip vertically
                
                # Convert OpenCV BGR to RGB for Pygame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize for display
                frame = cv2.resize(frame, (display_width, display_height))
                
                # Convert to Pygame surface
                video_surf = pygame.Surface((display_width, display_height))
                pygame.surfarray.blit_array(video_surf, frame)
                
                # Clear screen
                screen.fill(BLACK)
                
                # Add "Tutorial - Level 1" text - draw this BEFORE the video
                tutorial_text = font.render("Tutorial - Level 1", True, WHITE)  # Changed to Level 1
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
    return maze

# Show level screen
show_level_screen()

# Show tutorial video
if show_tutorial_video():
    # Reset start_time after the tutorial video
    start_time = time.time()
else:
    start_time = time.time()

# Initialize player position
player_x, player_y = 0, 0
maze = generate_maze()
last_teleport_time = time.time()
blinking = False
keys_enabled = True
blink_start_time = None

keys_pressed = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}

def get_random_open_position():
    """Returns a random position in the maze that is a path (not a wall)"""
    open_positions = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if maze[y][x] == 1]
    return random.choice(open_positions)

def draw_maze():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if maze[row][col] == 1:
                color = random.choice([WHITE, PURPLE]) if blinking else WHITE
            elif maze[row][col] == 3:
                color = GREEN
            else:
                color = BLACK
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    if not blinking:
        pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, RED)
    screen.blit(timer_text, (10, 10))

def move_player(dx, dy):
    global player_x, player_y

    if not keys_enabled:
        return

    new_x, new_y = player_x + dx, player_y + dy

    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and maze[new_y][new_x] in [1, 3]:
        player_x, player_y = new_x, new_y

        if maze[new_y][new_x] == 3:
            show_completion_screen()

def show_completion_screen():
    elapsed_time = int(time.time() - start_time)
    save_completion_time(1, elapsed_time)

    screen.fill(WHITE)
    # First line of text
    message1 = font.render(f"Level 1 Completed in {elapsed_time} Seconds!", True, BLACK)
    text_rect1 = message1.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(message1, text_rect1)
    
    # Second line of text
    message2 = font.render("You have stepped through all the possibilities", True, BLACK)
    text_rect2 = message2.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 40))
    screen.blit(message2, text_rect2)
    
    # Third line of textR
    message3 = font.render("and chosen your victory!", True, BLACK)
    text_rect3 = message3.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 80))
    screen.blit(message3, text_rect3)

    button_width, button_height = 250, 60
    button_x, button_y = WIDTH // 2 - button_width // 2, HEIGHT // 2 + 60  # Adjusted y position
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    pygame.draw.rect(screen, GRAY, button_rect, border_radius=10)

    button_text = font.render("Continue to Level 2", True, BLACK)
    button_text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, button_text_rect)

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    pygame.quit()
                    os.system("python sp_doors-Level2.py")
                    exit()

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)
    draw_maze()
    pygame.display.update()
    
    current_time = time.time()

    if current_time - last_teleport_time >= 10 and not blinking:
        blinking = True
        keys_enabled = False
        keys_pressed = {key: False for key in keys_pressed}
        blink_start_time = time.time()

    if blinking and blink_start_time and current_time - blink_start_time >= 2:
        keys_enabled = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if blinking and keys_enabled:
                player_x, player_y = get_random_open_position()
                last_teleport_time = time.time()
                blinking = False
            elif not blinking and keys_enabled and event.key in keys_pressed:
                keys_pressed[event.key] = True
        elif event.type == pygame.KEYUP:
            if event.key in keys_pressed:
                keys_pressed[event.key] = False

    if keys_enabled and not blinking:
        if keys_pressed[pygame.K_w]: move_player(0, -1)
        if keys_pressed[pygame.K_s]: move_player(0, 1)
        if keys_pressed[pygame.K_a]: move_player(-1, 0)
        if keys_pressed[pygame.K_d]: move_player(1, 0)

    clock.tick(10)

pygame.quit()