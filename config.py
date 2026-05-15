# config.py - Smart Home Climate Control Configuration
# Change BROKER_SELECT and MQTT settings here for different test environments

import socket
from datetime import datetime

# ============================================================================
# BROKER SELECTION (0=localhost, 1=HiveMQ, 2=custom)
# ============================================================================
BROKER_SELECT = 0  # Change this to switch brokers

# Broker configurations
BROKERS = [
    'localhost',                           # 0: Local Mosquitto
    'broker.hivemq.com',                   # 1: HiveMQ (public)
    '192.168.1.100'                        # 2: Custom broker (edit IP as needed)
]

PORTS = [1883, 1883, 1883]
USERNAMES = ['', '', '']  # Leave empty for public brokers
PASSWORDS = ['', '', '']  # Leave empty for public brokers

# Active broker settings (derived from BROKER_SELECT)
BROKER_IP = BROKERS[BROKER_SELECT]
BROKER_PORT = PORTS[BROKER_SELECT]
USERNAME = USERNAMES[BROKER_SELECT]
PASSWORD = PASSWORDS[BROKER_SELECT]

# ============================================================================
# MQTT TOPIC STRUCTURE
# ============================================================================
COMM_TOPIC = 'home/'  # Root topic

# Sensor topics (emulators publish here)
TOPICS = {
    'dht_living_room': COMM_TOPIC + 'living_room/dht',
    'dht_bedroom': COMM_TOPIC + 'bedroom/dht',
    'thermostat': COMM_TOPIC + 'thermostat/status',
    'ac_relay': COMM_TOPIC + 'ac/relay/status',
    
    # Manager publishes alerts here
    'alerts_temperature': COMM_TOPIC + 'alerts/temperature',
    'alerts_general': COMM_TOPIC + 'alerts/general',
    
    # Control topics (GUI publishes commands here)
    'ac_control': COMM_TOPIC + 'ac/control',
    'relay_control': COMM_TOPIC + 'ac/relay/command',
}

# Subscribe topics (manager listens to all)
MANAGER_SUBSCRIBE_TOPIC = COMM_TOPIC + '#'

# ============================================================================
# DATABASE SETTINGS
# ============================================================================
DB_NAME = 'smart_home.db'
DB_PATH = './db/'  # Relative to project root

# Table name
DATA_TABLE = 'iot_data'

# ============================================================================
# EMULATOR SETTINGS
# ============================================================================
DHT_PUBLISH_INTERVAL = 5  # seconds between readings

# Temperature/Humidity ranges for simulation
DHT_TEMP_RANGE = (18, 30)  # degrees Celsius
DHT_HUMIDITY_RANGE = (40, 70)  # percentage

THERMOSTAT_SETPOINT_MIN = 16
THERMOSTAT_SETPOINT_MAX = 30
THERMOSTAT_INITIAL_STATE = 'OFF'
THERMOSTAT_INITIAL_SETPOINT = 22

# ============================================================================
# ALARM THRESHOLDS
# ============================================================================
TEMP_WARNING_LOW = 18      # Below this = warning
TEMP_ALERT_LOW = 16        # Below this = critical alert
TEMP_WARNING_HIGH = 28     # Above this = warning
TEMP_ALERT_HIGH = 32       # Above this = critical alert

ALARM_CHECK_INTERVAL = 5   # seconds between alarm checks

# ============================================================================
# GUI SETTINGS
# ============================================================================
GUI_REFRESH_RATE = 1000  # milliseconds (1Hz = 1000ms)
CHART_TIME_RANGE = 3600  # seconds (1 hour of data in trend chart)
CHART_UPDATE_INTERVAL = 30  # Update chart every 30 seconds

# ============================================================================
# EMULATOR CLIENT NAMES (random suffixes added at runtime)
# ============================================================================
EMULATOR_NAMES = {
    'dht': 'IOT_DHT_',
    'thermostat': 'IOT_THERMOSTAT_',
    'relay': 'IOT_RELAY_',
    'manager': 'IOT_MANAGER_',
}

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOG_LEVEL = 'DEBUG'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'logs/smart_home.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_timestamp():
    """Return current timestamp in ISO format"""
    return datetime.now().isoformat()

def log_config():
    """Print current configuration"""
    print(f"\n{'='*60}")
    print(f"Smart Home Climate Control - Configuration")
    print(f"{'='*60}")
    print(f"Broker: {BROKER_IP}:{BROKER_PORT}")
    print(f"Root Topic: {COMM_TOPIC}")
    print(f"Database: {DB_PATH}{DB_NAME}")
    print(f"Temperature Thresholds: {TEMP_WARNING_LOW}°C (warn) - {TEMP_ALERT_LOW}°C (alert)")
    print(f"Temperature Thresholds: {TEMP_WARNING_HIGH}°C (warn) - {TEMP_ALERT_HIGH}°C (alert)")
    print(f"{'='*60}\n")

# Print config on import (optional - comment out if too verbose)
if __name__ != '__main__':
    pass  # Silently load configuration
