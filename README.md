# Voice-Controlled Battleships Game 🚢💥

A real-time multiplayer Battleship game with voice command support. Two players place their fleets, take turns attacking, and can fire coordinates completely hands-free using the integrated Python voice recognition module. Built with Node.js, Express, and Socket.io for WebSocket-based live gameplay.

---

## Overview

This is a browser-based multiplayer Battleships implementation where the entire game state is synchronized in real time between two players over WebSockets. The key differentiator is the voice command layer: a Python script runs alongside the browser client and listens for spoken coordinates like "B4" or "fire at D7", converting them to game actions without touching the mouse or keyboard.

---

## Features

**Real-time multiplayer** -- Socket.io keeps both players' boards in sync with sub-100ms latency. Every hit, miss, and ship placement is broadcast instantly.

**Voice control** -- a Python `voice_commands.py` module uses speech recognition to interpret spoken coordinate inputs and translate them into game events. Fire without lifting a finger.

**Ship placement with rotation** -- players drag ships onto the grid and can rotate them before locking in their fleet.

**Turn-based attack system** -- strict server-side turn enforcement ensures neither player can act out of order.

**Hit/miss feedback** -- real-time visual indicators show hits (red), misses (white), and sunk ships as the game progresses.

**Game over detection** -- the server detects when all ships of one player are sunk and announces the winner.

---

## Stack

![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat-square&logo=nodedotjs&logoColor=white)
![Express](https://img.shields.io/badge/Express-000000?style=flat-square&logo=express&logoColor=white)
![Socket.io](https://img.shields.io/badge/Socket.io-010101?style=flat-square&logo=socketdotio&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

---

## Repository Structure

```
Voice-Controlled-Battleships-Game/
├── index.html          # Game UI (board rendering, ship placement, attack interface)
├── server.js           # Node.js + Express + Socket.io game server
├── voice_commands.py   # Python voice recognition module
└── README.md
```

---

## Setup and Running

**Install Node.js dependencies:**
```bash
npm install
```

**Start the game server:**
```bash
node server.js
```

**Open the game:**
Go to `http://localhost:3000` in two separate browser tabs (or two devices on the same network) to start a match.

**Enable voice control (optional):**
```bash
pip install SpeechRecognition pyaudio
python voice_commands.py
```
Speak coordinates in the format "B4", "fire D7", or "attack at F2" to control the game hands-free.

---

## How to Play

1. Each player places their ships on the grid -- select a ship, click to place, use the Rotate button to change orientation.
2. Once both players have placed their fleets, Player 2 starts the game.
3. Players take turns clicking (or speaking) a coordinate on the opponent's grid to attack.
4. The board shows hits and misses in real time.
5. The first player to sink all of the opponent's ships wins.

---

## Live Demo

Deployed at: [coding-monarchs-nexathon-2025-neon.vercel.app](https://coding-monarchs-nexathon-2025-neon.vercel.app)
