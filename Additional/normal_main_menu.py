
import pygame
import random
import time
import json
import os

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Screen settings
WIDTH, HEIGHT = 600, 600
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
GRAY = (169, 169, 169)

font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 24)

# Game states
STATE_MENU = "menu"
STATE_USERNAME = "username"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"
STATE_SUCCESS = "success"
STATE_LEADERBOARD = "leaderboard"
current_state = STATE_MENU
username = ""
show_error = False

# Game variables
maze = []
player_x, player_y = 0, 0
start_time = 0
final_time = 0
move_delay = 0.1  # Delay between moves when key is held down
last_move_time = 0

# Track key states
key_states = {
    pygame.K_w: False,
    pygame.K_s: False,
    pygame.K_a: False,
    pygame.K_d: False,
    pygame.K_UP: False,
    pygame.K_DOWN: False,
    pygame.K_LEFT: False,
    pygame.K_RIGHT: False
}

# Music settings
music_file = "background_music.mp3"  # Make sure this file exists
pygame.mixer.music.set_volume(0.5)
music_enabled = True
menu_music_playing = False
music_icon_size = 40

# Load music icon
try:
    music_icon = pygame.image.load("music_icon.png")
    music_icon = pygame.transform.scale(music_icon, (music_icon_size, music_icon_size))
except:
    # Create a music note symbol as fallback
    music_icon = pygame.Surface((music_icon_size, music_icon_size), pygame.SRCALPHA)
    # Draw a music note
    pygame.draw.polygon(music_icon, WHITE, [
        (10, 5), (20, 5), (25, 15), (35, 15), (35, 25), (25, 25), (20, 35), (10, 35)
    ])
    pygame.draw.ellipse(music_icon, WHITE, (30, 25, 10, 10))  # Bottom circle
    pygame.draw.ellipse(music_icon, WHITE, (30, 5, 10, 10))   # Top circle

music_icon_rect = pygame.Rect(10, HEIGHT - music_icon_size - 10, music_icon_size, music_icon_size)

# Leaderboard file
LEADERBOARD_FILE = "leaderboard.json"  # Defined before first use

# Load music icon
try:
    music_icon = pygame.image.load("music_icon.png")
    music_icon_size = 40
    music_icon = pygame.transform.scale(music_icon, (music_icon_size, music_icon_size))
except:
    music_icon_size = 40
    music_icon = pygame.Surface((music_icon_size, music_icon_size))
    music_icon.fill(BLUE)
music_icon_rect = pygame.Rect(10, HEIGHT - music_icon_size - 10, music_icon_size, music_icon_size)

def play_menu_music():
    try:
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1, fade_ms=1000)
        global menu_music_playing
        menu_music_playing = True
    except Exception as e:
        print(f"Could not play music: {e}")
        menu_music_playing = False

def pause_music():
    pygame.mixer.music.pause()
    global menu_music_playing
    menu_music_playing = False

def resume_music():
    pygame.mixer.music.unpause()
    global menu_music_playing
    menu_music_playing = True

def stop_music():
    pygame.mixer.music.fadeout(1000)
    global menu_music_playing
    menu_music_playing = False

# Load leaderboard from file
def load_leaderboard():
    global leaderboard
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
    else:
        leaderboard = []

# Save leaderboard to file
def save_leaderboard():
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f)

# Add a new score to the leaderboard
def add_to_leaderboard(name, time):
    global leaderboard
    existing_player = next((entry for entry in leaderboard if entry["name"] == name), None)

    if existing_player:
        if time < existing_player["time"]:
            existing_player["time"] = time
    else:
        leaderboard.append({"name": name, "time": time})

    leaderboard.sort(key=lambda x: x["time"])
    if len(leaderboard) > 10:
        leaderboard = leaderboard[:10]
    save_leaderboard()

# Buttons
class Button:
    def __init__(self, text, x, y, width, height, action):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action

    def draw(self):
        pygame.draw.rect(screen, GRAY, self.rect)
        label = font.render(self.text, True, BLACK)
        screen.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2, 
                          self.rect.y + (self.rect.height - label.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Define buttons
buttons_main_menu = [
    Button("New Game", 200, 200, 200, 50, "new_game"),
    Button("Leaderboard", 200, 260, 200, 50, "leaderboard"),
    Button("Options", 200, 320, 200, 50, "options"),
    Button("Exit", 200, 380, 200, 50, "exit")
]

buttons_pause_menu = [
    Button("Continue", 200, 200, 200, 50, "continue"),
    Button("New Game", 200, 260, 200, 50, "new_game"),
    Button("Main Menu", 200, 320, 200, 50, "main_menu")
]

button_start = Button("Start", 250, 300, 100, 50, "start")
button_continue_success = Button("Continue", 200, 450, 200, 50, "continue_success")
button_leaderboard_continue = Button("Continue", 200, 500, 200, 50, "leaderboard_continue")

def draw_menu(buttons, show_title=False):
    screen.fill(BLACK)
    if show_title:
        title_text = title_font.render("Quantum Maze", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    for button in buttons:
        button.draw()
    
    if music_enabled:
        screen.blit(music_icon, music_icon_rect)
    else:
        faded_icon = music_icon.copy()
        faded_icon.fill((100, 100, 100, 128), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(faded_icon, music_icon_rect)
    
    pygame.display.update()

def draw_username_screen():
    screen.fill(BLACK)
    title_text = title_font.render("Enter Username", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
    pygame.draw.rect(screen, WHITE, (150, 200, 300, 50))
    username_text = font.render(username, True, BLACK)
    screen.blit(username_text, (160, 210))
    button_start.draw()
    if show_error:
        error_text = font.render("Username cannot be empty!", True, RED)
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, button_start.rect.bottom + 20))
    pygame.display.update()

def draw_success_screen():
    screen.fill(BLACK)
    success_text = title_font.render("Quantum Success!", True, GREEN)
    time_text = font.render(f"You escaped the Quantum Maze in {final_time} seconds", True, WHITE)
    
    screen.blit(success_text, (WIDTH//2 - success_text.get_width()//2, 200))
    screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 270))
    
    button_continue_success.draw()
    pygame.display.update()

def draw_leaderboard():
    screen.fill(BLACK)
    title_text = title_font.render("Leaderboard", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    
    if not leaderboard:
        no_scores = font.render("No scores yet!", True, WHITE)
        screen.blit(no_scores, (WIDTH // 2 - no_scores.get_width() // 2, 150))
    else:
        for i, entry in enumerate(leaderboard[:10]):
            rank = i + 1
            name = entry["name"]
            time = entry["time"]
            entry_text = small_font.render(f"{rank}. {name}: {time} seconds", True, WHITE)
            screen.blit(entry_text, (WIDTH // 2 - entry_text.get_width() // 2, 150 + i * 30))
    
    button_leaderboard_continue.draw()
    pygame.display.update()

def start_new_game():
    global maze, player_x, player_y, start_time, current_state, key_states
    maze = generate_maze()
    player_x, player_y = 0, 0
    start_time = time.time()
    current_state = STATE_RUNNING
    key_states = {key: False for key in key_states}
    
    # Pause menu music when game starts
    if music_enabled:
        pause_music()

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

def draw_maze():
    screen.fill(BLACK)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if maze[y][x] == 1:
                pygame.draw.rect(screen, WHITE, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif maze[y][x] == 3:
                pygame.draw.rect(screen, GREEN, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, RED)
    screen.blit(timer_text, (10, 10))

def handle_movement():
    global player_x, player_y, current_state, final_time, last_move_time
    
    current_time = time.time()
    if current_time - last_move_time < move_delay:
        return
    
    dx, dy = 0, 0
    
    if key_states[pygame.K_w] or key_states[pygame.K_UP]:
        dy = -1
    elif key_states[pygame.K_s] or key_states[pygame.K_DOWN]:
        dy = 1
    
    if key_states[pygame.K_a] or key_states[pygame.K_LEFT]:
        dx = -1
    elif key_states[pygame.K_d] or key_states[pygame.K_RIGHT]:
        dx = 1
    
    if dx != 0 or dy != 0:
        new_x, new_y = player_x + dx, player_y + dy
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and maze[new_y][new_x] in [1, 3]:
            player_x, player_y = new_x, new_y
            if maze[new_y][new_x] == 3:
                final_time = int(time.time() - start_time)
                add_to_leaderboard(username, final_time)
                current_state = STATE_SUCCESS
                if music_enabled:
                    resume_music()
        last_move_time = current_time

# Load leaderboard at startup
load_leaderboard()

# Start menu music if enabled
if music_enabled:
    play_menu_music()

running = True
while running:
    if current_state == STATE_MENU:
        if music_enabled and not menu_music_playing:
            resume_music()
        draw_menu(buttons_main_menu, show_title=True)
    elif current_state == STATE_USERNAME:
        draw_username_screen()
    elif current_state == STATE_PAUSED:
        if music_enabled and not menu_music_playing:
            resume_music()
        draw_menu(buttons_pause_menu)
    elif current_state == STATE_RUNNING:
        handle_movement()
        draw_maze()
        pygame.display.update()
    elif current_state == STATE_SUCCESS:
        draw_success_screen()
    elif current_state == STATE_LEADERBOARD:
        draw_leaderboard()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Music toggle handling
            if music_icon_rect.collidepoint(event.pos) and current_state in [STATE_MENU, STATE_PAUSED, STATE_LEADERBOARD]:
                music_enabled = not music_enabled
                if music_enabled:
                    play_menu_music()
                else:
                    pause_music()
            
            if current_state == STATE_MENU:
                for button in buttons_main_menu:
                    if button.is_clicked(event.pos):
                        if button.action == "new_game":
                            current_state = STATE_USERNAME
                            username = ""
                        elif button.action == "leaderboard":
                            current_state = STATE_LEADERBOARD
                        elif button.action == "exit":
                            running = False
            elif current_state == STATE_USERNAME:
                if button_start.is_clicked(event.pos):
                    if username.strip():
                        show_error = False
                        start_new_game()
                    else:
                        show_error = True
            elif current_state == STATE_PAUSED:
                for button in buttons_pause_menu:
                    if button.is_clicked(event.pos):
                        if button.action == "continue":
                            current_state = STATE_RUNNING
                            if music_enabled:
                                pause_music()
                        elif button.action == "new_game":
                            current_state = STATE_USERNAME
                            username = ""
                        elif button.action == "main_menu":
                            current_state = STATE_MENU
            elif current_state == STATE_SUCCESS:
                if button_continue_success.is_clicked(event.pos):
                    current_state = STATE_LEADERBOARD
            elif current_state == STATE_LEADERBOARD:
                if button_leaderboard_continue.is_clicked(event.pos):
                    current_state = STATE_MENU
        elif event.type == pygame.KEYDOWN:
            if current_state == STATE_USERNAME:
                if event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif event.key == pygame.K_RETURN:
                    if username.strip():
                        show_error = False
                        start_new_game()
                    else:
                        show_error = True
                else:
                    username += event.unicode
            elif current_state == STATE_RUNNING:
                if event.key in key_states:
                    key_states[event.key] = True
                elif event.key == pygame.K_ESCAPE:
                    current_state = STATE_PAUSED
                    if music_enabled:
                        resume_music()
        elif event.type == pygame.KEYUP:
            if current_state == STATE_RUNNING:
                if event.key in key_states:
                    key_states[event.key] = False

pygame.quit()