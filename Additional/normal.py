import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 21  # Ensuring an odd number for better randomness
CELL_SIZE = WIDTH // GRID_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quantum Maze Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)  # Player color
GREEN = (0, 255, 0)  # Exit color
RED = (255, 0, 0)  # Timer text color

font = pygame.font.Font(None, 36)

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

keys_pressed = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}

def draw_maze():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if maze[row][col] == 1:
                color = WHITE
            elif maze[row][col] == 3:
                color = GREEN  # Exit
            else:
                color = BLACK  # Walls
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    # Draw the player in blue
    pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
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
            print(f"You reached the exit in {int(time.time() - start_time)} seconds!")
            pygame.quit()
            exit()

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
    
    clock.tick(10)

pygame.quit()
