import tkinter as tk
import requests 
from bs4 import BeautifulSoup
from tkinter import messagebox, simpledialog
import random
import cv2
import serial
import time
import numpy as np
import threading
import pyttsx3
import pygame
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxx usb xxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxx usb xxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxx usb xxxxxxxxxxxxxxxxxxxxxxxxx
# Initialize the serial connection
# ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)  # Wait for the connection to establish

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Initialize pygame for PS4 controller
pygame.init()
pygame.joystick.init()

# Global variable to control the mode
mode = "STOP"
running = False

# Function to send command to ESP32
def send_command(command):
    ser.write((command + '\n').encode())
    time.sleep(0.1)  # Small delay to ensure command is sent

# Function to handle color following mode
import cv2
import numpy as np
from tkinter import messagebox

def color_following():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Could not open video stream")
        return

    lower_green = np.array([40, 70, 70])
    upper_green = np.array([80, 255, 255])

    global running
    running = True

    try:
        while mode == "COLOR_FOLLOW" and running:
            ret, frame = cap.read()
            if not ret:
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower_green, upper_green)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Find the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                contour_area = cv2.contourArea(largest_contour)

                # Consider the object valid only if it's larger than a minimum size
                min_area_threshold = 500  # Adjust this threshold based on your environment
                if contour_area > min_area_threshold:
                    # Calculate the moments of the largest contour
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)

                        # Draw the contour and bounding box around the object
                        cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                        x, y, w, h = cv2.boundingRect(largest_contour)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                        height, width, _ = frame.shape
                        centerX = width // 2

                        if cX < centerX - 50:
                            send_command('LEFT')
                        elif cX > centerX + 50:
                            send_command('RIGHT')
                        else:
                            send_command('GO')
                    else:
                        send_command('STOP')
                else:
                    send_command('STOP')  # Object is too small, stop the robot
            else:
                send_command('STOP')  # No contours found, stop the robot

            cv2.imshow('Robot Camera Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()




# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#  Function to handle PS4 controller mode
def ps4_controller():
    global running
    tts_engine.say("PS4 Controller mode activated")
    tts_engine.runAndWait()
    messagebox.showinfo("Info", "PS4 Controller mode activated")

    # Initialize PS4 controller
    if pygame.joystick.get_count() < 1:
        tts_engine.say("No PS4 controller found")
        tts_engine.runAndWait()
        messagebox.showerror("Error", "No PS4 controller found")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    global mode
    running = True

    try:
        while mode == "PS4_CONTROLLER" and running:
            pygame.event.pump()
            x_axis = joystick.get_axis(0)
            y_axis = joystick.get_axis(1)
            button_r1 = joystick.get_button(5)  # Example button mapping for GO
            button_l1 = joystick.get_button(4)  # Example button mapping for STOP

            if button_r1:
                send_command('GO')
            elif button_l1:
                send_command('BACKWARD')
            elif x_axis < -0.5:
                send_command('LEFT')
            elif x_axis > 0.5:
                send_command('RIGHT')
            elif y_axis > 0.5:
                send_command('FORWARD')
            elif y_axis < -0.5: 
                send_command('STOP')
            else:
                send_command('STOP')

            time.sleep(0.1)  # Delay to reduce CPU usage
    finally:
        joystick.quit()

# Function to display the robot face
def robot_face():
    running = True
    blink_time = 0
    blink_interval = 3  # seconds

    screen_width = 1920
    screen_height = 1080
    screen = pygame.display.set_mode((screen_width, screen_height))

    eye_color = (255, 0, 255)
    eye_radius = 80
    eye_center_left = (screen_width // 3, screen_height // 2)
    eye_center_right = (2 * screen_width // 3, screen_height // 2)

    def draw_eye(center, open=True):
        pygame.draw.circle(screen, eye_color, center, eye_radius)
        if not open:
            pygame.draw.rect(screen, (0, 0, 0), (center[0] - eye_radius, center[1] - eye_radius // 2, eye_radius * 2, eye_radius))

    def blink():
        draw_eye(eye_center_left, open=False)
        draw_eye(eye_center_right, open=False)
        pygame.display.flip()
        time.sleep(0.1)
        draw_eye(eye_center_left, open=True)
        draw_eye(eye_center_right, open=True)
        pygame.display.flip()

    while running and mode == "FREE_ROAM":
    
        screen.fill((0, 0, 0))
        draw_eye(eye_center_left)
        draw_eye(eye_center_right)
        pygame.display.flip()

        current_time = time.time()
        if current_time - blink_time >= blink_interval:
            blink()
            blink_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

# Function to handle free roam mode
def free_roam():
    threading.Thread(target=robot_face).start()  # Start the face display in a new thread
    send_command('GO')
    time.sleep(1)
    send_command('STOP')
    send_command('GO')
    time.sleep(1)
    send_command('RIGHT')
    time.sleep(1)
    send_command('GO')
    time.sleep(1)
    send_command('RIGHT')
    time.sleep(1)
    send_command('GO')
    time.sleep(1)
    send_command('RIGHT')
    time.sleep(1)
    send_command('STOP')

# Function to handle ROS mode
def ros_mode():
    tts_engine.say("ROS mode coming soon")
    tts_engine.runAndWait()
    messagebox.showinfo("Info", "ROS mode is still under construction")

# Function to handle chat with me mode
def chat_with_me():
    tts_engine.say("Let's Enjoy the Chats and Games")
    tts_engine.runAndWait()
    
    # Function to ask questions
    def ask_question(question):
        tts_engine.say(question)
        tts_engine.runAndWait()
        return simpledialog.askstring("Input", question)

    # Function to display a physical menu and get user's choice
    def display_menu():
        menu = (
            "1. Guess the Number\n"
            "2. Trivia Game\n"
            "3. Math Game\n"
            "4. Word Guessing Game\n"
            "5. Yes or No Game\n"
            "6. Riddles\n"
            "7. Rock Paper Scissors\n"
            "8. Memory Game\n"
            "Please enter the number of your choice:"
        )
        tts_engine.say(menu)
        tts_engine.runAndWait()
        return simpledialog.askstring("Game Menu", menu)

    # Function to play a number guessing game with levels
    def guess_number_game():
        tts_engine.say("Let's start the Number Guessing Game!")
        tts_engine.runAndWait()
        
        for level in range(1, 11):
            max_number = 10 * level
            number_to_guess = random.randint(1, max_number)
            attempts = level + 2  # Increase attempts with each level
            tts_engine.say(f"Level {level}: Guess the number between 1 and {max_number}. You have {attempts} attempts.")
            tts_engine.runAndWait()
            
            while attempts > 0:
                guess = simpledialog.askinteger("Guess the Number", f"Enter your guess (1-{max_number}):")
                if guess is None:
                    return
                attempts -= 1
                
                if guess < number_to_guess:
                    tts_engine.say(f"Too low! You have {attempts} attempts left.")
                    tts_engine.runAndWait()
                elif guess > number_to_guess:
                    tts_engine.say(f"Too high! You have {attempts} attempts left.")
                    tts_engine.runAndWait()
                else:
                    tts_engine.say(f"Correct! You've guessed the number in {level + 2 - attempts} attempts.")
                    tts_engine.runAndWait()
                    break
            else:
                tts_engine.say(f"Sorry, you've run out of attempts. The number was {number_to_guess}.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play a trivia game with levels
    def trivia_game():
        tts_engine.say("Let's start the Trivia Game!")
        tts_engine.runAndWait()
        
        trivia_questions = [
        
            {"question": "What is the capital of Zambia?", "answer": "Lusaka"},
            {"question": "Who when did Zambia get independence?", "answer": "1964"},
            {"question": "Who wrote 'Romeo and Juliet'?", "answer": "Shakespeare"},
            {"question": "What planet is known as the Red Planet?", "answer": "Mars"},
            {"question": "What is the largest ocean on Earth?", "answer": "Pacific Ocean"}
        ]
        
        for level in range(1, 11):
            question_data = random.choice(trivia_questions)
            tts_engine.say(f"Level {level}: {question_data['question']}")
            tts_engine.runAndWait()
            
            user_answer = simpledialog.askstring("Trivia Question", question_data['question'])
            if user_answer and user_answer.lower() == question_data['answer'].lower():
                tts_engine.say("Correct!")
                tts_engine.runAndWait()
            else:
                tts_engine.say(f"Sorry, the correct answer was {question_data['answer']}.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play a math game with levels
    def math_game():
        tts_engine.say("Let's start the Math Game!")
        tts_engine.runAndWait()
        
        for level in range(1, 11):
            num1 = random.randint(1, 10 * level)
            num2 = random.randint(1, 10 * level)
            correct_answer = num1 + num2
            tts_engine.say(f"Level {level}: What is {num1} plus {num2}?")
            tts_engine.runAndWait()
            
            user_answer = simpledialog.askinteger("Math Game", f"What is {num1} + {num2}?")
            if user_answer == correct_answer:
                tts_engine.say("Correct!")
                tts_engine.runAndWait()
            else:
                tts_engine.say(f"Sorry, the correct answer was {correct_answer}.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play a word guessing game with levels
    def word_guessing_game():
        tts_engine.say("Let's start the Word Guessing Game!")
        tts_engine.runAndWait()
        
        words = ["python", "robot", "programming", "machine", "engineer", "technology", "data", "science", "algorithm", "development"]
        
        for level in range(1, 11):
            word_to_guess = random.choice(words)
            guessed_letters = set()
            attempts = 10 - level  # Decrease attempts with each level
            
            while attempts > 0:
                display_word = " ".join(letter if letter in guessed_letters else "_" for letter in word_to_guess)
                tts_engine.say(f"Level {level}: Word to guess: {display_word}")
                tts_engine.runAndWait()
                guess = simpledialog.askstring("Guess a Letter", "Enter a letter:")
                
                if guess and len(guess) == 1:
                    if guess in word_to_guess:
                        guessed_letters.add(guess)
                        tts_engine.say("Correct letter!")
                        tts_engine.runAndWait()
                    else:
                        attempts -= 1
                        tts_engine.say(f"Incorrect letter! You have {attempts} attempts left.")
                        tts_engine.runAndWait()
                    if set(word_to_guess) == guessed_letters:
                        tts_engine.say(f"Congratulations! You've guessed the word '{word_to_guess}'.")
                        tts_engine.runAndWait()
                        break
                else:
                    tts_engine.say("Please enter a single letter.")
                    tts_engine.runAndWait()
            else:
                tts_engine.say(f"Sorry, you ran out of attempts. The word was '{word_to_guess}'.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play a yes/no game with levels
    def yes_no_game():
        tts_engine.say("Let's start the Yes/No Game!")
        tts_engine.runAndWait()
        
        questions = [
            "Is the sky blue?",
            "Can birds fly?",
            "Is water dry?",
            "Do fish swim in water?",
            "Is the sun hot?",
            "Can humans breathe underwater?",
            "Is ice cold?",
            "Do cars drive on roads?",
            "Can you touch the sky?",
            "Is fire hot?"
        ]
        
        for level in range(1, 11):
            question = random.choice(questions)
            tts_engine.say(f"Level {level}: {question}")
            tts_engine.runAndWait()
            
            user_answer = simpledialog.askstring("Yes/No Question", question).strip().lower()
            if user_answer in ["yes", "no"]:
                tts_engine.say("Thank you for your answer!")
                tts_engine.runAndWait()
            else:
                tts_engine.say("Please answer with 'yes' or 'no'.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play a riddle game with levels
    def riddles_game():
        tts_engine.say("Let's start the Riddles Game!")
        tts_engine.runAndWait()
        
        riddles = [
            {"riddle": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "answer": "Echo"},
            {"riddle": "I can be cracked, made, told, and played. What am I?", "answer": "Joke"},
            {"riddle": "The more you take, the more you leave behind. What am I?", "answer": "Footsteps"},
            {"riddle": "What has keys but can’t open locks?", "answer": "Piano"},
            {"riddle": "What has to be broken before you can use it?", "answer": "Egg"},
            {"riddle": "What gets wetter as it dries?", "answer": "Towel"},
            {"riddle": "What has a thumb and four fingers but is not alive?", "answer": "Glove"},
            {"riddle": "What is full of holes but still holds water?", "answer": "Sponge"},
            {"riddle": "What goes up but never comes down?", "answer": "Age"},
            {"riddle": "What can travel around the world while staying in a corner?", "answer": "Stamp"},
            {"riddle": "What has a heart that doesn’t beat?", "answer": "Artichoke"},
            {"riddle": "What has many teeth but can’t bite?", "answer": "Comb"}
        ]
        
        for level in range(1, 11):
            riddle = random.choice(riddles)
            tts_engine.say(f"Level {level}: {riddle['riddle']}")
            tts_engine.runAndWait()
            
            user_answer = simpledialog.askstring("Riddle", riddle['riddle']).strip().lower()
            if user_answer == riddle['answer'].lower():
                tts_engine.say("Correct!")
                tts_engine.runAndWait()
            else:
                tts_engine.say(f"Sorry, the correct answer was '{riddle['answer']}'.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play Rock Paper Scissors with levels
    def rock_paper_scissors():
        tts_engine.say("Let's play Rock Paper Scissors!")
        tts_engine.runAndWait()
        
        choices = ["rock", "paper", "scissors"]
        for level in range(1, 11):
            user_choice = simpledialog.askstring("Rock Paper Scissors", "Enter rock, paper, or scissors:").strip().lower()
            if user_choice not in choices:
                tts_engine.say("Invalid choice. Please choose rock, paper, or scissors.")
                tts_engine.runAndWait()
                continue
                
            computer_choice = random.choice(choices)
            tts_engine.say(f"Computer chose {computer_choice}.")
            tts_engine.runAndWait()
            
            if user_choice == computer_choice:
                result = "It's a tie!"
            elif (user_choice == "rock" and computer_choice == "scissors") or \
                 (user_choice == "paper" and computer_choice == "rock") or \
                 (user_choice == "scissors" and computer_choice == "paper"):
                result = "You win!"
            else:
                result = "You lose!"
            
            tts_engine.say(f"Level {level}: {result}")
            tts_engine.runAndWait()
            
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to play a memory game with levels
    def memory_game():
        tts_engine.say("Let's start the Memory Game!")
        tts_engine.runAndWait()
        
        for level in range(1, 11):
            items = [f"Item {i}" for i in range(1, 10 + level)]
            random.shuffle(items)
            displayed_items = items[:level + 2]
            tts_engine.say(f"Level {level}: Memorize these items: {', '.join(displayed_items)}")
            tts_engine.runAndWait()
            
            # Hide items
            simpledialog.messagebox.showinfo("Memory Game", "Memorize the items quickly!")
            simpledialog.messagebox.showinfo("Memory Game", "Items hidden. Try to recall them.")
            
            user_recall = simpledialog.askstring("Memory Game", "Enter the items you remember separated by commas:")
            user_recall_list = [item.strip() for item in user_recall.split(",")]
            
            if sorted(user_recall_list) == sorted(displayed_items):
                tts_engine.say(f"Level {level}: Correct!")
                tts_engine.runAndWait()
            else:
                tts_engine.say(f"Level {level}: Sorry, you remembered: {', '.join(user_recall_list)}. The correct items were: {', '.join(displayed_items)}.")
                tts_engine.runAndWait()
                
            # Ask if they want to proceed to the next level
            proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
            if proceed.lower() != "yes":
                break

    # Function to save user responses to a file
    def save_to_file(filename, data):
        with open(filename, "w") as file:
            file.write(data)
    
    # Start conversation with basic questions
    name = ask_question("What is your name?")
    age = ask_question("How old are you?")
    hobbies = ask_question("What are your hobbies?")
    feature_suggestions = ask_question("What features would you like to see on the robot?")

    # Prepare the content to be saved
    user_data = (
        f"Name: {name}\n"
        f"Age: {age}\n"
        f"Hobbies: {hobbies}\n"
        f"Feature Suggestions: {feature_suggestions}\n\n"
    )
    
    # Ask if the user wants to play games
    play_games = ask_question("Would you like to play some games? (yes or no)")
    if play_games.lower() == "yes":
        # Offer to play a game
        while True:
            menu_choice = display_menu()
            game_functions = {
                "1": guess_number_game,
                "2": trivia_game,
                "3": math_game,
                "4": word_guessing_game,
                "5": yes_no_game,
                "6": riddles_game,
                "7": rock_paper_scissors,
                "8": memory_game
            }
            
            if menu_choice in game_functions:
                game_functions[menu_choice]()
            else:
                tts_engine.say("Sorry, I didn't understand your choice.")
                tts_engine.runAndWait()
            
            # Ask if the user wants to play more
            play_more = ask_question("Would you like to play another game? (yes/no)")
            if play_more.lower() != "yes":
                break

    # Say something random and offer a survey
    tts_engine.say("I enjoyed playing with you!")
    tts_engine.runAndWait()
    survey_choice = ask_question("Would you like to take a survey? (yes or no)")
    
    if survey_choice.lower() == "yes":
        survey_answers = conduct_survey()
        user_data += "\nSurvey Responses:\n"
        for question, answer in survey_answers:
            user_data += f"{question}: {answer}\n"

    # Thank the user and suggest donation
    donation_message = "Thank you for your interest! If you would like to support our work, consider donating to the numbers.\n Airtel: 0 9 7 4 9 8 3 5 5 5 \n MTN:   0 9 6 7 6 8 9 5 7 2"
    tts_engine.say(donation_message)
    tts_engine.runAndWait()
    messagebox.showinfo("Support Our Work", donation_message)
    
    # Save all responses to a file named after the person
    filename = f"{name.replace(' ', '_')}_responses.txt"
    save_to_file(filename, user_data)

# Run the chat function in a separate thread to avoid blocking the main thread
thread = threading.Thread(target=chat_with_me)

# Picture taking 
def take_picture():
    beautify_comments = [
        "You're looking fabulous today!",
        "Get ready to shine like a star!",
        "This photo is going to be legendary!",
        "Your smile is brighter than the sun!",
        "Wow, you're glowing!",
        "Say cheese, superstar!",
        "Ready to capture that million-dollar smile?",
        "You're a natural in front of the camera!",
        "This picture will be one for the books!",
        "You're about to steal the show!"
    ]

    random_comment = random.choice(beautify_comments)
    tts_engine.say(random_comment)
    tts_engine.runAndWait()

    tts_engine.say("Are you sure you want to take a picture?")
    tts_engine.runAndWait()

    def confirm_picture():
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception("Could not open video stream")

            ret, frame = cap.read()
            if not ret:
                raise Exception("Failed to capture image")

            file_name = "captured_image.png"
            cv2.imwrite(file_name, frame)
            tts_engine.say(f"Picture taken and saved as {file_name}")
            tts_engine.runAndWait()
            cv2.imshow("Captured Image", frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            if cap is not None:
                cap.release()

        # Exit the function
        return

    if messagebox.askyesno("Take Picture", "Are you sure you want to take a picture?"):
        confirm_picture()
        # The function will return here, and the camera will be released


# Function to stop all activities
def stop_all():
    global running
    running = False
    send_command('STOP')
    tts_engine.say("All activities stopped")
    tts_engine.runAndWait()

# Function to start the chosen mode
def start_mode():
    global mode
    if mode == "COLOR_FOLLOW":
        threading.Thread(target=color_following).start()
    elif mode == "PS4_CONTROLLER":
        threading.Thread(target=ps4_controller).start()
    elif mode == "FREE_ROAM":
        threading.Thread(target=free_roam).start()
    elif mode == "ROS":
        threading.Thread(target=ros_mode).start()
    elif mode == "CHAT_WITH_ME":
        threading.Thread(target=chat_with_me).start()
    elif mode == "TAKE_PICTURE":
        threading.Thread(target=take_picture).start()
    else:
        messagebox.showerror("Error", "Invalid mode selected")

# Function to handle mode selection
def set_mode(new_mode):
    global mode
    mode = new_mode
    send_command('STOP')  # Ensure motors are stopped when changing modes
    stop_all()
    start_mode()

# Function to handle under construction response
def under_construction():
    tts_engine.say("This feature is under construction")
    tts_engine.runAndWait()
    messagebox.showinfo("Info", "This feature is under construction")


#  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx












































































# import tkinter as tk
# import requests 
# from bs4 import BeautifulSoup
# from tkinter import messagebox, simpledialog
# import random
# import cv2
# import serial
# import time
# import numpy as np
# import threading
# import pyttsx3
# import pygame


# # Function to send command to ESP32
# def send_command(command):
#     ser.write((command + '\n').encode())
#     time.sleep(0.1)  # Small delay to ensure command is sent

# # Function to handle color following mode
# import cv2
# import numpy as np
# from tkinter import messagebox

# def color_following():
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         messagebox.showerror("Error", "Could not open video stream")
#         return

#     lower_green = np.array([40, 70, 70])
#     upper_green = np.array([80, 255, 255])

#     global running
#     running = True

#     try:
#         while mode == "COLOR_FOLLOW" and running:
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
#             mask = cv2.inRange(hsv, lower_green, upper_green)
#             contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

#             if contours:
#                 # Find the largest contour
#                 largest_contour = max(contours, key=cv2.contourArea)
#                 contour_area = cv2.contourArea(largest_contour)

#                 # Consider the object valid only if it's larger than a minimum size
#                 min_area_threshold = 500  # Adjust this threshold based on your environment
#                 if contour_area > min_area_threshold:
#                     # Calculate the moments of the largest contour
#                     M = cv2.moments(largest_contour)
#                     if M["m00"] != 0:
#                         cX = int(M["m10"] / M["m00"])
#                         cY = int(M["m01"] / M["m00"])
#                         cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)

#                         # Draw the contour and bounding box around the object
#                         cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
#                         x, y, w, h = cv2.boundingRect(largest_contour)
#                         cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

#                         height, width, _ = frame.shape
#                         centerX = width // 2

#                         if cX < centerX - 50:
#                             send_command('LEFT')
#                         elif cX > centerX + 50:
#                             send_command('RIGHT')
#                         else:
#                             send_command('GO')
#                     else:
#                         send_command('STOP')
#                 else:
#                     send_command('STOP')  # Object is too small, stop the robot
#             else:
#                 send_command('STOP')  # No contours found, stop the robot

#             cv2.imshow('Robot Camera Feed', frame)
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#     except Exception as e:
#         messagebox.showerror("Error", f"An error occurred: {e}")
#     finally:
#         cap.release()
#         cv2.destroyAllWindows()


# # Function to handle PS4 controller mode
# def ps4_controller():
#     global running
#     tts_engine.say("PS4 Controller mode activated")
#     tts_engine.runAndWait()
#     messagebox.showinfo("Info", "PS4 Controller mode activated")

#     # Initialize PS4 controller
#     if pygame.joystick.get_count() < 1:
#         tts_engine.say("No PS4 controller found")
#         tts_engine.runAndWait()
#         messagebox.showerror("Error", "No PS4 controller found")
#         return

#     joystick = pygame.joystick.Joystick(0)
#     joystick.init()

#     global mode
#     running = True

#     try:
#         while mode == "PS4_CONTROLLER" and running:
#             pygame.event.pump()
#             x_axis = joystick.get_axis(0)
#             y_axis = joystick.get_axis(1)
#             button_r1 = joystick.get_button(5)  # Example button mapping for GO
#             button_l1 = joystick.get_button(4)  # Example button mapping for STOP

#             if button_r1:
#                 send_command('GO')
#             elif button_l1:
#                 send_command('BACKWARD')
#             elif x_axis < -0.5:
#                 send_command('LEFT')
#             elif x_axis > 0.5:
#                 send_command('RIGHT')
#             elif y_axis > 0.5:
#                 send_command('FORWARD')
#             elif y_axis < -0.5: 
#                 send_command('STOP')
#             else:
#                 send_command('STOP')

#             time.sleep(0.1)  # Delay to reduce CPU usage
#     finally:
#         joystick.quit()

# # Function to display the robot face
# def robot_face():
#     running = True
#     blink_time = 0
#     blink_interval = 3  # seconds

#     screen_width = 1920
#     screen_height = 1080
#     screen = pygame.display.set_mode((screen_width, screen_height))

#     eye_color = (255, 0, 255)
#     eye_radius = 80
#     eye_center_left = (screen_width // 3, screen_height // 2)
#     eye_center_right = (2 * screen_width // 3, screen_height // 2)

#     def draw_eye(center, open=True):
#         pygame.draw.circle(screen, eye_color, center, eye_radius)
#         if not open:
#             pygame.draw.rect(screen, (0, 0, 0), (center[0] - eye_radius, center[1] - eye_radius // 2, eye_radius * 2, eye_radius))

#     def blink():
#         draw_eye(eye_center_left, open=False)
#         draw_eye(eye_center_right, open=False)
#         pygame.display.flip()
#         time.sleep(0.1)
#         draw_eye(eye_center_left, open=True)
#         draw_eye(eye_center_right, open=True)
#         pygame.display.flip()

#     while running and mode == "FREE_ROAM":
    
#         screen.fill((0, 0, 0))
#         draw_eye(eye_center_left)
#         draw_eye(eye_center_right)
#         pygame.display.flip()

#         current_time = time.time()
#         if current_time - blink_time >= blink_interval:
#             blink()
#             blink_time = current_time

#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False

#     pygame.quit()

# # Function to handle free roam mode
# def free_roam():
#     threading.Thread(target=robot_face).start()  # Start the face display in a new thread
#     send_command('GO')
#     time.sleep(1)
#     send_command('STOP')
#     send_command('GO')
#     time.sleep(1)
#     send_command('RIGHT')
#     time.sleep(1)
#     send_command('GO')
#     time.sleep(1)
#     send_command('RIGHT')
#     time.sleep(1)
#     send_command('GO')
#     time.sleep(1)
#     send_command('RIGHT')
#     time.sleep(1)
#     send_command('STOP')

# # Function to handle ROS mode
# def ros_mode():
#     tts_engine.say("ROS mode coming soon")
#     tts_engine.runAndWait()
#     messagebox.showinfo("Info", "ROS mode is still under construction")

# # Function to handle chat with me mode
# def chat_with_me():
#     tts_engine.say("Let's Enjoy the Chats and Games")
#     tts_engine.runAndWait()
    
#     # Function to ask questions
#     def ask_question(question):
#         tts_engine.say(question)
#         tts_engine.runAndWait()
#         return simpledialog.askstring("Input", question)

#     # Function to display a physical menu and get user's choice
#     def display_menu():
#         menu = (
#             "1. Guess the Number\n"
#             "2. Trivia Game\n"
#             "3. Math Game\n"
#             "4. Word Guessing Game\n"
#             "5. Yes or No Game\n"
#             "6. Riddles\n"
#             "7. Rock Paper Scissors\n"
#             "8. Memory Game\n"
#             "Please enter the number of your choice:"
#         )
#         tts_engine.say(menu)
#         tts_engine.runAndWait()
#         return simpledialog.askstring("Game Menu", menu)

#     # Function to play a number guessing game with levels
#     def guess_number_game():
#         tts_engine.say("Let's start the Number Guessing Game!")
#         tts_engine.runAndWait()
        
#         for level in range(1, 11):
#             max_number = 10 * level
#             number_to_guess = random.randint(1, max_number)
#             attempts = level + 2  # Increase attempts with each level
#             tts_engine.say(f"Level {level}: Guess the number between 1 and {max_number}. You have {attempts} attempts.")
#             tts_engine.runAndWait()
            
#             while attempts > 0:
#                 guess = simpledialog.askinteger("Guess the Number", f"Enter your guess (1-{max_number}):")
#                 if guess is None:
#                     return
#                 attempts -= 1
                
#                 if guess < number_to_guess:
#                     tts_engine.say(f"Too low! You have {attempts} attempts left.")
#                     tts_engine.runAndWait()
#                 elif guess > number_to_guess:
#                     tts_engine.say(f"Too high! You have {attempts} attempts left.")
#                     tts_engine.runAndWait()
#                 else:
#                     tts_engine.say(f"Correct! You've guessed the number in {level + 2 - attempts} attempts.")
#                     tts_engine.runAndWait()
#                     break
#             else:
#                 tts_engine.say(f"Sorry, you've run out of attempts. The number was {number_to_guess}.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play a trivia game with levels
#     def trivia_game():
#         tts_engine.say("Let's start the Trivia Game!")
#         tts_engine.runAndWait()
        
#         trivia_questions = [
        
#             {"question": "What is the capital of Zambia?", "answer": "Lusaka"},
#             {"question": "Who when did Zambia get independence?", "answer": "1964"},
#             {"question": "Who wrote 'Romeo and Juliet'?", "answer": "Shakespeare"},
#             {"question": "What planet is known as the Red Planet?", "answer": "Mars"},
#             {"question": "What is the largest ocean on Earth?", "answer": "Pacific Ocean"}
#         ]
        
#         for level in range(1, 11):
#             question_data = random.choice(trivia_questions)
#             tts_engine.say(f"Level {level}: {question_data['question']}")
#             tts_engine.runAndWait()
            
#             user_answer = simpledialog.askstring("Trivia Question", question_data['question'])
#             if user_answer and user_answer.lower() == question_data['answer'].lower():
#                 tts_engine.say("Correct!")
#                 tts_engine.runAndWait()
#             else:
#                 tts_engine.say(f"Sorry, the correct answer was {question_data['answer']}.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play a math game with levels
#     def math_game():
#         tts_engine.say("Let's start the Math Game!")
#         tts_engine.runAndWait()
        
#         for level in range(1, 11):
#             num1 = random.randint(1, 10 * level)
#             num2 = random.randint(1, 10 * level)
#             correct_answer = num1 + num2
#             tts_engine.say(f"Level {level}: What is {num1} plus {num2}?")
#             tts_engine.runAndWait()
            
#             user_answer = simpledialog.askinteger("Math Game", f"What is {num1} + {num2}?")
#             if user_answer == correct_answer:
#                 tts_engine.say("Correct!")
#                 tts_engine.runAndWait()
#             else:
#                 tts_engine.say(f"Sorry, the correct answer was {correct_answer}.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play a word guessing game with levels
#     def word_guessing_game():
#         tts_engine.say("Let's start the Word Guessing Game!")
#         tts_engine.runAndWait()
        
#         words = ["python", "robot", "programming", "machine", "engineer", "technology", "data", "science", "algorithm", "development"]
        
#         for level in range(1, 11):
#             word_to_guess = random.choice(words)
#             guessed_letters = set()
#             attempts = 10 - level  # Decrease attempts with each level
            
#             while attempts > 0:
#                 display_word = " ".join(letter if letter in guessed_letters else "_" for letter in word_to_guess)
#                 tts_engine.say(f"Level {level}: Word to guess: {display_word}")
#                 tts_engine.runAndWait()
#                 guess = simpledialog.askstring("Guess a Letter", "Enter a letter:")
                
#                 if guess and len(guess) == 1:
#                     if guess in word_to_guess:
#                         guessed_letters.add(guess)
#                         tts_engine.say("Correct letter!")
#                         tts_engine.runAndWait()
#                     else:
#                         attempts -= 1
#                         tts_engine.say(f"Incorrect letter! You have {attempts} attempts left.")
#                         tts_engine.runAndWait()
#                     if set(word_to_guess) == guessed_letters:
#                         tts_engine.say(f"Congratulations! You've guessed the word '{word_to_guess}'.")
#                         tts_engine.runAndWait()
#                         break
#                 else:
#                     tts_engine.say("Please enter a single letter.")
#                     tts_engine.runAndWait()
#             else:
#                 tts_engine.say(f"Sorry, you ran out of attempts. The word was '{word_to_guess}'.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play a yes/no game with levels
#     def yes_no_game():
#         tts_engine.say("Let's start the Yes/No Game!")
#         tts_engine.runAndWait()
        
#         questions = [
#             "Is the sky blue?",
#             "Can birds fly?",
#             "Is water dry?",
#             "Do fish swim in water?",
#             "Is the sun hot?",
#             "Can humans breathe underwater?",
#             "Is ice cold?",
#             "Do cars drive on roads?",
#             "Can you touch the sky?",
#             "Is fire hot?"
#         ]
        
#         for level in range(1, 11):
#             question = random.choice(questions)
#             tts_engine.say(f"Level {level}: {question}")
#             tts_engine.runAndWait()
            
#             user_answer = simpledialog.askstring("Yes/No Question", question).strip().lower()
#             if user_answer in ["yes", "no"]:
#                 tts_engine.say("Thank you for your answer!")
#                 tts_engine.runAndWait()
#             else:
#                 tts_engine.say("Please answer with 'yes' or 'no'.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play a riddle game with levels
#     def riddles_game():
#         tts_engine.say("Let's start the Riddles Game!")
#         tts_engine.runAndWait()
        
#         riddles = [
#             {"riddle": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "answer": "Echo"},
#             {"riddle": "I can be cracked, made, told, and played. What am I?", "answer": "Joke"},
#             {"riddle": "The more you take, the more you leave behind. What am I?", "answer": "Footsteps"},
#             {"riddle": "What has keys but can’t open locks?", "answer": "Piano"},
#             {"riddle": "What has to be broken before you can use it?", "answer": "Egg"},
#             {"riddle": "What gets wetter as it dries?", "answer": "Towel"},
#             {"riddle": "What has a thumb and four fingers but is not alive?", "answer": "Glove"},
#             {"riddle": "What is full of holes but still holds water?", "answer": "Sponge"},
#             {"riddle": "What goes up but never comes down?", "answer": "Age"},
#             {"riddle": "What can travel around the world while staying in a corner?", "answer": "Stamp"},
#             {"riddle": "What has a heart that doesn’t beat?", "answer": "Artichoke"},
#             {"riddle": "What has many teeth but can’t bite?", "answer": "Comb"}
#         ]
        
#         for level in range(1, 11):
#             riddle = random.choice(riddles)
#             tts_engine.say(f"Level {level}: {riddle['riddle']}")
#             tts_engine.runAndWait()
            
#             user_answer = simpledialog.askstring("Riddle", riddle['riddle']).strip().lower()
#             if user_answer == riddle['answer'].lower():
#                 tts_engine.say("Correct!")
#                 tts_engine.runAndWait()
#             else:
#                 tts_engine.say(f"Sorry, the correct answer was '{riddle['answer']}'.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play Rock Paper Scissors with levels
#     def rock_paper_scissors():
#         tts_engine.say("Let's play Rock Paper Scissors!")
#         tts_engine.runAndWait()
        
#         choices = ["rock", "paper", "scissors"]
#         for level in range(1, 11):
#             user_choice = simpledialog.askstring("Rock Paper Scissors", "Enter rock, paper, or scissors:").strip().lower()
#             if user_choice not in choices:
#                 tts_engine.say("Invalid choice. Please choose rock, paper, or scissors.")
#                 tts_engine.runAndWait()
#                 continue
                
#             computer_choice = random.choice(choices)
#             tts_engine.say(f"Computer chose {computer_choice}.")
#             tts_engine.runAndWait()
            
#             if user_choice == computer_choice:
#                 result = "It's a tie!"
#             elif (user_choice == "rock" and computer_choice == "scissors") or \
#                  (user_choice == "paper" and computer_choice == "rock") or \
#                  (user_choice == "scissors" and computer_choice == "paper"):
#                 result = "You win!"
#             else:
#                 result = "You lose!"
            
#             tts_engine.say(f"Level {level}: {result}")
#             tts_engine.runAndWait()
            
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to play a memory game with levels
#     def memory_game():
#         tts_engine.say("Let's start the Memory Game!")
#         tts_engine.runAndWait()
        
#         for level in range(1, 11):
#             items = [f"Item {i}" for i in range(1, 10 + level)]
#             random.shuffle(items)
#             displayed_items = items[:level + 2]
#             tts_engine.say(f"Level {level}: Memorize these items: {', '.join(displayed_items)}")
#             tts_engine.runAndWait()
            
#             # Hide items
#             simpledialog.messagebox.showinfo("Memory Game", "Memorize the items quickly!")
#             simpledialog.messagebox.showinfo("Memory Game", "Items hidden. Try to recall them.")
            
#             user_recall = simpledialog.askstring("Memory Game", "Enter the items you remember separated by commas:")
#             user_recall_list = [item.strip() for item in user_recall.split(",")]
            
#             if sorted(user_recall_list) == sorted(displayed_items):
#                 tts_engine.say(f"Level {level}: Correct!")
#                 tts_engine.runAndWait()
#             else:
#                 tts_engine.say(f"Level {level}: Sorry, you remembered: {', '.join(user_recall_list)}. The correct items were: {', '.join(displayed_items)}.")
#                 tts_engine.runAndWait()
                
#             # Ask if they want to proceed to the next level
#             proceed = ask_question("Do you want to proceed to the next level? (yes/no)")
#             if proceed.lower() != "yes":
#                 break

#     # Function to save user responses to a file
#     def save_to_file(filename, data):
#         with open(filename, "w") as file:
#             file.write(data)
    
#     # Start conversation with basic questions
#     name = ask_question("What is your name?")
#     age = ask_question("How old are you?")
#     hobbies = ask_question("What are your hobbies?")
#     feature_suggestions = ask_question("What features would you like to see on the robot?")

#     # Prepare the content to be saved
#     user_data = (
#         f"Name: {name}\n"
#         f"Age: {age}\n"
#         f"Hobbies: {hobbies}\n"
#         f"Feature Suggestions: {feature_suggestions}\n\n"
#     )
    
#     # Ask if the user wants to play games
#     play_games = ask_question("Would you like to play some games? (yes or no)")
#     if play_games.lower() == "yes":
#         # Offer to play a game
#         while True:
#             menu_choice = display_menu()
#             game_functions = {
#                 "1": guess_number_game,
#                 "2": trivia_game,
#                 "3": math_game,
#                 "4": word_guessing_game,
#                 "5": yes_no_game,
#                 "6": riddles_game,
#                 "7": rock_paper_scissors,
#                 "8": memory_game
#             }
            
#             if menu_choice in game_functions:
#                 game_functions[menu_choice]()
#             else:
#                 tts_engine.say("Sorry, I didn't understand your choice.")
#                 tts_engine.runAndWait()
            
#             # Ask if the user wants to play more
#             play_more = ask_question("Would you like to play another game? (yes/no)")
#             if play_more.lower() != "yes":
#                 break

#     # Say something random and offer a survey
#     tts_engine.say("I enjoyed playing with you!")
#     tts_engine.runAndWait()
#     survey_choice = ask_question("Would you like to take a survey? (yes or no)")
    
#     if survey_choice.lower() == "yes":
#         survey_answers = conduct_survey()
#         user_data += "\nSurvey Responses:\n"
#         for question, answer in survey_answers:
#             user_data += f"{question}: {answer}\n"

#     # Thank the user and suggest donation
#     donation_message = "Thank you for your interest! If you would like to support our work, consider donating to the numbers.\n Airtel: 0 9 7 4 9 8 3 5 5 5 \n MTN:   0 9 6 7 6 8 9 5 7 2"
#     tts_engine.say(donation_message)
#     tts_engine.runAndWait()
#     messagebox.showinfo("Support Our Work", donation_message)
    
#     # Save all responses to a file named after the person
#     filename = f"{name.replace(' ', '_')}_responses.txt"
#     save_to_file(filename, user_data)

# # Run the chat function in a separate thread to avoid blocking the main thread
# thread = threading.Thread(target=chat_with_me)

# # Picture taking 
# def take_picture():
#     beautify_comments = [
#         "You're looking fabulous today!",
#         "Get ready to shine like a star!",
#         "This photo is going to be legendary!",
#         "Your smile is brighter than the sun!",
#         "Wow, you're glowing!",
#         "Say cheese, superstar!",
#         "Ready to capture that million-dollar smile?",
#         "You're a natural in front of the camera!",
#         "This picture will be one for the books!",
#         "You're about to steal the show!"
#     ]

#     random_comment = random.choice(beautify_comments)
#     tts_engine.say(random_comment)
#     tts_engine.runAndWait()

#     tts_engine.say("Are you sure you want to take a picture?")
#     tts_engine.runAndWait()

#     def confirm_picture():
#         cap = None
#         try:
#             cap = cv2.VideoCapture(0)
#             if not cap.isOpened():
#                 raise Exception("Could not open video stream")

#             ret, frame = cap.read()
#             if not ret:
#                 raise Exception("Failed to capture image")

#             file_name = "captured_image.png"
#             cv2.imwrite(file_name, frame)
#             tts_engine.say(f"Picture taken and saved as {file_name}")
#             tts_engine.runAndWait()
#             cv2.imshow("Captured Image", frame)
#             cv2.waitKey(0)
#             cv2.destroyAllWindows()

#         except Exception as e:
#             messagebox.showerror("Error", str(e))

#         finally:
#             if cap is not None:
#                 cap.release()

#         # Exit the function
#         return

#     if messagebox.askyesno("Take Picture", "Are you sure you want to take a picture?"):
#         confirm_picture()
#         # The function will return here, and the camera will be released

