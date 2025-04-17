import pygame
import random
import time
from collections import deque
import math
import subprocess
import sys
import os
import sqlite3
import cv2  # Added OpenCV for video handling just like in Level 5

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
BLUE = (0, 0, 255)  # Player color
GREEN = (0, 255, 0)  # Exit color
RED = (255, 0, 0)  # Timer text color
DARK_RED = (139, 0, 0)  # Dark red/brown for blinking effect
PURPLE = (128, 0, 128)  # Enemy color
YELLOW = (255, 255, 0)  # Quantum tunneling effect
GRAY = (200, 200, 200)  # Button color when hovered
BUTTON_COLOR = (200, 200, 200)
BUTTON_HOVER = (150, 150, 150)

# Database setup
db_file = "quantum_maze_data.db"

# Replace the current database functions with these:

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

# Initialize the database
init_db()

font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 35)  # Larger font for the title screen
congrats_font = pygame.font.Font(None, 35)  # Font for the congratulatory screen
button_font = pygame.font.Font(None, 32)  # Font for the button

def show_title_screen():
    screen.fill(WHITE)
    title_text = title_font.render("Level 4: Quantum Hunter", True, BLACK)
    text_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(title_text, text_rect)
    pygame.display.flip()
    time.sleep(4)  # Display for 4 seconds

# Function to show tutorial video with OpenCV (copied from Level 5 and modified)
def show_tutorial_video():
    # Create a start button
    button_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 40)
    
    video_path = "4.mp4"  # Changed to 4.mp4 for Level 4
    
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
                
                # Add "Tutorial - Level 4" text - draw this BEFORE the video
                tutorial_text = font.render("Tutorial - Level 4", True, WHITE)  # Changed to Level 4
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

def show_game_over_screen():
    """Show game over screen when player is caught by enemy"""
    running = True
    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 80, 300, 50)
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        button_hovered = button_rect.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_hovered:
                    # Create a signal file for the main menu to detect
                    try:
                        with open("return_to_menu.signal", "w") as f:
                            f.write("game_over")
                    except Exception as e:
                        print(f"Error creating signal file: {e}")
                    
                    pygame.quit()
                    sys.exit()
        
        # Draw the game over screen
        screen.fill(WHITE)
        
        # Draw "You Lost" text
        lost_text = congrats_font.render("You Lost", True, BLACK)
        lost_rect = lost_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        screen.blit(lost_text, lost_rect)
        
        # Draw the button
        button_color = GRAY if button_hovered else WHITE
        pygame.draw.rect(screen, button_color, button_rect)
        pygame.draw.rect(screen, BLACK, button_rect, 2)  # Button border
        
        button_text = button_font.render("Back to Main Menu", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)
        
        pygame.display.flip()

def show_congrats_screen(elapsed_time):
    # Save completion time to database
    save_completion_time(4, elapsed_time)
    
    running = True
    button_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 80, 300, 50)
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        button_hovered = button_rect.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_hovered:
                    pygame.quit()
                    try:
                        level5_path = "sp_walls-Level5.py"
                        subprocess.Popen([sys.executable, level5_path])
                        if not os.path.exists(level5_path):
                            print(f"Error: File '{level5_path}' not found!")
                            print(f"Current directory: {os.getcwd()}")
                            print("Trying to list files in directory:")
                            print(os.listdir())
                        sys.exit()
                    except Exception as e:
                        print(f"Error opening Level 5: {str(e)}")
                        error_font = pygame.font.Font(None, 30)
                        error_msg = error_font.render("Error: Could not load Level 5", True, RED)
                        screen.blit(error_msg, (WIDTH//2 - 150, HEIGHT//2 + 150))
                        pygame.display.flip()
                        time.sleep(3)
                        sys.exit()
        
        screen.fill(WHITE)
        
        # Draw congratulation texts
        line1 = congrats_font.render(f"Level 4 Completed in {elapsed_time} Seconds!", True, BLACK)
        line2 = congrats_font.render("You weren't the strongest. You were the exception!", True, BLACK)
        
        line1_rect = line1.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
        line2_rect = line2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        
        screen.blit(line1, line1_rect)
        screen.blit(line2, line2_rect)
        
        # Draw the button
        button_color = GRAY if button_hovered else WHITE
        pygame.draw.rect(screen, button_color, button_rect)
        pygame.draw.rect(screen, BLACK, button_rect, 2)
        
        button_text = button_font.render("Continue to Level 5", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)
        
        pygame.display.flip()

# Show the title screen before anything else
show_title_screen()

# Show tutorial video before game begins
# Add this call after the title screen
if show_tutorial_video():
    # Reset start_time after the tutorial video
    start_time = time.time()

def generate_maze():
    maze = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    stack = [(random.randint(0, GRID_SIZE // 2) * 2, random.randint(0, GRID_SIZE // 2) * 2)]  # Start at a random even cell
    visited = set(stack)
    
    directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
    while stack:
        x, y = stack[-1]
        random.shuffle(directions)
        found = False
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in visited:
                maze[y][x] = 1  # Mark as path
                maze[ny][nx] = 1  # Mark new position as path
                maze[y + dy // 2][x + dx // 2] = 1  # Break the wall between
                stack.append((nx, ny))
                visited.add((nx, ny))
                found = True
                break
        if not found:
            stack.pop()
    
    # Ensure start and exit points are open
    maze[0][0] = 1  # Start position
    maze[GRID_SIZE - 1][GRID_SIZE - 1] = 3  # Exit point
    return maze

# Initialize player position
player_x, player_y = 0, 0
maze = generate_maze()
start_time = time.time()

# Initialize enemy position
enemy_x, enemy_y = random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2)
while maze[enemy_y][enemy_x] != 1:
    enemy_x, enemy_y = random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2)

keys_pressed = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}

enemy_move_counter = 0  # Controls enemy speed
quantum_tunneling = False
tunnel_cooldown = 0
tunnel_effect = 0

# Teleportation variables
teleport_timer = 0
blinking = False
blink_timer = 0
blink_states = {}  # Dictionary to store random blink states for each cell
enemy_blink_state = False  # Track enemy's blink state

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_closer_white_blocks(current_x, current_y, target_x, target_y):
    """Returns all white blocks that are closer to the player than the enemy's current position"""
    closer_blocks = []
    current_dist = distance(current_x, current_y, target_x, target_y)
    
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if maze[y][x] in [1, 3]:  # It's a white block (path or exit)
                new_dist = distance(x, y, target_x, target_y)
                if new_dist < current_dist:
                    closer_blocks.append((x, y))
    
    return closer_blocks

def teleport_enemy():
    global enemy_x, enemy_y
    closer_blocks = get_closer_white_blocks(enemy_x, enemy_y, player_x, player_y)
    if closer_blocks:
        enemy_x, enemy_y = random.choice(closer_blocks)

def draw_maze():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if maze[row][col] == 1:  # Path
                if blinking:
                    # Each cell has its own random blink state
                    if (col, row) not in blink_states:
                        blink_states[(col, row)] = random.choice([True, False])
                    color = DARK_RED if blink_states[(col, row)] else WHITE
                else:
                    color = WHITE  # Normal white
            elif maze[row][col] == 3:
                color = GREEN  # Exit
            else:
                color = BLACK  # Walls
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    # Draw the player in blue
    pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    # Draw the enemy - blinking during teleport phase
    if blinking:
        enemy_color = DARK_RED if enemy_blink_state else WHITE
    else:
        enemy_color = RED
        if quantum_tunneling and maze[enemy_y][enemy_x] == 0:  # Only turn yellow if on a wall
            enemy_color = YELLOW
            
    pygame.draw.rect(screen, enemy_color, (enemy_x * CELL_SIZE, enemy_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    # Draw the timer
    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, RED)
    screen.blit(timer_text, (10, 10))

def move_player(dx, dy):
    global player_x, player_y
    new_x, new_y = player_x + dx, player_y + dy
    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and maze[new_y][new_x] in [1, 3]:
        player_x, player_y = new_x, new_y
        if maze[new_y][new_x] == 3:
            elapsed_time = int(time.time() - start_time)
            show_congrats_screen(elapsed_time)

def quantum_tunnel(enemy_x, enemy_y, player_x, player_y):
    """Calculate the next position when tunneling through walls"""
    # Calculate direction vector to player
    dx = player_x - enemy_x
    dy = player_y - enemy_y
    
    # Normalize direction (move 1 cell at a time)
    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
    
    # Prioritize the dominant direction
    if abs(dx) > abs(dy):
        step_y = 0
    else:
        step_x = 0
    
    new_x = enemy_x + step_x
    new_y = enemy_y + step_y
    
    # Ensure we stay within bounds
    new_x = max(0, min(GRID_SIZE - 1, new_x))
    new_y = max(0, min(GRID_SIZE - 1, new_y))
    
    return new_x, new_y

def move_enemy():
    global enemy_x, enemy_y, enemy_move_counter, quantum_tunneling, tunnel_cooldown, tunnel_effect
    global teleport_timer, blinking, blink_timer, blink_states, enemy_blink_state
    
    # Handle teleportation timing
    teleport_timer += 1
    if teleport_timer >= 11 * 10:  # 11 seconds (assuming 10 FPS)
        teleport_timer = 0
        blinking = True
        blink_timer = 0
        blink_states = {}  # Reset blink states
        enemy_blink_state = False  # Reset enemy blink state
    
    # Handle blinking effect
    if blinking:
        blink_timer += 1
        
        # Randomly toggle blink states for all path cells and enemy
        if blink_timer % 5 == 0:  # Change blink states every 5 frames (0.5s)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if maze[y][x] == 1:  # Only for path cells
                        blink_states[(x, y)] = random.choice([True, False])
            enemy_blink_state = not enemy_blink_state  # Toggle enemy blink
        
        if blink_timer >= 2 * 10:  # 2 seconds of blinking
            blinking = False
            blink_states = {}
            teleport_enemy()  # Actually teleport after blinking
    
    enemy_move_counter += 1
    if tunnel_cooldown > 0:
        tunnel_cooldown -= 1
    
    if tunnel_effect > 0:
        tunnel_effect -= 1
    
    if enemy_move_counter >= 6:  # Enemy moves every 6 frames
        enemy_move_counter = 0
        
        # Don't move normally while blinking (teleportation in progress)
        if blinking:
            return
        
        # Decide whether to tunnel (30% chance when not on cooldown)
        if random.random() < 0.3 and tunnel_cooldown == 0:
            quantum_tunneling = True
            tunnel_cooldown = 10  # Cooldown after tunneling
            tunnel_effect = 3  # Visual effect duration
        else:
            quantum_tunneling = False
        
        if quantum_tunneling:
            # Quantum tunneling movement (can go through walls)
            new_x, new_y = quantum_tunnel(enemy_x, enemy_y, player_x, player_y)
        else:
            # Normal BFS movement (pathfinding through maze)
            new_x, new_y = bfs_find_next_step(enemy_x, enemy_y, player_x, player_y)
        
        enemy_x, enemy_y = new_x, new_y
        
        # Check if the enemy caught the player
        if enemy_x == player_x and enemy_y == player_y:
            print("Game Over! The quantum enemy caught you!")
            show_game_over_screen()

def bfs_find_next_step(enemy_x, enemy_y, target_x, target_y):
    """Finds the next step for the enemy to move towards the player using BFS with strict prioritization."""
    queue = deque([(enemy_x, enemy_y)])
    visited = set()
    parent = {}  # To trace back the path

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Down, Right, Up, Left (prioritized)

    while queue:
        x, y = queue.popleft()

        if (x, y) in visited:
            continue
        visited.add((x, y))

        # If we reach the player, backtrack to find the first move
        if (x, y) == (target_x, target_y):
            while (x, y) in parent and parent[(x, y)] != (enemy_x, enemy_y):
                x, y = parent[(x, y)]
            return x, y  # Return the first move in the path

        # Check valid moves
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                maze[ny][nx] in [1, 3] and (nx, ny) not in visited):
                queue.append((nx, ny))
                parent[(nx, ny)] = (x, y)  # Store path

    # If BFS fails to find a path, return the current position
    return enemy_x, enemy_y

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)
    draw_maze()
    pygame.display.update()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in keys_pressed:
                keys_pressed[event.key] = True
        elif event.type == pygame.KEYUP:
            if event.key in keys_pressed:
                keys_pressed[event.key] = False
    
    if keys_pressed[pygame.K_w]:
        move_player(0, -1)
    if keys_pressed[pygame.K_s]:
        move_player(0, 1)
    if keys_pressed[pygame.K_a]:
        move_player(-1, 0)
    if keys_pressed[pygame.K_d]:
        move_player(1, 0)
    
    move_enemy()  # Move the enemy after the player moves
    
    clock.tick(10)

pygame.quit()