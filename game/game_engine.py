import random
import pygame
from game.block import Block
from game.debris import Debris

PERFECT_MARGIN = 3        # px error that still counts as perfect
PERFECT_BONUS = 2         # extra points on top of the normal +1
STREAK_FOR_GROWTH = 3     # perfects in a row needed to widen the block
GROWTH_AMOUNT = 10        # px added when the streak is reached


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
        self.debris = []

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

    def add_popup(self, text, x, y, color=(255, 215, 0)):
        self.popups.append({"text": text, "x": x, "y": y, "life": 50, "max_life": 50, "color": color})

    def spawn_debris(self, x, y, width, color, vx):
        if width <= 0.5:
            return
        self.debris.append(Debris(x, y, width, self.block_height, color,
                                  vx=vx, vy=random.uniform(-2.0, 0.0)))

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
            # missed completely: the whole block tumbles away
            self.spawn_debris(act.x, act.y, act.width, act.color, vx=act.direction * 2.0)
            self.game_over = True
            return

        is_perfect = abs(act.x - top_block.x) <= PERFECT_MARGIN
        popup_x = self.width // 2
        popup_y = act.y - 10

        if is_perfect:
            # snap into alignment, no trimming, bonus points
            new_x = top_block.x
            new_w = top_block.width
            self.perfect_streak += 1
            self.score += 1 + PERFECT_BONUS
            self.add_popup("PERFECT!", popup_x, popup_y)

            if self.perfect_streak >= STREAK_FOR_GROWTH:
                grown_w = min(float(self.base_width), new_w + GROWTH_AMOUNT)
                if grown_w > new_w:
                    new_x -= (grown_w - new_w) / 2
                    new_w = grown_w
                    new_x = max(20.0, min(new_x, self.width - 20 - new_w))
                    self.add_popup("WIDTH UP!", popup_x, popup_y - 34, color=(120, 255, 160))
                self.perfect_streak = 0
        else:
            # normal drop: trim to the overlap and shed the overhang as debris
            new_x = left
            new_w = max(10.0, overlap)
            self.perfect_streak = 0
            self.score += 1

            if act.x < left:
                self.spawn_debris(act.x, act.y, left - act.x, act.color, vx=-random.uniform(1.0, 2.5))
            if act.x + act.width > right:
                self.spawn_debris(right, act.y, (act.x + act.width) - right, act.color,
                                  vx=random.uniform(1.0, 2.5))

        new_block = Block(new_x, act.y, new_w, self.block_height, act.color, speed=0)
        self.stack.append(new_block)

        if new_block.y < 180:
            shift_amount = self.block_height + 4
            for b in self.stack:
                b.y += shift_amount
            for d in self.debris:
                d.y += shift_amount
            for p in self.popups:
                p["y"] += shift_amount

        self.spawn_active_block()

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and event.key in (pygame.K_r, pygame.K_SPACE)) or \
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

        # debris and popups keep animating even after game over
        for d in self.debris:
            d.update()
        self.debris = [d for d in self.debris if not d.is_offscreen(self.height)]

        for p in self.popups:
            p["y"] -= 0.8
            p["life"] -= 1
        self.popups = [p for p in self.popups if p["life"] > 0]

    def render(self, screen):
        screen.fill((24, 27, 36))

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(f"Height: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 54))

        streak_surf = self.font_hud.render(
            f"Perfect streak: {self.perfect_streak}/{STREAK_FOR_GROWTH}", True, (200, 200, 210))
        screen.blit(streak_surf, (12, self.height - 28))

        for b in self.stack:
            b.render(screen)

        for d in self.debris:
            d.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

        for p in self.popups:
            surf = self.font_popup.render(p["text"], True, p["color"])
            surf.set_alpha(int(255 * p["life"] / p["max_life"]))
            screen.blit(surf, (p["x"] - surf.get_width() // 2, int(p["y"])))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_surf = self.font_hud.render(f"Final Height: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_hud.render("Press [Space] or [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))
