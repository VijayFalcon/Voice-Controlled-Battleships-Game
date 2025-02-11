const express = require("express");
const http = require("http");
const socketIo = require("socket.io");
const { PythonShell } = require('python-shell');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Configure Python shell with absolute path
const pythonPath = path.join(__dirname, 'voice_commands.py');
const pythonShells = new Map();

function startPythonShell(playerNumber) {
    const pyshell = new PythonShell(pythonPath, {
        mode: 'text',
        pythonOptions: ['-u'],
        args: [playerNumber.toString()]
    });

    pyshell.on('message', function (message) {
        console.log(`Python output (Player ${playerNumber}):`, message);
        if (message.startsWith('PLACE_SHIP') || message.startsWith('FIRE')) {
            const [command, ...params] = message.split(' ');
            const player = parseInt(params[params.length - 1]);
            
            // Emit command only to the specific player
            const socketId = getSocketIdByPlayer(player);
            if (socketId) {
                io.to(socketId).emit('voiceCommand', message);
            }
        }
    });

    pyshell.on('error', function (err) {
        console.error(`Python error (Player ${playerNumber}):`, err);
    });

    pyshell.on('stderr', function (stderr) {
        console.error(`Python stderr (Player ${playerNumber}):`, stderr);
    });

    return pyshell;
}

app.use(express.static(__dirname));

// Game state
let players = {};
let ships = { 1: {}, 2: {} };
let boardHits = { 1: [], 2: [] };
let currentTurn = 1;
let gameStarted = false;
let placementPhase = { 1: true, 2: true };

io.on("connection", (socket) => {
    console.log("A player connected:", socket.id);

    let playerNumber = Object.keys(players).length + 1;
    if (playerNumber > 2) {
        socket.emit("gameFull");
        socket.disconnect();
        return;
    }

    players[socket.id] = playerNumber;
    socket.emit("playerNumber", playerNumber);

    // Start Python shell for this player
    pythonShells.set(playerNumber, startPythonShell(playerNumber));

    socket.on("placeShip", ({ shipType, positions }) => {
        let player = players[socket.id];
        if (!player || !placementPhase[player]) return;

        if (ships[player][shipType]) {
            socket.emit("shipAlreadyPlaced", shipType);
            return;
        }

        // Validate ship positions
        if (!validateShipPlacement(positions, player)) {
            socket.emit("invalidPlacement", shipType);
            return;
        }

        ships[player][shipType] = positions;
        socket.emit("shipPlaced", { shipType, positions });
        console.log(`Player ${player} placed ${shipType}`);

        if (Object.keys(ships[player]).length === 5) {
            socket.emit("readyToFinish");
        }
    });

    socket.on("finishPlacingShips", () => {
        let player = players[socket.id];
        if (!player || Object.keys(ships[player]).length < 5) {
            socket.emit("incompletePlacement");
            return;
        }

        placementPhase[player] = false;
        console.log(`Player ${player} finished placing ships`);

        if (!placementPhase[1] && !placementPhase[2]) {
            io.emit("readyToStart");
        } else if (player === 1) {
            io.emit("player2TurnToPlace");
        }
    });

    socket.on("startGame", () => {
        if (!placementPhase[1] && !placementPhase[2]) {
            gameStarted = true;
            currentTurn = 1;
            io.emit("gameStarted", currentTurn);
            io.to(getSocketIdByPlayer(currentTurn)).emit("yourTurn");
            console.log("Game Started! Player 1's turn.");
        } else {
            socket.emit("cannotStartGame");
        }
    });

    socket.on("attack", ({ row, col }) => {
        if (!gameStarted) return;

        let player = players[socket.id];
        if (!player || player !== currentTurn) {
            socket.emit("notYourTurn");
            return;
        }

        // Check if this coordinate was already attacked
        let opponent = player === 1 ? 2 : 1;
        if (boardHits[opponent].some(hit => hit.row === row && hit.col === col)) {
            socket.emit("alreadyAttacked");
            return;
        }

        let hit = isHit(row, col, opponent);
        boardHits[opponent].push({ row, col, hit });
        io.emit("attackResult", { row, col, hit, attacker: player });

        if (checkGameOver(opponent)) {
            io.emit("gameOver", { winner: player });
            resetGame();
            return;
        }

        // Switch turns
        currentTurn = opponent;
        io.emit("turnUpdate", currentTurn);
        io.to(getSocketIdByPlayer(currentTurn)).emit("yourTurn");
    });

    socket.on("disconnect", () => {
        let player = players[socket.id];
        if (player) {
            console.log(`Player ${player} disconnected`);
            if (pythonShells.has(player)) {
                pythonShells.get(player).terminate();
                pythonShells.delete(player);
            }
            delete players[socket.id];
            resetGame();
        }
    });

    socket.on("activateVoiceCommand", () => {
        const player = players[socket.id];
        if (player && pythonShells.has(player)) {
            console.log(`Voice command activated for Player ${player}`);
            pythonShells.get(player).send('start');
        }
    });
});

function validateShipPlacement(positions, player) {
    // Check if positions are within bounds
    if (!positions.every(pos => pos.row >= 0 && pos.row < 10 && pos.col >= 0 && pos.col < 10)) {
        return false;
    }

    // Check if positions overlap with existing ships
    return !positions.some(newPos => 
        Object.values(ships[player]).some(ship =>
            ship.some(pos => pos.row === newPos.row && pos.col === newPos.col)
        )
    );
}

function isHit(row, col, targetPlayer) {
    return Object.values(ships[targetPlayer]).some(ship =>
        ship.some(position => position.row === row && position.col === col)
    );
}

function checkGameOver(targetPlayer) {
    const totalShipPositions = Object.values(ships[targetPlayer]).reduce(
        (sum, ship) => sum + ship.length, 
        0
    );
    const totalHits = boardHits[targetPlayer].filter(h => h.hit).length;
    return totalHits === totalShipPositions;
}

function getSocketIdByPlayer(playerNumber) {
    return Object.keys(players).find(socketId => players[socketId] === playerNumber);
}

function resetGame() {
    ships = { 1: {}, 2: {} };
    boardHits = { 1: [], 2: [] };
    currentTurn = 1;
    gameStarted = false;
    placementPhase = { 1: true, 2: true };
    io.emit("gameReset");
}

// Helper function to validate turn sequence
function validateTurn(socket, action) {
    const player = players[socket.id];
    if (!player) {
        socket.emit("error", { message: "Player not found" });
        return false;
    }

    if (action === "placement" && !placementPhase[player]) {
        socket.emit("error", { message: "Placement phase already completed" });
        return false;
    }

    if (action === "attack" && !gameStarted) {
        socket.emit("error", { message: "Game hasn't started yet" });
        return false;
    }

    if (action === "attack" && player !== currentTurn) {
        socket.emit("error", { message: "Not your turn" });
        return false;
    }

    return true;
}

// Helper function to validate ship placement
function validateShipConfiguration(ships, player) {
    const requiredShips = {
        carrier: 5,
        battleship: 4,
        cruiser: 3,
        submarine: 3,
        destroyer: 2
    };

    for (const [shipType, length] of Object.entries(requiredShips)) {
        const ship = ships[player][shipType];
        if (!ship || ship.length !== length) {
            return false;
        }

        // Validate ship continuity
        if (!isShipContinuous(ship)) {
            return false;
        }
    }

    return true;
}

function isShipContinuous(positions) {
    if (positions.length < 2) return true;

    // Sort positions by row and column
    positions.sort((a, b) => {
        if (a.row === b.row) return a.col - b.col;
        return a.row - b.row;
    });

    // Check if positions are continuous
    let isHorizontal = positions[0].row === positions[1].row;
    let isVertical = positions[0].col === positions[1].col;

    if (!isHorizontal && !isVertical) return false;

    for (let i = 1; i < positions.length; i++) {
        if (isHorizontal) {
            if (positions[i].row !== positions[0].row || 
                positions[i].col !== positions[i-1].col + 1) {
                return false;
            }
        } else {
            if (positions[i].col !== positions[0].col || 
                positions[i].row !== positions[i-1].row + 1) {
                return false;
            }
        }
    }

    return true;
}

// Handle game state synchronization
function syncGameState(socket) {
    const player = players[socket.id];
    if (!player) return;

    socket.emit("gameState", {
        currentTurn,
        gameStarted,
        placementPhase: placementPhase[player],
        myShips: ships[player],
        myHits: boardHits[player === 1 ? 2 : 1],
        enemyHits: boardHits[player]
    });
}

// Error handling middleware
app.use((err, req, res, next) => {
    console.error("Server error:", err);
    res.status(500).json({ error: "Internal server error" });
});

// Cleanup function for when server shuts down
function cleanup() {
    console.log("Cleaning up resources...");
    for (const [player, pyshell] of pythonShells.entries()) {
        console.log(`Terminating Python shell for Player ${player}`);
        pyshell.terminate();
    }
    pythonShells.clear();
    process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

server.listen(3000, () => {
    console.log("Server running on http://localhost:3000");
});
