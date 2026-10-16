# 🏴 pyCTF

A local multiplayer **Capture The Flag** game built with **Python** and **Pygame** as part of a DCU / CTYI project.

Players are randomly assigned as either the attacker or defender and compete to capture the opposing team's flag while avoiding elimination and using movement abilities to gain an advantage.

---

## 🎮 Features

- Two-player local multiplayer
- Random attacker/defender selection
- Flag capture mechanics
- Score system
- Platforming movement
- Dashing and jumping abilities
- Sound effects and background music
- Custom game assets

---

## 🕹 Controls

### Player 1 (Red)

| Action | Key |
|----------|-----|
| Move Left | A |
| Move Right | D |
| Jump | W |
| Fall Through Platform | S |
| Dash Left | Q |
| Dash Right | E |

### Player 2 (Blue)

| Action | Key |
|----------|-----|
| Move Left | J |
| Move Right | L |
| Jump | I |
| Fall Through Platform | K |
| Dash Left | U |
| Dash Right | O |

---

## 🏁 Objective

At the start of each match, one player is randomly selected as the attacker.

### Attacker
- Reach the opposing team's flag.
- Capture the flag to score points.

### Defender
- Prevent the attacker from reaching the flag.
- Eliminate the attacker to score points.

### Additional Rules
- Falling into the void grants points to the opposing player.
- Players respawn after a score event.
- Teams are randomly assigned each match.

---

## 🛠 Technologies Used

- Python
- Pygame

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/kampans/pyCTF.git
cd pyCTF
```

Install dependencies:

```bash
pip install pygame
```

Run the game:

```bash
python main.py
```

---

## 📁 Project Structure

```text
pyCTF/
│
├── elements/
│   ├── blueflag.png
│   ├── redflag.png
│   ├── Untitled.png
│   ├── jump.ogg
│   ├── woosh.ogg
│   └── gamemusic.ogg
│
├── main.py
├── README.md
└── .gitignore
```

---

## 🌐 Browser Version

I experimented with exporting the game to run in a web browser using Pygame web tooling. The current browser build is not fully functional due to dependency/runtime issues, so the recommended way to play the game is the desktop version on a 1920x1080 resolution // I might update it if im bothered.

---

## 📚 Background

This project was originally created in **2024** as part of a **CTYI Early University Entry (EUE)** project associated with **Dublin City University (DCU)**.

The game was developed to explore:
- Object-oriented programming
- Physics and collision systems
- Event-driven game design
- Multiplayer gameplay mechanics
- Asset management in Python

---

## 👨‍💻 Authors

- Nicolas Campan
- Matthew Duff

### Music
Created by Nicolas Campan and John Brennan.

---

## 🚀 Future Improvements

Potential future updates include:

- Improved graphics and animations
- Match timer and win conditions
- Online multiplayer support
- Better UI and menus
- Improved browser compatibility
- Leaderboards and statistics

---

Thanks for checking out the project!