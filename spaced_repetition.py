import datetime

class SpacedRepetitionScheduler:
    def __init__(self, db):
        self.db = db
        self.load_due_words()
        self.load_new_words()
        self.current_word_data = None

    def load_due_words(self):
        due_words = self.db.get_due_words()
        for word in due_words:
            try:
                # Ensure that word[6] (next_review_date) is in the correct format
                next_review_date_str = word[6]
                if isinstance(next_review_date_str, int):
                    # Convert timestamp to datetime if necessary
                    next_review_date = datetime.datetime.fromtimestamp(next_review_date_str)
                elif isinstance(next_review_date_str, str):
                    next_review_date = datetime.datetime.strptime(next_review_date_str, '%Y-%m-%d')
                else:
                    raise ValueError(f"Unexpected type for next_review_date: {type(next_review_date_str)}")


            except IndexError:
                print(f"Unexpected tuple structure for word: {word}")
            except ValueError as e:
                print(f"Error processing word: {word}. Error: {e}")

    def load_new_words(self):
        # Use the correct method name 'get_new_word'
        word = self.db.get_new_word()
        if word:
            # Process the word if needed (e.g., adding it to a list for tracking)
            pass

    def update_progress(self, word_id, quality, correct):
        # Only proceed if current_word_data is set
        if not self.current_word_data:
            print("Error: current_word_data is None")
            return  # Exit early if there’s no current word data

        progress = self.db.get_word_progress(word_id)
        if progress:
            interval, repetitions, ease_factor, next_review_date_str, correct_answers = progress

            # Update based on whether the answer was correct
            if correct:
                correct_answers += 1
            else:
                correct_answers = 0  # Reset on incorrect answer

            # Adjust spaced repetition calculations as needed
            if quality < 3:
                repetitions = 0
                interval = 1
            else:
                repetitions += 1
                interval = 1 if repetitions == 1 else (6 if repetitions == 2 else int(interval * ease_factor))

            ease_factor = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

            next_review_date = datetime.date.today() + datetime.timedelta(days=interval)
            next_review_date_str = next_review_date.isoformat()

            self.db.update_word_progress(word_id, interval, repetitions, ease_factor, next_review_date_str,
                                         correct_answers)

            # Update current word data to reflect these changes
            self.current_word_data = (
                'due', word_id, self.current_word_data[2], self.current_word_data[3], correct_answers,
                self.current_word_data[5], interval, repetitions, ease_factor, next_review_date_str
            )

    def get_due_word(self, ignore_due_date=False):
        if ignore_due_date:
            return self.db.get_any_review_word()
        return self.db.get_due_words()

    def get_next_word(self):
        """Fetch the next word for introduction or review."""
        new_word = self.db.get_new_word()
        if new_word:
            self.db.mark_word_as_introduced(new_word[1])  # Mark as introduced immediately upon selection
            return new_word
        return self.get_due_word(ignore_due_date=True)  # Fall back on due words if no new words are available

    def get_due_word(self, ignore_due_date=False):
        """Retrieve a review word, ignoring due dates if specified."""
        if ignore_due_date:
            return self.db.get_any_review_word()
        return self.db.get_due_words()




