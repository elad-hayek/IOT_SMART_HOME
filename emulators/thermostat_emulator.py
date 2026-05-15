# emulators/thermostat_emulator.py - Thermostat/AC Unit Controller Emulator
import sys
import os
import time
import json
from threading import Thread
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import (
    TOPICS, THERMOSTAT_INITIAL_STATE, THERMOSTAT_INITIAL_SETPOINT,
    THERMOSTAT_SETPOINT_MIN, THERMOSTAT_SETPOINT_MAX,
    EMULATOR_NAMES, get_timestamp
)
from emulators.mqtt_client import MqttClient

class ThermostatEmulator(MqttClient):
    """Thermostat/AC Unit controller"""
    
    def __init__(self):
        super().__init__(EMULATOR_NAMES['thermostat'])
        self.topic_status = TOPICS['thermostat']
        self.topic_control = TOPICS['ac_control']
        self.state = THERMOSTAT_INITIAL_STATE  # 'OFF', 'HEATING', 'COOLING', 'ON'
        self.setpoint = THERMOSTAT_INITIAL_SETPOINT  # Target temperature
        self.running = False
    
    def on_message(self, client, userdata, msg):
        """Handle control commands"""
        topic = msg.topic
        message = str(msg.payload.decode('utf-8', 'ignore'))
        
        print(f"[Thermostat] Received command: {message}")
        
        try:
            command = json.loads(message)
            if 'state' in command:
                self.state = command['state']
            if 'setpoint' in command:
                setpoint = float(command['setpoint'])
                if THERMOSTAT_SETPOINT_MIN <= setpoint <= THERMOSTAT_SETPOINT_MAX:
                    self.setpoint = setpoint
                    print(f"[Thermostat] Setpoint updated to {self.setpoint}°C")
            
            # Publish state change
            self.publish_state()
        except json.JSONDecodeError:
            print(f"[Thermostat] Invalid JSON command: {message}")
    
    def publish_state(self):
        """Publish thermostat state"""
        message = json.dumps({
            'state': self.state,
            'setpoint': self.setpoint,
            'timestamp': get_timestamp()
        })
        
        self.publish(self.topic_status, message)
        print(f"[Thermostat] State: {self.state}, Setpoint: {self.setpoint}°C")
    
    def status_update_loop(self):
        """Periodically publish state"""
        while self.running:
            if self.connected:
                self.publish_state()
            time.sleep(10)  # Update every 10 seconds
    
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
        print(f"[Thermostat] Emulator started")
        return True
    
    def stop(self):
        """Stop the emulator"""
        self.running = False
        self.stop_loop()
        self.disconnect()
        print(f"[Thermostat] Emulator stopped")

def run_thermostat():
    """Run thermostat emulator"""
    emulator = ThermostatEmulator()
    emulator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        emulator.stop()

if __name__ == '__main__':
    run_thermostat()
