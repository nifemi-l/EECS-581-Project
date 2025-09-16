import curses
from curses.textpad import Textbox, rectangle
import platform
from src.classes import GameManager, Cell, CellState, GameStatus

ROWS, COLS = 10, 10
CELL_W, CELL_H = 3, 1   # 3 chars per cell, 1 row high

class Frontend():
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.game_manager = GameManager()
        self.cur_r = 0
        self.cur_c = 0
        self.clicked_cells = []
        self.alphabet = "abcdefghijklmnopqrstuvwxyz"

    def set_num_mines(self):
        self.stdscr.addstr(0, 0, "Enter the number of mines for this game: (CTRL-G to send)")

        editwin = curses.newwin(5,30, 2,1)
        rectangle(self.stdscr, 1,0, 1+5+1, 1+30+1)
        self.stdscr.refresh()

        box = Textbox(editwin)

        # Let the user edit until Ctrl-G is struck.
        box.edit()

        # Get resulting contents
        num_mines = box.gather()
        num_mines = int(num_mines.strip())
        self.game_manager.set_total_mines(num_mines)

    def center_offsets(self, scr_h, scr_w, rows, cols, cw, ch):
        board_w = cols * cw
        board_h = rows * ch
        off_y = max((scr_h - board_h) // 2, 0)
        off_x = max((scr_w - board_w) // 2, 0)
        return off_y, off_x

    def correct_terminal_size(self, scr_h, sch_w, required_h = (ROWS + 1) * CELL_H + 3, required_w = (COLS + 1) * CELL_W):
        if scr_h < required_h or sch_w < required_w: 
            return False
        return True

    def display_size_warning(self):
        warning = "Terminal too small! Please resize window."
        self.stdscr.addstr(0, 0, warning)
        self.stdscr.refresh()

    def find_start_key(self):
        os_name = platform.system()
        if os_name == "Darwin":
            return "Return"
        
        return "Enter"

    def draw_start_screen(self): 
        self.stdscr.erase()
        sh, sw = self.stdscr.getmaxyx()
        start_key = self.find_start_key()

        while not self.correct_terminal_size(sh, sw):
            self.display_size_warning()
            sh, sw = self.stdscr.getmaxyx()
            self.correct_terminal_size(sh, sw)

        off_y, _ = self.center_offsets(sh, sw, ROWS, COLS, CELL_W, CELL_H)

        title = "MINESWEEPER"
        prompt = f"Press {start_key} to start with {self.game_manager.total_mines} mines"
        controls = "Arrows=move  Space=Reveal  f=Flag  Mouse: Left=Reveal Right=Flag  q=Quit"

        # Calculate starting locations on x-axis (padding)
        title_scr_x = max((sw - len(title)) // 2, 0)
        prompt_scr_x = max((sw - len(prompt)) // 2, 0)
        controls_scr_x = max((sw - len(controls)) // 2, 0)

        # Display centered text
        self.stdscr.addstr(off_y, title_scr_x, title)
        self.stdscr.addstr(off_y + 2, prompt_scr_x, prompt)
        self.stdscr.addstr(off_y + 4, controls_scr_x, controls)
        self.stdscr.refresh()

    def start_game(self):
        self.draw_start_screen()

        sh, sw = self.stdscr.getmaxyx()
        off_y, _ = self.center_offsets(sh, sw, ROWS, COLS, CELL_W, CELL_H)

        mode = "menu"
        while True: 
            success = self.process_input(self.get_input())
            if self.game_manager.should_quit or not success:
                break
            else:
                self.draw_board()

    def draw_board(self):
        """Draw the game board on the screen"""
        
        self.stdscr.erase()
        sh, sw = self.stdscr.getmaxyx()

        # Print clicked cells at the top
        clicks_str = "Clicked: " + ", ".join([f"({self.alphabet[r]},{c+1})" for r, c in self.clicked_cells])
        self.stdscr.addstr(0, 0, clicks_str[:sw-1])  # top row

        if not self.correct_terminal_size(sh, sw):
            self.display_size_warning()
            return

        off_y, off_x = self.center_offsets(sh, sw, ROWS, COLS, CELL_W, CELL_H)

        # Draw column numbers
        for c in range(COLS):
            x = off_x + c * CELL_W
            self.stdscr.addstr(off_y - 1, x + 1, f"{c+1}")

        # Draw row letters
        for r in range(ROWS):
            y = off_y + r * CELL_H
            self.stdscr.addstr(y, off_x - 2, f"{self.alphabet[r]}")

        for r in range(ROWS):
            for c in range(COLS):
                # Get cell and render output depending on cell status
                cell = self.game_manager.grid[r % ROWS][c % COLS]

                # Calculate screen coordinates for this cell
                y = off_y + r * CELL_H
                x = off_x + c * CELL_W

                if cell.flagged:
                    ch = "⚑"
                if cell.hidden and not cell.flagged:
                    ch = "H"
                elif cell.state == CellState.MINED:
                    ch = "M" 
                elif cell.state == CellState.HASADJACENT:
                    ch = str(cell.adjacent)
                elif cell.state == CellState.MINE:
                    ch = "X"
                elif cell.state == CellState.NONEADJACENT:
                    ch = " "
                elif cell.state is None and not cell.flagged:
                    ch = " "

                # highlight cursor
                if (self.cur_r, self.cur_c) == (r, c):
                    self.stdscr.attron(curses.A_REVERSE)
                    self.stdscr.addstr(y, x, f"[{ch}]")
                    self.stdscr.attroff(curses.A_REVERSE)
                else:
                    self.stdscr.addstr(y, x, f"[{ch}]")

        # Simple help bar
        self.stdscr.addstr(sh-1, 0,
            f"Remaining Mines: {self.game_manager.remaining_mine_count}"
        )
        self.stdscr.addstr(sh-2, 0,
            f"Game State: {self.game_manager.game_status}"
        )
        self.stdscr.addstr(sh-3, 0,
            "Arrows=move  Space=Reveal  f=Flag  Mouse: Left=Reveal Right=Flag  q=Quit  ",
        )
        self.stdscr.clrtoeol()
        self.stdscr.refresh()

    def mouse_to_cell(self, mx, my):
        """Processes user clicks on cells"""
        sh, sw = self.stdscr.getmaxyx()
        off_y, off_x = self.center_offsets(sh, sw, ROWS, COLS, CELL_W, CELL_H)
        # inside board?
        if my < off_y or mx < off_x:
            return None
        if my >= off_y + ROWS * CELL_H or mx >= off_x + COLS * CELL_W:
            return None
        r = (my - off_y) // CELL_H
        c = (mx - off_x) // CELL_W
        if 0 <= r < ROWS and 0 <= c < COLS:
            return (r, c)
        return None

    def handle_left_click(self, r, c):
        self.game_manager.hide_cell(r, c)

    def handle_right_click(self, r, c):
        if self.game_manager.is_flagged(r, c):
            self.game_manager.remove_flag(r, c)
        else:
            self.game_manager.place_flag(r, c)

    def get_input(self):
        return self.stdscr.getch()
    
    def process_input(self, ch):
        if ch == ord('q'):
            self.game_manager.should_quit = True
            return False

        if ch == curses.KEY_RESIZE:
            self.draw_board(self.stdscr)
            return True

        if ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
            except curses.error:
                return True
            
            if self.game_manager.game_status == GameStatus.PLAYING:
                pos = self.mouse_to_cell(mx, my)

                if not pos:
                    return True
                
                r, c = pos
                self.cur_r, self.cur_c = r, c

                # Left-click (terminals vary: check CLICKED/PRESSED)
                if bstate & curses.BUTTON1_CLICKED or bstate & curses.BUTTON1_PRESSED:
                    self.handle_left_click(r, c)
                    self.clicked_cells.append((r, c))  # add clicked cell

                # Right-click
                elif bstate & curses.BUTTON3_CLICKED or bstate & curses.BUTTON3_PRESSED:
                    self.handle_right_click(r, c)

                # Redraw on valid board interaction
                self.draw_board()

            return True

        # Keyboard navigation
        if ch in (curses.KEY_UP, ord('k')):   self.cur_r = (self.cur_r - 1) % ROWS
        elif ch in (curses.KEY_DOWN, ord('j')): self.cur_r = (self.cur_r + 1) % ROWS
        elif ch in (curses.KEY_LEFT, ord('h')): self.cur_c = (self.cur_c - 1) % COLS
        elif ch in (curses.KEY_RIGHT, ord('l')): self.cur_c = (self.cur_c + 1) % COLS
        elif ch in (ord(' '), ord('\n')):     self.handle_left_click(self.cur_r, self.cur_c)
        elif ch in (ord('f'), ord('F')):      self.handle_left_click(self.cur_r, self.cur_c)
        return True

