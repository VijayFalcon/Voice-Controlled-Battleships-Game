import speech_recognition as sr
import sys
import joblib
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from pathlib import Path

MODEL_PATH = "battleship_model.pkl"
VECTORIZER_PATH = "battleship_vectorizer.pkl"


class BattleshipVoiceClassifier:
    def __init__(self):
        self.number_map = self.generate_number_map()
        self.ship_types = ['carrier', 'battleship', 'destroyer', 'cruiser', 'submarine']
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3))
        self.classifier = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500)

        if Path(MODEL_PATH).exists() and Path(VECTORIZER_PATH).exists():
            self.load_model()
        else:
            self.train_classifier()

    def generate_number_map(self):
        return {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
                'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'}

    def generate_training_data(self):
        training_phrases = []
        commands = []

        for ship in self.ship_types:
            for i in range(10):
                for j in range(10):
                    num_word_i = self.get_number_word(i)
                    num_word_j = self.get_number_word(j)

                    phrases = [
                        f"place {ship} at {i} {j} horizontal",
                        f"place {ship} at {num_word_i} {num_word_j} horizontal",
                        f"put {ship} at row {i} column {j} horizontal",
                        f"put {ship} at {num_word_i} {num_word_j} horizontally",
                        f"place {ship} at {i} {j} vertical",
                        f"place {ship} at {num_word_i} {num_word_j} vertical",
                        f"put {ship} at row {i} column {j} vertical",
                        f"put {ship} at {num_word_i} {num_word_j} vertically"
                    ]
                    command = f"PLACE_SHIP {ship} {i} {j}"
                    training_phrases.extend(phrases)
                    commands.extend([command] * len(phrases))

        return training_phrases, commands

    def get_number_word(self, num):
        reverse_map = {v: k for k, v in self.number_map.items()}
        return reverse_map.get(str(num), str(num))

    def train_classifier(self):
        print("Training model...")
        X_train, y_train = self.generate_training_data()
        X_vectors = self.vectorizer.fit_transform(X_train)
        self.classifier.fit(X_vectors.toarray(), y_train)
        joblib.dump(self.classifier, MODEL_PATH)
        joblib.dump(self.vectorizer, VECTORIZER_PATH)
        print("Training complete. Model saved.")

    def load_model(self):
        print("Loading pre-trained model...")
        self.classifier = joblib.load(MODEL_PATH)
        self.vectorizer = joblib.load(VECTORIZER_PATH)
        print("Model loaded.")

    def preprocess_text(self, text):
        text = text.lower().strip()
        for word, digit in self.number_map.items():
            text = re.sub(r'\b' + word + r'\b', digit, text)
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        return text

    def predict_command(self, text):
        processed_text = self.preprocess_text(text)
        X_vector = self.vectorizer.transform([processed_text]).toarray()
        prediction = self.classifier.predict(X_vector)[0]
        return prediction


def recognize_speech():
    recognizer = sr.Recognizer()
    classifier = BattleshipVoiceClassifier()

    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
        print("Listening for command...")

        try:
            audio = recognizer.listen(source, timeout=10)  # Increased timeout
            print("Processing speech...")
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")

            command = classifier.predict_command(text)
            print(f"Predicted command: {command}")

            return command if command else "Invalid command"
        except sr.UnknownValueError:
            print("Could not understand the audio")
            return "Could not understand the audio"
        except sr.RequestError:
            print("Speech recognition service unavailable")
            return "Speech recognition service unavailable"


def main():
    while True:
        try:
            command = input("Press Enter to start voice recognition or type 'exit' to quit: ").strip()
            if command.lower() == 'exit':
                break
            print(recognize_speech())
        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
