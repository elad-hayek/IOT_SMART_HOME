# gui/gui_main.py - Main PyQt5 GUI Application
import sys
import os
import json
import time
from datetime import datetime
from threading import Thread

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QSlider, QTextEdit, QGridLayout, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QFont

from config import (
    BROKER_IP, BROKER_PORT, USERNAME, PASSWORD, TOPICS, MANAGER_SUBSCRIBE_TOPIC,
    GUI_REFRESH_RATE, get_timestamp
)
from emulators.mqtt_client import MqttClient
from db.data_acq import da
from gui.gui_helpers import GuiHelpers, MessageFormatter

class GuiMqttClient(MqttClient):
    """MQTT client for GUI (subscribes to all topics)"""
    
    def __init__(self, parent=None):
        super().__init__('IOT_GUI_')
        self.parent = parent
        self.message_queue = []
    
    def on_message(self, client, userdata, msg):
        """Queue messages for GUI processing"""
        topic = msg.topic
        message_str = str(msg.payload.decode('utf-8', 'ignore'))
        self.message_queue.append((topic, message_str))

class GuiSignals(QObject):
    """Signals for GUI updates"""
    update_sensor = pyqtSignal(str, str, float, str)  # device, sensor_type, value, unit
    update_alert = pyqtSignal(str, str, str)  # severity, device, message
    connection_changed = pyqtSignal(bool)

class SmartHomeGui(QMainWindow):
    """Main GUI Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Home Climate Control System")
        self.setGeometry(100, 100, 1200, 800)
        
        self.signals = GuiSignals()
        self.mqtt_client = GuiMqttClient(self)
        self.sensor_values = {}
        
        self.init_ui()
        self.init_mqtt()
        self.setup_timers()
        self.enable_ac_controls(False)  # Disabled until connected
    
    def init_ui(self):
        """Initialize UI components"""
        # Use dock widgets for full-space layout - no central widget needed
        
        # Connection Panel (Top-left dock)
        self.connection_dock = QDockWidget("Connection & Settings")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.connection_dock)
        self.setup_connection_panel()
        
        # Sensors Panel (Top-right dock)
        self.sensors_dock = QDockWidget("Live Sensor Data")
        self.addDockWidget(Qt.RightDockWidgetArea, self.sensors_dock)
        self.setup_sensors_panel()
        
        # AC Control Panel (Middle-left dock)
        self.ac_control_dock = QDockWidget("AC Unit Control")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.ac_control_dock)
        self.setup_ac_control_panel()
        
        # Alerts Panel (Bottom dock)
        self.alerts_dock = QDockWidget("Alerts & Status Messages")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.alerts_dock)
        self.setup_alerts_panel()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def setup_connection_panel(self):
        """Setup connection and settings panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Broker info
        layout.addWidget(QLabel("Broker Settings:"))
        broker_label = QLabel(f"Broker: {BROKER_IP}:{BROKER_PORT}")
        layout.addWidget(broker_label)
        
        # Connect button
        self.connect_button = QPushButton("Connect to Broker")
        self.connect_button.clicked.connect(self.on_connect_clicked)
        layout.addWidget(self.connect_button)
        
        # Disconnect button
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        layout.addWidget(self.disconnect_button)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.connection_dock.setWidget(widget)
    
    def setup_sensors_panel(self):
        """Setup live sensor data panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Real-time Sensor Readings:"))
        
        # Living Room DHT
        layout.addWidget(QLabel("Living Room:"))
        self.label_living_room_temp = QLabel("Temperature: -- °C")
        self.label_living_room_humidity = QLabel("Humidity: -- %")
        layout.addWidget(self.label_living_room_temp)
        layout.addWidget(self.label_living_room_humidity)
        
        layout.addSpacing(10)
        
        # Bedroom DHT
        layout.addWidget(QLabel("Bedroom:"))
        self.label_bedroom_temp = QLabel("Temperature: -- °C")
        self.label_bedroom_humidity = QLabel("Humidity: -- %")
        layout.addWidget(self.label_bedroom_temp)
        layout.addWidget(self.label_bedroom_humidity)
        
        layout.addSpacing(10)
        
        # Thermostat Status
        layout.addWidget(QLabel("Thermostat:"))
        self.label_thermostat_state = QLabel("State: -- ")
        self.label_thermostat_setpoint = QLabel("Setpoint: -- °C")
        layout.addWidget(self.label_thermostat_state)
        layout.addWidget(self.label_thermostat_setpoint)
        
        layout.addSpacing(10)
        
        # Relay Status
        layout.addWidget(QLabel("AC Relay:"))
        self.label_relay_state = QLabel("Relay State: -- ")
        layout.addWidget(self.label_relay_state)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.sensors_dock.setWidget(widget)
    
    def setup_ac_control_panel(self):
        """Setup AC unit control panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Manual AC Control:"))
        
        # Setpoint slider
        layout.addWidget(QLabel("AC Setpoint:"))
        self.setpoint_slider = QSlider(Qt.Horizontal)
        self.setpoint_slider.setMinimum(16)
        self.setpoint_slider.setMaximum(30)
        self.setpoint_slider.setValue(22)
        self.setpoint_slider.setTickPosition(QSlider.TicksBelow)
        self.setpoint_slider.valueChanged.connect(self.on_setpoint_changed)
        layout.addWidget(self.setpoint_slider)
        
        self.label_setpoint_value = QLabel("22°C")
        layout.addWidget(self.label_setpoint_value)
        
        layout.addSpacing(10)
        
        # State buttons
        layout.addWidget(QLabel("AC State:"))
        
        self.button_ac_off = QPushButton("Turn OFF")
        self.button_ac_off.clicked.connect(lambda: self.send_ac_command('OFF'))
        layout.addWidget(self.button_ac_off)
        
        self.button_ac_heat = QPushButton("Heating Mode")
        self.button_ac_heat.clicked.connect(lambda: self.send_ac_command('HEATING'))
        layout.addWidget(self.button_ac_heat)
        
        self.button_ac_cool = QPushButton("Cooling Mode")
        self.button_ac_cool.clicked.connect(lambda: self.send_ac_command('COOLING'))
        layout.addWidget(self.button_ac_cool)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.ac_control_dock.setWidget(widget)
    
    def setup_alerts_panel(self):
        """Setup alerts and status messages panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("System Alerts & Messages:"))
        
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(400)
        layout.addWidget(self.alerts_text)
        
        widget.setLayout(layout)
        self.alerts_dock.setWidget(widget)
    
    def init_mqtt(self):
        """Initialize MQTT connection"""
        self.mqtt_client.set_on_connected_callback(self.on_mqtt_connected)
    
    def setup_timers(self):
        """Setup periodic timers"""
        # GUI refresh timer (1Hz)
        self.gui_timer = QTimer()
        self.gui_timer.timeout.connect(self.update_gui)
        self.gui_timer.start(GUI_REFRESH_RATE)
    
    def on_connect_clicked(self):
        """Connect to MQTT broker"""
        if self.mqtt_client.connect():
            self.mqtt_client.start_loop()
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.update_status("Connecting...", False)
    
    def on_disconnect_clicked(self):
        """Disconnect from MQTT broker"""
        self.mqtt_client.stop_loop()
        self.mqtt_client.disconnect()
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.update_status("Disconnected", False)
        self.enable_ac_controls(False)
    
    def on_mqtt_connected(self):
        """Called when MQTT connects"""
        self.mqtt_client.subscribe(MANAGER_SUBSCRIBE_TOPIC)
        self.update_status("Connected", True)
        self.enable_ac_controls(True)
    
    def update_status(self, status, connected):
        """Update connection status"""
        if connected:
            self.status_label.setText(f"Status: {status}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText(f"Status: {status}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def enable_ac_controls(self, enabled):
        """Enable/disable AC control buttons and slider"""
        self.setpoint_slider.setEnabled(enabled)
        self.button_ac_off.setEnabled(enabled)
        self.button_ac_heat.setEnabled(enabled)
        self.button_ac_cool.setEnabled(enabled)
    
    def on_setpoint_changed(self, value):
        """Handle setpoint slider change"""
        self.label_setpoint_value.setText(f"{value}°C")
    
    def send_ac_command(self, state):
        """Send AC control command"""
        setpoint = self.setpoint_slider.value()
        command = {
            'state': state,
            'setpoint': setpoint
        }
        message = json.dumps(command)
        self.mqtt_client.publish(TOPICS['ac_control'], message)
        self.add_alert(f"Sent AC command: {state} at {setpoint}°C", 'normal')
    
    def add_alert(self, message, severity='info'):
        """Add message to alerts panel"""
        formatted_msg = MessageFormatter.format_alert_message(severity, 'System', message)
        self.alerts_text.append(formatted_msg)
        
        # Auto-scroll to bottom
        scrollbar = self.alerts_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_gui(self):
        """Update GUI with latest data from database and MQTT messages"""
        # Process MQTT messages
        while self.mqtt_client.message_queue:
            topic, message_str = self.mqtt_client.message_queue.pop(0)
            self.process_mqtt_message(topic, message_str)
        
        # Update sensor displays from database
        self.update_sensor_displays()
    
    def process_mqtt_message(self, topic, message_str):
        """Process incoming MQTT message"""
        try:
            data = json.loads(message_str)
            
            if 'alerts/temperature' in topic:
                severity = data.get('severity', 'info')
                device = data.get('device', 'Unknown')
                msg = data.get('message', 'Temperature alert')
                self.add_alert(msg, severity)
            
            elif 'alerts/general' in topic:
                msg = data.get('message', 'System alert')
                self.add_alert(msg, 'warning')
        
        except json.JSONDecodeError:
            pass
    
    def update_sensor_displays(self):
        """Update sensor display labels from database"""
        # Living Room DHT
        lr_temp = da.fetch_latest_by_device('DHT_Living_Room', limit=2)
        if not lr_temp.empty:
            temp_data = lr_temp[lr_temp['sensor_type'] == 'temperature']
            hum_data = lr_temp[lr_temp['sensor_type'] == 'humidity']
            
            if not temp_data.empty:
                temp_val = temp_data.iloc[0]['value']
                self.label_living_room_temp.setText(f"Temperature: {temp_val}°C")
                color = GuiHelpers.get_status_color(temp_val, '°C', 'temperature')
                self.label_living_room_temp.setStyleSheet(f"color: {color};")
            
            if not hum_data.empty:
                hum_val = hum_data.iloc[0]['value']
                self.label_living_room_humidity.setText(f"Humidity: {hum_val}%")
        
        # Bedroom DHT
        br_temp = da.fetch_latest_by_device('DHT_Bedroom', limit=2)
        if not br_temp.empty:
            temp_data = br_temp[br_temp['sensor_type'] == 'temperature']
            hum_data = br_temp[br_temp['sensor_type'] == 'humidity']
            
            if not temp_data.empty:
                temp_val = temp_data.iloc[0]['value']
                self.label_bedroom_temp.setText(f"Temperature: {temp_val}°C")
                color = GuiHelpers.get_status_color(temp_val, '°C', 'temperature')
                self.label_bedroom_temp.setStyleSheet(f"color: {color};")
            
            if not hum_data.empty:
                hum_val = hum_data.iloc[0]['value']
                self.label_bedroom_humidity.setText(f"Humidity: {hum_val}%")
        
        # Thermostat (display only - slider is a control input, not a sensor display)
        thermo = da.fetch_latest_by_device('Thermostat', limit=2)
        if not thermo.empty:
            state_data = thermo[thermo['sensor_type'] == 'state']
            setpoint_data = thermo[thermo['sensor_type'] == 'setpoint']
            
            if not state_data.empty:
                state = state_data.iloc[0]['value']
                self.label_thermostat_state.setText(f"State: {state}")
            
            if not setpoint_data.empty:
                setpoint = setpoint_data.iloc[0]['value']
                self.label_thermostat_setpoint.setText(f"Setpoint: {setpoint}°C")
        
        # Relay
        relay = da.fetch_latest_by_device('AC_Relay')
        if not relay.empty:
            relay_state = relay.iloc[0]['value']
            self.label_relay_state.setText(f"Relay State: {relay_state}")

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    gui = SmartHomeGui()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
