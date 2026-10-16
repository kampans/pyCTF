# I created this game in 2024; and a part of a python DCU Project
# for CTYI EUE (Early Univeristy Entry)
# I tried to get it to play in the browser; just see the other files in the directory; 
# I couldn't get it to work so if you can LMK! Might make more updates or something related to the game though...

import os
import random
import math
from os import listdir
from os.path import isfile, join
import sys
import pygame
from pygame.locals import *
from pygame import mixer
import asyncio
# ONBOARDING SCREEN
def display_keybinds():
    keybinds_text = [
        "Keybinds:",
        "",
        "Player 1:",
        "  Movement: W, A, S ,D",
        "  Jump: W",
        "  Dash Left: Q",
        "  Dash Right: E",
        "",
        "Player 2:",
        "  Movement: I, J, K, L",
        "  Jump: I",
        "  Dash Left: U",
        "  Dash Right: O",
        "",
        "Press any key to continue...",
        "",
        "Thanks for playing, music by me and John Brennan.",
        "Game coded by Nicolas Campan and Matthew Duff",
        "Want to switch teams? Teams are randomly chosen so good luck!",
    ]
    
    onboarding_font = pygame.font.Font(None, 36)
    text_surfaces = [onboarding_font.render(line, True, (0, 0, 0)) for line in keybinds_text]
    max_width = max(surface.get_width() for surface in text_surfaces)
    total_height = sum(surface.get_height() for surface in text_surfaces)
    
    background_surface = pygame.Surface((max_width + 40, total_height + 40))
    background_surface.fill((255, 255, 255))
    screen.fill((25, 51, 7, 1))
    
    y_offset = 20
    for surface in text_surfaces:
        background_surface.blit(surface, (20, y_offset))
        y_offset += surface.get_height()
        
    background_rect = background_surface.get_rect(center=screen.get_rect().center)
    screen.blit(background_surface, background_rect)
    pygame.display.flip()
    waiting = True
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
            elif event.type == pygame.QUIT:
                waiting = False
                
pygame.init()

# GAME VALUES
WIDTH, HEIGHT = 1600, 900
ACC = 0.9
FRICT = -0.12

dt = 0
match_counter = 0
vec = pygame.math.Vector2

player1_score = 0
player2_score = 0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Capture the flag")
bg_img = pygame.image.load(r'elements\Untitled.png').convert()
clock = pygame.time.Clock()
running = True

# Chooses who goes first
def game_chooser():
    return random.choice([1, 2])

result = game_chooser()

# Fonts & Music
font = pygame.font.Font("freesansbold.ttf", 25)
player_header = pygame.font.Font("freesansbold.ttf", 15)
score_text = pygame.font.Font("freesansbold.ttf", 40)

mixer.music.load(r'elements\gamemusic.ogg')
mixer.music.play(20)
mixer.music.set_volume(0.2)
s = "sound"
jump = pygame.mixer.Sound(os.path.join(r'elements\jump.ogg'))
woosh = pygame.mixer.Sound(os.path.join(r'elements\woosh.ogg'))

class MakePlayers(pygame.sprite.Sprite):

    def __init__(self, group1, group2, size_x, size_y, color, pos_x, pos_y):
        super().__init__()
        self.surf = pygame.Surface((size_x, size_y))
        self.surf.fill(color)
        self.rect = self.surf.get_rect()
        self.pos = vec((pos_x, pos_y))
        start_pos = self.pos
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.jumping = False
        self.wooshing = False
        group1.add(self)
        group2.add(self)
        print(start_pos)

    def move(self, x, y, z, v, c, b):
        self.acc = vec(0, 0.5)
        keys = pygame.key.get_pressed()
        if keys[x]:
            self.acc.x = -ACC
        if keys[y]:
            self.acc.x = ACC
        if keys[z]:
            self.jump()
        if keys[v]:
            self.fall()
        if keys[c]:
            self.dash_right()
        if keys[b]:
            self.dash_left()

        self.acc.x += self.vel.x * FRICT
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        if self.pos.x >= (WIDTH - 20):
            self.pos.x = 1570
        if self.pos.x <= 20:
            self.pos.x += 15

        self.rect.midbottom = self.pos

    def jump(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits and not self.jumping:
            self.vel.y = -17.5
            self.jumping = True
            pygame.mixer.Sound.play(jump)

    def fall(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits:
            self.vel.y = 10.5
            self.pos.y = hits[0].rect.top + 44

    def dash_left(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if not hits and not self.wooshing:
            self.vel.x = 50
            self.wooshing = True
            pygame.mixer.Sound.play(woosh)

    def dash_right(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if not hits and not self.wooshing:
            self.vel.x = -50
            self.wooshing = True
            pygame.mixer.Sound.play(woosh)

    def drawChar(self, DrawWithDisplay):
        if DrawWithDisplay:
            DisplayNameText = player_header.render(str("Player"), 1, "white")
            text_rect = DisplayNameText.get_rect(midbottom=self.rect.midtop)
            screen.blit(DisplayNameText, text_rect)

    def update(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if self.vel.y > 0:
            if hits:
                self.vel.y = 0
                self.pos.y = hits[0].rect.top + 1
                self.jumping = False
                self.wooshing = False

class MakePlatforms(pygame.sprite.Sprite):
    def __init__(self, group2, color, size_x, size_y, x, y):
        super().__init__()
        self.surf = pygame.Surface((size_x, size_y))
        self.surf.fill(color)
        self.rect = self.surf.get_rect(center=(x, y))
        screen.blit(self.surf, self.rect)
        group2.add(self)

class Void(pygame.sprite.Sprite):
    def __init__(self, group2, color, size_x, size_y, x, y):
        super().__init__()
        self.surf = pygame.Surface((size_x, size_y))
        self.surf.fill(color)
        self.rect = self.surf.get_rect(center=(x, y))
        screen.blit(self.surf, self.rect)
        group2.add(self)

class MakeFlags(pygame.sprite.Sprite):
    def __init__(self, group1, size_x, size_y, x, y, path):
        super().__init__()
        self.surf = pygame.Surface((size_x, size_y), pygame.SRCALPHA)
        self.image = pygame.image.load(path).convert_alpha()
        self.rect = self.image.get_rect()
        print("Image dimensions:", self.image.get_size())
        self.pos = vec((x, y))
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        group1.add(self)

    def move(self):
        self.acc = vec(0, 0.5)
        self.acc.x += self.vel.x * FRICT
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        self.rect.midbottom = self.pos

    def drawChar(self, DrawWithDisplay):
        if DrawWithDisplay:
            self.surf.blit(self.image, (0, 0))

    def update(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if self.vel.y > 0:
            if hits:
                self.pos.y = hits[0].rect.top + 1
                self.vel.y = 0

class MakeCollisionBox(pygame.sprite.Sprite):

    def __init__(self, size_x, size_y):
        super().__init__()
        self.rect = pygame.rect.Rect(0, 0, size_x, size_y)

    def draw_hitbox(self, gamePlayer, window, color, width, border_radius):
        self.rect.midbottom = gamePlayer.pos
        # pygame.draw.rect(window, color, self.rect, width, border_radius)

def doCollisions(sprite1, sprite2, ):
    collision = sprite1.colliderect(sprite2)
    return collision

middle_y_pos = 450.75

def returnPlayers():
    Player1.pos = vec((200, middle_y_pos))
    Player2.pos = vec((1400, middle_y_pos))

def unKill(group1, sprite):
    group1.add(sprite)

def GameRule(attacker, defender, attacker_hitbox, defender_hitbox, defender_flag_hitbox, attacker_score, defender_score, defender_flag, middle_y_pos):
    unKill(flags, defender_flag)
        
    # print("Middle Y position:", middle_y_pos) 
    
    if doCollisions(attacker_hitbox, defender_flag_hitbox):
        text1 = score_text.render("ATTACKER SCORE", True, "white", )
        screen.blit(text1, (WIDTH / 2 - 175, 60))
        pygame.display.flip()
        attacker_score += 10
        returnPlayers()
        pygame.time.wait(750)
             
    if doCollisions(attacker_hitbox, defender_hitbox):
        text2 = score_text.render("DEFENDER SCORE", True, "white", )
        screen.blit(text2, (WIDTH / 2 - 175, 60))
        pygame.display.flip()
        defender_score += 10
        returnPlayers()
        pygame.time.wait(500)

    return attacker_score, defender_score
        
def update_Scores():
    # score_text1 = font.render(f"{player1_score} | {player2_score}", True, ("green"))
    # screen.blit(score_text1, (10, 10))
    
    red_text = font.render(f"{player1_score}", True, ("red"))
    screen.blit(red_text, (10, 10))
    
    blue_text = font.render(f"{player2_score}", True, (77, 109, 242, 255))
    screen.blit(blue_text, (1565, 10))

all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()
void = pygame.sprite.Group()
middle_lower = MakePlatforms(platforms, "dark green", 700, 20, WIDTH / 2, HEIGHT / 1.5 + 50)
middle_higher = MakePlatforms(platforms, "dark green", 700, 20, WIDTH / 2, HEIGHT / 4)
PT4 = MakePlatforms(platforms, "dark green", 500, 20, 100, HEIGHT / 2)
PT5 = MakePlatforms(platforms, "dark green", 500, 20, 1500, HEIGHT / 2)
upper = MakePlatforms(platforms, "orange", 160, 20, 150, 112)
lower = MakePlatforms(platforms, "orange", 120, 20, 1440, 750)
void_death = Void(void, "dark green", WIDTH, 30, WIDTH / 2, HEIGHT)

players = pygame.sprite.Group()
Player1 = MakePlayers(all_sprites, players, 32, 32, "red", WIDTH - 1400, 450)
Player1_hitbox = MakeCollisionBox(45, 45)
Player2 = MakePlayers(all_sprites, players, 32, 32, (77, 109, 242, 255), 1400, 450)
Player2_hitbox = MakeCollisionBox(45, 45)

flags = pygame.sprite.Group()
Flag1 = MakeFlags(flags, 32, 32, WIDTH - 1550, 440, r"elements\redflag.png")
Flag1_hitbox = MakeCollisionBox(45, 45)
Flag2 = MakeFlags(flags, 32, 32, WIDTH - 50, 440, r"elements\blueflag.png")
Flag2_hitbox = MakeCollisionBox(45, 45)

Flag1.kill()
Flag2.kill()

display_keybinds()

async def main():
    global player1_score, player2_score, running

    while running:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit()
            elif keys[pygame.K_ESCAPE]:
                running = False
                sys.exit()

        screen.fill((25, 51, 7, 1))
        screen.blit(bg_img, (0, 0))

        Player1.update()
        Player1.move(K_a, K_d, K_w, K_s, K_q, K_e)
        Player1.drawChar(True)
        Player1_hitbox.draw_hitbox(Player1, screen, "green", 2, 3)

        Player2.update()
        Player2.move(K_j, K_l, K_i, K_k, K_u, K_o)
        Player2.drawChar(True)
        Player2_hitbox.draw_hitbox(Player2, screen, "red", 2, 3)

        Flag1.update()
        Flag1.move()
        Flag1.drawChar(True)
        Flag1_hitbox.draw_hitbox(Flag1, screen, "green", 2, 3)

        Flag2.update()
        Flag2.move()
        Flag2.drawChar(True)
        Flag2_hitbox.draw_hitbox(Flag2, screen, "red", 2, 3)

        if pygame.sprite.spritecollide(Player1, void, False):
            text3 = score_text.render("PLAYER 1 DEAD", True, "white", )
            screen.blit(text3, (WIDTH / 2 - 175, 60))
            pygame.display.flip()
            player2_score += 5
            returnPlayers()
            pygame.time.wait(500)

        if pygame.sprite.spritecollide(Player2, void, False):
            text4 = score_text.render("PLAYER 2 DEAD", True, "white")
            screen.blit(text4, (WIDTH / 2 - 175, 60))
            pygame.display.flip()
            player1_score += 5
            returnPlayers()
            pygame.time.wait(500)



        for entity in all_sprites:
            screen.blit(entity.surf, entity.rect)

        if result == 1:
            player1_score, player2_score = GameRule(Player1, Player2, Player1_hitbox.rect, Player2_hitbox.rect, Flag2_hitbox.rect, player1_score, player2_score, Flag2, middle_y_pos )

        if result == 2:
            player2_score, player1_score = GameRule(Player2, Player1, Player2_hitbox.rect, Player1_hitbox.rect, Flag1_hitbox.rect, player2_score, player1_score, Flag1, middle_y_pos)

        update_Scores()

        for entity in flags:
            screen.blit(entity.surf, entity.rect)

        # for entity in platforms:
        #     screen.blit(entity.surf, entity.rect)

        pygame.display.flip()
        dt = clock.tick(60) / 1000
        await asyncio.sleep(0)

asyncio.run(main())
quit()



