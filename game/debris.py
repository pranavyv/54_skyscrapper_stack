import random
import pygame


class Debris:
    """A sliced-off piece of a block that tumbles and falls off the screen."""

    GRAVITY = 0.5

    def __init__(self, x, y, width, height, color, vx=0.0, vy=0.0, ang_vel=None):
        self.x = float(x)
        self.y = float(y)
        self.width = max(1.0, float(width))
        self.height = float(height)
        self.color = color
        self.vx = vx
        self.vy = vy
        self.angle = 0.0
        if ang_vel is None:
            # spin in the same direction the piece is flying
            spin = random.uniform(3.0, 8.0)
            ang_vel = spin if vx >= 0 else -spin
        self.ang_vel = ang_vel

    def update(self):
        self.vy += self.GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.angle += self.ang_vel

    def is_offscreen(self, screen_height):
        return self.y > screen_height + 120

    def render(self, surface):
        piece = pygame.Surface((max(1, int(self.width)), max(1, int(self.height))), pygame.SRCALPHA)
        pygame.draw.rect(piece, self.color, piece.get_rect(), border_radius=4)
        pygame.draw.rect(piece, (245, 245, 250), piece.get_rect(), width=2, border_radius=4)

        rotated = pygame.transform.rotate(piece, -self.angle)
        center = (self.x + self.width / 2, self.y + self.height / 2)
        surface.blit(rotated, rotated.get_rect(center=center))
