import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (192, 192, 192)

# Initialize the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Screen Switching with Buttons")

# Define a Button class
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font = pygame.font.Font(None, 36)

    def draw(self):
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

# Create the menu and game screen functions
def menu_screen():
    buttons = [Button(300, 200, 200, 50, "Start Game", game_screen), Button(300, 300, 200, 50, "Quit", quit_game)]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for button in buttons:
                button.handle_event(event)

        screen.fill(BLACK)
        for button in buttons:
            button.draw()
        pygame.display.flip()

# ...

# Create the game screen function
def game_screen():
    back_to_menu_button = Button(300, 500, 200, 50, "Back to Menu", menu_screen)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                menu_screen()

            # Handle events for the back to menu button
            back_to_menu_button.handle_event(event)

        screen.fill(WHITE)
        # Draw game elements here

        # Draw the back to menu button
        back_to_menu_button.draw()

        pygame.display.flip()

# ...

def quit_game():
    pygame.quit()
    sys.exit()

# Start with the menu screen
if __name__ == '__main__':
    menu_screen()
