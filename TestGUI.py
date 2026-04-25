import sys
import os

# This ensures Python can find your folders
sys.path.append(os.getcwd())

print("1. Attempting to import GUI...")
try:
    from Frontend.GUI import GraphicalUserInterface
    print("2. Import successful. Launching window...")
    
    # Launch the GUI
    GraphicalUserInterface()
    
except Exception as e:
    print("------------------------------------------------")
    print("GUI CRASHED WITH ERROR:")
    print(e)
    print("------------------------------------------------")
    input("Press Enter to close...")