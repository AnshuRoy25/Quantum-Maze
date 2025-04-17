import pygame
import random
import time

# Initialize Pygame
pygame.init()

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
WHITE_DOOR = (255, 255, 255)  
PURPLE = (128, 0, 128)  

font = pygame.font.Font(None, 36)

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
    
    # **Limit to exactly 3 pairs**
    max_pairs = 3  
    for i in range(0, max_pairs * 2, 2):  
        door1, door2 = door_positions[i], door_positions[i + 1]
        maze[door1[1]][door1[0]] = 2  
        maze[door2[1]][door2[0]] = 2  
        door_states[door1] = True  
        door_states[door2] = False  
        entangled_pairs.append((door1, door2))

    return maze, door_states, entangled_pairs

player_x, player_y = 0, 0
maze, door_states, entangled_pairs = generate_maze()
start_time = time.time()

keys_pressed = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}

def draw_maze():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if maze[row][col] == 1:
                color = WHITE  
            elif maze[row][col] == 3:
                color = GREEN
            elif maze[row][col] == 2:
                color = RED if not door_states.get((col, row), False) else WHITE_DOOR
            else:
                color = BLACK
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, (255, 0, 0))
    screen.blit(timer_text, (10, 10))

def move_player(dx, dy):
    global player_x, player_y
    
    new_x, new_y = player_x + dx, player_y + dy
    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
        if maze[new_y][new_x] == 2:
            if door_states.get((new_x, new_y), False):
                player_x, player_y = new_x, new_y
        elif maze[new_y][new_x] in [1, 3]:
            player_x, player_y = new_x, new_y
        
        if maze[new_y][new_x] == 3:
            print(f"You reached the exit in {int(time.time() - start_time)} seconds!")
            pygame.quit()
            exit()

def is_adjacent_to_door():
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        adj_x, adj_y = player_x + dx, player_y + dy
        if (adj_x, adj_y) in door_states:
            return (adj_x, adj_y)
    return None

def toggle_door():
    adjacent_door = is_adjacent_to_door()
    if adjacent_door:
        for pair in entangled_pairs:
            if adjacent_door in pair:
                door1, door2 = pair
                door_states[door1] = not door_states[door1]
                door_states[door2] = not door_states[door2]
                break  

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
            elif event.key == pygame.K_f:
                toggle_door()
        elif event.type == pygame.KEYUP:
            if event.key in keys_pressed:
                keys_pressed[event.key] = False
    
    if keys_pressed[pygame.K_w]: move_player(0, -1)
    if keys_pressed[pygame.K_s]: move_player(0, 1)
    if keys_pressed[pygame.K_a]: move_player(-1, 0)
    if keys_pressed[pygame.K_d]: move_player(1, 0)
    
    clock.tick(10)

pygame.quit()
