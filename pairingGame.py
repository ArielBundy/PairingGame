# Coded by Ariel Shaked
"""
Created on Tue Feb  4 11:52:23 2025
"""
import re
import sys
import os
import datetime
import random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QSpacerItem, QSizePolicy, QMessageBox, QInputDialog
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.QtCore import Qt, QMimeData

# Helper functions
def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)

def extract_filename(filepath):
    """ Extracts only the filename without path and extension """
    filename = os.path.basename(filepath)
    match = re.match(r'(target\d+|pair\d+)', filename)
    return match.group(0) if match else filename  # Ensure no crash if filename doesn't match expected pattern

# Create results folder
RESULTS_FOLDER = os.path.join(os.getcwd(), "results")
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

# Define two phases of images
TARGET_SETS = [
    [resource_path(f"images\\target{i}.png") for i in range(1, 7)],
    [resource_path(f"images\\target{i}.png") for i in range(7, 13)]
]
DRAGGABLE_SETS = [
    [resource_path(f"images\\pair{i}.png") for i in range(1, 7)],
    [resource_path(f"images\\pair{i}.png") for i in range(7, 13)]
]

class DraggableLabel(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setPixmap(QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio))
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(False)
        self.is_placed = False  # Tracks if the image is in a box
        self.update_border()  # Set initial border (red)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            mimeData = QMimeData()
            mimeData.setText(self.image_path)

            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(self.pixmap())
            drag.exec_(Qt.MoveAction)

    def mark_as_used(self):
        """Change border to black when the image is placed inside a box."""
        self.is_placed = True
        self.update_border()

    def mark_as_available(self):
        """Change border to red when the image is removed from a box or replaced."""
        self.is_placed = False
        self.update_border()

    def update_border(self):
        """Set border color based on whether the image is in a box or not."""
        if self.is_placed:
            self.setStyleSheet("border: 2px solid black;")  # Black when placed
        else:
            self.setStyleSheet("border: 2px solid red;")  # Red when available

class DropLabel(QLabel):
    def __init__(self, game_window, parent=None):
        super().__init__(parent)
        self.game_window = game_window
        self.setFixedSize(100, 100)
        self.setStyleSheet("border: 2px dashed gray; background-color: white;")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.current_image = None
        self.setText("Drop Here")  # Initial placeholder text

    def dragEnterEvent(self, event):
        """Allow drops only for image paths."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        image_path = event.mimeData().text()
        previous_box = self.game_window.find_image_in_boxes(image_path)

        if previous_box and previous_box != self:
            if not self.current_image:
                previous_box.clear()
            else:
                reply = QMessageBox.question(self.game_window, "Replace Image", "Replace the current image?", 
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                self.game_window.update_draggable_status(previous_box.current_image, placed=False)
                previous_box.clear()

        if self.current_image:
            self.game_window.update_draggable_status(self.current_image, placed=False)

        self.setPixmap(QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio))
        self.current_image = image_path
        self.setText("")  # Remove placeholder text
        self.game_window.update_draggable_status(image_path, placed=True)
        self.game_window.check_phase_completion()

    def clear(self):
        if self.current_image:
            self.game_window.update_draggable_status(self.current_image, placed=False)
        self.setPixmap(QPixmap())
        self.current_image = None
        self.setText("Drop Here")  # Restore placeholder text

class ImagePairingGame(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Pairing Game")
        self.setGeometry(100, 100, 900, 700)
    
        self.user_code, _ = QInputDialog.getText(self, "Enter Code", "Enter code name:")
        self.phase_order = random.choice([(0, 1), (1, 0)])  # Randomize order of phases
        self.current_phase = 0
    
        # **Store results for both phases**
        self.phase_results = {0: [], 1: []}
    
        self.load_phase(self.phase_order[self.current_phase])

    def load_phase(self, phase_index):
        """Loads a new phase with new targets and draggable images."""
    
        # **Ensure layout is initialized**
        if self.layout() is None:
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)
        else:
            # **Remove all existing widgets before loading new phase**
            while self.layout().count():
                item = self.layout().takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
    
        self.targets = TARGET_SETS[phase_index]
        self.draggables = DRAGGABLE_SETS[phase_index]
        
        # **Shuffle the draggable images for a random order**
        random.shuffle(self.draggables)
        
        self.drop_labels = []
        self.draggable_labels = []
    
        # **Center the two columns (targets & drop boxes)**
        columns_layout = QHBoxLayout()
        columns_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    
        grid_layout = QGridLayout()
        for i in range(6):
            target_label = QLabel()
            target_label.setPixmap(QPixmap(self.targets[i]).scaled(100, 100, Qt.KeepAspectRatio))
            drop_label = DropLabel(self)
            grid_layout.addWidget(target_label, i, 0)
            grid_layout.addWidget(drop_label, i, 1)
            self.drop_labels.append((self.targets[i], drop_label))
    
        columns_layout.addLayout(grid_layout)
        columns_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.layout().addLayout(columns_layout)
    
        # **Center the bottom row with shuffled draggable images**
        h_layout_bottom = QHBoxLayout()
        h_layout_bottom.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        for image_path in self.draggables:
            draggable_label = DraggableLabel(image_path)
            h_layout_bottom.addWidget(draggable_label)
            self.draggable_labels.append(draggable_label)
        h_layout_bottom.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.layout().addLayout(h_layout_bottom)
    
        # **Update the button based on the phase**
        if self.current_phase == 0:  # First phase
            self.next_button = QPushButton("Next")
            self.next_button.clicked.connect(self.next_phase)
        else:  # Second phase (change to Save button)
            self.next_button = QPushButton("Save Answers")
            self.next_button.clicked.connect(self.save_results)
    
        self.next_button.setEnabled(False)  # Ensure the button is disabled until all pairs are matched
        self.layout().addWidget(self.next_button, alignment=Qt.AlignCenter)  # Center the button

    def save_results(self):
        """Ensure Phase 2 results are stored and save both phases correctly."""
    
        # **Explicitly store Phase 2 results before writing to the file**
        if self.current_phase == 1 and not self.phase_results[1]:  
            self.phase_results[1] = [
                (target_image, drop_label) for target_image, drop_label in self.drop_labels
            ]
    
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(RESULTS_FOLDER, f"{self.user_code}_{timestamp}.txt")
    
        with open(filename, "w") as file:
            file.write("Phase 1 Results:\n")
            if 0 in self.phase_results and self.phase_results[0]:  
                for target_image, drop_label in self.phase_results[0]:
                    image_name = extract_filename(drop_label.current_image) if drop_label.current_image else 'None'
                    file.write(f"{extract_filename(target_image)} -> {image_name}\n")
    
            file.write("\nPhase 2 Results:\n")
            if 1 in self.phase_results and self.phase_results[1]:  
                for target_image, drop_label in self.phase_results[1]:
                    image_name = extract_filename(drop_label.current_image) if drop_label.current_image else 'None'
                    file.write(f"{extract_filename(target_image)} -> {image_name}\n")
    
        # **Show prompt asking if the user wants to quit**
        reply = QMessageBox.question(
            self, "Saved", "Answers saved. Quit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
    
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Goodbye", "Thank you!")
            self.close()  # Exit the program    
            
    def check_phase_completion(self):
        """Enable the 'Next Phase' button or 'Save' button only when all drop boxes are filled."""
        if all(drop_label.current_image is not None for _, drop_label in self.drop_labels):
            self.next_button.setEnabled(True)
        else:
            self.next_button.setEnabled(False)

    def next_phase(self):
        """Handles transitioning between phases and ensures both phases are saved correctly."""
        # **Store results of the current phase before switching**
        self.phase_results[self.current_phase] = [
            (target_image, drop_label) for target_image, drop_label in self.drop_labels
        ]
    
        if self.current_phase == 0:  # Transitioning from Phase 1 to Phase 2
            self.current_phase += 1
            self.load_phase(self.phase_order[self.current_phase])  # Load Phase 2
        else:  # **If Phase 2 is complete, store results and save them**
            self.phase_results[1] = [
                (target_image, drop_label) for target_image, drop_label in self.drop_labels
            ]
            self.save_results()  # Save both phases and prompt the user

    def find_image_in_boxes(self, image_path):
        """Find if the image is already inside a DropLabel."""
        for _, drop_label in self.drop_labels:
            if drop_label.current_image == image_path:
                return drop_label
        return None  # Return None if not found

    def update_draggable_status(self, image_path, placed):
        """Update draggable label to show whether it is placed in a box or available."""
        for label in self.draggable_labels:
            if label.image_path == image_path:
                if placed:
                    label.mark_as_used()  # Black border when placed
                else:
                    label.mark_as_available()  # Red border when available
                break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImagePairingGame()
    window.show()
    sys.exit(app.exec_())
