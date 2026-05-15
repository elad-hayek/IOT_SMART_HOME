# gui/gui_helpers.py - GUI helper functions and utilities
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import CHART_TIME_RANGE
from db.data_acq import da

class GuiHelpers:
    """Utility functions for GUI"""
    
    @staticmethod
    def format_timestamp(iso_timestamp):
        """Convert ISO timestamp to readable format"""
        try:
            dt = datetime.fromisoformat(iso_timestamp)
            return dt.strftime("%H:%M:%S")
        except:
            return iso_timestamp
    
    @staticmethod
    def format_value(value, unit=''):
        """Format sensor value with unit"""
        try:
            if unit:
                return f"{float(value):.1f}{unit}"
            return f"{float(value):.2f}"
        except:
            return str(value)
    
    @staticmethod
    def get_status_color(value, unit, device_type):
        """Return color based on value and thresholds"""
        from config import TEMP_WARNING_LOW, TEMP_ALERT_LOW, TEMP_WARNING_HIGH, TEMP_ALERT_HIGH
        
        if unit == '°C' or 'temp' in device_type.lower():
            if value < TEMP_ALERT_LOW or value > TEMP_ALERT_HIGH:
                return '#FF4444'  # Red (alert)
            elif value < TEMP_WARNING_LOW or value > TEMP_WARNING_HIGH:
                return '#FFAA00'  # Orange (warning)
            else:
                return '#44AA44'  # Green (normal)
        return '#AAAAAA'  # Gray (unknown)
    
    @staticmethod
    def get_chart_data(device_name, sensor_type, hours=1):
        """Get chart data for a sensor (last N hours)"""
        df = da.fetch_range(device_name, sensor_type, limit=1000)
        
        if df.empty:
            return [], []
        
        # Return (timestamps, values)
        times = [GuiHelpers.format_timestamp(t) for t in df['timestamp']]
        values = df['value'].tolist()
        
        return times, values

class MessageFormatter:
    """Format various messages for display"""
    
    @staticmethod
    def format_sensor_message(device_name, sensor_type, value, unit=''):
        """Format sensor reading for display"""
        return f"{device_name} {sensor_type}: {GuiHelpers.format_value(value, unit)}"
    
    @staticmethod
    def format_alert_message(severity, device_name, message):
        """Format alert message - compact format"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            'alert': '⚠ [ALERT]',
            'warning': '⚠ [WARN]',
            'normal': '[INFO]'
        }.get(severity, '[INFO]')
        
        # Extract key info from message (shorten verbose temperature alerts)
        if 'temperature' in message.lower() and '°C' in message:
            # Extract temperature and threshold from message
            import re
            match = re.search(r'(\d+\.?\d*°C).+?(\d+°C)', message)
            if match:
                temp, threshold = match.groups()
                message = f"{device_name}: {temp} vs {threshold}"
        
        return f"{timestamp} {prefix}: {message}"
    
    @staticmethod
    def format_status_message(status):
        """Format device status"""
        if status == 'connected':
            return '🟢 Connected'
        elif status == 'connecting':
            return '🟡 Connecting...'
        else:
            return '🔴 Disconnected'
