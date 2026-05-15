# emulators/dht_emulator.py - DHT Temperature/Humidity Sensor Emulator
import sys
import os
import random
import time
import json
from threading import Thread
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import (
    TOPICS, DHT_PUBLISH_INTERVAL, DHT_TEMP_RANGE, DHT_HUMIDITY_RANGE,
    EMULATOR_NAMES, get_timestamp
)
from emulators.mqtt_client import MqttClient

class DhtEmulator(MqttClient):
    """DHT Sensor emulator - publishes temperature and humidity"""
    
    def __init__(self, room_name):
        super().__init__(EMULATOR_NAMES['dht'])
        self.room_name = room_name
        self.topic = TOPICS[f'dht_{room_name}']
        self.running = False
        self.temp = DHT_TEMP_RANGE[0]
        self.humidity = DHT_HUMIDITY_RANGE[0]
        self.ac_state = 'OFF'  # Track AC state (OFF, HEATING, COOLING)
        self.ac_setpoint = 22  # Track target temperature
    
    def on_message(self, client, userdata, msg):
        """Handle thermostat state changes"""
        topic = msg.topic
        message_str = str(msg.payload.decode('utf-8', 'ignore'))
        
        try:
            if 'thermostat/status' in topic:
                data = json.loads(message_str)
                self.ac_state = data.get('state', 'OFF')
                self.ac_setpoint = data.get('setpoint', 22)
                print(f"[{self.room_name} DHT] AC State: {self.ac_state}, Setpoint: {self.ac_setpoint}°C")
        except json.JSONDecodeError:
            pass
    
    def generate_readings(self):
        """Simulate realistic temperature/humidity variations"""
        # AC-based temperature adjustment
        if self.ac_state == 'HEATING':
            # Move toward setpoint when heating
            if self.temp < self.ac_setpoint:
                self.temp += random.uniform(0.3, 0.8)  # Positive trend toward setpoint
            else:
                self.temp += random.uniform(-0.2, 0.2)  # Maintain around setpoint
        elif self.ac_state == 'COOLING':
            # Move toward setpoint when cooling
            if self.temp > self.ac_setpoint:
                self.temp -= random.uniform(0.3, 0.8)  # Negative trend toward setpoint
            else:
                self.temp += random.uniform(-0.2, 0.2)  # Maintain around setpoint
        else:
            # Random walk when AC is OFF
            self.temp += random.uniform(-0.5, 0.5)
        
        # Humidity varies naturally
        self.humidity += random.uniform(-2, 2)
        
        # Keep within bounds
        self.temp = max(DHT_TEMP_RANGE[0], min(DHT_TEMP_RANGE[1], self.temp))
        self.humidity = max(DHT_HUMIDITY_RANGE[0], min(DHT_HUMIDITY_RANGE[1], self.humidity))
        
        return round(self.temp, 2), round(self.humidity, 1)
    
    def publish_reading(self):
        """Publish temperature and humidity reading"""
        temp, humidity = self.generate_readings()
        
        # Format: JSON message
        message = json.dumps({
            'temperature': temp,
            'humidity': humidity,
            'unit_temp': 'C',
            'unit_humidity': '%',
            'timestamp': get_timestamp()
        })
        
        self.publish(self.topic, message)
        print(f"[{self.room_name} DHT] Published: Temp={temp}°C, Humidity={humidity}%")
    
    def publishing_loop(self):
        """Continuous publishing loop"""
        while self.running:
            if self.connected:
                self.publish_reading()
            time.sleep(DHT_PUBLISH_INTERVAL)
    
    def start(self):
        """Start the emulator"""
        if not self.connect():
            return False
        
        self.start_loop()
        self.running = True

        time.sleep(1)
        
        # Subscribe to thermostat status to track AC state and setpoint
        self.subscribe(TOPICS['thermostat'])
        
        # Start publishing thread
        thread = Thread(target=self.publishing_loop, daemon=True)
        thread.start()
        print(f"[{self.room_name} DHT] Emulator started")
        return True
    
    def stop(self):
        """Stop the emulator"""
        self.running = False
        self.stop_loop()
        self.disconnect()
        print(f"[{self.room_name} DHT] Emulator stopped")

def run_dht_living_room():
    """Run living room DHT emulator"""
    emulator = DhtEmulator('living_room')
    emulator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        emulator.stop()

def run_dht_bedroom():
    """Run bedroom DHT emulator"""
    emulator = DhtEmulator('bedroom')
    emulator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        emulator.stop()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'bedroom':
        run_dht_bedroom()
    else:
        run_dht_living_room()
