# main.py - Main entry point (optional - for reference)
# This script shows how to start all components programmatically
# In practice, each component runs in its own terminal for better control and visibility

import subprocess
import sys
import time
import os

def run_component(script_path, args=None, name="Component"):
    """Run a component in a subprocess"""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"[Main] Starting {name}...")
    try:
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"[Main] Failed to start {name}: {e}")
        return None

def main():
    """Start all system components"""
    print("="*60)
    print("Smart Home Climate Control System - Starting")
    print("="*60)
    
    processes = []
    
    # Startup sequence
    print("\n[Main] Waiting for broker connection...")
    time.sleep(2)
    
    print("[Main] Starting Data Manager...")
    p_manager = run_component("manager/data_manager.py", name="Data Manager")
    if p_manager:
        processes.append(p_manager)
        time.sleep(2)  # Let manager connect first
    
    print("[Main] Starting DHT Emulators...")
    p_dht1 = run_component("emulators/dht_emulator.py", name="DHT Living Room")
    if p_dht1:
        processes.append(p_dht1)
    
    p_dht2 = run_component("emulators/dht_emulator.py", ["bedroom"], name="DHT Bedroom")
    if p_dht2:
        processes.append(p_dht2)
    
    time.sleep(1)
    
    print("[Main] Starting Thermostat Controller...")
    p_thermo = run_component("emulators/thermostat_emulator.py", name="Thermostat")
    if p_thermo:
        processes.append(p_thermo)
    
    print("[Main] Starting AC Relay...")
    p_relay = run_component("emulators/relay_emulator.py", name="AC Relay")
    if p_relay:
        processes.append(p_relay)
    
    time.sleep(1)
    
    print("[Main] Starting GUI Dashboard...")
    p_gui = run_component("gui/gui_main.py", name="GUI")
    if p_gui:
        processes.append(p_gui)
    
    print("\n" + "="*60)
    print("✅ All components started!")
    print("="*60)
    print("\nRunning all processes. Press Ctrl+C to stop all components.\n")
    
    try:
        # Wait for all processes
        for p in processes:
            if p:
                p.wait()
    
    except KeyboardInterrupt:
        print("\n\n[Main] Shutting down all components...")
        for i, p in enumerate(processes):
            if p:
                p.terminate()
                print(f"[Main] Terminated process {i+1}")
        
        # Wait for graceful shutdown
        time.sleep(1)
        
        # Kill any remaining processes
        for p in processes:
            if p:
                p.kill()
        
        print("[Main] All components stopped.")
        print("="*60)

if __name__ == '__main__':
    # NOTE: This approach captures subprocess output
    # For better terminal interaction, run each component in separate terminal:
    #   Terminal 1: python manager/data_manager.py
    #   Terminal 2: python emulators/dht_emulator.py
    #   Terminal 3: python emulators/dht_emulator.py bedroom
    #   Terminal 4: python emulators/thermostat_emulator.py
    #   Terminal 5: python emulators/relay_emulator.py
    #   Terminal 6: python gui/gui_main.py
    
    # Uncomment to use subprocess approach:
    # main()
    
    print("See README.md for manual startup instructions")
    print("Or run: python main.py  (uncomment main() above)")
