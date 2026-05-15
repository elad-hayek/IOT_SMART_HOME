# emulators/relay_emulator.py - AC Relay/Switch Emulator
import sys
import os
import time
import json
from threading import Thread
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import TOPICS, EMULATOR_NAMES, get_timestamp
from emulators.mqtt_client import MqttClient

class RelayEmulator(MqttClient):
    """AC Relay/Switch controller"""
    
    def __init__(self):
        super().__init__(EMULATOR_NAMES['relay'])
        self.topic_status = TOPICS['ac_relay']
        self.topic_control = TOPICS['relay_control']
        self.state = 'OFF'  # 'ON' or 'OFF'
        self.running = False
    
    def on_message(self, client, userdata, msg):
        """Handle relay control commands"""
        topic = msg.topic
        message = str(msg.payload.decode('utf-8', 'ignore'))
        
        print(f"[Relay] Received command: {message}")
        
        try:
            command = json.loads(message)
            if 'state' in command:
                new_state = command['state'].upper()
                if new_state in ['ON', 'OFF']:
                    self.state = new_state
                    print(f"[Relay] State changed to {self.state}")
                    # Simulate relay activation delay
                    time.sleep(0.5)
                    self.publish_state()
        except json.JSONDecodeError:
            print(f"[Relay] Invalid JSON command: {message}")
    
    def publish_state(self):
        """Publish relay state"""
        message = json.dumps({
            'relay_state': self.state,
            'timestamp': get_timestamp()
        })
        
        self.publish(self.topic_status, message)
        print(f"[Relay] Published state: {self.state}")
    
    def status_update_loop(self):
        """Periodically publish state"""
        while self.running:
            if self.connected:
                self.publish_state()
            time.sleep(15)  # Update every 15 seconds
    
    def start(self):
        """Start the emulator"""
        if not self.connect():
            return False
        
        self.start_loop()
        self.running = True

        time.sleep(1)
        
        # Subscribe to control commands
        self.subscribe(self.topic_control)
        
        # Start status update thread
        thread = Thread(target=self.status_update_loop, daemon=True)
        thread.start()
        
        # Publish initial state
        self.publish_state()
        print(f"[Relay] Emulator started")
        return True
    
    def stop(self):
        """Stop the emulator"""
        self.running = False
        self.stop_loop()
        self.disconnect()
        print(f"[Relay] Emulator stopped")

def run_relay():
    """Run relay emulator"""
    emulator = RelayEmulator()
    emulator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        emulator.stop()

if __name__ == '__main__':
    run_relay()
