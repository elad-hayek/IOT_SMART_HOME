# emulators/mqtt_client.py - Base MQTT client class (reused from SmartHome pattern)
import paho.mqtt.client as mqtt
import random
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import BROKER_IP, BROKER_PORT, USERNAME, PASSWORD

class MqttClient:
    """Base MQTT client class for emulators"""
    
    def __init__(self, client_name):
        self.broker = BROKER_IP
        self.port = BROKER_PORT
        self.username = USERNAME
        self.password = PASSWORD
        self.client_name = client_name + str(random.randrange(1, 10000000))
        self.client = None
        self.connected = False
        self.on_connected_callback = None
    
    def set_on_connected_callback(self, callback):
        """Set callback when connected"""
        self.on_connected_callback = callback
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for connection"""
        if rc == 0:
            print(f"[{self.client_name}] Connected to broker")
            self.connected = True
            if self.on_connected_callback:
                self.on_connected_callback()
        else:
            print(f"[{self.client_name}] Connection failed with code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for disconnection"""
        print(f"[{self.client_name}] Disconnected from broker")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Override this in subclass"""
        pass
    
    def on_log(self, client, userdata, level, buf):
        """Log callback"""
        pass
    
    def connect(self):
        """Connect to MQTT broker"""
        self.client = mqtt.Client(self.client_name, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log
        
        if self.username:
            self.client.username_pw_set(self.username, self.password)
        
        try:
            print(f"[{self.client_name}] Connecting to {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port)
            return True
        except Exception as e:
            print(f"[{self.client_name}] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        if self.client:
            self.client.disconnect()
    
    def publish(self, topic, message):
        """Publish message to topic"""
        if self.connected:
            self.client.publish(topic, message)
    
    def subscribe(self, topic):
        """Subscribe to topic"""
        if self.connected:
            self.client.subscribe(topic)
    
    def start_loop(self):
        """Start non-blocking message loop"""
        if self.client:
            self.client.loop_start()
    
    def stop_loop(self):
        """Stop message loop"""
        if self.client:
            self.client.loop_stop()
    
    def is_connected(self):
        """Check if connected"""
        return self.connected
