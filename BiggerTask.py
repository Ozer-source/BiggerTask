"""
BiggerTask - A Python Macro Recorder similar to TinyTask

This program can record mouse and keyboard actions and replay them later.
Recordings are saved to custom .rec files for later playback.

Key Features:
- Record all mouse and keyboard activity
- Store actions with accurate timing
- Save/load recordings to .rec files
- Playback with exact timing reproduction
- TinyTask-style GUI interface with buttons
- Automatic recording folder management
"""

import json
import time
import threading
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from pynput import mouse, keyboard
from pynput.keyboard import Key, Listener as KeyboardListener, KeyCode
from pynput.mouse import Listener as MouseListener, Button


# ============================================================================
# CONFIGURATION
# ============================================================================

# Determine base directory for file storage
# If running as PyInstaller executable, use executable directory
# If running as Python script, use script directory
if getattr(sys, 'frozen', False):
    # Running as compiled executable (PyInstaller)
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as Python script
    BASE_DIR = Path(__file__).parent

# Automatically create and use playbacks folder next to executable or script
PLAYBACK_FOLDER = BASE_DIR / "playbacks"
PLAYBACK_FOLDER.mkdir(exist_ok=True)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class MouseMoveEvent:
    """Represents a mouse movement event"""
    type: str = "mouse_move"
    x: int = 0
    y: int = 0
    time: float = 0.0


@dataclass
class MouseClickEvent:
    """Represents a mouse click event (press or release)"""
    type: str = "mouse_click"
    button: str = "left"  # "left" or "right"
    pressed: bool = True  # True for press, False for release
    x: int = 0
    y: int = 0
    time: float = 0.0


@dataclass
class MouseScrollEvent:
    """Represents a mouse scroll event"""
    type: str = "mouse_scroll"
    x: int = 0
    y: int = 0
    dx: int = 0
    dy: int = 0
    time: float = 0.0


@dataclass
class KeyboardEvent:
    """Represents a keyboard key press or release"""
    type: str = "key_press"  # or "key_release"
    key: str = ""
    time: float = 0.0


# ============================================================================
# RECORDING STATE
# ============================================================================

class RecorderState:
    """Manages the state of the recorder"""
    
    def __init__(self, status_callback=None):
        self.is_recording = False
        self.events: List[dict] = []
        self.recording_start_time = 0.0
        self.listeners = []
        self.status_callback = status_callback  # Optional GUI callback
    
    def start_recording(self):
        """Initialize recording state"""
        self.is_recording = True
        self.events = []
        self.recording_start_time = time.time()
        self._update_status("Recording...", "green")
    
    def stop_recording(self):
        """Stop recording and return event count"""
        if self.is_recording:
            self.is_recording = False
            event_count = len(self.events)
            self._update_status(f"Idle ({event_count} events)", "black")
            return event_count
        return 0
    
    def add_event(self, event: dict):
        """Add a recorded event"""
        if self.is_recording:
            # Calculate relative time from recording start
            current_time = time.time()
            event['time'] = current_time - self.recording_start_time
            self.events.append(event)
    
    def _update_status(self, message: str, color: str = "black"):
        """Update GUI status if callback is provided"""
        if self.status_callback:
            self.status_callback(message, color)


# Global state object
recorder = RecorderState()  # Initialize without callback, will be updated by GUI
playback_speed = 1.0  # Playback speed multiplier
is_looping = False  # Loop mode toggle
is_playing = False  # Playback state - allows stopping playback with F8


# ============================================================================
# INPUT LISTENER IMPLEMENTATION
# ============================================================================

def create_mouse_listener():
    """
    Creates a listener for mouse events.
    
    The listener captures:
    - Mouse movement
    - Mouse clicks (left and right buttons)
    - Mouse scrolling
    """
    
    def on_move(x, y):
        """Called when mouse moves"""
        event = asdict(MouseMoveEvent(x=x, y=y))
        recorder.add_event(event)
    
    def on_click(x, y, button, pressed):
        """Called when mouse button is pressed or released"""
        button_name = "left" if button == Button.left else "right"
        event = asdict(MouseClickEvent(
            button=button_name,
            pressed=pressed,
            x=x,
            y=y
        ))
        recorder.add_event(event)
    
    def on_scroll(x, y, dx, dy):
        """Called when mouse wheel is scrolled"""
        event = asdict(MouseScrollEvent(x=x, y=y, dx=dx, dy=dy))
        recorder.add_event(event)
    
    # Create and return the mouse listener
    listener = MouseListener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    )
    return listener


def create_keyboard_listener():
    """
    Creates a listener for keyboard events.
    
    The listener captures:
    - Key presses
    - Key releases
    - Special keys (Shift, Ctrl, Alt, etc.)
    """
    
    def on_press(key):
        """Called when a key is pressed"""
        try:
            # Try to get the character value
            key_str = key.char if hasattr(key, 'char') else str(key)
        except AttributeError:
            # Special keys (Shift, Ctrl, etc.)
            key_str = str(key).replace('Key.', '')
        
        event = asdict(KeyboardEvent(
            type="key_press",
            key=key_str
        ))
        recorder.add_event(event)
        
        # Handle recording control hotkeys
        handle_hotkey_press(key)
    
    def on_release(key):
        """Called when a key is released"""
        try:
            key_str = key.char if hasattr(key, 'char') else str(key)
        except AttributeError:
            key_str = str(key).replace('Key.', '')
        
        event = asdict(KeyboardEvent(
            type="key_release",
            key=key_str
        ))
        recorder.add_event(event)
    
    # Create and return the keyboard listener
    listener = KeyboardListener(
        on_press=on_press,
        on_release=on_release
    )
    return listener


# ============================================================================
# HOTKEY HANDLING (F8, F9, F10, F11)
# ============================================================================

# GUI reference and callback for status updates
gui_reference = None

def handle_hotkey_press(key):
    """
    Handles special hotkeys for recording control.
    
    F8 - Universal toggle (smart hotkey)
         • If not recording → start recording
         • If recording → stop recording
         • If stopped with events → start playback
         • If playing → stop playback
    """
    global gui_reference, is_playing
    try:
        if key == Key.f8:
            # F8: Universal toggle hotkey
            if recorder.is_recording:
                # Currently recording → STOP RECORDING
                recorder.stop_recording()
                if gui_reference:
                    gui_reference.update_recording_status()
            
            elif is_playing:
                # Currently playing → STOP PLAYBACK
                is_playing = False
                if gui_reference:
                    gui_reference.update_status("Stopped", "black")
                    gui_reference.update_recording_status()
            
            elif recorder.events:
                # Has events but not recording or playing → START PLAYBACK
                is_playing = True
                if gui_reference:
                    gui_reference.update_status("Playing...", "blue")
                
                # Start playback in background
                def play_and_reset():
                    global is_playing
                    playback_events(recorder.events)
                    is_playing = False
                    if gui_reference:
                        gui_reference.update_status("Idle", "black")
                        gui_reference.update_recording_status()
                
                thread = threading.Thread(target=play_and_reset, daemon=True)
                thread.start()
            
            else:
                # No events → START RECORDING
                recorder.start_recording()
                if gui_reference:
                    gui_reference.update_recording_status()
    
    except AttributeError:
        pass


# ============================================================================
# FILE OPERATIONS - SAVING AND LOADING
# ============================================================================

def save_recording(filename: str, folder: Path = PLAYBACK_FOLDER) -> bool:
    """
    Saves the recorded events to a .rec file in the playbacks folder.
    
    Args:
        filename: Name of the file to save (can include or exclude .rec extension)
        folder: Folder to save to (defaults to playbacks/)
    
    The file format is JSON with the following structure:
    {
        "version": 1,
        "event_count": N,
        "total_duration": X.XXX,
        "events": [...]
    }
    """
    # Ensure .rec extension
    if not filename.endswith('.rec'):
        filename += '.rec'
    
    # Full path in playbacks folder
    filepath = folder / filename
    
    # Create recording data structure
    recording_data = {
        "version": 1,
        "event_count": len(recorder.events),
        "total_duration": recorder.events[-1]['time'] if recorder.events else 0,
        "events": recorder.events
    }
    
    try:
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(recording_data, f, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Save Error", f"Error saving file: {e}")
        return False


def load_recording(filename: str, folder: Path = PLAYBACK_FOLDER) -> bool:
    """
    Loads a recording from a .rec file in the playbacks folder.
    
    Args:
        filename: Name of the .rec file to load
        folder: Folder to load from (defaults to playbacks/)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure .rec extension
        if not filename.endswith('.rec'):
            filename += '.rec'
        
        # Full path in playbacks folder
        filepath = folder / filename
        
        # Check if file exists
        if not filepath.exists():
            messagebox.showerror("Load Error", f"File not found: {filename}")
            return False
        
        # Read and parse JSON
        with open(filepath, 'r') as f:
            recording_data = json.load(f)
        
        # Load events from file
        recorder.events = recording_data.get('events', [])
        return True
    
    except json.JSONDecodeError:
        messagebox.showerror("Load Error", f"Invalid .rec file format: {filename}")
        return False
    except Exception as e:
        messagebox.showerror("Load Error", f"Error loading file: {e}")
        return False


# ============================================================================
# PLAYBACK ENGINE
# ============================================================================

def perform_event(event: dict):
    """
    Executes a recorded event during playback.
    
    Args:
        event: Dictionary containing event data
    
    Supported event types:
    - mouse_move: Move cursor to position
    - mouse_click: Click mouse button (left/right, press/release)
    - mouse_scroll: Scroll the mouse wheel
    - key_press: Press a key
    - key_release: Release a key
    """
    event_type = event.get('type')
    
    try:
        if event_type == 'mouse_move':
            # Move cursor to position
            mouse_controller.position = (event['x'], event['y'])
        
        elif event_type == 'mouse_click':
            # Click button (press or release)
            button = Button.left if event['button'] == 'left' else Button.right
            if event['pressed']:
                mouse_controller.press(button)
            else:
                mouse_controller.release(button)
        
        elif event_type == 'mouse_scroll':
            # Scroll wheel
            mouse_controller.scroll(event['dx'], event['dy'])
        
        elif event_type == 'key_press':
            # Press a key
            key_str = event['key']
            press_key(key_str)
        
        elif event_type == 'key_release':
            # Release a key
            key_str = event['key']
            release_key(key_str)
    
    except Exception as e:
        print(f"Error performing event {event_type}: {e}")


def press_key(key_str: str):
    """Presses a key on the keyboard"""
    try:
        # Try to get special key
        special_keys = {
            'shift': Key.shift,
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'enter': Key.enter,
            'space': ' ',
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
        }
        
        if key_str.lower() in special_keys:
            keyboard_controller.press(special_keys[key_str.lower()])
        else:
            # Regular character
            keyboard_controller.press(key_str)
    except Exception as e:
        pass


def release_key(key_str: str):
    """Releases a key on the keyboard"""
    try:
        special_keys = {
            'shift': Key.shift,
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'enter': Key.enter,
            'space': ' ',
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
        }
        
        if key_str.lower() in special_keys:
            keyboard_controller.release(special_keys[key_str.lower()])
        else:
            keyboard_controller.release(key_str)
    except Exception as e:
        pass


def playback_events(events: List[dict]):
    """
    Replays recorded events with proper timing.
    Can be stopped by setting is_playing = False (via F8 hotkey).
    
    Algorithm:
    1. Get the duration of the first event (as starting point)
    2. For each event, calculate the delay from the previous event
    3. Sleep for that duration
    4. Execute the event
    5. Update the previous time
    6. Check if is_playing flag is still True (allows F8 to stop)
    
    The playback_speed multiplier can speed up or slow down playback.
    """
    if not events:
        print("No events to playback")
        return
    
    def run_playback():
        global is_looping, is_playing
        
        loop_count = 1
        while True:
            previous_time = 0.0
            
            for event in events:
                # Check if playback was stopped via F8
                if not is_playing:
                    print("✓ Playback stopped by user")
                    return
                
                # Calculate delay between this event and the previous one
                current_time = event.get('time', 0)
                delay = (current_time - previous_time) / playback_speed
                
                # Wait for the delay
                if delay > 0:
                    time.sleep(delay)
                
                # Execute the event
                perform_event(event)
                
                # Update previous time
                previous_time = current_time
            
            if is_looping and is_playing:
                loop_count += 1
                print(f"Loop {loop_count}...")
                time.sleep(0.5)
            else:
                break
        
        print("✓ Playback completed")
    
    # Run playback in separate thread to not block
    playback_thread = threading.Thread(target=run_playback, daemon=True)
    playback_thread.start()


# ============================================================================
# GUI APPLICATION
# ============================================================================

class MacroRecorderGUI:
    """TinyTask-style GUI for the macro recorder"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("BiggerTask - Macro Recorder")
        self.root.geometry("600x320")
        self.root.resizable(False, False)
        
        # Set global GUI reference for hotkeys
        global gui_reference
        gui_reference = self
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="BiggerTask - Macro Recorder",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=5, pady=(0, 20))
        
        # Control buttons
        self.record_btn = ttk.Button(
            main_frame,
            text="Record (F8)",
            command=self.on_record,
            width=12
        )
        self.record_btn.grid(row=1, column=0, padx=5)
        
        self.stop_btn = ttk.Button(
            main_frame,
            text="Stop (F8)",
            command=self.on_stop,
            width=12,
            state=tk.DISABLED
        )
        self.stop_btn.grid(row=1, column=1, padx=5)
        
        self.play_btn = ttk.Button(
            main_frame,
            text="Play (F8)",
            command=self.on_play,
            width=12
        )
        self.play_btn.grid(row=1, column=2, padx=5)
        
        self.save_btn = ttk.Button(
            main_frame,
            text="Save",
            command=self.on_save,
            width=12
        )
        self.save_btn.grid(row=1, column=3, padx=5)
        
        # Loop button - with red/green color indicator
        self.loop_btn = tk.Button(
            main_frame,
            text="Loop",
            command=self.on_loop,
            width=12,
            bg="red",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.loop_btn.grid(row=1, column=4, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="Idle",
            font=("Arial", 10),
            foreground="black"
        )
        self.status_label.grid(row=2, column=0, columnspan=5, pady=(15, 0))
        
        # Recording dropdown label and selector
        dropdown_label = ttk.Label(main_frame, text="Saved Recordings:", font=("Arial", 10))
        dropdown_label.grid(row=3, column=0, columnspan=5, pady=(20, 5), sticky=tk.W)
        
        # Dropdown frame
        dropdown_frame = ttk.Frame(main_frame)
        dropdown_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.recordings_var = tk.StringVar()
        self.recordings_dropdown = ttk.Combobox(
            dropdown_frame,
            textvariable=self.recordings_var,
            state="readonly",
            width=50
        )
        self.recordings_dropdown.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            dropdown_frame,
            text="Refresh",
            command=self.refresh_recordings,
            width=8
        )
        self.refresh_btn.grid(row=0, column=1)
        
        # Load button
        self.load_btn = ttk.Button(
            dropdown_frame,
            text="Load",
            command=self.on_load,
            width=6
        )
        self.load_btn.grid(row=0, column=2, padx=(3, 0))
        
        # Initial dropdown refresh
        self.refresh_recordings()
    
    def on_loop(self):
        """Toggle loop mode"""
        global is_looping
        is_looping = not is_looping
        
        # Update button color
        if is_looping:
            self.loop_btn.config(bg="green")
            status = "Loop ON"
        else:
            self.loop_btn.config(bg="red")
            status = "Loop OFF"
        
        self.update_status(status, "black")
    
    def refresh_recordings(self):
        """Scan playbacks folder and update dropdown"""
        try:
            # Get all .rec files from playbacks folder
            rec_files = sorted([f.stem for f in PLAYBACK_FOLDER.glob("*.rec")])
            
            if rec_files:
                self.recordings_dropdown['values'] = rec_files
                self.recordings_dropdown.current(0)
            else:
                self.recordings_dropdown['values'] = []
                self.recordings_var.set("(No recordings)")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading recordings folder: {e}")
    
    def on_record(self):
        """Start recording"""
        if not recorder.is_recording:
            recorder.start_recording()
            self.record_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.play_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)
    
    def on_stop(self):
        """Stop recording"""
        if recorder.is_recording:
            recorder.stop_recording()
            self.record_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.play_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
    
    def on_play(self):
        """Play the loaded recording"""
        global is_playing
        
        if not recorder.events:
            messagebox.showwarning("Warning", "No recording loaded. Please load a recording first.")
            return
        
        if recorder.is_recording:
            messagebox.showwarning("Warning", "Cannot play while recording. Press Stop first.")
            return
        
        is_playing = True
        self.update_status("Playing...", "blue")
        self.play_btn.config(state=tk.DISABLED)
        
        def play_and_reset():
            global is_playing
            playback_events(recorder.events)
            is_playing = False
            self.update_status("Idle", "black")
            self.play_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=play_and_reset, daemon=True)
        thread.start()
    
    def on_save(self):
        """Save current recording"""
        if not recorder.events:
            messagebox.showwarning("Warning", "No recording to save.")
            return
        
        # Ask for filename
        filename = simpledialog.askstring(
            "Save Recording",
            "Enter filename (without .rec extension):",
            parent=self.root
        )
        
        if filename:
            if save_recording(filename):
                messagebox.showinfo("Success", f"Recording saved to playbacks/{filename}.rec")
                self.refresh_recordings()
            else:
                messagebox.showerror("Error", "Failed to save recording.")
    
    def on_load(self):
        """Load selected recording"""
        selected = self.recordings_var.get()
        
        if not selected or selected == "(No recordings)":
            messagebox.showwarning("Warning", "Please select a recording to load.")
            return
        
        if load_recording(selected):
            messagebox.showinfo("Success", f"Loaded: {selected}.rec")
            self.update_status(f"Loaded: {selected}", "black")
        else:
            messagebox.showerror("Error", f"Failed to load: {selected}.rec")
    
    def update_status(self, message: str, color: str):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.root.update()
    
    def update_recording_status(self):
        """Update button states based on recording status"""
        if recorder.is_recording:
            self.record_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.play_btn.config(state=tk.DISABLED)
            self.save_btn.config(state=tk.DISABLED)
            self.update_status("Recording...", "green")
        else:
            self.record_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            if recorder.events:
                self.play_btn.config(state=tk.NORMAL)
                self.save_btn.config(state=tk.NORMAL)
            else:
                self.play_btn.config(state=tk.DISABLED)
                self.save_btn.config(state=tk.DISABLED)
            event_count = len(recorder.events)
            self.update_status(f"Idle ({event_count} events)" if event_count > 0 else "Idle", "black")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

# Global controller objects (for playback)
mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()


def main():
    """Main program - launches GUI with recording system"""
    
    global gui_reference
    
    # Create tkinter root window
    root = tk.Tk()
    
    # Create GUI
    gui = MacroRecorderGUI(root)
    
    # Update recorder's callback to use GUI's update_status method
    recorder.status_callback = gui.update_status
    
    # Create and start listeners
    mouse_listener = create_mouse_listener()
    keyboard_listener = create_keyboard_listener()
    
    try:
        # Start listeners in background
        mouse_listener.start()
        keyboard_listener.start()
        
        # Start GUI event loop
        root.mainloop()
    
    finally:
        # Stop listeners when window closes
        mouse_listener.stop()
        keyboard_listener.stop()


if __name__ == "__main__":
    main()
