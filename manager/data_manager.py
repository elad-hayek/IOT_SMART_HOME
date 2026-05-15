# manager/data_manager.py - Central data collection and alarm manager
import sys
import os
import time
import json
from threading import Thread
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import (
    MANAGER_SUBSCRIBE_TOPIC, TOPICS, ALARM_CHECK_INTERVAL,
    TEMP_WARNING_LOW, TEMP_ALERT_LOW, TEMP_WARNING_HIGH, TEMP_ALERT_HIGH,
    EMULATOR_NAMES, get_timestamp
)
from emulators.mqtt_client import MqttClient
from db.data_acq import da

class DataManager(MqttClient):
    """Central manager - receives MQTT messages and stores in database"""
    
    def __init__(self):
        super().__init__(EMULATOR_NAMES['manager'])
        self.subscribe_topic = MANAGER_SUBSCRIBE_TOPIC
        self.running = False
        self.last_temp = {}  # Track last temperatures for alarm logic
        self.last_thermostat_state = None  # Track state changes to control relay
    
    def on_message(self, client, userdata, msg):
        """Process incoming MQTT message and store in database"""
        topic = msg.topic
        message_str = str(msg.payload.decode('utf-8', 'ignore'))
        
        print(f"[Manager] Message from {topic}: {message_str}")
        
        try:
            data = json.loads(message_str)
            timestamp = get_timestamp()
            
            # DHT Sensor messages
            if 'living_room/dht' in topic:
                device_name = 'DHT_Living_Room'
                temp = data.get('temperature')
                humidity = data.get('humidity')
                
                if temp is not None:
                    da.add_iot_data(timestamp, device_name, 'temperature', temp, '°C')
                    self.last_temp[device_name] = temp
                if humidity is not None:
                    da.add_iot_data(timestamp, device_name, 'humidity', humidity, '%')
            
            elif 'bedroom/dht' in topic:
                device_name = 'DHT_Bedroom'
                temp = data.get('temperature')
                humidity = data.get('humidity')
                
                if temp is not None:
                    da.add_iot_data(timestamp, device_name, 'temperature', temp, '°C')
                    self.last_temp[device_name] = temp
                if humidity is not None:
                    da.add_iot_data(timestamp, device_name, 'humidity', humidity, '%')
            
            # Thermostat messages
            elif 'thermostat/status' in topic:
                device_name = 'Thermostat'
                state = data.get('state')
                setpoint = data.get('setpoint')
                
                if state:
                    da.add_iot_data(timestamp, device_name, 'state', state, '')
                    
                    # Auto-control relay based on thermostat state
                    if state != self.last_thermostat_state:
                        self.last_thermostat_state = state
                        relay_state = 'ON' if state in ['HEATING', 'COOLING'] else 'OFF'
                        self.send_relay_command(relay_state)
                
                if setpoint:
                    da.add_iot_data(timestamp, device_name, 'setpoint', setpoint, '°C')
            
            # Relay messages
            elif 'ac/relay/status' in topic:
                device_name = 'AC_Relay'
                relay_state = data.get('relay_state')
                
                if relay_state:
                    da.add_iot_data(timestamp, device_name, 'relay_state', relay_state, '')
            
            else:
                # Generic message handling
                print(f"[Manager] Unhandled topic: {topic}")
        
        except json.JSONDecodeError:
            print(f"[Manager] Invalid JSON: {message_str}")
    
    def send_relay_command(self, relay_state):
        """Send command to relay to turn ON/OFF"""
        command = json.dumps({
            'state': relay_state,
            'timestamp': get_timestamp()
        })
        self.publish(TOPICS['relay_control'], command)
        print(f"[Manager] Sent relay command: {relay_state}")
    
    def check_alarms(self):
        """Check temperature readings against thresholds and trigger alerts"""
        for device_name, temp in self.last_temp.items():
            severity = 'normal'
            alert_msg = None
            
            if temp < TEMP_ALERT_LOW:
                severity = 'alert'
                alert_msg = f"CRITICAL: {device_name} temperature {temp}°C below alert threshold {TEMP_ALERT_LOW}°C"
            elif temp < TEMP_WARNING_LOW:
                severity = 'warning'
                alert_msg = f"WARNING: {device_name} temperature {temp}°C below warning threshold {TEMP_WARNING_LOW}°C"
            elif temp > TEMP_ALERT_HIGH:
                severity = 'alert'
                alert_msg = f"CRITICAL: {device_name} temperature {temp}°C above alert threshold {TEMP_ALERT_HIGH}°C"
            elif temp > TEMP_WARNING_HIGH:
                severity = 'warning'
                alert_msg = f"WARNING: {device_name} temperature {temp}°C above warning threshold {TEMP_WARNING_HIGH}°C"
            
            if alert_msg:
                # Log alert to database
                da.add_iot_data(get_timestamp(), 'ALERT_SYSTEM', 'temperature_alarm', 0, device_name, severity)
                # Publish alert to MQTT
                alert_payload = json.dumps({
                    'device': device_name,
                    'temperature': temp,
                    'severity': severity,
                    'message': alert_msg,
                    'timestamp': get_timestamp()
                })
                self.publish(TOPICS['alerts_temperature'], alert_payload)
                print(f"[Manager] {alert_msg}")
    
    def alarm_check_loop(self):
        """Periodically check for alarm conditions"""
        while self.running:
            if self.connected:
                self.check_alarms()
            time.sleep(ALARM_CHECK_INTERVAL)
    
    def start(self):
        """Start the data manager"""
        if not self.connect():
            return False
        
        self.start_loop()
        self.running = True
        
        time.sleep(1)

        # Subscribe to all home topics
        self.subscribe(self.subscribe_topic)
        print(f"[Manager] Subscribed to {self.subscribe_topic}")
        
        # Start alarm checking thread
        thread = Thread(target=self.alarm_check_loop, daemon=True)
        thread.start()
        
        print(f"[Manager] Data manager started")
        return True
    
    def stop(self):
        """Stop the manager"""
        self.running = False
        self.stop_loop()
        self.disconnect()
        print(f"[Manager] Data manager stopped")

def run_data_manager():
    """Run data manager"""
    manager = DataManager()
    manager.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()

if __name__ == '__main__':
    run_data_manager()
