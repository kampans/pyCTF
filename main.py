# I created this game in 2024; and a part of a python DCU Project
# for CTYI EUE (Early Univeristy Entry)
# I tried to get it to play in the browser; using pygbag 0.9.3, turns out https://pygame-web.github.io/cdn/0.9.3/browserfs.min.js was dead a long time ago... 
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
from collections import defaultdict
import pyctfnet as netmod

# ONLINE STATE: "local" (same keyboard), "host" (runs the game) or "guest" (sends inputs, draws)
net = netmod.Net()
mode = "local"
remote_keys = defaultdict(bool)  # the guest's held keys, shaped like pygame.key.get_pressed()

# ONBOARDING SCREEN

async def display_keybinds():
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
        await asyncio.sleep(0)
                
pygame.init()

# GAME VALUES
WIDTH, HEIGHT = 1600, 900
ACC = 0.9
FRICT = -0.12

dt = 0
match_counter = 0
freeze_until = 0 # replace pygame.time.wait()
vec = pygame.math.Vector2

player1_score = 0
player2_score = 0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Capture the flag")
bg_img = pygame.image.load(r'elements/Untitled.png').convert()
clock = pygame.time.Clock()

running = True

IN_BROWSER = sys.platform == "emscripten"

if IN_BROWSER:
    import js
    from pyodide.ffi import create_once_callable

async def next_frame():
    if IN_BROWSER:
        fut = asyncio.get_running_loop().create_future()
        js.requestAnimationFrame(create_once_callable(lambda t: fut.set_result(None)))
        await fut
    else:
        await asyncio.sleep(0)


# Chooses who goes first
def game_chooser():
    return random.choice([1, 2])

result = game_chooser()

# Fonts & Music
font = pygame.font.Font("freesansbold.ttf", 25)
player_header = pygame.font.Font("freesansbold.ttf", 15)
score_text = pygame.font.Font("freesansbold.ttf", 40)

mixer.music.load(r'elements/gamemusic.ogg')
mixer.music.play(20)
mixer.music.set_volume(0.2)
s = "sound"
jump = pygame.mixer.Sound(os.path.join(r'elements/jump.ogg'))
woosh = pygame.mixer.Sound(os.path.join(r'elements/woosh.ogg'))



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
        self.name = "Player"
        group1.add(self)
        group2.add(self)
        # print(start_pos)

    def move(self, x, y, z, v, c, b, pressed=None):
        self.acc = vec(0, 0.5)
        # pressed lets online play feed in the remote player's keys
        keys = pressed if pressed is not None else pygame.key.get_pressed()
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
            DisplayNameText = player_header.render(str(self.name), 1, "white")
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
        # print("Image dimensions:", self.image.get_size())
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
        attacker_score += 10
        returnPlayers()
        announce("ATTACKER SCORE", 750)

    if doCollisions(attacker_hitbox, defender_hitbox):
        defender_score += 10
        returnPlayers()
        announce("DEFENDER SCORE", 500)

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
Flag1 = MakeFlags(flags, 32, 32, WIDTH - 1550, 440, r"elements/redflag.png")
Flag1_hitbox = MakeCollisionBox(45, 45)
Flag2 = MakeFlags(flags, 32, 32, WIDTH - 50, 440, r"elements/blueflag.png")
Flag2_hitbox = MakeCollisionBox(45, 45)

Flag1.kill()
Flag2.kill()

# ONLINE PLAY: menu, lobby, host/guest helpers

_panel_font = None

def draw_panel(lines):
    """White text panel on the green background (same look as the keybinds screen)."""
    global _panel_font
    if _panel_font is None:
        _panel_font = pygame.font.Font(None, 36)
    surfs = [_panel_font.render(line, True, (0, 0, 0)) for line in lines]
    width = max(s.get_width() for s in surfs)
    height = sum(s.get_height() for s in surfs)
    panel = pygame.Surface((width + 40, height + 40))
    panel.fill((255, 255, 255))
    y = 20
    for s in surfs:
        panel.blit(s, (20, y))
        y += s.get_height()
    screen.fill((25, 51, 7))
    screen.blit(panel, panel.get_rect(center=screen.get_rect().center))
    pygame.display.flip()

async def menu_tick():
    if IN_BROWSER:
        await next_frame()
    else:
        await asyncio.sleep(0.016)

async def choose_mode():
    """Returns "local", "host", "join", or None if the window was closed."""
    msg = ""
    while True:
        lines = ["pyCTF - Capture the flag", "",
                 "1 - Local 2-player (same keyboard)",
                 "2 - Create an online lobby",
                 "3 - Join an online lobby with a code"]
        if msg:
            lines += ["", msg]
        draw_panel(lines)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key in (K_1, K_KP1):
                    return "local"
                if event.key in (K_2, K_KP2, K_3, K_KP3):
                    if net.available:
                        return "host" if event.key in (K_2, K_KP2) else "join"
                    msg = "Online play only works in the browser version."
        await menu_tick()

async def wait_for_key():
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                return
        await menu_tick()

async def online_lobby(choice):
    """Host: show a code and wait. Join: type a code and connect. True when connected."""
    net.close()
    if choice == "host":
        net.host()
    else:
        code = ""
        submitted = False
        while not submitted:
            draw_panel(["Join a lobby", "",
                        "Type the code your friend gave you:", "",
                        "      " + (code or "_"), "",
                        "Enter - join      Esc - back"])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        return False
                    elif event.key == K_BACKSPACE:
                        code = code[:-1]
                    elif event.key in (K_RETURN, K_KP_ENTER):
                        if len(code) == netmod.CODE_LEN:
                            submitted = True
                    elif event.unicode and event.unicode.upper() in netmod.ALPHABET and len(code) < netmod.CODE_LEN:
                        code += event.unicode.upper()
            await menu_tick()
        net.join(code)

    # Waiting for the connection to come up
    while net.status != "connected":
        st = net.status
        if st == "error":
            draw_panel(["Could not connect", "", net.error, "", "Press any key to go back"])
            net.close()
            await wait_for_key()
            return False
        if choice == "host" and st == "waiting":
            draw_panel(["Your lobby code:", "", "      " + net.code, "",
                        "Give this code to your friend.",
                        "Waiting for them to join...", "", "Esc - cancel"])
        else:
            draw_panel(["Connecting...", "", "Esc - cancel"])
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                net.close()
                return False
        await menu_tick()

    # Connected: show controls for a moment so both sides start together
    end = pygame.time.get_ticks() + 3000
    while pygame.time.get_ticks() < end:
        secs = (end - pygame.time.get_ticks()) // 1000 + 1
        who = "red (Player 1)" if choice == "host" else "blue (Player 2)"
        draw_panel(["Connected! You are " + who, "",
                    "Move: A / D        Jump: W        Drop through platform: S",
                    "Dash left: Q        Dash right: E", "",
                    "Starting in " + str(secs) + "..."])
        pygame.event.pump()
        if net.status != "connected":
            return False
        await menu_tick()
    return True

async def connection_lost():
    draw_panel(["Connection lost", "", "Your friend left or the network dropped.",
                "Refresh the page to play again."])
    net.close()

def announce(text, ms):
    """Show a banner and freeze the round briefly. Tells the guest too when hosting."""
    global freeze_until
    surf = score_text.render(text, True, "white")
    screen.blit(surf, (WIDTH / 2 - 175, 60))
    pygame.display.flip()
    freeze_until = pygame.time.get_ticks() + ms
    if mode == "host":
        net.send({"t": "ev", "text": text, "ms": ms})

def send_state():
    """Host -> guest: everything the guest needs to draw one frame."""
    net.send({
        "t": "s",
        "p": [round(Player1.pos.x, 1), round(Player1.pos.y, 1),
              round(Player2.pos.x, 1), round(Player2.pos.y, 1)],
        "f": [round(Flag1.pos.x, 1), round(Flag1.pos.y, 1),
              round(Flag2.pos.x, 1), round(Flag2.pos.y, 1)],
        "sc": [player1_score, player2_score],
        "a": result,
    })

def handle_host_net():
    """Host: read the guest's held keys. Order matches Player2.move(J, L, I, K, U, O)."""
    for msg in net.poll():
        if msg.get("t") == "in":
            k = msg["k"]
            for key, down in zip((K_j, K_l, K_i, K_k, K_u, K_o), k):
                remote_keys[key] = bool(down)

async def run_guest():
    """Guest: send our keys to the host, draw whatever state it sends back."""
    global player1_score, player2_score, running
    Player1.name, Player2.name = "Friend", "You"
    state = None
    banner_text, banner_until = "", 0
    last_sent, last_sent_at = None, 0
    # Same order as the host expects: left, right, jump, fall, dash(Q), dash(E)
    my_keys = (K_a, K_d, K_w, K_s, K_q, K_e)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        for msg in net.poll():
            t = msg.get("t")
            if t == "s":
                state = msg
            elif t == "ev":
                banner_text = msg["text"]
                banner_until = pygame.time.get_ticks() + msg["ms"]

        if net.status != "connected":
            await connection_lost()
            return

        now = pygame.time.get_ticks()
        pressed = [1 if keys[k] else 0 for k in my_keys]
        if pressed != last_sent or now - last_sent_at > 100:
            net.send({"t": "in", "k": pressed})
            last_sent, last_sent_at = pressed, now

        screen.blit(bg_img, (0, 0))
        if state is not None:
            p, f = state["p"], state["f"]
            Player1.pos = vec(p[0], p[1])
            Player2.pos = vec(p[2], p[3])
            Flag1.pos = vec(f[0], f[1])
            Flag2.pos = vec(f[2], f[3])
            for sprite in (Player1, Player2, Flag1, Flag2):
                sprite.rect.midbottom = sprite.pos
                sprite.drawChar(True)
            flags.empty()
            flags.add(Flag2 if state["a"] == 1 else Flag1)
            player1_score, player2_score = state["sc"]

            for entity in all_sprites:
                screen.blit(entity.surf, entity.rect)
            update_Scores()
            for entity in flags:
                screen.blit(entity.surf, entity.rect)

        if now < banner_until:
            screen.blit(score_text.render(banner_text, True, "white"), (WIDTH / 2 - 175, 60))

        fps_surf = font.render(f"{clock.get_fps():.0f} fps", True, "white")
        screen.blit(fps_surf, (WIDTH // 2 - 30, 10))
        pygame.display.flip()
        clock.tick(60)
        await next_frame()

async def main():
    global player1_score, player2_score, running, freeze_until, mode

    # Menu: local keeps the original behaviour, online adds host/guest
    while True:
        choice = await choose_mode()
        if choice is None:
            return
        if choice == "local":
            mode = "local"
            await display_keybinds()
            break
        if await online_lobby(choice):
            mode = "host" if choice == "host" else "guest"
            break

    if mode == "guest":
        await run_guest()
        return
    if mode == "host":
        Player1.name, Player2.name = "You", "Friend"

    while running:

        if mode == "host":
            if net.status != "connected":
                await connection_lost()
                break
            handle_host_net()

        if pygame.time.get_ticks() < freeze_until:
            await asyncio.sleep(0.016)
            continue

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif keys[pygame.K_ESCAPE]:
                running = False

        screen.blit(bg_img, (0, 0))

        Player1.update()
        Player1.move(K_a, K_d, K_w, K_s, K_q, K_e)
        Player1.drawChar(True)
        Player1_hitbox.draw_hitbox(Player1, screen, "green", 2, 3)

        Player2.update()
        if mode == "host":
            Player2.move(K_j, K_l, K_i, K_k, K_u, K_o, remote_keys)
        else:
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
            player2_score += 5
            returnPlayers()
            announce("PLAYER 1 DEAD", 500)

        if pygame.sprite.spritecollide(Player2, void, False):
            player1_score += 5
            returnPlayers()
            announce("PLAYER 2 DEAD", 500)



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

        fps_surf = font.render(f"{clock.get_fps():.0f} fps", True, "white")
        screen.blit(fps_surf, (WIDTH // 2 - 30, 10))

        pygame.display.flip()
        if mode == "host":
            send_state()
        dt = clock.tick(60) / 1000
        await next_frame()

if __name__ == "__main__":
    asyncio.run(main())