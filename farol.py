"""
FAROL — game jam prototype, one input (SPACE).
Requires: pip install pygame
Run: python3 farol.py
"""

import math
import random
import sys
import os
import pygame

pygame.init()
pygame.mixer.init()

# Carregamento e configuração dos áudios
# 1. Som ambiente em loop de fundo
if os.path.exists("somAmbiente.mp3"):
    pygame.mixer.music.load("somAmbiente.mp3")
    pygame.mixer.music.play(-1)  # -1 faz o áudio tocar infinitamente
    pygame.mixer.music.set_volume(0.5)

# 2. Efeito sonoro do monstro
snd_monstro = None
if os.path.exists("somMonstro.mp3"):
    snd_monstro = pygame.mixer.Sound("somMonstro.mp3")
    snd_monstro.set_volume(0.8)

# Variável de controle para não disparar o som repetidamente a cada frame
monstro_som_tocado = False

# Resolução interna fixa
W, H = 960, 600

# Tela cheia do monitor
display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("FAROL — Apenas um Input")

# O jogo continua sendo desenhado em 960 x 600
screen = pygame.Surface((W, H))
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("dejavusans", 19)
SMALL = pygame.font.SysFont("dejavusans", 15)
BIG = pygame.font.SysFont("dejavusans", 42, bold=True)

WHITE = (235, 238, 228)
SEA = (12, 37, 56)
SKY = (7, 14, 32)
GOLD = (255, 224, 132)
RED = (237, 96, 95)

NIGHT_LENGTH = 48
TOTAL_NIGHTS = 5


def text(s, x, y, font=FONT, color=WHITE, center=False):
    img = font.render(s, True, color)
    screen.blit(
        img,
        img.get_rect(center=(x, y)) if center else (x, y)
    )


def reset():
    global monstro_som_tocado
    monstro_som_tocado = False
    return dict(
        mode="title",
        night=1,
        time=0.,
        lit=False,
        boats=[],
        spawn=3.,
        threat=0.,
        saved=0,
        lost=0,
        total_saved=0,
        total_lost=0,
        message="A luz guia os barcos. Mas atrai algo do fundo.",
        msg_timer=5.,
        flash=0.,
        ending=""
    )


g = reset()

stars = [
    (random.randrange(W), random.randrange(260), random.randint(1, 2))
    for _ in range(65)
]

waves = [
    (random.randrange(W), random.randrange(340, 530), random.randint(8, 24))
    for _ in range(40)
]


def message(s, duration=3):
    g["message"], g["msg_timer"] = s, duration


def new_night():
    global monstro_som_tocado
    monstro_som_tocado = False
    g.update(
        mode="play",
        time=0.,
        lit=False,
        boats=[],
        spawn=2.8,
        threat=0.,
        saved=0,
        lost=0,
        flash=0.
    )

    lines = [
        "NOITE 1: Guie os barcos. ESPACO alterna a luz.",
        "NOITE 2: Algo nas profundezas segue a luz...",
        "NOITE 3: Mais embarcacoes estao chegando.",
        "NOITE 4: A tempestade dificulta a travessia.",
        "NOITE 5: Nem todo sinal no mar e humano."
    ]

    message(lines[g["night"] - 1], 6)


def spawn_boat():
    fake = g["night"] == 5 and random.random() < .24

    # Barcos surgem dentro da tela, sempre visiveis
    g["boats"].append(
        dict(
            x=random.randint(300, W - 50),
            y=random.randint(365, 450),
            progress=0.,
            darkness=0.,
            fake=fake,
            speed=random.uniform(31, 43)
        )
    )


def advance(dt):
    global monstro_som_tocado
    g["time"] += dt
    g["msg_timer"] = max(0, g["msg_timer"] - dt)
    g["flash"] = max(0, g["flash"] - dt)
    g["spawn"] -= dt

    interval = max(3.7, 9.5 - g["night"] * 1.1)

    if g["spawn"] <= 0 and g["time"] < NIGHT_LENGTH - 7:
        spawn_boat()
        g["spawn"] = random.uniform(
            interval * .75,
            interval * 1.3
        )

        if g["night"] == 3 and random.random() < .3:
            spawn_boat()

    if g["lit"]:
        g["threat"] += dt * (3.0 + g["night"] * .8)
    else:
        g["threat"] -= dt * 3.3

    g["threat"] = max(0., min(100., g["threat"]))

    # Toca o som do monstro quando ele começa a aparecer na água
    if g["threat"] > 25 and not monstro_som_tocado:
        if snd_monstro:
            snd_monstro.play()
        monstro_som_tocado = True
    elif g["threat"] <= 25:
        monstro_som_tocado = False

    if g["threat"] >= 100:
        g["mode"] = "end"
        g["ending"] = "O mar finalmente alcancou o farol."
        if snd_monstro:
            snd_monstro.play()
        return

    for boat in g["boats"][:]:
        if boat["fake"]:
            boat["x"] -= dt * boat["speed"] * .65

            if g["lit"]:
                g["threat"] = min(
                    100,
                    g["threat"] + dt * 5
                )

            if boat["x"] < 195:
                g["boats"].remove(boat)
                message(
                    "RADIO: ...essa embarcacao nao consta nos registros.",
                    4
                )

            continue

        if g["lit"]:
            boat["x"] -= dt * boat["speed"] * (
                .75 if g["night"] == 4 else 1
            )
            boat["darkness"] = max(
                0,
                boat["darkness"] - dt * 1.2
            )
        else:
            boat["darkness"] += dt

        if boat["x"] <= 195:
            g["boats"].remove(boat)
            g["saved"] += 1
            g["total_saved"] += 1
            message(
                "RADIO: Obrigado, farol! Estamos a salvo.",
                2.5
            )

        elif boat["darkness"] >= (
            13 if g["night"] == 4 else 17
        ):
            g["boats"].remove(boat)
            g["lost"] += 1
            g["total_lost"] += 1

            # Perder o segundo barco encerra a partida
            if g["total_lost"] > 1:
                g["mode"] = "end"
                g["ending"] = (
                    "Dois barcos foram perdidos. "
                    "O farol falhou."
                )
                if snd_monstro:
                    snd_monstro.play()
                return

            message(
                "RADIO: Sinal perdido. Um barco desapareceu.",
                3
            )

    if g["time"] >= NIGHT_LENGTH:
        # Barcos que ainda estiverem no mar tambem podem ser perdidos
        for boat in g["boats"]:
            if not boat["fake"]:
                g["lost"] += 1
                g["total_lost"] += 1

        g["boats"].clear()
        g["lit"] = False

        # Duas perdas no total encerram o jogo
        if g["total_lost"] > 1:
            g["mode"] = "end"
            g["ending"] = (
                "Dois barcos foram perdidos. "
                "O farol falhou."
            )
            if snd_monstro:
                snd_monstro.play()
        else:
            g["mode"] = (
                "between"
                if g["night"] < TOTAL_NIGHTS
                else "win"
            )


def draw_scene():
    screen.fill(SKY)

    for x, y, r in stars:
        pygame.draw.circle(
            screen,
            (95, 114, 143),
            (x, y),
            r
        )

    pygame.draw.circle(
        screen,
        (187, 195, 192),
        (810, 83),
        29
    )

    pygame.draw.rect(
        screen,
        SEA,
        (0, 330, W, H - 330)
    )

    tick = pygame.time.get_ticks() / 1000

    for x, y, width in waves:
        shift = math.sin(tick * 1.5 + y) * 8

        pygame.draw.line(
            screen,
            (30, 69, 85),
            (x + shift, y),
            (x + width + shift, y),
            2
        )

    # Ilha rochosa e farol
    pygame.draw.polygon(
        screen,
        (29, 37, 44),
        [
            (0, 485), (45, 465), (110, 475),
            (168, 450), (222, 490), (255, 560),
            (0, 600)
        ]
    )

    pygame.draw.polygon(
        screen,
        (198, 199, 188),
        [(79, 461), (91, 270), (143, 270), (157, 461)]
    )

    pygame.draw.polygon(
        screen,
        (132, 57, 63),
        [(91, 270), (117, 244), (143, 270)]
    )

    pygame.draw.rect(
        screen,
        (32, 39, 51),
        (98, 279, 39, 25)
    )

    pygame.draw.rect(
        screen,
        GOLD if g["lit"] else (71, 77, 80),
        (104, 282, 27, 18)
    )

    pygame.draw.rect(
        screen,
        (36, 44, 53),
        (111, 415, 18, 46)
    )

    if g["lit"]:
        beam = pygame.Surface((W, H), pygame.SRCALPHA)

        pygame.draw.polygon(
            beam,
            (255, 218, 105, 40),
            [(133, 292), (960, 210), (960, 480)]
        )

        screen.blit(beam, (0, 0))

    # Barcos
    for boat in g["boats"]:
        x, y = int(boat["x"]), int(boat["y"])

        hull = (
            (118, 52, 70)
            if boat["fake"] and g["lit"]
            else (190, 183, 153)
        )

        pygame.draw.polygon(
            screen,
            hull,
            [
                (x - 20, y),
                (x + 20, y),
                (x + 12, y + 10),
                (x - 12, y + 10)
            ]
        )

        pygame.draw.line(
            screen,
            WHITE,
            (x, y),
            (x, y - 24),
            2
        )

        pygame.draw.polygon(
            screen,
            (205, 209, 201),
            [(x + 2, y - 22), (x + 16, y - 3), (x + 2, y - 3)]
        )

        if not boat["fake"]:
            pygame.draw.rect(
                screen,
                (70, 85, 89),
                (x - 20, y + 15, 40, 4)
            )

            pygame.draw.rect(
                screen,
                RED if boat["darkness"] > 10 else GOLD,
                (
                    x - 20,
                    y + 15,
                    max(
                        0,
                        int(40 * (1 - boat["darkness"] / 17))
                    ),
                    4
                )
            )

    # Ameaca nas profundezas
    if g["threat"] > 25:
        yy = 520 - int(g["threat"] * .25)

        pygame.draw.ellipse(
            screen,
            (5, 19, 27),
            (620, yy, 210, 65)
        )

        if g["threat"] > 50:
            pygame.draw.circle(
                screen, RED, (680, yy + 24), 4
            )
            pygame.draw.circle(
                screen, RED, (740, yy + 24), 4
            )

    # Chuva durante as noites finais
    if g["night"] >= 4 and g["mode"] == "play":
        for i in range(35):
            x = (i * 73 + int(tick * 110)) % W
            y = (i * 49 + int(tick * 170)) % H

            pygame.draw.line(
                screen,
                (71, 91, 111),
                (x, y),
                (x - 9, y + 17),
                1
            )


def hud():
    pygame.draw.rect(
        screen,
        (8, 15, 27),
        (0, 0, W, 76)
    )

    text(f"NOITE {g['night']}/5", 18, 12)

    text(
        f"Salvos: {g['total_saved']}   Perdidos: {g['total_lost']}",
        18, 41, SMALL
    )

    remaining = max(
        0,
        math.ceil(NIGHT_LENGTH - g["time"])
    )

    text(f"Amanhecer em {remaining}s", 400, 12)

    text("AMEACA", 690, 12, SMALL)

    pygame.draw.rect(
        screen,
        (50, 53, 64),
        (690, 39, 238, 16)
    )

    pygame.draw.rect(
        screen,
        RED,
        (690, 39, int(238 * g["threat"] / 100), 16)
    )

    text(
        "LUZ ACESA" if g["lit"] else "LUZ APAGADA",
        400, 43, SMALL,
        GOLD if g["lit"] else WHITE
    )

    if g["msg_timer"] > 0:
        pygame.draw.rect(
            screen,
            (9, 16, 29),
            (125, 535, 710, 38),
            border_radius=5
        )

        text(
            g["message"],
            480, 554, SMALL, GOLD, True
        )

    text(
        "ESPACO: ligar / desligar o farol",
        480, 584, SMALL, WHITE, True
    )


def overlay(title, lines, prompt):
    veil = pygame.Surface((W, H), pygame.SRCALPHA)
    veil.fill((3, 8, 17, 210))
    screen.blit(veil, (0, 0))

    text(title, W // 2, 178, BIG, GOLD, True)

    for i, line in enumerate(lines):
        text(
            line,
            W // 2,
            254 + i * 35,
            FONT,
            WHITE,
            True
        )

    text(prompt, W // 2, 455, FONT, GOLD, True)


# Loop principal
running = True

while running:
    dt = min(clock.tick(60) / 1000, .05)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif (
                event.key == pygame.K_SPACE
                and not getattr(event, "repeat", False)
            ):
                if g["mode"] == "title":
                    new_night()

                elif g["mode"] == "play":
                    g["lit"] = not g["lit"]

                elif g["mode"] == "between":
                    g["night"] += 1
                    new_night()

                elif g["mode"] in ("end", "win"):
                    g = reset()
                    new_night()

    if g["mode"] == "play":
        advance(dt)

    draw_scene()

    if g["mode"] == "play":
        hud()

    elif g["mode"] == "title":
        overlay(
            "FAROL",
            [
                "Um unico botao. Cinco noites.",
                "Acenda para guiar os barcos. Apague para afastar o que vive no mar.",
                "Barcos no escuro por muito tempo desaparecem, NÃO PERCA NENHUM DELES!!."
            ],
            "PRESSIONE ESPACO PARA COMECAR"
        )

    elif g["mode"] == "between":
        overlay(
            f"AMANHECEU — NOITE {g['night']}",
            [
                f"Barcos salvos nesta noite: {g['saved']}",
                f"Barcos perdidos nesta noite: {g['lost']}",
                "O radio chia. Outra noite se aproxima."
            ],
            "PRESSIONE ESPACO PARA A PROXIMA NOITE"
        )

    elif g["mode"] == "end":
        overlay(
            "O FAROL SE APAGOU",
            [
                g["ending"],
                f"Total de barcos salvos: {g['total_saved']}",
                f"Total de barcos perdidos: {g['total_lost']}"
            ],
            "PRESSIONE ESPACO PARA RECOMECAR"
        )

    elif g["mode"] == "win":
        overlay(
            "O ULTIMO AMANHECER",
            [
                "A superficie se ilumina. Sob a ilha, algo imenso se move.",
                "O que voce viu durante as noites era apenas uma pequena parte.",
                f"Barcos salvos: {g['total_saved']}   |   Perdidos: {g['total_lost']}",
                "Obrigado por manter a luz acesa."
            ],
            "PRESSIONE ESPACO PARA JOGAR NOVAMENTE"
        )

    # Exibe o jogo em tela cheia sem distorcer a proporcao
    display.fill((0, 0, 0))

    display_w, display_h = display.get_size()

    scale = min(
        display_w / W,
        display_h / H
    )

    new_w = int(W * scale)
    new_h = int(H * scale)

    scaled_screen = pygame.transform.scale(
        screen,
        (new_w, new_h)
    )

    x = (display_w - new_w) // 2
    y = (display_h - new_h) // 2

    display.blit(scaled_screen, (x, y))
    pygame.display.flip()

pygame.quit()
sys.exit()