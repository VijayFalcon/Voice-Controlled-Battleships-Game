from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# Global variables for game state
player_board = [[' ' for _ in range(10)] for _ in range(10)]
computer_board = [[' ' for _ in range(10)] for _ in range(10)]
player_ships = []
computer_ships = []
current_turn = 1  # Player 1 starts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    global player_board, computer_board, current_turn, player_ships, computer_ships

    data = request.json
    player_board = data['player1_board']
    computer_board = data['player2_board']
    
    player_ships = extract_ships(player_board)
    computer_ships = extract_ships(computer_board)
    
    current_turn = 1  # Player 1 starts

    return jsonify({
        'message': 'Game started! Player 1 will start attacking.',
        'turn': current_turn
    })

@app.route('/make_move', methods=['POST'])
def make_move():
    global player_board, computer_board, current_turn

    data = request.json
    row, col = data['row'], data['col']

    if current_turn == 1:
        hit = process_attack(computer_board, row, col)
        message = 'Player 1: Hit!' if hit else 'Player 1: Miss!'

        if all_ships_sunk(computer_board):
            return jsonify({'message': 'Player 1 wins!', 'game_over': True})

        current_turn = 2

    else:
        hit = process_attack(player_board, row, col)
        message = 'Player 2: Hit!' if hit else 'Player 2: Miss!'

        if all_ships_sunk(player_board):
            return jsonify({'message': 'Player 2 wins!', 'game_over': True})

        current_turn = 1

    return jsonify({
        'message': message,
        'turn': current_turn,
        'player_board': player_board,
        'computer_board': mask_board(computer_board),
    })

def process_attack(board, row, col):
    if board[row][col] == 'O':  # Ship is there
        board[row][col] = 'X'  # Mark as hit
        return True
    elif board[row][col] == ' ':
        board[row][col] = 'M'  # Mark as miss
    return False

def mask_board(board):
    return [['X' if cell == 'X' else 'M' if cell == 'M' else ' ' for cell in row] for row in board]

def all_ships_sunk(board):
    return all(cell != 'O' for row in board for cell in row)

def extract_ships(board):
    return [(r, c) for r in range(10) for c in range(10) if board[r][c] == 'O']

if __name__ == '__main__':
    app.run(port=5000, debug=True)
