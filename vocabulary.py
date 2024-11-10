import csv
import requests
import os


class Word:
    def __init__(self, spanish, english, level='A1', image_link=None, image_path=None, word_id=None):
        self.spanish = spanish
        self.english = english
        self.level = level
        self.image_link = image_link
        self.image_path = image_path
        self.word_id = word_id



def load_vocabulary(file_path, db):
    images_folder = 'images'
    os.makedirs(images_folder, exist_ok=True)  # Create images folder if it doesn't exist

    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                image_link = row.get('image_link', None)
                image_path = None

                if image_link:
                    # Download the image
                    try:
                        response = requests.get(image_link, timeout=10)
                        response.raise_for_status()  # Raise exception for HTTP errors
                        # Save the image to the local file system
                        image_extension = os.path.splitext(image_link)[1]
                        image_filename = f"{row['spanish']}{image_extension}"
                        image_filepath = os.path.join(images_folder, image_filename)
                        with open(image_filepath, 'wb') as image_file:
                            image_file.write(response.content)
                        image_path = image_filepath
                    except requests.RequestException as e:
                        print(f"Failed to download image for '{row['spanish']}': {e}")

                word = Word(
                    spanish=row['spanish'],
                    english=row['english'],
                    level=row['level'],
                    image_link=image_link,
                    image_path=image_path
                )

                db.insert_word(word)
    except FileNotFoundError:
        print(f"Vocabulary file '{file_path}' not found.")