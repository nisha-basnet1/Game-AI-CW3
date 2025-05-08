import pygame 
import heapq   
import math    

# Initialize pygame
pygame.init()

#GAME CONSTANTS 
GRID_SIZE = 20       # Number of cells in the game grid (20x20)
CELL_SIZE = 25       # Size of each cell in pixels
SCREEN_WIDTH = GRID_SIZE * CELL_SIZE  # Total window width
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE # Total window height
FPS = 60             # Frames per second for game loop

# Movement directions
DIRECTIONS = {
    'UP': (0, 1),    
    'DOWN': (0, -1), 
    'LEFT': (1, 0), 
    'RIGHT': (-1, 0) 
}

#COLOR DEFINITIONS 
WHITE = (255, 255, 255)   # Background/walls 
BLACK = (0, 0, 0)         # Pellets 
RED = (255, 0, 0)         # Walls 
PURPLE = (128, 0, 128)    # Ghost color 
GREEN = (0, 255, 0)       # Player 1 default color 
GOLDEN = (255, 215, 0)    # Player color option 
ORANGE = (255, 165, 0)    # Player color option 
AVAILABLE_COLORS = [GREEN, GOLDEN, ORANGE] # Player color choices

# PRIORITY QUEUE FOR A* PATHFINDING 
class PriorityQueue:
    def __init__(self):
        self.elements = []  # Stores elements with priorities

    def empty(self):
        return len(self.elements) == 0  # Check if queue is empty

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))  # Add item with priority

    def get(self):
        return heapq.heappop(self.elements)[1]  # Get item with lowest priority

# PLAYER CLASS (MULTIPLAYER) 
class Player:
    def __init__(self, id, x, y, color, name):
        self.id = id          
        self.position = (x, y) 
        self.color = color     # Player color (chosen in menu)
        self.name = name       # "Player 1" or "Player 2"
        self.direction = DIRECTIONS['RIGHT']  # Initial movement direction
        self.score = 0       
        self.speed = 0.5       
        self.radius = CELL_SIZE // 2  # Visual size

    def move(self, grid):
        """Move player based on current direction if move is valid"""
        new_x = self.position[0] + self.direction[0] * self.speed
        new_y = self.position[1] + self.direction[1] * self.speed
        if self.is_valid_move(new_x, new_y, grid):
            self.position = (new_x, new_y)
            self.collect_pellet(grid)  # Check if moved onto a pellet

    def is_valid_move(self, x, y, grid):
        """Check if position is within bounds and not a wall"""
        return (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE 
                and grid[int(y)][int(x)] != 1)

    def collect_pellet(self, grid):
        """Check current position for pellets and collect if present"""
        x, y = round(self.position[0]), round(self.position[1])
        if grid[y][x] == 2:  # 2 represents a pellet
            grid[y][x] = 0   # Remove pellet
            self.score += 10 # Increase score

    def change_direction(self, new_direction):
        """Change movement direction (called from keyboard input)"""
        self.direction = new_direction

    def draw(self, screen):
        """Render player as a colored circle"""
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.position[0] * CELL_SIZE + CELL_SIZE // 2),
             int(self.position[1] * CELL_SIZE + CELL_SIZE // 2)),
            self.radius
        )

# GHOST CLASS 
class Ghost:
    def __init__(self, x, y, color):
        self.position = (x, y)  # Starting position
        self.color = color      # Visual color
        self.speed = 0.1       # Movement speed (slower from 0.2)
        self.radius = CELL_SIZE // 2  # Visual size
        self.path = []          # Stores calculated path to player

    def set_path(self, path):
        """Set a new path for the ghost to follow"""
        self.path = path

    def move(self, grid):
        """Move ghost along the calculated path"""
        if self.path:
            next_pos = self.path[0]
            # Calculate direction to next path node
            dx = next_pos[0] - self.position[0]
            dy = next_pos[1] - self.position[1]
            # Update position
            self.position = (
                self.position[0] + self.speed * dx,
                self.position[1] + self.speed * dy
            )
            # If reached next node, remove it from path
            if abs(self.position[0] - next_pos[0]) < 0.1 and abs(self.position[1] - next_pos[1]) < 0.1:
                self.position = next_pos
                self.path.pop(0)

    def draw(self, screen):
        """Render ghost as a colored circle"""
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.position[0] * CELL_SIZE + CELL_SIZE // 2),
             int(self.position[1] * CELL_SIZE + CELL_SIZE // 2)),
            self.radius
        )

#PATHFINDING FUNCTIONS
def heuristic(a, b):
    """Manhattan distance heuristic for A* algorithm"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(start, goal, grid):
    """A* pathfinding algorithm to find path from start to goal"""
    start = (round(start[0]), round(start[1]))  # Snap to grid
    goal = (round(goal[0]), round(goal[1]))    # Snap to grid
    
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}  # Tracks path
    cost_so_far = {}  # Tracks movement cost
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()
        if current == goal:  # Reached target
            break
        
        # Explore all valid neighbors
        for next_pos in get_neighbors(current, grid):
            new_cost = cost_so_far[current] + 1
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + heuristic(goal, next_pos)
                frontier.put(next_pos, priority)
                came_from[next_pos] = current

    # Reconstruct path
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from.get(current)
        if current is None:  # No path found
            break
    path.reverse()
    return path

def get_neighbors(pos, grid):
    """Get valid adjacent cells (no walls/diagonals)"""
    x, y = map(int, pos)
    neighbors = []
    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # 4-directional
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and grid[ny][nx] != 1:
            neighbors.append((nx, ny))
    return neighbors

def sync_paths(players, ghosts, grid):
    """Update ghost paths to chase the closest player"""
    for ghost in ghosts:
        # Find nearest player using Manhattan distance
        closest_player = min(players, key=lambda player: heuristic(ghost.position, player.position))
        # Calculate new path
        path = a_star_search(ghost.position, closest_player.position, grid)
        ghost.set_path(path)

# GAME WORLD FUNCTIONS
def create_grid():
    """Create the game maze with walls and pellets"""
    grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Border walls
    for i in range(GRID_SIZE):
        grid[0][i] = grid[GRID_SIZE - 1][i] = 1  # Top and bottom
        grid[i][0] = grid[i][GRID_SIZE - 1] = 1  # Left and right
    
    # Inner walls
    for i in range(5, 15):
        grid[5][i] = grid[15][i] = 1  # Horizontal barriers
    
    # Add pellets to all empty spaces
    for i in range(1, GRID_SIZE - 1):
        for j in range(1, GRID_SIZE - 1):
            if grid[j][i] == 0:
                grid[j][i] = 2  # 2 represents a pellet
    return grid

def draw_grid(screen, grid):
    """Render the game grid with walls and pellets"""
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if grid[y][x] == 1:  # Wall
                pygame.draw.rect(screen, RED, rect)
            elif grid[y][x] == 2:  # Pellet
                pygame.draw.circle(
                    screen,
                    BLACK,
                    (int(x * CELL_SIZE + CELL_SIZE // 2),
                     int(y * CELL_SIZE + CELL_SIZE // 2)),
                    3
                )

def check_collision(players, ghosts):
    """Check if any ghost caught any player"""
    for player in players:
        for ghost in ghosts:
            if math.dist(player.position, ghost.position) < 0.5:  # Collision distance
                return player.name  # Return which player lost
    return None

# UI FUNCTIONS 
def draw_text(screen, text, position, color=BLACK, size=24):
    """Helper function to render text"""
    font = pygame.font.Font(None, size)
    label = font.render(text, True, color)
    screen.blit(label, position)

def color_selection_menu(screen, player_number):
    """Menu for players to choose their colors"""
    selected_color = 0
    while True:
        screen.fill(WHITE)
        draw_text(screen, f"Player {player_number}: Choose Your Color", 
                 (SCREEN_WIDTH // 6, SCREEN_HEIGHT // 4), BLACK, 36)
        
        # Display color options
        for idx, color in enumerate(AVAILABLE_COLORS):
            pygame.draw.circle(screen, color, 
                             (SCREEN_WIDTH // 4 + idx * 100, SCREEN_HEIGHT // 2), 20)
            if idx == selected_color:  # Highlight selected option
                pygame.draw.circle(screen, BLACK, 
                                 (SCREEN_WIDTH // 4 + idx * 100, SCREEN_HEIGHT // 2), 25, 2)
        
        draw_text(screen, "Use LEFT/RIGHT to select, ENTER to confirm", 
                 (SCREEN_WIDTH // 8, SCREEN_HEIGHT // 1.5), ORANGE, 24)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected_color = (selected_color - 1) % len(AVAILABLE_COLORS)
                elif event.key == pygame.K_RIGHT:
                    selected_color = (selected_color + 1) % len(AVAILABLE_COLORS)
                elif event.key == pygame.K_RETURN:
                    return AVAILABLE_COLORS[selected_color]

def start_menu(screen):
    """Initial game menu"""
    running = True
    while running:
        screen.fill(WHITE)
        draw_text(screen, "PAC-MAN Multiplayer with A*", 
                 (SCREEN_WIDTH // 6, SCREEN_HEIGHT // 3), BLACK, 36)
        draw_text(screen, "Press ENTER to Start", 
                 (SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2), ORANGE, 24)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                running = False

def game_over_menu(screen, loser):
    """End game screen showing who lost"""
    while True:
        screen.fill(WHITE)
        draw_text(screen, f"Game Over! {loser} loses!", 
                 (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 3), PURPLE, 36)
        draw_text(screen, "Press R to Retry or ESC to Exit", 
                 (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2), ORANGE, 24)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Restart game
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

# GAME LOOP
def main():
    """Main game initialization and loop"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PAC-MAN Multiplayer with A*")
    clock = pygame.time.Clock()

    while True:  # Outer loop for game restarts
        start_menu(screen)

        # MULTIPLAYER SETUP: Each player chooses their color
        player1_color = color_selection_menu(screen, 1)
        player2_color = color_selection_menu(screen, 2)

        grid = create_grid()

        # MULTIPLAYER: Create two player instances
        player1 = Player(1, 1, 1, player1_color, "Player 1")  # Top-left start
        player2 = Player(2, GRID_SIZE - 2, GRID_SIZE - 2, player2_color, "Player 2")  # Bottom-right start
        players = [player1, player2]  # Store both players

        # Create ghosts
        ghost1 = Ghost(GRID_SIZE // 2, GRID_SIZE // 2, PURPLE)
        ghost2 = Ghost(GRID_SIZE // 2 + 2, GRID_SIZE // 2, ORANGE)
        ghosts = [ghost1, ghost2]

        running = True
        while running:  # Main game loop
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                
                # MULTIPLAYER INPUT: Different controls for each player
                if event.type == pygame.KEYDOWN:
                    # Player 1 controls (WASD)
                    if event.key == pygame.K_w:
                        player1.change_direction(DIRECTIONS['UP'])
                    elif event.key == pygame.K_s:
                        player1.change_direction(DIRECTIONS['DOWN'])
                    elif event.key == pygame.K_a:
                        player1.change_direction(DIRECTIONS['LEFT'])
                    elif event.key == pygame.K_d:
                        player1.change_direction(DIRECTIONS['RIGHT'])
                    # Player 2 controls (Arrow keys)
                    elif event.key == pygame.K_UP:
                        player2.change_direction(DIRECTIONS['UP'])
                    elif event.key == pygame.K_DOWN:
                        player2.change_direction(DIRECTIONS['DOWN'])
                    elif event.key == pygame.K_LEFT:
                        player2.change_direction(DIRECTIONS['LEFT'])
                    elif event.key == pygame.K_RIGHT:
                        player2.change_direction(DIRECTIONS['RIGHT'])

            # MULTIPLAYER:
            for player in players:
                player.move(grid)
            
            # Ghost AI: Chase closest player
            sync_paths(players, ghosts, grid)
            for ghost in ghosts:
                ghost.move(grid)

            # MULTIPLAYER: Check if any player was caught
            loser = check_collision(players, ghosts)
            if loser:
                retry = game_over_menu(screen, loser)
                if retry:
                    break  # Restart game

            # Rendering
            screen.fill(WHITE)
            draw_grid(screen, grid)
            
            # MULTIPLAYER: Draw both players and their scores
            for player in players:
                player.draw(screen)
                draw_text(screen, f"{player.name}: {player.score}", 
                         (10, player.id * 30), BLACK)
            
            for ghost in ghosts:
                ghost.draw(screen)
            
            pygame.display.flip()
            clock.tick(FPS)

if __name__ == "__main__":
    main()