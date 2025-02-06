# Image Pairing Game

## Overview
This is a simple drag-and-drop image pairing game built using **Python** and **PyQt5**. The game consists of two phases where the user must match images into empty boxes. A coin flip determines the starting phase, and after completing the first phase, the user proceeds to the second phase.

## Features
- **Two Phases:** The game consists of two distinct sets of images.
- **Randomized Start:** A coin flip determines which set appears first.
- **Drag-and-Drop Interface:** Users can drag images into boxes to pair them.
- **Undo and Reassign:** Users can change their selections before proceeding.
- **Results Logging:** The game saves the results as a `.txt` file, named using the entered code name and timestamp.

## Installation
### Prerequisites
Ensure you have **Python 3.8+** installed along with the required dependencies.

### Install Dependencies
Run the following command to install the necessary packages:
```sh
pip install PyQt5
```

### Run the Game
Clone the repository and navigate to the project folder:
```sh
git clone https://github.com/ArielBundy/PairingGame.git
cd <PairingGame_folder>
python pairingGame.py
```

## Usage
1. **Launch the game** by running `python pairing_game.py`.
2. **Enter a code name** when prompted.
3. **Drag and drop** images into the correct boxes.
4. **Once all boxes are filled**, the "Next" button becomes enabled.
5. **Confirm the transition**, then complete the second phase.
6. **Results are saved** in the `results/` folder.

## Building a Standalone Executable
To create a standalone `.exe` file (Windows):
```sh
pyinstaller --onefile --windowed --hidden-import=PyQt5.sip pairing_game.py
```
After building, the executable will be located in the `dist/` folder.

## File Structure
```
📂 image-pairing-game/
 ├── pairing_game.py      # Main application script
 ├── results/             # Folder where results are saved
 ├── images/              # Contains target and draggable images
 ├── README.md            # Project documentation
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author
Developed by **Ariel Shaked**. Feel free to connect via [GitHub](https://github.com/ArielBundy).

