# leaderboard.py
import pygame
import sqlite3
import sys
import os

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 700, 600  # Increased width to accommodate more columns
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quantum Maze Leaderboard")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
DARK_GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
BLUE = (100, 149, 237)
LIGHT_BLUE = (173, 216, 230)

# Fonts
title_font = pygame.font.Font(None, 50)
header_font = pygame.font.Font(None, 36)
leaderboard_font = pygame.font.Font(None, 30)
button_font = pygame.font.Font(None, 30)
level_font = pygame.font.Font(None, 26)

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

def get_player_id(username):
    """Get player ID from username, creating a new player if needed"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check if player exists
    cursor.execute("SELECT id FROM players WHERE username = ?", (username,))
    player = cursor.fetchone()
    
    if player:
        player_id = player[0]
    else:
        # Create new player
        cursor.execute("INSERT INTO players (username) VALUES (?)", (username,))
        conn.commit()
        player_id = cursor.lastrowid
    
    conn.close()
    return player_id

def save_level_time(username, level, completion_time):
    """Save completion time for a specific level"""
    player_id = get_player_id(username)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
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

def save_total_time(username, total_time):
    """Save total completion time for all levels"""
    player_id = get_player_id(username)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO total_times (player_id, total_time) VALUES (?, ?)",
        (player_id, total_time)
    )
    
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    """Get the top players ordered by total time"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.username, tt.total_time, tt.completed_date, p.id
        FROM total_times tt
        JOIN players p ON tt.player_id = p.id
        ORDER BY tt.total_time ASC
        LIMIT ?
    """, (limit,))
    
    results = cursor.fetchall()
    
    # Enhanced results with level times
    enhanced_results = []
    for username, total_time, completed_date, player_id in results:
        # Get individual level times
        cursor.execute("""
            SELECT level, completion_time
            FROM level_times
            WHERE player_id = ?
            ORDER BY level
        """, (player_id,))
        
        level_times = {level: time for level, time in cursor.fetchall()}
        
        # Add to enhanced results
        enhanced_results.append((username, total_time, completed_date, level_times))
    
    conn.close()
    
    return enhanced_results

def format_time(seconds):
    """Format seconds into mm:ss format"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def draw_leaderboard():
    """Draw the leaderboard screen"""
    screen.fill(BLACK)
    
    # Draw title
    title = title_font.render("QUANTUM MAZE LEADERBOARD", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
    
    # Get leaderboard data
    leaderboard_data = get_leaderboard()
    
    # Draw headers
    headers = [("Rank", 60), ("Player", 170), ("L1", 250), ("L2", 310), ("L3", 370), ("L4", 430), ("L5", 490), ("Total", 570)]
    
    for header_text, x_pos in headers:
        header = header_font.render(header_text, True, WHITE)
        screen.blit(header, (x_pos - header.get_width()//2, 90))
    
    # Draw separator line
    pygame.draw.line(screen, WHITE, (50, 125), (650, 125), 2)
    
    # Draw leaderboard entries
    y_position = 140
    for i, (username, total_time, date, level_times) in enumerate(leaderboard_data):
        # Row background for readability (alternate colors)
        if i % 2 == 0:
            pygame.draw.rect(screen, DARK_GRAY, (50, y_position-5, 600, 35))
        
        # Draw rank with medal for top 3
        rank_text = f"{i+1}"
        
        if i == 0:
            rank_color = GOLD
        elif i == 1:
            rank_color = SILVER
        elif i == 2:
            rank_color = BRONZE
        else:
            rank_color = WHITE
            
        rank = leaderboard_font.render(rank_text, True, rank_color)
        name = leaderboard_font.render(username, True, WHITE)
        time = leaderboard_font.render(format_time(total_time), True, WHITE)
        
        screen.blit(rank, (60 - rank.get_width()//2, y_position))
        screen.blit(name, (170 - name.get_width()//2, y_position))
        screen.blit(time, (570 - time.get_width()//2, y_position))
        
        # Draw individual level times
        for level in range(1, 6):
            if level in level_times:
                level_time = format_time(level_times[level])
                level_color = WHITE
            else:
                level_time = "--:--"
                level_color = GRAY
            
            level_text = level_font.render(level_time, True, level_color)
            level_x = 250 + (level-1) * 60
            screen.blit(level_text, (level_x - level_text.get_width()//2, y_position+2))
        
        y_position += 40
    
    # Draw button
    button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 80, 200, 50)
    mouse_pos = pygame.mouse.get_pos()
    button_color = DARK_GRAY if button_rect.collidepoint(mouse_pos) else GRAY
    
    pygame.draw.rect(screen, button_color, button_rect, border_radius=10)
    button_text = button_font.render("Main Menu", True, BLACK)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    
    return button_rect

def show_personal_results(username, total_time):
    """Show the player's results before the leaderboard"""
    screen.fill(BLACK)
    
    # Draw title
    title = title_font.render("QUANTUM MAZE COMPLETED!", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
    
    # Get player's level times
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    player_id = get_player_id(username)
    cursor.execute("""
        SELECT level, completion_time
        FROM level_times
        WHERE player_id = ?
        ORDER BY level
    """, (player_id,))
    
    level_times = cursor.fetchall()
    conn.close()
    
    # Draw player results
    username_text = header_font.render(f"Player: {username}", True, WHITE)
    screen.blit(username_text, (WIDTH//2 - username_text.get_width()//2, 160))
    
    # Draw individual level times
    y_pos = 200
    for level, time in level_times:
        level_text = header_font.render(f"Level {level}: {format_time(time)}", True, LIGHT_BLUE)
        screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, y_pos))
        y_pos += 40
    
    # Draw total time
    total_time_text = header_font.render(f"Total Time: {format_time(total_time)}", True, GOLD)
    screen.blit(total_time_text, (WIDTH//2 - total_time_text.get_width()//2, y_pos + 10))
    
    # Draw button
    button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 150, 200, 50)
    pygame.draw.rect(screen, GRAY, button_rect, border_radius=10)
    button_text = button_font.render("View Leaderboard", True, BLACK)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    waiting = False

# In leaderboard.py, modify the main() function:

def main(username, total_time=None):
    """Main leaderboard function"""
    init_db()
    
    # If total_time is provided, save it and show personal results
    if total_time is not None:
        save_total_time(username, total_time)
        show_personal_results(username, total_time)
    
    # Show leaderboard
    running = True
    while running:
        button_rect = draw_leaderboard()
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    # Create a signal file that GAME.py can detect
                    try:
                        with open("return_to_menu.signal", "w") as f:
                            f.write("return")
                    except Exception as e:
                        print(f"Error creating signal file: {e}")
                    
                    # Close the leaderboard window
                    pygame.quit()
                    sys.exit()
    
    pygame.quit()

if __name__ == "__main__":
    # If run directly, check for command line arguments
    if len(sys.argv) > 1:
        username = sys.argv[1]
        if len(sys.argv) > 2:
            total_time = int(sys.argv[2])
            main(username, total_time)
        else:
            main(username)
    else:
        # Default for testing
        main("TestPlayer")