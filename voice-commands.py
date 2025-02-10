import speech_recognition as sr
import keyboard
import re
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from Levenshtein import distance as levenshtein_distance

# Define ship types and their sizes
ship_types = {
    "battleship": 5, "cruiser": 4, "destroyer": 3, "submarine": 2,
    "carrier": (3, 2)  # Carrier is a 3x2 rectangle
}
placed_ships = {}

# State control for placement and firing phases
phase = "placement"

# Machine learning setup
vectorizer = CountVectorizer()
classifier = MultinomialNB()

# Regex patterns for commands
grid_pattern = r"[0-9]{2}"
phonetic_corrections = {}

# Grid for collision detection
grid_size = 10
occupied_cells = [[False] * grid_size for _ in range(grid_size)]

# Define training phrases dynamically for all coordinates
def generate_training_phrases():
    training_phrases = []
    labels = []

    orientations = ["horizontally", "vertically"]
    for row in range(10):
        for col in range(10):
            grid = f"{row:01}{col:01}"
            for ship_type in ship_types:
                for orientation in orientations:
                    training_phrases.append(f"place {ship_type} at {grid} {orientation}")
                    labels.append(f"placement_{ship_type}_{grid}_{orientation}")
            # Firing commands
            training_phrases.append(f"fire at {grid}")
            labels.append(f"firing_{grid}")

    return training_phrases, labels


def train_model():
    training_phrases, labels = generate_training_phrases()
    X_train = vectorizer.fit_transform(training_phrases)
    classifier.fit(X_train, labels)


def predict_action(text):
    X_test = vectorizer.transform([text])
    prediction = classifier.predict(X_test)[0]
    return prediction


def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... (Release 'Alt' key to stop)")
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return None
        except sr.RequestError:
            print("Speech recognition service is unavailable.")
            return None


def is_within_grid(row, col):
    return 0 <= row < grid_size and 0 <= col < grid_size


def is_collision(ship_type, row, col, orientation):
    size = ship_types[ship_type]

    if ship_type == "carrier":
        length, width = size
        for i in range(length):
            for j in range(width):
                r = row + (i if orientation == "vertically" else 0)
                c = col + (j if orientation == "horizontally" else 0)
                if not is_within_grid(r, c) or occupied_cells[r][c]:
                    return True
        return False

    for i in range(size):
        r = row + (i if orientation == "vertically" else 0)
        c = col + (i if orientation == "horizontally" else 0)
        if not is_within_grid(r, c) or occupied_cells[r][c]:
            return True

    return False


def mark_cells(ship_type, row, col, orientation):
    size = ship_types[ship_type]

    if ship_type == "carrier":
        length, width = size
        for i in range(length):
            for j in range(width):
                r = row + (i if orientation == "vertically" else 0)
                c = col + (j if orientation == "horizontally" else 0)
                if is_within_grid(r, c):
                    occupied_cells[r][c] = True
    else:
        for i in range(size):
            r = row + (i if orientation == "vertically" else 0)
            c = col + (i if orientation == "horizontally" else 0)
            if is_within_grid(r, c):
                occupied_cells[r][c] = True


def parse_placement_command(prediction, command_text):
    match = re.match(r"placement_(\w+)_(\d{2})_(\w+)", prediction)
    if match:
        ship_type, grid, orientation = match.groups()

        # Handle spaced integers and potential phonetic errors for coordinates
        grid_text = re.sub(r"[^0-9]", "", command_text)

        if len(grid_text) == 2:
            row, col = int(grid_text[0]), int(grid_text[1])
        elif len(grid_text) == 3 and grid_text[1] == '0':
            row, col = int(grid_text[0:2]), int(grid_text[2])
        else:
            return "Invalid grid coordinates."

        if ship_type in placed_ships:
            return f"{ship_type.capitalize()} has been placed already at {placed_ships[ship_type][0]} {placed_ships[ship_type][1]}."

        if is_collision(ship_type, row, col, orientation):
            return f"Cannot place {ship_type.capitalize()} at {row}{col} {orientation} due to a collision or out-of-bound placement."

        placed_ships[ship_type] = (f"{row}{col}", orientation)
        mark_cells(ship_type, row, col, orientation)

        if len(placed_ships) == len(ship_types):
            global phase
            phase = "firing"
            return f"All ships placed. {ship_type.capitalize()} placed at {row}{col} {orientation}. Switching to firing phase."

        return f"{ship_type.capitalize()} placed at {row}{col} {orientation}."
    return "Invalid placement command."


def parse_firing_command(prediction):
    match = re.match(r"firing_(\d{2})", prediction)
    if match:
        grid = match.group(1)
        return f"Fire at {grid}"
    return "Unrecognized command."


def main():
    train_model()
    print("Hold 'Alt' key to talk. Release when done. Press Ctrl+C to exit.")
    while True:
        if keyboard.is_pressed('alt'):
            command_text = recognize_speech()
            if command_text:
                prediction = predict_action(command_text)
                if phase == "placement":
                    game_action = parse_placement_command(prediction, command_text)
                else:
                    game_action = parse_firing_command(prediction)
                if game_action:
                    print(f"Game Action: {game_action}")

if __name__ == "__main__":
    main()
#File commited.