import tkinter as tk
from tkinter import messagebox, font
from matplotlib import pyplot as plt
from tkinter import ttk
from database import Database
from vocabulary import Word
from spaced_repetition import SpacedRepetitionScheduler
import datetime
import random
from PIL import Image, ImageTk
import os


class VocabularyApp:
    def __init__(self):
        self.db = Database()
        self.scheduler = SpacedRepetitionScheduler(self.db)
        self.root = tk.Tk()
        self.root.title("Spanish Vocabulary App")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        self.default_font = font.Font(size=14)
        self.setup_main_menu()
        self.session_stats = {'new_words': 0, 'words_progressed': 0}

        # New word introduction tracking
        self.max_new_words_in_a_row = 5
        self.max_new_words_per_minute = 10
        self.new_words_introduced = 0
        self.new_words_in_last_minute = 0
        self.last_minute_start_time = datetime.datetime.now()
        self.practice_end_time = 0

    def setup_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        welcome_label = tk.Label(
            self.root,
            text="Welcome to the Spanish Vocabulary App",
            font=("Helvetica", 24),
            bg="#f0f0f0",
            fg="#333"
        )
        welcome_label.pack(pady=20)

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Take Level Test",
            font=self.default_font,
            command=self.start_level_test,
            width=20,
            bg="#4CAF50",
            fg="black"
        ).pack(pady=10)

        tk.Button(
            btn_frame,
            text="Practice Vocabulary",
            font=self.default_font,
            command=self.setup_practice_options,
            width=20,
            bg="#2196F3",
            fg="black"
        ).pack(pady=10)

        tk.Button(
            btn_frame,
            text="Visualize Progress",
            font=self.default_font,
            command=self.visualize_progress,
            width=20,
            bg="#FF9800",
            fg="black"
        ).pack(pady=10)

        tk.Button(
            btn_frame,
            text="Exit",
            font=self.default_font,
            command=self.root.quit,
            width=20,
            bg="#f44336",
            fg="black"
        ).pack(pady=10)

    def start_level_test(self):
        # For simplicity, we'll assume the user is at level A1
        messagebox.showinfo("Level Test", "Level Test is under development.\nAssuming level A1 for now.")
        # Load vocabulary for level A1
        self.db.initialize_progress()

    def setup_practice_options(self):
        self.options_window = tk.Toplevel(self.root)
        self.options_window.title("Practice Options")
        self.options_window.geometry("400x300")
        self.options_window.configure(bg="#f0f0f0")

        tk.Label(
            self.options_window,
            text="Set Practice Time (minutes):",
            font=self.default_font,
            bg="white",
            fg="black"
        ).pack(pady=20)

        self.time_entry = tk.Entry(self.options_window, font=self.default_font)
        self.time_entry.insert(0, "15")
        self.time_entry.pack(pady=10)

        tk.Label(
            self.options_window,
            text="Research suggests sessions between 10-20 minutes.",
            font=self.default_font,
            bg="white",
            fg="black"
        ).pack(pady=5)

        tk.Button(
            self.options_window,
            text="Start Practice",
            font=self.default_font,
            command=self.start_vocab_practice,
            bg="#4CAF50",
            fg="black"
        ).pack(pady=20)

    def start_vocab_practice(self):
        time_str = self.time_entry.get()
        try:
            self.practice_time = int(time_str) * 60
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of minutes.")
            return

        self.options_window.destroy()
        self.practice_window = tk.Toplevel(self.root)
        self.practice_window.title("Vocabulary Practice")
        self.practice_window.geometry("600x600")
        self.practice_window.configure(bg="#f0f0f0")

        self.timer_var = tk.StringVar()
        self.timer_var.set(str(datetime.timedelta(seconds=self.practice_time)))
        self.timer_label = tk.Label(
            self.practice_window,
            textvariable=self.timer_var,
            font=self.default_font,
            bg="#f0f0f0",
            fg="black"
        )
        self.timer_label.pack()

        self.content_frame = tk.Frame(self.practice_window, bg="#f0f0f0")
        self.content_frame.pack(fill='both', expand=True)

        self.practice_end_time = datetime.datetime.now() + datetime.timedelta(seconds=self.practice_time)
        self.update_timer()
        self.next_word()

    def update_timer(self):
        remaining_time = self.practice_end_time - datetime.datetime.now()
        remaining_seconds = int(remaining_time.total_seconds())

        if remaining_seconds <= 0:
            self.timer_var.set("Time's up!")
            self.timer_label.config(fg='black')
            # No need to schedule next update
            return
        else:
            if remaining_seconds <= 60:
                # Less than or equal to 30 seconds left
                self.timer_label.config(fg='red')
                self.timer_var.set(f'{remaining_seconds} seconds left')
            else:
                minutes_left = remaining_seconds // 60
                self.timer_label.config(fg='black')
                self.timer_var.set(f'{minutes_left} minutes left')
            # Schedule next update after 1 second
            self.practice_window.after(1000, self.update_timer)

    def next_word(self):
        if datetime.datetime.now() >= self.practice_end_time:
            self.show_session_report()
            return

        # Determine if the next word should be new or review based on user’s performance

        review_chance = 1/((self.session_stats['words_progressed'])*.025 +1)

        # Use probabilistic choice for new or review
        if random.random() < review_chance:
            word_data = self.scheduler.get_due_word(ignore_due_date=True)
        else:
            word_data = self.scheduler.get_next_word()

        # If no word was found, ensure fallback to any word available for practice
        if not word_data:
            word_data = self.scheduler.get_any_word()

        # Display the word data
        if word_data:
            self.display_word(word_data)
        else:
            self.show_session_report()

    def display_word(self, word_data):
        try:
            word_type, word_id, spanish, english, correct_answers, image_path, interval, repetitions, ease_factor, next_review_date = word_data
        except ValueError:
            word_type, word_id, spanish, english, correct_answers, image_path = word_data

        self.current_word = Word(spanish, english, word_id=word_id, image_path=image_path)
        self.correct_answers = correct_answers

        if word_type == 'new':
            self.show_new_word(self.current_word)
        elif word_type in ('due', 'in_session'):
            if correct_answers < 4:
                self.show_multiple_choice(self.current_word)
            else:
                self.show_word_written(self.current_word)

    def show_new_word(self, word):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if hasattr(self, "image_label"):
            self.image_label.destroy()

        tk.Label(
            self.content_frame,
            text="New Word Introduction",
            font=("Helvetica", 18),
            bg="#f0f0f0",
            fg="#333"
        ).pack(pady=10)

        if word.image_path:
            try:
                image_path = word.image_path
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    img = img.resize((200, 200))
                    photo = ImageTk.PhotoImage(img)
                    self.image_label = tk.Label(self.practice_window, image=photo, bg="#f0f0f0")
                    self.image_label.image = photo
                    self.image_label.pack(pady=10)
                else:
                    print(f"Image file not found: {image_path}")
            except Exception as e:
                print(f"Error loading image: {e}")

        tk.Label(
            self.content_frame,
            text=f"{word.spanish} - {word.english}",
            font=("Helvetica", 32),
            bg="#f0f0f0",
            fg="#000"
        ).pack(pady=20)

        btn_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Know This",
            font=self.default_font,
            command=self.know_this_word,
            bg="#4CAF50",
            fg="black"
        ).pack(side='left', padx=10)

        tk.Button(
            btn_frame,
            text="Don't Know",
            font=self.default_font,
            command=self.dont_know_word,
            bg="#f44336",
            fg="black"
        ).pack(side='left', padx=10)


    def show_multiple_choice(self, word):
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.image_label.destroy() if hasattr(self, "image_label") else None


        tk.Label(
            self.content_frame,
            text="Select the correct Spanish translation:",
            font=("Helvetica", 18),
            bg="#f0f0f0",
            fg="#333"
        ).pack(pady=10)

        tk.Label(
            self.content_frame,
            text=word.english,
            font=("Helvetica", 24),
            bg="#f0f0f0",
            fg="black"
        ).pack(pady=20)

        # Generate multiple choices
        choices = self.generate_choices(word.spanish)
        random.shuffle(choices)

        self.choice_var = tk.StringVar()

        for choice in choices:
            tk.Radiobutton(
                self.content_frame,
                text=choice,
                variable=self.choice_var,
                value=choice,
                font=self.default_font,
                bg="#f0f0f0",
                fg="black"
            ).pack(anchor='w', padx=20)

        tk.Button(
            self.content_frame,
            text="Submit",
            font=self.default_font,
            command=self.check_multiple_choice,
            bg="#2196F3",
            fg="black"
        ).pack(pady=20)

    def generate_choices(self, correct_spanish):
        all_words = self.db.get_all_words()
        choices = [correct_spanish]
        while len(choices) < 4:
            word = random.choice(all_words)
            spanish = word[1]
            if spanish not in choices:
                choices.append(spanish)
        return choices

    def check_multiple_choice(self):
        selected = self.choice_var.get()
        is_correct = (selected == self.current_word.spanish)

        # Display the image for the word after the answer
        if self.current_word.image_path:
            try:
                image_path = self.current_word.image_path
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    img = img.resize((200, 200))  # Resize for display
                    photo = ImageTk.PhotoImage(img)

                    # Display the image in the content frame
                    if hasattr(self, "image_label") and self.image_label:
                        self.image_label.destroy()  # Destroy previous image if it exists
                    self.image_label = tk.Label(self.practice_window, image=photo, bg="#f0f0f0")
                    self.image_label.image = photo  # Keep a reference to prevent garbage collection
                    self.image_label.pack(pady=10)
                else:
                    print(f"Image file not found: {image_path}")
            except Exception as e:
                print(f"Error loading image: {e}")

        # Set quality and correctness based on the answer
        if is_correct:
            feedback_message = "Correct!"
            quality = 5
            correct = True
            self.session_stats['new_words'] += 1
            self.session_stats['words_progressed'] += 1
        else:
            feedback_message = f"Incorrect. The correct answer is: {self.current_word.spanish}"
            quality = 2
            correct = False

        # Log response in the database
        self.db.log_response(self.current_word.word_id, correct)

        # Update word progress based on the response quality
        self.practice_window.after(100, lambda: messagebox.showinfo("Result", feedback_message))

        self.scheduler.update_progress(self.current_word.word_id, quality, correct)

        # Delay to let user see feedback and move to the next word
        self.practice_window.after(100, self.next_word)

    def show_word_written(self, word):
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.content_frame,
            text="Translate to Spanish:",
            font=("Helvetica", 18),
            bg="#f0f0f0",
            fg="#333"
        ).pack(pady=10)

        tk.Label(
            self.content_frame,
            text=word.english,
            font=("Helvetica", 32),
            bg="#f0f0f0",
            fg="#000"
        ).pack(pady=20)

        self.answer_entry = tk.Entry(self.content_frame, font=("Helvetica", 24))
        self.answer_entry.pack(pady=10)
        self.answer_entry.focus_set()

        tk.Button(
            self.content_frame,
            text="Submit",
            font=self.default_font,
            command=self.check_answer_written,
            bg="#2196F3",
            fg="black"
        ).pack(pady=20)

    def check_answer_written(self):
        user_answer = self.answer_entry.get().strip().lower()
        correct_answer = self.current_word.spanish.lower()

        if self.current_word.image_path:
            try:
                image_path = self.current_word.image_path
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    img = img.resize((200, 200))  # Resize for display
                    photo = ImageTk.PhotoImage(img)

                    # Display the image in the content frame
                    if hasattr(self, "image_label") and self.image_label:
                        self.image_label.destroy()  # Destroy previous image if it exists
                    self.image_label = tk.Label(self.practice_window, image=photo, bg="#f0f0f0")
                    self.image_label.image = photo  # Keep a reference to prevent garbage collection
                    self.image_label.pack(pady=10)
                else:
                    print(f"Image file not found: {image_path}")
            except Exception as e:
                print(f"Error loading image: {e}")

        if user_answer == correct_answer:
            messagebox.showinfo("Result", "Correct!")
            quality = 5
            correct = True
            self.session_stats['words_progressed'] += 1
        else:
            messagebox.showinfo("Result", f"Incorrect. The correct answer is: {self.current_word.spanish}")
            quality = 2
            correct = False
        self.db.log_response(self.current_word.word_id, correct)

        # Update word progress based on the response quality
        self.scheduler.update_progress(self.current_word.word_id, quality, correct)

        # Move to the next word
        self.practice_window.after(100, self.next_word)

    def show_session_report(self):
        total_words = self.db.get_total_words()
        mastered_words = self.db.get_mastered_words()
        percent_learned = (mastered_words / total_words) * 100 if total_words > 0 else 0

        report_message = (
            f"Session Report:\n\n"
            f"New words learned: {self.session_stats['new_words']}\n"
            f"Words progressed: {self.session_stats['words_progressed']}\n"
            f"Total words mastered: {mastered_words}/{total_words}\n"
            f"Current level learned: {percent_learned:.2f}%"
        )

        messagebox.showinfo("Session Report", report_message)
        self.practice_window.destroy()
        self.setup_main_menu()

    def run(self):
        self.root.mainloop()

    def know_this_word(self):
        # Set correct_answers to the threshold (e.g., 5) to mark as mastered
        correct_answers = 5  # Threshold for mastery
        interval = 3  # Next review in 30 days
        repetitions = 5
        ease_factor = 2.5
        next_review_date = datetime.date.today() + datetime.timedelta(days=interval)
        next_review_date_str = next_review_date.isoformat()

        # Update progress in the database
        self.db.insert_progress(
            self.current_word.word_id,
            interval,
            repetitions,
            ease_factor,
            next_review_date_str,
            correct_answers
        )

        messagebox.showinfo("Word Known", f"Great! '{self.current_word.spanish}' marked as known.")
        self.next_word()

    def dont_know_word(self):
        # Initialize progress for the word
        correct_answers = 0
        interval = 1
        repetitions = 0
        ease_factor = 2.5
        next_review_date = datetime.date.today().isoformat()

        self.db.insert_progress(
            self.current_word.word_id,
            interval,
            repetitions,
            ease_factor,
            next_review_date,
            correct_answers
        )

        messagebox.showinfo("Word Added", f"'{self.current_word.spanish}' added to your learning queue.")
        self.next_word()

    def visualize_progress(self):
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Progress Visualization")
        progress_window.geometry("700x500")

        # Create a Canvas for scrolling
        canvas = tk.Canvas(progress_window)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a vertical scrollbar linked to the Canvas
        scrollbar = tk.Scrollbar(progress_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        # Create a frame within the canvas to hold the progress bars
        progress_frame = tk.Frame(canvas)

        # Update the canvas to scroll with the scrollbar
        canvas.create_window((0, 0), window=progress_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add all word progress bars to the frame
        words = self.db.get_all_words()
        for word_id, spanish, english, image_path in words:
            progress_bar_frame = tk.Frame(progress_frame)
            progress_bar_frame.pack(fill="x", pady=5, padx=10)

            word_label = tk.Label(progress_bar_frame, text=f"{spanish} - {english}", font=self.default_font)
            word_label.pack(side="left", padx=5)

            # Get progress and set the bar value based on the mastery level (out of 5)
            word_progress = self.db.get_word_progress(word_id)
            if word_progress:
                correct_answers = word_progress[4] if word_progress[4] is not None else 0
                progress_value = correct_answers  # Value should directly represent progress towards 5 correct answers
            else:
                progress_value = 0

            # Create and place the progress bar with a maximum of 5
            progress_bar = ttk.Progressbar(progress_bar_frame, length=200, mode='determinate', maximum=5)
            progress_bar['value'] = progress_value/20
            progress_bar.pack(side="left", padx=5)

            # Add button to view detailed word performance
            view_button = tk.Button(
                progress_bar_frame, text="View", font=self.default_font,
                command=lambda w_id=word_id: self.show_word_performance(w_id)
            )
            view_button.pack(side="left", padx=5)

        # Configure scrolling region
        progress_frame.update_idletasks()  # Ensure frame has updated height
        canvas.config(scrollregion=canvas.bbox("all"))  # Define scrollable region

    def show_word_performance(self, word_id):
        # Fetch performance data from the database
        performance_data = self.db.get_word_performance_history(word_id)
        dates = [data[0] for data in performance_data]
        correct_counts = [data[1] for data in performance_data]
        incorrect_counts = [data[2] for data in performance_data]

        # Calculate cumulative correct and incorrect counts
        cumulative_correct = [sum(correct_counts[:i + 1]) for i in range(len(correct_counts))]
        cumulative_incorrect = [sum(incorrect_counts[:i + 1]) for i in range(len(incorrect_counts))]

        # Set up the plot with a secondary y-axis for mastery percentage
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Plot cumulative correct and incorrect responses on the primary y-axis
        ax1.plot(dates, cumulative_correct, label="Cumulative Correct", color="green")
        ax1.plot(dates, cumulative_incorrect, label="Cumulative Incorrect", color="red")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Total Responses")
        ax1.set_title("Performance Over Time")

        # Secondary y-axis for mastery level percentage
        mastery_threshold = 5  # Define mastery threshold (e.g., 5 correct answers for mastery)
        ax2 = ax1.twinx()  # Instantiate a second y-axis that shares the same x-axis
        mastery_percentage = [(correct / 20)*100 for correct in cumulative_correct]
        ax2.plot(dates, mastery_percentage, label="Mastery Level (%)", color="blue", linestyle="--")
        ax2.set_ylabel("Mastery Level (%)")
        ax2.set_ylim(0, 100)  # Set limits from 0 to 100%

        # Add horizontal reference line for 100% mastery on the right y-axis

        # Combine legends from both axes
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc="upper left")

        plt.tight_layout()
        plt.show()



