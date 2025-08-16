import pygame
import random
import pyaudio
import numpy as np

# -------------------------
# --- Pygame Initialization
# -------------------------
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Happy Birthday :>")
clock = pygame.time.Clock()

# --- Font and Colors ---
FONT = pygame.font.Font(None, 30)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (255, 105, 180)        # Normal button color
DARK_PINK = (219, 0, 144)    # Hover color

card_anim_progress = 0.0    # 0 → card closed, 1 → fully opened
CARD_ANIM_SPEED = 0.05      # Adjust for faster/slower animation

# -------------------------
# --- Load Assets
# -------------------------
try:
    cake_img = pygame.image.load("cake.png").convert_alpha()
    candle_img = pygame.image.load("candle.png").convert_alpha()
    flame_sprites = [pygame.image.load(f"flame_{i}.png").convert_alpha() for i in range(4)]
    flame_out_sprites = [pygame.image.load(f"flame_out_{i}.png").convert_alpha() for i in range(2)]
    background_img = pygame.image.load("background.png").convert()
except pygame.error as e:
    print(f"Error loading images: {e}")
    pygame.quit()
    exit()

# Scale images
cake_img = pygame.transform.scale(cake_img, (400, 350))
candle_img = pygame.transform.scale(candle_img, (30, 80))
flame_sprites = [pygame.transform.scale(img, (30, 40)) for img in flame_sprites]
flame_out_sprites = [pygame.transform.scale(img, (40, 50)) for img in flame_out_sprites]
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# -------------------------
# --- PyAudio Setup
# -------------------------
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
MIC_THRESHOLD = 50     # Minimum mic RMS to detect a blow
BLOW_DURATION = 0.5    # How long to blow before candles go out

p = pyaudio.PyAudio()
try:
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
except Exception as e:
    print(f"Mic error: {e}")
    stream = None

# -------------------------
# --- Candle Class
# -------------------------
class Candle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.flame_frame = 0
        self.blow_flame_frame = 0
        self.is_lit = True
        self.is_blowing_out = False
        self.animation_timer = 0
        self.blow_animation_timer = 0

    def start_blowing_out(self):
        """Trigger blow-out animation."""
        if self.is_lit and not self.is_blowing_out:
            self.is_blowing_out = True
            self.blow_flame_frame = 0
            self.blow_animation_timer = 0

    def update(self):
        if self.is_lit:
            if not self.is_blowing_out:
                # Flickering flame animation
                self.animation_timer += 1
                if self.animation_timer > 5:
                    self.flame_frame = (self.flame_frame + 1) % len(flame_sprites)
                    self.animation_timer = 0
            else:
                # Blow-out animation
                self.blow_animation_timer += 1
                if self.blow_animation_timer > 5:
                    if self.blow_flame_frame < len(flame_out_sprites) - 1:
                        self.blow_flame_frame += 1
                    else:
                        # Animation finished → turn candle off
                        self.is_lit = False
                        self.is_blowing_out = False
                    self.blow_animation_timer = 0

    def draw(self, surface):
        surface.blit(candle_img, (self.x, self.y))
        if self.is_lit:
            if not self.is_blowing_out:
                surface.blit(flame_sprites[self.flame_frame], (self.x, self.y - 30))
            else:
                surface.blit(flame_out_sprites[self.blow_flame_frame], (self.x - 5, self.y - 40))

# -------------------------
# --- Button Class
# -------------------------
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        text_surf = FONT.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.action:
                self.action()

# -------------------------
# --- Game Variables
# -------------------------
age = 0
candles = []
game_state = "input_age"  # States: input_age → awaiting_blow → blown_out

CAKE_X = 170
CAKE_Y = 270
CAKE_WIDTH = 350

# -------------------------
# --- Functions
# -------------------------
def add_candle():
    global age
    age += 1
    candle_x = random.randint(CAKE_X + 20, CAKE_X + CAKE_WIDTH - 50)
    candle_y = CAKE_Y + 40
    candles.append(Candle(candle_x, candle_y))

def remove_candle():
    global age
    if age > 0:
        age -= 1
        if candles:
            candles.pop()

def confirm_age():
    global game_state
    game_state = "awaiting_blow"
    for c in candles:
        c.is_lit = True
        c.is_blowing_out = False
        c.blow_flame_frame = 0

# --- Buttons ---
up_button = Button(650, 100, 100, 50, "+", PINK, DARK_PINK, add_candle)
down_button = Button(650, 170, 100, 50, "-", PINK, DARK_PINK, remove_candle)
confirm_button = Button(650, 240, 100, 50, "Confirm", PINK, DARK_PINK, confirm_age)


# -------------------------
# --- Main Loop
# -------------------------
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_state == "input_age":
            up_button.handle_event(event)
            down_button.handle_event(event)
            confirm_button.handle_event(event)

    # --- Mic Blow Detection ---
    if game_state == "awaiting_blow" and stream:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            numpy_data = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.maximum(0, np.mean(np.square(numpy_data))))
            if rms > MIC_THRESHOLD:
                proportion = min(1, (rms - MIC_THRESHOLD) / 30) #lower from 35 to increase mic sensitivity or higher from 35 to decrease mic sensitivity 
                candles_to_out = int(proportion * len([c for c in candles if c.is_lit]))
                lit_candles = [c for c in candles if c.is_lit]
                for i in range(candles_to_out):
                    lit_candles[i].start_blowing_out()
        except IOError as e:
            print(f"Mic error: {e}")

        # End game when all candles are out
        if all(not c.is_lit for c in candles):
            game_state = "blown_out"

    # --- Update ---
    for c in candles:
        c.update()

    # --- Draw ---
    if background_img:
        #screen.blit(background_img, (0, 0))
        screen.blit(background_img, (0, 0))
        # Draw black overlay with transparency
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)   # Adjust opacity
        overlay.fill((255, 255, 255))  # White overlay = fade, black = darken
        screen.blit(overlay, (0, 0))
        
    else:
        screen.fill(WHITE)

    screen.blit(cake_img, (CAKE_X - 20, CAKE_Y - 20))
    for c in candles:
        c.draw(screen)

    # Title + Age
    title_text = FONT.render("Happy Birthday!", True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
    screen.blit(title_text, title_rect)

    age_text = FONT.render(f"Your Age: {age}", True, BLACK)
    age_rect = age_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
    screen.blit(age_text, age_rect)

    if game_state == "input_age":
        up_button.draw(screen)
        down_button.draw(screen)
        confirm_button.draw(screen)
    elif game_state == "awaiting_blow":
        message = FONT.render("Blow on the mic to blow out the candles!", True, BLACK)
        message_rect = message.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(message, message_rect)
    elif game_state == "blown_out":
        # Animate card opening
        card_anim_progress = min(1.0, card_anim_progress + CARD_ANIM_SPEED)
        
        # Card dimensions
        FULL_CARD_WIDTH, CARD_HEIGHT = 500, 300
        CARD_X = (SCREEN_WIDTH - FULL_CARD_WIDTH) // 2
        CARD_Y = (SCREEN_HEIGHT - CARD_HEIGHT) // 2
        LIGHT_BROWN = (205, 133, 63)
        DARK_BROWN = (160, 82, 45)
        WHITE = (255, 255, 255)
        PADDING = 20

        # Current animated width (simulate half-fold)
        current_width = int(FULL_CARD_WIDTH * card_anim_progress)
        current_x = CARD_X + (FULL_CARD_WIDTH - current_width) // 2  # Keep centered

        # Draw card
        pygame.draw.rect(screen, LIGHT_BROWN, (current_x, CARD_Y, current_width, CARD_HEIGHT), border_radius=20)

        # Add texture only if card has some width
        if current_width > 2 * PADDING:
            for i in range(0, CARD_HEIGHT, 10):
                start_pos = (current_x + PADDING, CARD_Y + i)
                end_pos = (current_x + current_width - PADDING, CARD_Y + i)
                pygame.draw.line(screen, DARK_BROWN, start_pos, end_pos, 1)

        # Display text only when card is fully opened
        if card_anim_progress >= 1.0:
            wish_text = [
                " Happy Birthday! <3",
                f"Congratulations on turning {age}!",
                "May your day be filled with joy and cake!", # Add more lines with "" and seperate each line with a comma (,)
            ]
            for idx, line in enumerate(wish_text):
                text_surf = FONT.render(line, True, WHITE)
                text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, CARD_Y + 50 + idx * 40))
                screen.blit(text_surf, text_rect)

    pygame.display.flip()
    clock.tick(60)

# --- Cleanup ---
if stream:
    stream.stop_stream()
    stream.close()
p.terminate()
pygame.quit()
