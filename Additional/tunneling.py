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
YELLOW = (255, 255, 0)  

font = pygame.font.Font(None, 36)

# Initialize variables
player_x, player_y = 0, 0
tunneling_probability = 20  
tunnel_cooldown_time = 10  
last_tunnel_time = 0  

# Generate the maze
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

    for _ in range(3):  
        while True:
            ex, ey = random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2)
            if maze[ey][ex] == 1:
                maze[ey][ex] = 4  
                break
    return maze

maze = generate_maze()
start_time = time.time()

def draw_maze():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if maze[row][col] == 1:
                color = WHITE  
            elif maze[row][col] == 3:
                color = GREEN  
            elif maze[row][col] == 4:
                color = YELLOW  
            else:
                color = BLACK  
            pygame.draw.rect(screen, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    pygame.draw.rect(screen, BLUE, (player_x * CELL_SIZE, player_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    elapsed_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {elapsed_time}s", True, RED)
    prob_text = font.render(f"Tunnel %: {tunneling_probability}%", True, YELLOW)
    tunnel_cd_text = font.render(f"Tunnel CD: {max(0, tunnel_cooldown_time - int(time.time() - last_tunnel_time))}s", True, RED)

    screen.blit(timer_text, (10, 10))
    screen.blit(prob_text, (10, 40))
    screen.blit(tunnel_cd_text, (10, 70))

def move_player(dx, dy):
    global player_x, player_y, tunneling_probability

    new_x, new_y = player_x + dx, player_y + dy
    if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
        if maze[new_y][new_x] in [1, 3]:  
            player_x, player_y = new_x, new_y
        elif maze[new_y][new_x] == 4:  
            tunneling_probability = min(100, tunneling_probability + 10)
            maze[new_y][new_x] = 1
            player_x, player_y = new_x, new_y
        if maze[new_y][new_x] == 3:  
            print(f"You reached the exit in {int(time.time() - start_time)} seconds!")
            pygame.quit()
            exit()

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
    draw_maze()
    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                keys = pygame.key.get_pressed()
                dx = (keys[pygame.K_d] - keys[pygame.K_a])
                dy = (keys[pygame.K_s] - keys[pygame.K_w])
                attempt_tunneling(dx, dy)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        move_player(0, -1)
    if keys[pygame.K_s]:
        move_player(0, 1)
    if keys[pygame.K_a]:
        move_player(-1, 0)
    if keys[pygame.K_d]:
        move_player(1, 0)

    clock.tick(10)

pygame.quit()
