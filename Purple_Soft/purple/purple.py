from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox
import sys

# Placeholder for activity functions
def set_mode(mode):
    print(f"Mode set to {mode}")
    QMessageBox.information(None, "Mode Change", f"Mode has been set to: {mode}")

def stop_all():
    print("All modes stopped")
    QMessageBox.warning(None, "Stop", "All activities have been stopped!")

# Main window class
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RC Purple Bot")
        self.setGeometry(100, 100, 800, 600)

        # Central widget and main layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Create the stacked layout to handle different menus
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

        # Add menus to the stacked layout
        self.stacked_layout.addWidget(self.menu_widget)
        self.stacked_layout.addWidget(self.home_widget)
        self.stacked_layout.addWidget(self.pay_load_widget)
        self.stacked_layout.addWidget(self.farm_widget)

        # Show the main menu initially
        self.stacked_layout.setCurrentWidget(self.menu_widget)

        # Apply styling
        self.set_style()

    def set_style(self):
        """Set a modern industrial black and yellow style."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f5f5f5;
                font-size: 18px;
            }
            QPushButton {
                background-color: #ffcc00;
                border: 2px solid #ffaa00;
                border-radius: 10px;
                padding: 10px;
                color: #000;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffaa00;
            }
            QPushButton:pressed {
                background-color: #ddaa00;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #f5f5f5;
            }
        """)

    def create_main_menu(self):
        """Create the main menu with various options."""
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
        """Create the Home menu with specific commands."""
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
            ("Back", lambda: self.stacked_layout.setCurrentWidget(self.menu_widget)),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 4
            col = index % 4
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def create_pay_load_menu(self):
        """Create the PayLoad menu."""
        layout = QtWidgets.QGridLayout()
        self.pay_load_widget.setLayout(layout)

        buttons = [
            ("PS4 Controller", lambda: set_mode("PS4_CONTROLLER")),
            ("Color Following", lambda: set_mode("COLOR_FOLLOW")),
            ("Free Roam", lambda: set_mode("FREE_ROAM")),
            ("ROS Mode", lambda: set_mode("ROS")),
            ("Stop", stop_all),
            ("Back", lambda: self.stacked_layout.setCurrentWidget(self.menu_widget)),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 3
            col = index % 3
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def create_farm_menu(self):
        """Create the Farm Mode menu."""
        layout = QtWidgets.QGridLayout()
        self.farm_widget.setLayout(layout)

        buttons = [
            ("Mapping", lambda: set_mode("Mapping")),
            ("Disinfect", lambda: set_mode("Disinfection")),
            ("Watering", lambda: set_mode("Watering")),
            ("Plant Health", lambda: set_mode("Plant_health")),
            ("Harvesting", lambda: set_mode("Harvesting")),
            ("Stop", stop_all),
            ("Back", lambda: self.stacked_layout.setCurrentWidget(self.menu_widget)),
        ]

        for index, (name, func) in enumerate(buttons):
            row = index // 4
            col = index % 4
            button = QtWidgets.QPushButton(name)
            button.setFixedSize(150, 80)
            button.clicked.connect(func)
            layout.addWidget(button, row, col, QtCore.Qt.AlignCenter)

    def show_message(self, message):
        """Show a message box with the given message."""
        QMessageBox.information(self, "Info", message)

# Run the application
app = QtWidgets.QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())
