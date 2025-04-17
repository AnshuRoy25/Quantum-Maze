# game_launcher.py - A wrapper script that ensures clean closing of windows
import sys
import os
import subprocess
import time

def main():
    """Main launcher function that manages game windows"""
    print("Starting Quantum Maze...")
    
    # Run the main game
    try:
        # Start the game process
        if sys.platform == "win32":
            # Windows: Hide console
            game_process = subprocess.Popen(
                [sys.executable, "GAME.py"], 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # macOS/Linux: Run normally
            game_process = subprocess.Popen([sys.executable, "GAME.py"])
        
        # Wait for the game to finish
        game_process.wait()
        
    except Exception as e:
        print(f"Error running game: {e}")
    
    print("Game closed.")

if __name__ == "__main__":
    main()