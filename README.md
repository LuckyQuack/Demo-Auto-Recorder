# CS2 Demo Auto-Recorder

Automated pipeline to extract clips from Counter-Strike 2 demo files.

## Overview
This tool automates the process of turning a `.dem.zst` file into individual video clips of a specific player's highlights (or all rounds/deaths).

**Workflow**:
1.  **Decompress**: Converts `.dem.zst` to `.dem`.
2.  **Parse**: Analyzes the demo to find player segments (Round Start -> Death/End).
3.  **Record**: Automates CS2 and OBS Studio to record these segments.

## Prerequisites

*   **Counter-Strike 2**
*   **OBS Studio**
*   **OBS WebSocket** 
*   **Python 3.10+**
*   **.NET 8.0 SDK**

## Installation

1.  **Install Python Dependencies**:
    ```bash
    pip install -r src/recorder/requirements.txt
    ```

2.  **Build the Parser**:
    ```powershell
    cd src/parser
    dotnet build -c Release
    ```

## Usage Workflow

### 1. Decompress Demo
If you have a compressed Faceit demo file (`.dem.zst`), unpack it first.
```bash
python src/recorder/unpack_demo.py "input_file.dem.zst" "output_file.dem"
```

### 2. Parse Demo
Run the C# parser to analyze the demo and generate a `segments.json` file.
*   `<DEMO_PATH>`: Path to the `.dem` file.
*   `<STEAMID64>`: The SteamID64 of the player you want to highlight.

```powershell
.\src\parser\bin\Debug\net8.0\parser.exe "path\to\demo.dem" 76561199032006224
```
*Output: `segments.json` in the project root.*

### 3. Auto-Record Clips
Launch the auto-recorder. This script will:
*   Launch CS2.
*   Connect to OBS.
*   Load the demo.
*   Fast-forward to each segment.
*   Record the gameplay automatically.

```bash
python src/recorder/auto_recorder.py segments.json --auto
```

**Important**:
*   **Do not touch your mouse/keyboard** while the recorder is running. It uses the console to control the game.
*   The script waits **30 seconds** for CS2 to launch.
*   It automatically trims **dead time** (skips freeze time, cuts shortly after death).

## Configuration
You can tweak settings in `src/recorder/auto_recorder.py`:
*   `self.obs_password`: Set this if your OBS WebSocket has a password.
*   `start_trim` / `end_trim`: Adjust how much time is cut from start/end of clips.

## Directory Structure
*   `src/parser/`: C# Demo parsing logic.
*   `src/recorder/`: Python automation scripts.
*   `segments.json`: generated recording instructions.

## Acknowledgments
*   [DemoFile](https://github.com/saul/demofile-net) by [saul](https://github.com/saul) - High-performance CS2 demo parser library.
