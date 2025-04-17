import pygame
import random
import time
import sys
import os
import cv2  # OpenCV for video handling

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
BUTTON_COLOR = (200, 200, 200)
BUTTON_HOVER = (150, 150, 150)

font = pygame.font.Font(None, 36)
button_font = pygame.font.Font(None, 30)

# Function to display the start screen
def show_start_screen():
    screen.fill(WHITE)
    text = font.render("Level 5: Quantum Master", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.update()
    time.sleep(4)

# Function to show tutorial video with OpenCV
def show_tutorial_video():
    # Create a start button
    button_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 40)
    
    video_path = "5.mp4"
    
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
                
                # Add "Tutorial - Level 5" text - draw this BEFORE the video
                tutorial_text = font.render("Tutorial - Level 5", True, WHITE)
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

# Function to display the end screen with a button
def show_end_screen():
    global start_time
    elapsed_time = int(time.time() - start_time)
    
    # Get username from shared file
    try:
        with open("current_player.txt", "r") as f:
            username = f.read().strip()
    except:
        username = "Player"  # Default if file not found

    # Calculate total time from the database
    import sqlite3
    total_time = elapsed_time  # Start with current level time
    
    try:
        conn = sqlite3.connect("quantum_maze_data.db")
        cursor = conn.cursor()
        
        # Get player ID
        cursor.execute("SELECT id FROM players WHERE username = ?", (username,))
        player_result = cursor.fetchone()
        
        if player_result:
            player_id = player_result[0]
            
            # Get times for previous levels
            cursor.execute("""
                SELECT level, completion_time FROM level_times 
                WHERE player_id = ? AND level < 5
            """, (player_id,))
            
            level_times = cursor.fetchall()
            
            # Add up all previous level times
            for _, level_time in level_times:
                total_time += level_time
        
        # Save this level's time
        cursor.execute("""
            INSERT OR REPLACE INTO level_times (player_id, level, completion_time)
            VALUES ((SELECT id FROM players WHERE username = ?), 5, ?)
        """, (username, elapsed_time))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

    screen.fill(WHITE)
    
    # Create text surfaces
    line1 = font.render(f"Level 5 Completed in {elapsed_time} Seconds!", True, BLACK)
    line2 = font.render("You have mastered the Quantum Multiverse.", True, BLACK)
    line3 = font.render("You are no longer a player - now an Architect", True, BLACK)
    line4 = font.render("The Quantum Master", True, BLACK)
    
    # Position text
    line1_rect = line1.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
    line2_rect = line2.get_rect(center=(WIDTH//2, HEIGHT//2 - 20))
    line3_rect = line3.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
    line4_rect = line4.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
    
    # Button to view leaderboard
    button_rect = pygame.Rect(WIDTH // 2 - 125, HEIGHT // 2 + 100, 250, 50) 
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)
        
        # Draw text
        screen.blit(line1, line1_rect)
        screen.blit(line2, line2_rect)
        screen.blit(line3, line3_rect)
        screen.blit(line4, line4_rect)
        
        # Change button color on hover
        button_color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, button_color, button_rect)

        # Button text
        button_text = button_font.render("View Leaderboard", True, BLACK)
        text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, text_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(mouse_pos):
                pygame.quit()
                # Launch the leaderboard with username and total time
                import subprocess
                subprocess.Popen([sys.executable, "leaderboard.py", username, str(total_time)])
                sys.exit()


# Generate Maze
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

def draw_maze(blink=False):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if blink:
                color = random.choice([WHITE, BLACK])  # Random blinking effect
            else:
                color = WHITE if maze[row][col] == 1 else BLACK
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))

            # Draw the exit in green
            if maze[row][col] == 3:
                pygame.draw.rect(screen, GREEN, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Draw the player in blue (after the maze is drawn)
    pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Draw the timer
    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, RED)
    screen.blit(timer_text, (10, 10))

def move_player(dx, dy):
    global player_x, player_y, start_time
    new_x, new_y = player_x + dx, player_y + dy
    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and maze[new_y][new_x] in [1, 3]:
        player_x, player_y = new_x, new_y
        if maze[new_y][new_x] == 3:
            print(f"You reached the exit in {int(time.time() - start_time)} seconds!")
            show_end_screen()  # Show end screen with the button
            pygame.quit()
            exit()

direction = None
blinking = False
running = True
clock = pygame.time.Clock()

def toggle_superposition():
    global blinking
    blinking = True
    pygame.time.set_timer(pygame.USEREVENT, 200)

def stop_superposition():
    global blinking, maze
    blinking = False
    pygame.time.set_timer(pygame.USEREVENT, 0)
    maze = generate_maze()

# Show start screen before game begins
show_start_screen()

# Show tutorial video before game begins
# Reset start_time after the tutorial video
if show_tutorial_video():
    start_time = time.time()

while running:
    screen.fill(BLACK)
    draw_maze(blinking)
    pygame.display.update()

    if direction and not blinking:
        move_player(*direction)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                direction = (0, -1)
            elif event.key == pygame.K_s:
                direction = (0, 1)
            elif event.key == pygame.K_a:
                direction = (-1, 0)
            elif event.key == pygame.K_d:
                direction = (1, 0)
            stop_superposition()
        elif event.type == pygame.KEYUP:
            direction = None
            toggle_superposition()
        elif event.type == pygame.USEREVENT and blinking:
            draw_maze(blink=True)

    clock.tick(10)

pygame.quit()