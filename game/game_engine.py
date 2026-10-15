import random
import pygame
from game.block import Block

# --- Perfect-drop tuning ---
PERFECT_TOLERANCE = 3    
PERFECT_BONUS = 2  
PERFECT_STREAK_WIDEN = 3  
WIDEN_AMOUNT = 20  
POPUP_FRAMES = 45         


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)
        self.font_popup = pygame.font.SysFont(None, 40)

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.game_over = False
        self.perfect_streak = 0
        self.popups = []

        base_x = (self.width - self.base_width) // 2
        base_y = self.height - 60
        base_block = Block(base_x, base_y, self.base_width, self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - 4
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        start_x = 25 if random.choice([True, False]) else self.width - 25 - top_block.width
        self.active_block = Block(start_x, next_y, top_block.width, self.block_height, color, speed=speed)

    def add_popup(self, text, x, y, color=(255, 230, 90)):
        self.popups.append({"text": text, "x": x, "y": y, "life": POPUP_FRAMES, "color": color})

    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        is_successful_drop = overlap > 0

        if not is_successful_drop:
            self.game_over = True
            return

        # Perfect drop: aligned within tolerance -> snap to the block below
        is_perfect = abs(act.x - top_block.x) <= PERFECT_TOLERANCE

        if is_perfect:
            new_x = top_block.x
            new_width = top_block.width  # nothing gets trimmed
            self.perfect_streak += 1
            self.score += 1 + PERFECT_BONUS
            popup_text = "PERFECT!"

            if self.perfect_streak >= PERFECT_STREAK_WIDEN:
                widened = min(float(self.base_width), new_width + WIDEN_AMOUNT)
                gained = widened - new_width
                if gained > 0:
                    # grow evenly on both sides, keep inside the play area
                    new_x -= gained / 2
                    new_x = max(20.0, min(new_x, self.width - 20 - widened))
                    new_width = widened
                    popup_text = "PERFECT! WIDER!"
                self.perfect_streak = 0
        else:
            new_x = left
            new_width = max(10.0, overlap)
            self.perfect_streak = 0
            popup_text = None

        new_block = Block(new_x, act.y, new_width, self.block_height, act.color, speed=0)
        self.stack.append(new_block)
        if not is_perfect:
            self.score += 1

        if new_block.y < 180:
            shift_amount = self.block_height + 4
            for b in self.stack:
                b.y += shift_amount

        if popup_text:
            self.add_popup(popup_text, new_block.x + new_block.width / 2, new_block.y - 10)

        self.spawn_active_block()

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_r) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)

        for p in self.popups:
            p["life"] -= 1
            p["y"] -= 0.8
        self.popups = [p for p in self.popups if p["life"] > 0]

    def render(self, screen):
        screen.fill((24, 27, 36))

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 54))

        for b in self.stack:
            b.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

        for p in self.popups:
            surf = self.font_popup.render(p["text"], True, p["color"])
            surf.set_alpha(int(255 * p["life"] / POPUP_FRAMES))
            screen.blit(surf, (p["x"] - surf.get_width() / 2, p["y"] - surf.get_height()))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_surf = self.font_hud.render(f"Final Score: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_hud.render("Press [R] or Click to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))
