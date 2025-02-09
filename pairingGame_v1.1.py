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
        """Handle the image drop and update `self.current_image` properly."""
        image_path = event.mimeData().text()
        
        # Check if this image is already in another DropLabel
        previous_box = self.game_window.find_image_in_boxes(image_path)

        # Prevent duplicate placements unless replacing an image
        if previous_box and previous_box != self:
            if not self.current_image:  # If this drop box is empty, move image
                previous_box.clear()
            else:
                reply = QMessageBox.question(self.game_window, "Replace Image", "Replace the current image?", 
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                self.game_window.update_draggable_status(previous_box.current_image, placed=False)
                previous_box.clear()

        # If this box already contains an image, free up the previous one
        if self.current_image:
            self.game_window.update_draggable_status(self.current_image, placed=False)

        #  Update DropLabel's image and refresh UI
        self.setPixmap(QPixmap(image_path).scaled(self.width(), self.height(), Qt.KeepAspectRatio))
        self.current_image = image_path
        self.setText("")  # Remove placeholder text

        #  Mark the image as placed so it gets a black border
        self.game_window.update_draggable_status(image_path, placed=True)

        #  Check if all images are placed so "Next" button activates
        self.game_window.check_phase_completion()

    def clear(self):
        """Clear the drop box when an image is removed."""
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
        # Prompt user for a code name and quit if Cancel is pressed
        self.user_code, ok = QInputDialog.getText(self, "Enter Code", "Enter code name:")
        # handle quit scenerio
        if not ok or not self.user_code:  # If Cancel is pressed or empty input
            sys.exit(0)  # Quit the application immediately
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
            main_layout.setAlignment(Qt.AlignCenter)
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
    
        # **Create a grid layout with targets and drop boxes in rows**
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignCenter)
        grid_layout.setVerticalSpacing(30)  # Add more space between rows
        screen_size = QApplication.primaryScreen().availableGeometry()
        image_size = min(screen_size.width() // 6, screen_size.height() // 4)  # Enlarged images
        enlarged_image_size = min(screen_size.width() // 5, screen_size.height() // 3)  # Further enlarged
        
        for i in range(3):
            for j in range(2):  # 2 rows
                idx = i + j * 3  # Adjust index for row-major layout
                if idx < len(self.targets):
                    target_label = QLabel()
                    target_label.setPixmap(QPixmap(self.targets[idx]).scaled(image_size, image_size, Qt.KeepAspectRatio))
                    drop_label = DropLabel(self)
                    drop_label.setFixedSize(image_size, image_size)
                    self.drop_labels.append(drop_label)
                    spacer = QLabel()  # Invisible spacer for separation
                    spacer.setFixedSize(70, image_size)  # Increased separation width
                    
                    # Place target and drop box adjacent to each other, then add a spacer
                    grid_layout.addWidget(target_label, j, i * 3)
                    grid_layout.addWidget(drop_label, j, i * 3 + 1)
                    grid_layout.addWidget(spacer, j, i * 3 + 2)
    
        self.layout().addLayout(grid_layout)
    
        # **Add space between upper rows and bottom row**
        self.layout().addSpacing(70)  # Increase separation further
    
        # **Center the bottom row with shuffled draggable images and make them even larger**
        h_layout_bottom = QHBoxLayout()
        h_layout_bottom.setAlignment(Qt.AlignCenter)
        for image_path in self.draggables:
            draggable_label = DraggableLabel(image_path)
            draggable_label.setPixmap(QPixmap(image_path).scaled(image_size, image_size, Qt.KeepAspectRatio))
            h_layout_bottom.addWidget(draggable_label)
            self.draggable_labels.append(draggable_label)
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
        
        # **Maximize window for full screen experience**
        self.showMaximized()

    def save_results(self):
        """Ensure Phase 2 results are stored and save both phases correctly."""
    
        # **Store Phase 2 results if not already stored**
        if self.current_phase == 1 and not self.phase_results[1]:  
            self.phase_results[1] = [
                (self.targets[i], self.drop_labels[i].current_image) for i in range(len(self.drop_labels))
            ]
    
    
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(RESULTS_FOLDER, f"{self.user_code}_{timestamp}.txt")
    
        with open(filename, "w") as file:
            file.write("Phase 1 Results:\n")
            if 0 in self.phase_results and self.phase_results[0]:  
                for target_image, image_path in self.phase_results[0]:
                    image_name = extract_filename(image_path) if image_path else 'None'
                    file.write(f"{extract_filename(target_image)} -> {image_name}\n")
    
            file.write("\nPhase 2 Results:\n")
            if 1 in self.phase_results and self.phase_results[1]:  
                for target_image, image_path in self.phase_results[1]:
                    image_name = extract_filename(image_path) if image_path else 'None'
                    file.write(f"{extract_filename(target_image)} -> {image_name}\n")
    
        # Show prompt asking if the user wants to quit
        QMessageBox.information(self, "Goodbye", "Answers saved, \nThank you!")
        self.close()  # Exit the program
        
    def check_phase_completion(self):
        """Enable the 'Next' or 'Save' button only when all drop boxes are filled."""
        if all(drop_label.current_image is not None for drop_label in self.drop_labels):
            self.next_button.setEnabled(True)
        else:
            self.next_button.setEnabled(False)

    def next_phase(self):
        """Handles transitioning between phases and ensures both phases are saved correctly."""
        
        #  Store results using image file paths instead of `pixmap()`
        self.phase_results[self.current_phase] = [
            (self.targets[i], self.drop_labels[i].current_image) for i in range(len(self.drop_labels))]
    
        if self.current_phase == 0:  # Transitioning from Phase 1 to Phase 2
            self.current_phase += 1
            self.load_phase(self.phase_order[self.current_phase])  # Load Phase 2
        else:  # **If Phase 2 is complete, store results and save them**
            self.save_results()  # Save both phases and prompt the user

    def find_image_in_boxes(self, image_path):
        """Find if the image is already inside a DropLabel."""
        for drop_label in self.drop_labels:
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