from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QLabel
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import cv2
import numpy as np
import pygame
import serial
import time
import pyttsx3
import threading

# Import all activity functions
from activity_funtions import *

# Initialize serial connection
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2)
except serial.SerialException:
    print("Warning: Could not open serial connection")
    ser = None

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Initialize pygame for PS4 controller
pygame.init()
pygame.joystick.init()

# Global variables
current_mode = None
running = False

class ColorFollowingThread(QThread):
    finished = pyqtSignal()

    def run(self):
        color_following()  # Use the imported function
        self.finished.emit()

class PS4ControllerThread(QThread):
    finished = pyqtSignal()

    def run(self):
        ps4_controller()  # Use the imported function
        self.finished.emit()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RC Purple Bot")
        self.setGeometry(100, 100, 800, 600)

        # Set background image
        self.set_background_image("background.jpg")

        # Central widget and main layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Create the stacked layout
        self.stacked_layout = QtWidgets.QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # Create menu widgets
        self.menu_widget = QtWidgets.QWidget()
        self.home_widget = QtWidgets.QWidget()
        self.pay_load_widget = QtWidgets.QWidget()
        self.farm_widget = QtWidgets.QWidget()

        # Setup menus
        self.create_main_menu()
        self.create_home_menu()
        self.create_pay_load_menu()
        self.create_farm_menu()

        # Add menus to stacked layout
        self.stacked_layout.addWidget(self.menu_widget)
        self.stacked_layout.addWidget(self.home_widget)
        self.stacked_layout.addWidget(self.pay_load_widget)
        self.stacked_layout.addWidget(self.farm_widget)

        # Show main menu initially
        self.stacked_layout.setCurrentWidget(self.menu_widget)

        # Create navigation bar
        self.create_navigation_bar()

        # Create mode display label
        self.mode_label = QLabel("No active mode")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.mode_label)

        # Apply styling
        self.set_style()

        # Start mode update timer
        self.mode_timer = QtCore.QTimer(self)
        self.mode_timer.timeout.connect(self.update_mode_display)
        self.mode_timer.start(1000)

        # Create keyboard handler
        self.key_handler = KeyHandler()
        self.installEventFilter(self.key_handler)

    def set_background_image(self, image_path):
        try:
            background = QPixmap(image_path)
            if background.isNull():
                raise FileNotFoundError("Image file not found or invalid")
            
            scaled_background = background.scaled(self.size(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled_background))
            self.setPalette(palette)
            self.setAutoFillBackground(True)
        except Exception as e:
            print(f"Error setting background image: {e}")
            self.setStyleSheet("background-color: #2b2b2b;")

    def set_style(self):
        self.setStyleSheet("""
            QWidget {
                color: #f5f5f5;
                font-size: 18px;
            }
            QPushButton {
                background-color: rgba(255, 204, 0, 200);
                border: 2px solid #ffaa00;
                border-radius: 10px;
                padding: 10px;
                color: #000;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 170, 0, 200);
            }
            QPushButton:pressed {
                background-color: rgba(221, 170, 0, 200);
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #f5f5f5;
            }
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: #ffffff;
                padding: 5px;
                border-radius: 5px;
            }
        """)

    def create_navigation_bar(self):
        nav_bar = QtWidgets.QHBoxLayout()
        self.main_layout.insertLayout(0, nav_bar)

        nav_buttons = [
            ("Main Menu", lambda: self.stacked_layout.setCurrentWidget(self.menu_widget)),
            ("Home", lambda: self.stacked_layout.setCurrentWidget(self.home_widget)),
            ("PayLoad", lambda: self.stacked_layout.setCurrentWidget(self.pay_load_widget)),
            ("Farm", lambda: self.stacked_layout.setCurrentWidget(self.farm_widget)),
        ]

        for name, func in nav_buttons:
            button = QtWidgets.QPushButton(name)
            button.clicked.connect(func)
            nav_bar.addWidget(button)

    def create_main_menu(self):
        layout = QtWidgets.QGridLayout()
        self.menu_widget.setLayout(layout)

        buttons = [
            ("Home", lambda: self.stacked_layout.setCurrentWidget(self.home_widget)),
            ("Super Market", lambda: self.show_message("Super Market menu is under construction")),
            ("Farm Mode", lambda: self.stacked_layout.setCurrentWidget(self.farm_widget)),
            ("Disaster", lambda: self.show_message("Disaster menu is under construction")),
            ("Food And Other", lambda: self.show_message("This menu is under construction")),
            ("Self Driven", lambda: self.show_message("This menu is under construction")),
            ("Mobile App", lambda: self.show_message("This menu is under construction")),
            ("PayLoad", lambda: self.stacked_layout.setCurrentWidget(self.pay_load_widget)),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 4
            col = index % 4
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def create_home_menu(self):
        layout = QtWidgets.QGridLayout()
        self.home_widget.setLayout(layout)

        buttons = [
            ("PS4 Controller", lambda: set_mode("PS4_CONTROLLER")),
            ("Color Following", lambda: set_mode("COLOR_FOLLOW")),
            ("Free Roam", lambda: set_mode("FREE_ROAM")),
            ("ROS Mode", lambda: set_mode("ROS")),
            ("Chat with Me", lambda: set_mode("CHAT_WITH_ME")),
            ("Take Picture", lambda: set_mode("TAKE_PICTURE")),
            ("Stop", stop_all),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 4
            col = index % 4
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def create_pay_load_menu(self):
        layout = QtWidgets.QGridLayout()
        self.pay_load_widget.setLayout(layout)

        buttons = [
            ("PS4 Controller", lambda: set_mode("PS4_CONTROLLER")),
            ("Color Following", lambda: set_mode("COLOR_FOLLOW")),
            ("Free Roam", lambda: set_mode("FREE_ROAM")),
            ("ROS Mode", lambda: set_mode("ROS")),
            ("Stop", stop_all),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 3
            col = index % 3
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def create_farm_menu(self):
        layout = QtWidgets.QGridLayout()
        self.farm_widget.setLayout(layout)

        buttons = [
            ("Mapping", lambda: set_mode("MAPPING")),
            ("Disinfect", lambda: set_mode("DISINFECTION")),
            ("Watering", lambda: set_mode("WATERING")),
            ("Plant Health", lambda: set_mode("PLANT_HEALTH")),
            ("Harvesting", lambda: set_mode("HARVESTING")),
            ("Stop", stop_all),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 4
            col = index % 4
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def show_message(self, message):
        QMessageBox.information(self, "Info", message)

    def update_mode_display(self):
        if current_mode:
            self.mode_label.setText(f"Active mode: {current_mode}")
        else:
            self.mode_label.setText("No active mode")

class KeyHandler(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if current_mode == "FREE_ROAM":
                if event.key() == Qt.Key_W:
                    send_command('FORWARD')
                elif event.key() == Qt.Key_S:
                    send_command('BACKWARD')
                elif event.key() == Qt.Key_A:
                    send_command('LEFT')
                elif event.key() == Qt.Key_D:
                    send_command('RIGHT')
                elif event.key() == Qt.Key_Space:
                    send_command('STOP')
            return True
        return super().eventFilter(obj, event)

def set_mode(mode):
    global current_mode, running
    if current_mode:
        stop_all()
    
    current_mode = mode
    running = True
    
    if mode == "COLOR_FOLLOW":
        color_thread = ColorFollowingThread()
        color_thread.start()
    elif mode == "PS4_CONTROLLER":
        tts_engine.say("PS4 Controller mode activated")
        tts_engine.runAndWait()
        ps4_thread = PS4ControllerThread()
        ps4_thread.start()
    elif mode == "FREE_ROAM":
        tts_engine.say("Free roam mode activated. Use WASD keys to control the robot.")
        tts_engine.runAndWait()
    # Add other modes as needed

def stop_all():
    global current_mode, running
    running = False
    current_mode = None
    send_command('STOP')
    tts_engine.say("Stopping all activities")
    tts_engine.runAndWait()

# Run the application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())