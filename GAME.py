import pygame
import random
import time
import subprocess
import sys
import os
import sqlite3

class Color:
    """Constants for colors used in the game"""
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    PURPLE = (128, 0, 128)
    GRAY = (169, 169, 169)

class GameState:
    """Game state constants"""
    MENU = "menu"
    USERNAME = "username"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"

class Button:
    """Button class for UI elements"""
    def __init__(self, text, x, y, width, height, action):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action

    def draw(self, screen, font):
        pygame.draw.rect(screen, Color.GRAY, self.rect)
        label = font.render(self.text, True, Color.BLACK)
        screen.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2, 
                          self.rect.y + (self.rect.height - label.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class MusicManager:
    """Handles all music-related functionality"""
    def __init__(self, music_file="background_music.mp3"):
        self.music_file = music_file
        self.enabled = True
        self.playing = False
        self.icon_size = 40
        
        # Load or create music icon
        try:
            self.icon = pygame.image.load("music_icon.png")
            self.icon = pygame.transform.scale(self.icon, (self.icon_size, self.icon_size))
        except:
            # Create a music note symbol as fallback
            self.icon = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            # Draw a music note
            pygame.draw.polygon(self.icon, Color.WHITE, [
                (10, 5), (20, 5), (25, 15), (35, 15), (35, 25), (25, 25), (20, 35), (10, 35)
            ])
            pygame.draw.ellipse(self.icon, Color.WHITE, (30, 25, 10, 10))  # Bottom circle
            pygame.draw.ellipse(self.icon, Color.WHITE, (30, 5, 10, 10))   # Top circle

        self.icon_rect = None
        pygame.mixer.music.set_volume(0.5)
        
    def set_icon_position(self, x, y):
        """Set the position of the music icon"""
        self.icon_rect = pygame.Rect(x, y, self.icon_size, self.icon_size)
    
    def play(self):
        """Start playing music"""
        if not self.enabled:
            return
        try:
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(-1, fade_ms=1000)
            self.playing = True
        except Exception as e:
            print(f"Could not play music: {e}")
            self.playing = False
    
    def pause(self):
        """Pause the music"""
        pygame.mixer.music.pause()
        self.playing = False
    
    def resume(self):
        """Resume paused music"""
        if self.enabled:
            pygame.mixer.music.unpause()
            self.playing = True
    
    def stop(self):
        """Stop the music with fade-out"""
        pygame.mixer.music.fadeout(1000)
        self.playing = False
    
    def toggle(self):
        """Toggle music on/off"""
        self.enabled = not self.enabled
        if self.enabled:
            self.play()
        else:
            self.pause()
    
    def draw(self, screen):
        """Draw the music icon"""
        if self.enabled:
            screen.blit(self.icon, self.icon_rect)
        else:
            faded_icon = self.icon.copy()
            faded_icon.fill((100, 100, 100, 128), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(faded_icon, self.icon_rect)

class MazeGenerator:
    """Generates and manages the maze"""
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.maze = []
        
    def generate(self):
        """Generate a new random maze using depth-first search algorithm"""
        self.maze = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        stack = [(random.randint(0, self.grid_size // 2) * 2, random.randint(0, self.grid_size // 2) * 2)]
        visited = set(stack)
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        
        while stack:
            x, y = stack[-1]
            random.shuffle(directions)
            found = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size and (nx, ny) not in visited:
                    self.maze[y][x] = 1
                    self.maze[ny][nx] = 1
                    self.maze[y + dy // 2][x + dx // 2] = 1
                    stack.append((nx, ny))
                    visited.add((nx, ny))
                    found = True
                    break
            if not found:
                stack.pop()
        
        # Set start and exit points
        self.maze[0][0] = 1
        self.maze[self.grid_size - 1][self.grid_size - 1] = 3
        
        return self.maze
    
    def draw(self, screen, cell_size, player_pos):
        """Draw the maze and player"""
        screen.fill(Color.BLACK)
        
        # Draw maze cells
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.maze[y][x] == 1:
                    pygame.draw.rect(screen, Color.WHITE, (x * cell_size, y * cell_size, cell_size, cell_size))
                elif self.maze[y][x] == 3:
                    pygame.draw.rect(screen, Color.GREEN, (x * cell_size, y * cell_size, cell_size, cell_size))
        
        # Draw player
        player_x, player_y = player_pos
        pygame.draw.rect(screen, Color.BLUE, (player_x * cell_size, player_y * cell_size, cell_size, cell_size))

class Player:
    """Player class to handle movement and position"""
    def __init__(self):
        self.x = 0
        self.y = 0
        self.last_move_time = 0
        self.move_delay = 0.1  # Delay between moves when key is held down
        self.key_states = {
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False
        }
    
    def reset(self):
        """Reset player position to start"""
        self.x = 0
        self.y = 0
    
    def handle_movement(self, maze, grid_size):
        """Handle player movement based on key states"""
        current_time = time.time()
        if current_time - self.last_move_time < self.move_delay:
            return False  # No movement occurred
        
        dx, dy = 0, 0
        
        if self.key_states[pygame.K_w] or self.key_states[pygame.K_UP]:
            dy = -1
        elif self.key_states[pygame.K_s] or self.key_states[pygame.K_DOWN]:
            dy = 1
        
        if self.key_states[pygame.K_a] or self.key_states[pygame.K_LEFT]:
            dx = -1
        elif self.key_states[pygame.K_d] or self.key_states[pygame.K_RIGHT]:
            dx = 1
        
        if dx != 0 or dy != 0:
            new_x, new_y = self.x + dx, self.y + dy
            if 0 <= new_x < grid_size and 0 <= new_y < grid_size and maze[new_y][new_x] in [1, 3]:
                self.x, self.y = new_x, new_y
                self.last_move_time = current_time
                return True  # Movement occurred
        
        return False

    def is_at_exit(self, maze):
        """Check if player has reached the exit"""
        return maze[self.y][self.x] == 3

class UIManager:
    """Manages all UI elements and screens"""
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 50)
        
        # Create buttons - updated positions for 800x800 screen
        self.buttons_main_menu = [
            Button("New Game", 300, 250, 200, 50, "new_game"),
            Button("Leaderboard", 300, 320, 200, 50, "leaderboard"),
            Button("Exit", 300, 390, 200, 50, "exit")
        ]
        
        self.buttons_pause_menu = [
            Button("Continue", 300, 250, 200, 50, "continue"),
            Button("New Game", 300, 320, 200, 50, "new_game"),
            Button("Main Menu", 300, 390, 200, 50, "main_menu")
        ]
        
        self.button_start = Button("Start", 350, 350, 100, 50, "start")
        self.button_continue_success = Button("Continue", 300, 450, 200, 50, "continue_success")
    
    def draw_menu(self, buttons, music_manager, show_title=False):
        """Draw a menu screen with buttons"""
        self.screen.fill(Color.BLACK)
        
        if show_title:
            title_text = self.title_font.render("Quantum Maze", True, Color.WHITE)
            self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))
        
        for button in buttons:
            button.draw(self.screen, self.font)
        
        music_manager.draw(self.screen)
        pygame.display.update()
    
    def draw_username_screen(self, username, show_error):
        """Draw the username input screen"""
        self.screen.fill(Color.BLACK)
        
        title_text = self.title_font.render("Enter Username", True, Color.WHITE)
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 150))
        
        pygame.draw.rect(self.screen, Color.WHITE, (250, 250, 300, 50))
        username_text = self.font.render(username, True, Color.BLACK)
        self.screen.blit(username_text, (260, 260))
        
        self.button_start.draw(self.screen, self.font)
        
        if show_error:
            error_text = self.font.render("Username cannot be empty!", True, Color.RED)
            self.screen.blit(error_text, (self.width // 2 - error_text.get_width() // 2, 
                                        self.button_start.rect.bottom + 20))
        
        pygame.display.update()
    
    def draw_game_screen(self, maze_generator, player, start_time):
        """Draw the main game screen with maze and timer"""
        maze_generator.draw(self.screen, self.width // maze_generator.grid_size, (player.x, player.y))
        
        elapsed_time = int(time.time() - start_time)
        timer_text = self.font.render(f"Time: {elapsed_time}s", True, Color.RED)
        self.screen.blit(timer_text, (10, 10))
        
        pygame.display.update()
    
    def draw_success_screen(self, final_time):
        """Draw the success screen"""
        self.screen.fill(Color.BLACK)
        
        success_text = self.title_font.render("Quantum Success!", True, Color.GREEN)
        time_text = self.font.render(f"You escaped the Quantum Maze in {final_time} seconds", True, Color.WHITE)
        
        self.screen.blit(success_text, (self.width//2 - success_text.get_width()//2, 300))
        self.screen.blit(time_text, (self.width//2 - time_text.get_width()//2, 370))
        
        self.button_continue_success.draw(self.screen, self.font)
        pygame.display.update()

class Game:
    """Main game class that manages everything"""
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        
        # Game settings - updated to 800x800
        self.width = 800
        self.height = 800
        self.grid_size = 21
        self.cell_size = self.width // self.grid_size
        
        # Create screen
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Quantum Maze Game")
        
        # Initialize components
        self.music_manager = MusicManager()
        self.music_manager.set_icon_position(10, self.height - self.music_manager.icon_size - 10)
        
        self.ui_manager = UIManager(self.screen, self.width, self.height)
        self.maze_generator = MazeGenerator(self.grid_size)
        self.player = Player()
        
        # Game state variables
        self.current_state = GameState.MENU
        self.username = ""
        self.show_error = False
        self.start_time = 0
        self.final_time = 0
        self.running = True
    
    def init_leaderboard_db(self):
        """Initialize the leaderboard database"""
        try:
            conn = sqlite3.connect("quantum_maze_data.db")
            cursor = conn.cursor()
            
            # Create players table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE
                )
            """)
            
            # Create level times table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS level_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    level INTEGER,
                    completion_time INTEGER,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """)
            
            # Create total times table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS total_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    total_time INTEGER,
                    completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """)
            
            # Insert or ignore the current player
            cursor.execute("""
                INSERT OR IGNORE INTO players (username) VALUES (?)
            """, (self.username,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def save_username(self):
        """Save the current username to a file for other levels to access"""
        try:
            with open("current_player.txt", "w") as f:
                f.write(self.username)
        except Exception as e:
            print(f"Error saving username: {e}")
    
    def start_new_game(self):
        """Start a new game by launching the Level 1 module"""
        # Clear the main window to black
        self.screen.fill(Color.BLACK)
        pygame.display.flip()
        
        # Pause menu music if enabled
        if self.music_manager.enabled:
            self.music_manager.pause()
        
        try:
            if sys.platform == "win32":
                # Windows: Hide console
                subprocess.Popen(
                    [sys.executable, "sp_electron (Level 1).py"], 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # macOS/Linux: Run normally
                subprocess.Popen([sys.executable, "sp_electron (Level 1).py"])
            
            # Keep the main window "paused" (black) while Level 1 runs
            level1_active = True
            while level1_active and self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        level1_active = False
                
                # Check for the signal file
                if os.path.exists("return_to_menu.signal"):
                    try:
                        os.remove("return_to_menu.signal")
                    except Exception as e:
                        print(f"Error removing signal file: {e}")
                    level1_active = False
                    
                # Check if Level 1 window is still open (optional)
                pygame.time.delay(100)  # Prevent high CPU usage
                
        except Exception as e:
            print(f"Error launching Level 1: {e}")
        
        # When Level 1 closes, return to menu
        self.current_state = GameState.MENU
        if self.music_manager.enabled:
            self.music_manager.resume()
    
    def handle_menu_click(self, pos):
        """Handle clicks in the main menu"""
        if self.music_manager.icon_rect.collidepoint(pos):
            self.music_manager.toggle()
            return
            
        for button in self.ui_manager.buttons_main_menu:
            if button.is_clicked(pos):
                if button.action == "new_game":
                    self.current_state = GameState.USERNAME
                    self.username = ""
                elif button.action == "leaderboard":
                    # Show leaderboard when options is clicked
                    try:
                        subprocess.Popen([sys.executable, "leaderboard.py"])
                    except Exception as e:
                        print(f"Error launching leaderboard: {e}")
                elif button.action == "exit":
                    self.running = False
    
    def handle_username_click(self, pos):
        """Handle clicks in the username screen"""
        if self.ui_manager.button_start.is_clicked(pos):
            if self.username.strip():
                self.show_error = False
                # Save username before starting game
                self.save_username()
                # Initialize the database
                self.init_leaderboard_db()
                # Start the game
                self.start_new_game()
            else:
                self.show_error = True
    
    def handle_pause_click(self, pos):
        """Handle clicks in the pause menu"""
        if self.music_manager.icon_rect.collidepoint(pos):
            self.music_manager.toggle()
            return
            
        for button in self.ui_manager.buttons_pause_menu:
            if button.is_clicked(pos):
                if button.action == "continue":
                    self.current_state = GameState.RUNNING
                    if self.music_manager.enabled:
                        self.music_manager.pause()
                elif button.action == "new_game":
                    self.current_state = GameState.USERNAME
                    self.username = ""
                elif button.action == "main_menu":
                    self.current_state = GameState.MENU
    
    def handle_success_click(self, pos):
        """Handle clicks in the success screen"""
        if self.ui_manager.button_continue_success.is_clicked(pos):
            self.current_state = GameState.MENU
    
    def handle_username_key(self, event):
        """Handle keyboard input in username screen"""
        if event.key == pygame.K_BACKSPACE:
            self.username = self.username[:-1]
        elif event.key == pygame.K_RETURN:
            if self.username.strip():
                self.show_error = False
                # Save username before starting game
                self.save_username()
                # Initialize the database
                self.init_leaderboard_db()
                # Start the game
                self.start_new_game()
            else:
                self.show_error = True
        else:
            self.username += event.unicode
    
    def handle_running_key(self, event, pressed):
        """Handle keyboard input during gameplay"""
        if event.key in self.player.key_states:
            self.player.key_states[event.key] = pressed
        elif event.key == pygame.K_ESCAPE and pressed:
            self.current_state = GameState.PAUSED
            if self.music_manager.enabled:
                self.music_manager.resume()
    
    def run(self):
        """Main game loop"""
        # Start menu music if enabled
        if self.music_manager.enabled:
            self.music_manager.play()
        
        while self.running:
            # Handle state-specific logic
            if self.current_state == GameState.MENU:
                if self.music_manager.enabled and not self.music_manager.playing:
                    self.music_manager.resume()
                self.ui_manager.draw_menu(self.ui_manager.buttons_main_menu, self.music_manager, show_title=True)
            elif self.current_state == GameState.USERNAME:
                self.ui_manager.draw_username_screen(self.username, self.show_error)
            elif self.current_state == GameState.PAUSED:
                if self.music_manager.enabled and not self.music_manager.playing:
                    self.music_manager.resume()
                self.ui_manager.draw_menu(self.ui_manager.buttons_pause_menu, self.music_manager)
            elif self.current_state == GameState.RUNNING:
                if self.player.handle_movement(self.maze_generator.maze, self.grid_size):
                    if self.player.is_at_exit(self.maze_generator.maze):
                        self.final_time = int(time.time() - self.start_time)
                        self.current_state = GameState.SUCCESS
                        if self.music_manager.enabled:
                            self.music_manager.resume()
                self.ui_manager.draw_game_screen(self.maze_generator, self.player, self.start_time)
            elif self.current_state == GameState.SUCCESS:
                self.ui_manager.draw_success_screen(self.final_time)
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_state == GameState.MENU:
                        self.handle_menu_click(event.pos)
                    elif self.current_state == GameState.USERNAME:
                        self.handle_username_click(event.pos)
                    elif self.current_state == GameState.PAUSED:
                        self.handle_pause_click(event.pos)
                    elif self.current_state == GameState.SUCCESS:
                        self.handle_success_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if self.current_state == GameState.USERNAME:
                        self.handle_username_key(event)
                    elif self.current_state == GameState.RUNNING:
                        self.handle_running_key(event, True)
                elif event.type == pygame.KEYUP:
                    if self.current_state == GameState.RUNNING:
                        self.handle_running_key(event, False)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()