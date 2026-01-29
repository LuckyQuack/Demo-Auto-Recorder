import os
import shutil
import json
import sys
import time
import webbrowser
import pyautogui
from obswebsocket import obsws, requests as obs_requests

class AutoRecorder:
    def __init__(self, segments_file, auto_mode=False, cs2_path=r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo"):
        self.segments_file = segments_file
        self.auto_mode = auto_mode
        self.cs2_path = cs2_path
        self.cs2_demo_folder = cs2_path
        self.cs2_cfg_folder = os.path.join(cs2_path, "cfg")
        
        # OBS Settings
        self.obs_host = "localhost"
        self.obs_port = 4455
        self.obs_password = ""
        self.obs_client = None

        # Load segments
        self.data = self._load_segments()

    def _load_segments(self):
        """Read segments.json file"""
        if not os.path.exists(self.segments_file):
            raise FileNotFoundError(f"Segments file not found: {self.segments_file}")
            
        with open(self.segments_file, 'r') as f:
            data = json.load(f)
            print(f"Loaded {len(data.get('segments', []))} segments for player {data.get('player', 'Unknown')}")
            return data

    def prepare_demo(self):
        """Copy demo to CS2 demo folder"""
        demo_filename = self.data.get("demo")
        if not demo_filename:
            raise ValueError("No demo filename found in segments.json")
            
        source_dir = os.path.dirname(os.path.abspath(self.segments_file))
        source_demo_path = os.path.join(source_dir, demo_filename)
        
        if not os.path.exists(source_demo_path):
             raise FileNotFoundError(f"Demo file not found at: {source_demo_path}")

        dest_path = os.path.join(self.cs2_demo_folder, demo_filename)
        
        if os.path.abspath(source_demo_path) != os.path.abspath(dest_path):
            print(f"Copying {source_demo_path} to {dest_path}...")
            shutil.copy2(source_demo_path, dest_path)
        else:
            print("Demo file is already in destination folder.")

        return demo_filename

    def generate_cs2_config(self, demo_filename):
        """Generate auto_record.cfg (aliases only, no playdemo)"""
        player_name = self.data.get("player", "target")
        segments = self.data.get("segments", [])
        
        config_path = os.path.join(self.cs2_cfg_folder, 'auto_record.cfg')
        
        print(f"Generating config at: {config_path}")
        
        with open(config_path, 'w') as f:
            f.write('cl_draw_only_deathnotices 0\n')
            f.write('cl_drawhud 1\n')
            f.write('r_drawviewmodel 1\n')
            f.write('demoui 0\n')
            
            # Trimming offsets (in seconds)
            start_trim = 2.0 
            
            for i, segment in enumerate(segments):
                start_tick = segment.get("start_tick")
                if start_tick is not None:
                    # Adjust start tick to skip early moments (~2s)
                    adjusted_tick = start_tick + int(start_trim * 64)
                    # Alias to go to tick
                    f.write(f'alias seg{i} "demo_gototick {adjusted_tick}; demo_resume"\n')
            
            f.write('echo "=== Auto-recorder ready ==="\n')
        
        print(f"Generated config: {config_path}")

    def launch_cs2(self):
        """Launch CS2 via Steam URL"""
        launch_url = 'steam://rungameid/730//+exec auto_record.cfg -console -novid'
        print(f"Launching CS2: {launch_url}")
        webbrowser.open(launch_url)
        
        print("Waiting 30 seconds for CS2 to launch...")
        time.sleep(30)
        
        if self.auto_mode:
            print("Auto-mode: Waiting 30s (assuming loaded)...")
        else:
            input("Press ENTER when CS2 is fully loaded and you see the main menu/console...")

    def load_demo(self):
        """Send playdemo command to console"""
        demo_filename = self.data.get("demo")
        print(f"Loading demo: {demo_filename}...")
        
        self.send_console_command(f'playdemo "{demo_filename}"')
        
        # Wait for demo load
        print("Waiting for demo to load...")
        if self.auto_mode:
            print("Auto-mode: Waiting 7s for demo load...")
            time.sleep(7)
            # Re-apply config settings just in case
            self.send_console_command("exec auto_record", fast=True)
            time.sleep(1)
            self.send_console_command("demo_pause", fast=True)
        else:
            input("Press ENTER when the demo is fully loaded and paused...")
            self.send_console_command("exec auto_record", fast=True)
            self.send_console_command("demo_pause", fast=True)

    def connect_obs(self):
        """Connect to OBS WebSocket"""
        print("Connecting to OBS...")
        try:
            self.obs_client = obsws(self.obs_host, self.obs_port, self.obs_password)
            self.obs_client.connect()
            print("Connected to OBS!")
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            print("Make sure OBS is running and WebSocket server is enabled (Tools -> WebSocket Server Settings)")
            sys.exit(1)

    def send_console_command(self, cmd, fast=False):
        """Send command to CS2 console via keyboard"""
        try:
            # Assume console is closed, open it
            pyautogui.press('`') 
            if not fast:
                time.sleep(0.5)
            else:
                time.sleep(0.1)
            
            # Clear any existing text
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            
            if fast:
                pyautogui.write(cmd) # Instant
            else:
                pyautogui.write(cmd, interval=0.05) # Type slightly slower
            
            if not fast:
                time.sleep(0.1)
            
            pyautogui.press('enter')
            
            if not fast:
                time.sleep(0.1)
                
            # Close console
            pyautogui.press('`')
        except pyautogui.FailSafeException:
            print("PyAutoGUI FailSafe triggered from mouse movement.")
            if self.auto_mode:
                print("Continuing...")
            else:
                sys.exit(1)

    def get_account_id(self, steamid64):
        """Convert SteamID64 to AccountID (SteamID3)"""
        try:
            return int(steamid64) - 76561197960265728
        except:
            return None

    def ensure_spectating(self):
        """Force spectate the target player using user-identified sequence"""
        steamid = self.data.get("steamid")
        player_name = self.data.get("player")
        account_id = self.get_account_id(steamid)

        # Player Name
        print(f"Spectating Name: {player_name}")
        self.send_console_command(f'spec_player "{player_name}"', fast=True)
        time.sleep(0.1)

    def record_segments(self):
        """Main recording loop"""
        segments = self.data.get("segments", [])
        
        # Timing Trims (seconds)
        start_trim = 1.0 
        end_trim = 3.5 # Cut 3.5s from the end (death/round end)
        
        print(f"\nStarting recording loop for {len(segments)} segments...")
        
        for i, segment in enumerate(segments):
            duration = segment.get("duration_sec", 10)
            start_tick = segment.get("start_tick")
            
            # Calculate actual record time
            record_duration = duration - start_trim - end_trim
            if record_duration < 1.0:
                 record_duration = 2.0 # Minimum sanity clip
            
            print(f"\n--- Segment {i+1}/{len(segments)} ---")
            print(f"Original Duration: {duration:.2f}s")
            print(f"Record Duration: {record_duration:.2f}s (Trim start: {start_trim}s, End: {end_trim}s)")
            
            if self.auto_mode:
                print(f"Auto-mode: Recording segment {i+1}...")
            else:
                user_input = input("Press ENTER to record this segment (or 's' to skip, 'q' to quit): ")
                if user_input.lower() == 's':
                    continue
                if user_input.lower() == 'q':
                    break
                
            # 1. Execute alias to jump to tick
            print(f"Jumping to segment {i}...")
            self.send_console_command(f"seg{i}", fast=True)
            
            # Wait for seek (demo_gototick takes time)
            time.sleep(3.0) 
            
            # 2. Ensure Spectating
            self.ensure_spectating()
            time.sleep(1.0) # wait for camera switch
            
            # 3. Start Recording
            print("Start Recording...")
            self.obs_client.call(obs_requests.StartRecord())
            
            # 4. Wait for duration
            print(f"Recording for {record_duration:.1f} seconds...")
            time.sleep(record_duration)
            
            # 5. Stop Recording
            print("Stop Recording...")
            self.obs_client.call(obs_requests.StopRecord())
            
            # 6. Pause demo to keep things stable
            self.send_console_command("demo_pause", fast=True)
            
        print("\nRecording complete!")

    def cleanup(self):
        if self.obs_client:
            self.obs_client.disconnect()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='CS2 Auto Recorder')
    parser.add_argument('segments_file', help='Path to segments.json')
    parser.add_argument('--auto', action='store_true', help='Run in auto mode without manual confirmation')
    parser.add_argument('--only-segments', type=int, nargs='+', help='Process only specific segment indices (0-based)')
    args = parser.parse_args()

    recorder = AutoRecorder(args.segments_file, auto_mode=args.auto)
    
    # Filter segments if requested
    if args.only_segments:
        all_segments = recorder.data.get("segments", [])
        filtered_segments = []
        for idx in args.only_segments:
            if 0 <= idx < len(all_segments):
                filtered_segments.append(all_segments[idx])
            else:
                print(f"Warning: Segment index {idx} out of range, skipping.")
        
        if not filtered_segments:
            print("No valid segments selected. Exiting.")
            sys.exit(1)
            
        print(f"Filtering to {len(filtered_segments)} selected segments: {args.only_segments}")
        recorder.data["segments"] = filtered_segments
    
    try:
        recorder.prepare_demo()
        recorder.generate_cs2_config(recorder.data.get("demo"))
        
        recorder.connect_obs()
        recorder.launch_cs2()
        recorder.load_demo()
        recorder.record_segments()
        
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main()
