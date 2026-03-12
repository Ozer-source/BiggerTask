# BiggerTask - Python Macro Recorder

A complete Python implementation of a macro recorder similar to TinyTask. This program records mouse and keyboard actions and can replay them with exact timing reproduction.

## Features

✅ **Record Mouse & Keyboard Activity**
- Mouse movement tracking
- Left and right click detection (press and release)
- Mouse scrolling
- All keyboard key presses and releases
- Special key support (Shift, Ctrl, Alt, etc.)

✅ **Accurate Timing**
- Each event is timestamped relative to recording start
- Playback reproduces exact timing between events
- Adjustable playback speed

✅ **Custom File Format (.rec)**
- Save recordings to `.rec` files
- Load previously saved recordings
- JSON-based format for easy inspection

✅ **Playback Control**
- Play back recordings exactly as recorded
- Loop mode for repeated playback
- Speed multiplier for faster/slower playback

✅ **Keyboard Shortcuts**
- **F8**: Start recording
- **F9**: Stop recording
- **F10**: Play back current recording
- **F11**: Toggle loop mode

## Installation

### Requirements
- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
pip install pynput
```

The `pynput` library provides:
- Mouse listener and controller for tracking and simulating mouse events
- Keyboard listener and controller for tracking and simulating keyboard events

### Step 2: Download BiggerTask

Download `BiggerTask.py` to your preferred location.

## Running the Program

### Basic Usage

```bash
python BiggerTask.py
```

The program will:
1. Start listening for keyboard and mouse events
2. Display the interactive command prompt `>`
3. Show instructions for using keyboard shortcuts

### Example Session

```
============================================================
   BiggerTask - Python Macro Recorder
============================================================

Starting listeners... Press F8 to begin recording!
Type 'help' for commands or 'exit' to quit.

> help

============================================================
BiggerTask - Macro Recorder
============================================================

Keyboard Shortcuts:
  F8   - Start recording
  F9   - Stop recording
  F10  - Play back recording
  F11  - Toggle loop mode

Shell Commands:
  save [filename]  - Save recording to .rec file
  load [filename]  - Load recording from .rec file
  clear            - Clear current recording
  info             - Show recording info
  speed [N]        - Set playback speed (1.0 = normal)
  help             - Show this help
  exit             - Exit the program
============================================================

> save my_macro
✓ Recording saved to: my_macro.rec

> load my_macro
✓ Loaded: my_macro.rec (145 events, 12.34s)

> exit
✓ Program closed
```

## How to Use

### Recording a Macro

1. **Start the program**: `python BiggerTask.py`
2. **Press F8** to begin recording
3. **Perform actions** with your mouse and keyboard
4. **Press F9** to stop recording
5. Observe: `⏹ Recording stopped. Captured X events.`

### Saving a Recording

After recording, save to a `.rec` file:

```
> save my_first_macro
✓ Recording saved to: my_first_macro.rec
```

The file can be named anything; `.rec` extension is added automatically.

### Loading a Recording

Load a previously saved recording:

```
> load my_first_macro
✓ Loaded: my_first_macro.rec (145 events, 12.34s)
```

### Playing Back a Recording

**Option 1**: Using keyboard shortcut
- Press **F10** to play back the current recording

**Option 2**: Using shell command (future-proofing)
- After loading a file, press F10

### Viewing Recording Info

```
> info

Recording Info:
  Events: 145
  Duration: 12.34 seconds
  Status: Idle
```

### Adjusting Playback Speed

Play back at different speeds:

```
> speed 0.5
Playback speed: 0.5x

> speed 2.0
Playback speed: 2.0x

> speed 1.0
Playback speed: 1.0x
```

Speed values:
- `0.5`: Half speed (slower)
- `1.0`: Normal speed (default)
- `2.0`: Double speed (faster)

### Loop Mode

Toggle continuous playback:

```
> F11
🔄 Loop mode: ON

> F11
🔄 Loop mode: OFF
```

When loop mode is enabled, pressing F10 will repeatedly play the recording.

### Clearing a Recording

Remove all events from memory:

```
> clear
✓ Recording cleared
```

## Program Architecture

### 1. **Data Structures** (Top of file)

Events are stored as dictionaries with the following structures:

**Mouse Move Event**:
```python
{
    "type": "mouse_move",
    "x": 500,
    "y": 300,
    "time": 0.432
}
```

**Mouse Click Event**:
```python
{
    "type": "mouse_click",
    "button": "left",  # or "right"
    "pressed": True,   # True = press, False = release
    "x": 500,
    "y": 300,
    "time": 0.435
}
```

**Mouse Scroll Event**:
```python
{
    "type": "mouse_scroll",
    "x": 500,
    "y": 300,
    "dx": 1,           # horizontal scroll
    "dy": 3,           # vertical scroll
    "time": 0.438
}
```

**Keyboard Event**:
```python
{
    "type": "key_press",  # or "key_release"
    "key": "a",
    "time": 0.5
}
```

### 2. **Recording State** (RecorderState class)

Manages:
- Recording status (is_recording)
- Event list storage
- Recording start time
- Event timestamp calculation

```python
recorder = RecorderState()
recorder.start_recording()   # Begin recording
recorder.add_event(event)    # Record an event
recorder.stop_recording()    # End recording
```

### 3. **Input Listeners** (Listener Functions)

#### Mouse Listener
- Tracks mouse position
- Detects all click events
- Records scroll wheel movements

```python
listener = create_mouse_listener()
listener.start()
```

#### Keyboard Listener
- Detects key presses and releases
- Identifies special keys (Shift, Ctrl, etc.)
- Intercepts hotkey combinations (F8, F9, F10, F11)

```python
listener = create_keyboard_listener()
listener.start()
```

### 4. **File Operations**

#### save_recording(filename)
Saves events to `.rec` file:
```python
save_recording("my_macro")
# Creates: my_macro.rec
```

File format (JSON):
```json
{
  "version": 1,
  "event_count": 145,
  "total_duration": 12.34,
  "events": [
    {"type": "mouse_move", "x": 500, "y": 300, "time": 0.1},
    {"type": "key_press", "key": "a", "time": 0.5},
    ...
  ]
}
```

#### load_recording(filename)
Loads events from `.rec` file:
```python
load_recording("my_macro")
# Loads: my_macro.rec into recorder.events
```

### 5. **Playback Engine**

#### perform_event(event)
Executes a single recordedevent during playback.

Handles all event types by:
- Moving mouse cursor to position
- Pressing/releasing buttons
- Typing keys
- Scrolling

#### playback_events(events)
Main playback loop:

```
1. Loop through all events
2. For each event:
   - Calculate delay from previous event
   - Sleep for delay duration
   - Execute the event
3. If loop mode enabled, repeat
```

**Timing Algorithm**:
```python
previous_time = 0.0
for event in events:
    delay = (event_time - previous_time) / playback_speed
    sleep(delay)
    perform_event(event)
    previous_time = event_time
```

### 6. **Hotkey Handler**

```python
handle_hotkey_press(key):
  F8:  Start recording
  F9:  Stop recording
  F10: Play back events
  F11: Toggle loop mode
```

## Technical Details

### Timing Precision

Events are timestamped using `time.time()`:

```python
recording_start = time.time()

# When event occurs:
event_time = time.time() - recording_start
```

This ensures:
- All timestamps are relative (not absolute)
- Timing is independent of when you started the program
- Playback can reproduce exact delays

### Thread Safety

The program uses threading:
- **Main thread**: Interactive shell for user commands
- **Listener threads**: Background tracking of mouse/keyboard
- **Playback thread**: Runs playback in background (non-blocking)

This allows you to interact with the shell while playback is running.

### Special Key Handling

Special keys are converted to readable names:

```python
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
```

### Error Handling

The program gracefully handles:
- Missing files
- Invalid JSON
- Invalid playback speeds
- Keyboard interrupts (Ctrl+C)
- Missing event data

## Common Workflows

### Workflow 1: Record and Save a Simple Macro

```
> F8
▶ Recording started...

[Perform mouse clicks and type text]

> F9
⏹ Recording stopped. Captured 42 events.

> save notepad_macro
✓ Recording saved to: notepad_macro.rec

> exit
```

### Workflow 2: Load and Replay Multiple Times

```
> load notepad_macro
✓ Loaded: notepad_macro.rec (42 events, 5.23s)

> F11
🔄 Loop mode: ON

> F10
▶ Starting playback...
Loop 2...
Loop 3...
[Let it loop several times, then press Ctrl+C or F11 again]

> F11
🔄 Loop mode: OFF
```

### Workflow 3: Speed Up a Recording

```
> load notepad_macro
✓ Loaded: notepad_macro.rec (42 events, 5.23s)

> speed 2.0
Playback speed: 2.0x

> F10
▶ Starting playback...
[Recording plays in 2.6 seconds instead of 5.23]
```

## Limitations & Future Improvements

### Current Limitations
- Does not record window focus changes
- Does not record clipboard operations
- Does not record typing of passwords (security feature)
- Playback requires the same screen resolution as recording

### Possible Future Features
- Screen resolution adjustment for different monitors
- Hotspot clicking (click relative to image positions)
- Conditional logic in macros
- Event filtering/editing before playback
- GUI interface with tkinter
- Encryption for sensitive recordings
- Cloud backup of .rec files

## Troubleshooting

### "Permission denied" error

**Issue**: Program cannot access mouse/keyboard on some Linux systems

**Solution**: 
```bash
sudo python BiggerTask.py
```

### Playback not working

**Issue**: Recorded keys not appearing in application

**Solutions**:
1. Make sure the target application is in focus when playback starts
2. Ensure playback speed is not too fast (try `speed 0.5`)
3. Some applications require focus/click before accepting input

### .rec file not found

**Issue**: File save/load commands fail

**Solutions**:
1. Specify full path: `save /path/to/my_macro`
2. Use quotes with spaces: `save "my macro"`
3. Check current directory: `load ./my_macro`

## Code Quality Features

✅ **Clean & Modular**
- Separated concerns (input, storage, file I/O, playback)
- Dataclass structures for type safety
- Clear function names and docstrings

✅ **Well Commented**
- Section headers for each major component
- Inline comments explaining complex logic
- Docstring for every function

✅ **Extensible Design**
- Easy to add new event types
- Simple to implement new file formats
- Pluggable listener architecture

✅ **Robust Error Handling**
- Try-except blocks around risky operations
- Gracefuldefaults for invalid input
- User-friendly error messages

## Example Programs You Can Record

### Example 1: Auto-Fill Form
```
1. Click username field
2. Type username
3. Press Tab
4. Type password
5. Click Submit button
```

### Example 2: Screenshot & Edit
```
1. Press Shift+S (screenshot tool)
2. Select area
3. Right-click and select edit
4. Draw on image
5. Save file
```

### Example 3: Data Entry
```
1. Open spreadsheet
2. Type data in cells
3. Navigate with arrow keys
4. Copy/paste values
```

## System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.7+
- **RAM**: Minimal (< 50MB)
- **Disk**: Minimal (< 10MB)

## License

This code is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all dependencies are installed: `pip install pynput`
3. Try running with Python 3.8+
4. Check your system's permissions for mouse/keyboard access

---

**Happy Recording! 🎙️**
#   B i g g e r T a s k  
 