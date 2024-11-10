import sqlite3
import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('vocab_app.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.load_vocabulary_if_needed()

    def create_tables(self):
        # Create the tables with an `introduced` column if it does not exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spanish TEXT,
                english TEXT,
                level TEXT,
                theme TEXT,
                image_path TEXT,
                introduced INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0
            )
        ''')

        # Create the progress table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                word_id INTEGER PRIMARY KEY,
                interval INTEGER,
                repetitions INTEGER,
                ease_factor REAL,
                next_review_date TEXT,
                FOREIGN KEY(word_id) REFERENCES words(id)
            )
        ''')

        # Create response_history table for tracking individual responses
        self.cursor.execute('''
             CREATE TABLE IF NOT EXISTS response_history (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 word_id INTEGER,
                 response_date TEXT,
                 correct INTEGER,
                 FOREIGN KEY(word_id) REFERENCES words(id)
             )
         ''')
        self.conn.commit()

        # Check if the 'correct_answers' column is missing and add it if necessary
        self.cursor.execute("PRAGMA table_info(progress)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'correct_answers' not in columns:
            self.cursor.execute("ALTER TABLE progress ADD COLUMN correct_answers INTEGER DEFAULT 0")


        # Commit all changes
        self.conn.commit()

    def get_due_words(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            SELECT 'due' AS word_type, w.id, w.spanish, w.english, w.correct_answers, w.image_path,
                   p.interval, p.repetitions, p.ease_factor, p.next_review_date
            FROM words w
            JOIN progress p ON w.id = p.word_id
            WHERE w.introduced = 1 AND p.next_review_date <= ?
        ''', (today,))
        return self.cursor.fetchall()

    def get_new_word(self):
        self.cursor.execute('''
            SELECT 'new' AS word_type, id, spanish, english, 0 AS correct_answers, image_path
            FROM words
            WHERE introduced = 0
            LIMIT 1
        ''')
        return self.cursor.fetchone()

    def get_words_in_session(self):
        self.cursor.execute('''
            SELECT 'in_session' AS word_type, id, spanish, english, correct_answers, image_path
            FROM words
            WHERE introduced = 1 AND correct_answers < 5
        ''')
        return self.cursor.fetchall()




    def mark_word_as_introduced(self, word_id):
        """Mark a word as introduced so it is not treated as a new word again."""
        self.cursor.execute('''
            UPDATE words
            SET introduced = 1
            WHERE id = ?
        ''', (word_id,))
        self.conn.commit()

    def log_response(self, word_id, correct):
        # Insert data into `response_history` without the `response` column
        response_date = datetime.date.today().isoformat()
        self.cursor.execute('''
            INSERT INTO response_history (word_id, response_date, correct)
            VALUES (?, ?, ?)
        ''', (word_id, response_date, int(correct)))
        self.conn.commit()

    def load_vocabulary_if_needed(self):
        self.cursor.execute('SELECT COUNT(*) FROM words')
        count = self.cursor.fetchone()[0]
        if count == 0:
            from vocabulary import load_vocabulary
            load_vocabulary('vocabulary.csv', self)
            print("Vocabulary loaded successfully!")

    def insert_progress(self, word_id, interval, repetitions, ease_factor, next_review_date, correct_answers):
        self.cursor.execute('''
            INSERT OR REPLACE INTO progress (
                word_id, interval, repetitions, ease_factor, next_review_date, correct_answers
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            word_id, interval, repetitions, ease_factor, next_review_date, correct_answers
        ))
        self.conn.commit()

    def insert_word(self, word):
        self.cursor.execute('''
            INSERT INTO words (spanish, english, level, image_path)
            VALUES (?, ?, ?, ?)
        ''', (word.spanish, word.english, word.level, word.image_path))
        self.conn.commit()

    def get_all_words(self):
        self.cursor.execute('SELECT id, spanish, english, image_path FROM words')
        return self.cursor.fetchall()


    def get_word_progress(self, word_id):
        self.cursor.execute('''
            SELECT interval, repetitions, ease_factor, next_review_date, correct_answers
            FROM progress
            WHERE word_id = ?
        ''', (word_id,))
        return self.cursor.fetchone()

    def update_word_progress(self, word_id, interval, repetitions, ease_factor, next_review_date, correct_answers):
        self.cursor.execute('''
            UPDATE progress
            SET interval = ?, repetitions = ?, ease_factor = ?, next_review_date = ?, correct_answers = ?
            WHERE word_id = ?
        ''', (interval, repetitions, ease_factor, next_review_date, correct_answers, word_id))
        self.conn.commit()

    def initialize_progress(self):
        words = self.get_all_words()
        for word in words:
            word_id = word[0]
            # Insert default progress only if it doesn't exist
            self.cursor.execute('''
                INSERT OR IGNORE INTO progress (
                    word_id, interval, repetitions, ease_factor, next_review_date, correct_answers
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                word_id, 1, 0, 2.5, datetime.date.today().isoformat(), 0
            ))
        self.conn.commit()

    def get_total_words(self):
        self.cursor.execute('SELECT COUNT(*) FROM words')
        return self.cursor.fetchone()[0]

    def get_mastered_words(self):
        self.cursor.execute('SELECT COUNT(*) FROM progress WHERE correct_answers >= ?', (5,))
        return self.cursor.fetchone()[0]


    def increment_correct_answers(self, word_id):
        """Increment correct answers for a word and mark it fully learned if it reaches 5."""
        self.cursor.execute('''
            UPDATE words
            SET correct_answers = correct_answers + 1
            WHERE id = ?
        ''', (word_id,))
        self.conn.commit()

    def get_any_review_word(self):
        """
        Retrieve any word that has been introduced (for review) regardless of due date.
        """
        self.cursor.execute('''
            SELECT 'due' AS word_type, id, spanish, english, correct_answers, image_path
            FROM words
            WHERE introduced = 1
            ORDER BY RANDOM()
            LIMIT 1
        ''')
        return self.cursor.fetchone()

    def get_random_word(self):
        """
        Retrieve any word from the database, ignoring its status.
        """
        self.cursor.execute('''
            SELECT 'random' AS word_type, id, spanish, english, correct_answers, image_path
            FROM words
            ORDER BY RANDOM()
            LIMIT 1
        ''')
        return self.cursor.fetchone()

    def get_word_performance_history(self, word_id):
        """Fetch performance history for a specific word, including dates and counts of correct/incorrect responses."""
        self.cursor.execute('''
            SELECT response_date, 
                   SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN correct = 0 THEN 1 ELSE 0 END) AS incorrect_count
            FROM response_history
            WHERE word_id = ?
            GROUP BY response_date
            ORDER BY response_date
        ''', (word_id,))
        return self.cursor.fetchall()







