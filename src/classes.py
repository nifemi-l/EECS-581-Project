from enum import Enum
import random

class CellState(Enum):
    NONEADJACENT = 0
    MINE = 1
    HASADJACENT = 2
    MINED = 3

class GameStatus(Enum):
    WELCOME = 0
    STARTING = 1
    PLAYING = 2
    LOSE = 3
    WIN = 4
    END = 5

# Think of this like the frontend manager. When the backend needs to change the state
# of the frontend, it will call these methods.
class Screen:
    def set_welcome(self):
        pass

    def set_start(self):
        pass

    def set_playing(self):
        pass

    def set_lose(self):
        pass

    def set_win(self):
        pass

    def set_end(self):
        pass

class Cell:
    def __init__(self):
        # value >= 0 --> number of mines in a 9x9 are around the cell
        # value = -1 --> uninitialized
        self.state : None | CellState = None
        self.adjacent : int = -1
        self.hidden : bool = True
        self.flagged : bool = False

    def is_valid(self):
        return True if self.adjacent >= 0 else False
    
    def has_mine(self):
        return self.state == CellState.MINED
    
    def is_hidden(self):
        return self.hidden
    
    def get_value(self):
        return self.adjacent
    
    def __str__(self):
        return "X" if self.hidden else "M" if self.state == CellState.MINED else str(self.adjacent)
    
    def __repr__(self):
        return str(self.adjacent)

class GameManager:
    def __init__(self, seed=None):
        """Constructor function for the GamerManager Class"""
        self.screen = Screen()
        self.should_quit = False

        # Save number of rows & cols
        self.rows = 10
        self.cols = 10

        # Save number of mines & mines left
        # Defaults to 10. We need to call set_total_mines to actually update it.
        self.total_mines = 10
        self.remaining_mine_count = self.total_mines

        # Generate grid
        self.grid = [[Cell() for i in range(self.cols)] for i in range(self.rows)]

        # Set game state to 'Starting'
        self.game_status = GameStatus.WELCOME
        
        # Generate Seed
        if seed is not None:
            self.seed = seed
        else:
            self.seed = random.randrange(1 << 30)

        self.generate_mines()

    def set_total_mines(self, total_mines):
        self.total_mines = total_mines
        self.remaining_mine_count = total_mines

    def hide_cell(self, r, c):
        self.grid[r][c].hidden = False
    
    def place_flag(self, r, c):
        self.grid[r][c].flagged = True
    
    def remove_flag(self, r, c):
        self.grid[r][c].flagged = False

    def is_flagged(self, r, c):
        return self.grid[r][c].flagged

    # Debug function to print our cell grid
    def print_grid(self):
        """Prints the grid"""
        for row in self.grid:
            out_row = ""
            for column in row:
                out_row += str(column)
            print(out_row)

    def change_state(self, status):
        match status:
            case GameStatus.WELCOME:
                self.game_status = GameStatus.WELCOME
                self.screen.set_welcome()
            case GameStatus.STARTING:
                self.game_status = GameStatus.STARTING
                self.screen.set_start()
            case GameStatus.PLAYING:
                self.game_status = GameStatus.PLAYING
                self.screen.set_playing()
            case GameStatus.LOSE:
                self.game_status = GameStatus.LOSE
                self.screen.set_lose()
            case GameStatus.WIN:
                self.game_status = GameStatus.WIN
                self.screen.set_win()
            case GameStatus.END:
                self.game_status = GameStatus.END
                self.screen.set_end()
            case _:
                pass
            
    def generate_mines(self):
        """Randomly places mines on the grid"""

        rows = len(self.grid)
        cols = len(self.grid[0])

        # Use a seeded RNG if a seed was provided, otherwise use system randomness
        seed_num = random.Random(self.seed)

        # Select unique mine positions across the grid
        mine_positions = seed_num.sample(range(rows * cols), self.total_mines)

        for pos in mine_positions:
            # Convert 1D position -> (row, col)
            row = pos // cols
            col = pos % cols

            # Place a mine
            self.grid[row][col].state = CellState.MINED

            # Update all neighbors to increase their adjacent count
            for adj_row in [-1, 0, 1]:
                for adj_col in [-1, 0, 1]:
                    # Skip the mine itself
                    if adj_row == 0 and adj_col == 0:
                        continue

                    temp_row = row + adj_row
                    temp_col = col + adj_col

                    # Only update if neighbor is inside grid bounds
                    if 0 <= temp_row < rows and 0 <= temp_col < cols:
                        self.grid[temp_row][temp_col].adjacent += 1
