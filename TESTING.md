# Testing Guide - Smart Home Climate Control System

## Test Environment Setup

### Prerequisites Check

```bash
# Verify Python version
python --version          # Should be 3.7 or higher

# Verify pip
pip --version

# Check installed packages
pip list | grep -E "paho|PyQt5|pandas"
```

### Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

---

## Unit Testing - Component Verification

### Test 1: Configuration Module

**File:** `config.py`

**Objective:** Verify all configuration values are accessible

```python
# From Python shell in project directory
python
>>> from config import BROKER_IP, BROKER_PORT, TOPICS, TEMP_WARNING_LOW
>>> print(f"Broker: {BROKER_IP}:{BROKER_PORT}")
Broker: localhost:1883
>>> print(f"Topics: {list(TOPICS.keys())}")
Topics: ['dht_living_room', 'dht_bedroom', 'thermostat', 'ac_relay', 'alerts_temperature', 'alerts_general', 'ac_control', 'relay_control']
>>> print(f"Temp threshold: {TEMP_WARNING_LOW}°C")
Temp threshold: 18°C
>>> exit()
```

**Expected:** All values printed without errors ✅

---

### Test 2: Database Module

**File:** `db/data_acq.py`

**Objective:** Verify SQLite database creation and operations

```python
# From Python shell in project directory
python
>>> from db.data_acq import da
[DB] Connected to ./db/smart_home.db
[DB] Table 'iot_data' ready

>>> # Test insert
>>> result = da.add_iot_data("2026-05-10T14:30:00", "TEST_DEVICE", "temperature", 22.5, "°C")
>>> print(f"Inserted record ID: {result}")
Inserted record ID: 1

>>> # Test query
>>> df = da.fetch_latest_by_device("TEST_DEVICE")
>>> print(df[['device_name', 'sensor_type', 'value']])
  device_name sensor_type  value
0 TEST_DEVICE  temperature   22.5

>>> exit()
```

**Expected:** Records inserted and retrieved successfully ✅

**Database File Created:** `db/smart_home.db` should now exist

---

### Test 3: MQTT Client Base Class

**File:** `emulators/mqtt_client.py`

**Objective:** Verify MQTT client initialization (does not connect yet)

```python
# From Python shell
python
>>> from emulators.mqtt_client import MqttClient
>>> client = MqttClient("TEST_CLIENT")
>>> print(f"Client name: {client.client_name}")
Client name: TEST_CLIENT<random_number>
>>> print(f"Broker: {client.broker}:{client.port}")
Broker: localhost:1883
>>> exit()
```

**Expected:** Client object created with correct parameters ✅

---

## Integration Testing - Component Communication

### Test Setup (6 Terminals)

Ensure all terminals are open in the `final-project` directory:

```bash
cd e:\projects\HIT\IOT\final-project
```

---

### Test Sequence 1: Manager Receives Sensor Data

**Terminal 1 - Start Data Manager:**

```bash
python manager/data_manager.py
```

**Expected Output:**

```
[IOT_MANAGER_xxxxxxx] Connecting to localhost:1883
[Manager] Connected to broker
[Manager] Subscribed to home/#
[Manager] Data manager started
```

✅ **Checkpoint 1:** Manager running and subscribed

**Terminal 2 - Start Living Room DHT:**

```bash
python emulators/dht_emulator.py
```

**Expected Output:**

```
[IOT_DHT_xxxxxxx] Connecting to localhost:1883
[IOT_DHT_xxxxxxx] Connected to broker
[Living_Room DHT] Emulator started
[Living_Room DHT] Published: Temp=22.5°C, Humidity=55%
[Living_Room DHT] Published: Temp=22.3°C, Humidity=54%
...
```

✅ **Checkpoint 2:** Emulator publishing

**Back to Terminal 1 (Manager) - Expected New Output:**

```
[Manager] Message from home/living_room/dht: {"temperature":22.5,"humidity":55,...}
[Manager] Inserted: DHT_Living_Room temperature 22.5°C
[Manager] Inserted: DHT_Living_Room humidity 55%
[Manager] Message from home/living_room/dht: {"temperature":22.3,"humidity":54,...}
...
```

✅ **Checkpoint 3:** Manager receiving and storing data

**Verify Database:**

```bash
# In new terminal in project directory
sqlite3 db/smart_home.db "SELECT COUNT(*) as count FROM iot_data;"
```

**Expected Output:**

```
count
2
```

(2 records per reading: temp + humidity)

✅ **Test Passed:** Data flows from emulator → MQTT → Manager → SQLite

---

### Test Sequence 2: Thermostat Control

**Terminal 3 - Start Thermostat:**

```bash
python emulators/thermostat_emulator.py
```

**Expected Output:**

```
[IOT_THERMOSTAT_xxxxxxx] Connecting to localhost:1883
[IOT_THERMOSTAT_xxxxxxx] Connected to broker
[Thermostat] Emulator started
[Thermostat] State: OFF, Setpoint: 22°C
```

**Terminal 1 (Manager) Should Now Show:**

```
[Manager] Message from home/thermostat/status: {"state":"OFF","setpoint":22,...}
[Manager] Inserted: Thermostat state OFF
[Manager] Inserted: Thermostat setpoint 22.0°C
```

✅ **Checkpoint 4:** Thermostat publishing state

---

### Test Sequence 3: Temperature Alarm Triggering

**Modify config.py:**

```python
# Change this line (line ~67):
DHT_TEMP_RANGE = (5, 15)  # Simulate extreme cold instead of (18, 30)
```

**Restart DHT Emulator in Terminal 2:**

```bash
# Press Ctrl+C to stop
# Then restart:
python emulators/dht_emulator.py
```

**Expected Output:**

```
[Living_Room DHT] Published: Temp=6.8°C, Humidity=45%
```

**Terminal 1 (Manager) Should Show Alert:**

```
[Manager] CRITICAL: DHT_Living_Room temperature 6.8°C below alert threshold 16°C
[Manager] Inserted: ALERT_SYSTEM temperature_alarm with severity=alert
```

**Verify Alert in Database:**

```bash
sqlite3 db/smart_home.db "SELECT * FROM iot_data WHERE severity='alert';"
```

✅ **Test Passed:** Alarm system working

**Restore config.py:**

```python
DHT_TEMP_RANGE = (18, 30)  # Back to normal
```

---

### Test Sequence 4: GUI Dashboard

**Terminal 6 - Start GUI:**

```bash
python gui/gui_main.py
```

**Expected:** GUI window appears with panels

**In GUI:**

1. Click **"Connect to Broker"**
   - Status should change to **"Connected"** (green)
   - Connection panel updates

2. Check **Live Sensor Data panel (top-right)**
   - Living Room Temperature: Should show a number like "22.5°C"
   - Living Room Humidity: Should show a number like "55%"
   - Bedroom Temperature: Should show a number
   - Bedroom Humidity: Should show a number
   - Thermostat State: Should show "OFF"
   - Thermostat Setpoint: Should show "22°C"

3. Check **AC Control Panel (left)**
   - Setpoint slider: Should be at 22
   - All buttons enabled

✅ **Checkpoint 5:** GUI connected and displaying data

---

### Test Sequence 5: Manual AC Control

**In GUI AC Control Panel:**

1. Click **"HEATING"** button
   - Message: "Sent AC command: HEATING at 22°C" appears in alerts panel

**Terminal 3 (Thermostat) Should Show:**

```
[Thermostat] Received command: {"state":"HEATING","setpoint":22}
[Thermostat] State: HEATING, Setpoint: 22°C
```

**Terminal 1 (Manager) Should Show:**

```
[Manager] Message from home/thermostat/status: {"state":"HEATING",...}
```

2. In GUI, drag **Setpoint Slider** to 24°C

**Terminal 3 Should Show:**

```
[Thermostat] Received command: {"state":"HEATING","setpoint":24}
[Thermostat] Setpoint updated to 24°C
[Thermostat] State: HEATING, Setpoint: 24°C
```

**GUI Setpoint Label Updates to:** "24°C"

✅ **Checkpoint 6:** Manual control working

**Terminal 2 (Relay) Should Show:**

```
[IOT_RELAY_xxxxxxx] Connecting to localhost:1883
[IOT_RELAY_xxxxxxx] Connected to broker
[Relay] Emulator started
[Relay] Published state: OFF
```

---

### Test Sequence 6: Relay Control

**Terminal 5 - Start AC Relay (if not already started):**

```bash
python emulators/relay_emulator.py
```

**In GUI, click "Turn OFF"** (if it's not already OFF)

**Terminal 5 Should Show:**

```
[Relay] Received command: {"state":"OFF"}
[Relay] State changed to OFF
[Relay] Published state: OFF
```

**GUI Relay Status Updates to:** "OFF"

✅ **Test Passed:** Full end-to-end control working

---

## Performance Testing

### Latency Measurement

**Objective:** Measure time from sensor publish to GUI display

**Method 1: Visual Observation**

1. In Terminal 2, watch for sensor publish message with timestamp
2. In GUI, watch when value updates
3. Manually estimate latency (target: <200ms)

**Method 2: Database Timestamps**

```bash
sqlite3 db/smart_home.db
sqlite> SELECT device_name, sensor_type, value, timestamp FROM iot_data WHERE device_name='DHT_Living_Room' ORDER BY timestamp DESC LIMIT 5;
```

Each record should have a unique timestamp. Consecutive readings should be ~5 seconds apart.

✅ **Expected:** Latency < 300ms

---

### Throughput Test

**Objective:** Verify system handles multiple concurrent messages

**Count Records After 1 Minute:**

```bash
sqlite3 db/smart_home.db
sqlite> SELECT COUNT(*) FROM iot_data;
```

**Expected:** ~20-30 records (depends on publish rates)

- 2 DHT sensors × 2 readings (temp+humidity) = 4 messages per 5 sec = ~48 records/min
- Actual may vary due to lag

---

## Advanced Feature Testing

### Test 1: Automatic Relay Control

**Objective:** Verify Manager automatically controls relay based on thermostat state

**Setup:**

- All components running (Manager, Thermostat, Relay, DHT emulators, GUI)
- GUI connected

**Steps:**

1. Check **GUI Relay State:** Should show "OFF"

2. In GUI, click **"HEATING"** button at setpoint 25°C

3. **Terminal 5 (Relay) Should Show:**

   ```
   [Relay] Received command: {"state":"ON"}
   [Relay] State changed to ON
   [Relay] Published state: ON
   ```

4. **GUI Relay State Updates to:** "ON" (automatically, within 1-2 seconds)

5. In GUI, click **"Turn OFF"** button

6. **Terminal 5 (Relay) Should Show:**

   ```
   [Relay] Received command: {"state":"OFF"}
   [Relay] State changed to OFF
   [Relay] Published state: OFF
   ```

7. **GUI Relay State Updates to:** "OFF"

✅ **Test Passed:** Manager automatically controls relay on state changes (no manual relay commands needed)

---

### Test 2: AC-Responsive DHT Temperature

**Objective:** Verify DHT temperature moves toward thermostat setpoint when AC is on

**Setup:**

- All components running
- GUI connected
- Current temperature displayed (e.g., 22.5°C)

**Steps:**

1. **Note current temperature** in GUI (e.g., 22.5°C)

2. In GUI, click **"HEATING"** button and set setpoint to **28°C**

3. **Watch Terminal 2 (DHT Living Room) - Temperature should INCREASE:**

   ```
   [Living_Room DHT] Published: Temp=22.5°C, Humidity=55%
   [Living_Room DHT] Published: Temp=23.1°C, Humidity=54%
   [Living_Room DHT] Published: Temp=23.8°C, Humidity=54%
   [Living_Room DHT] Published: Temp=24.5°C, Humidity=55%
   ...continues increasing toward 28°C
   ```

4. **GUI Temperature Label Should Update** - Moving from 22.5°C toward 28°C in ~30 seconds

5. **Terminal 1 (Manager) Should Show - AC State Tracking:**

   ```
   [Living_Room DHT] AC State: HEATING, Setpoint: 28°C
   ```

6. In GUI, change to **"COOLING"** button at setpoint **20°C**

7. **Watch Terminal 2 - Temperature should now DECREASE:**

   ```
   [Living_Room DHT] Published: Temp=24.5°C, Humidity=55%
   [Living_Room DHT] Published: Temp=23.8°C, Humidity=55%
   [Living_Room DHT] Published: Temp=23.1°C, Humidity=54%
   ...continues decreasing toward 20°C
   ```

8. In GUI, click **"Turn OFF"**

9. **Watch Terminal 2 - Temperature should now be RANDOM WALK:**
   ```
   [Living_Room DHT] Published: Temp=20.5°C, Humidity=55%
   [Living_Room DHT] Published: Temp=20.8°C, Humidity=54%
   [Living_Room DHT] Published: Temp=20.3°C, Humidity=55%
   ...fluctuates randomly ±0.5°C
   ```

✅ **Test Passed:** DHT emulator responds realistically to AC state changes

---

### Test 3: GUI Connection-Based Control Enabling

**Objective:** Verify AC controls are disabled when broker is disconnected

**Setup:**

- GUI is open and connected

**Steps:**

1. **Check AC Control Panel - All buttons should be ENABLED (clickable)**
   - Turn OFF button: clickable
   - Heating Mode button: clickable
   - Cooling Mode button: clickable
   - Setpoint Slider: movable

2. Click **"Disconnect"** button

3. **Check AC Control Panel - All controls should be DISABLED (grayed out)**
   - Buttons appear grayed/inactive
   - Slider cannot be moved
   - Attempting to click produces no action

4. Click **"Connect to Broker"**

5. **Check AC Control Panel - Controls should be RE-ENABLED**
   - Buttons are now clickable
   - Slider is movable again

✅ **Test Passed:** AC controls properly enable/disable based on connection status

---

### Test 4: Setpoint Slider as Control-Only Input

**Objective:** Verify setpoint slider does NOT get overwritten by database updates

**Setup:**

- All components running
- GUI connected
- Thermostat in OFF mode

**Steps:**

1. In GUI, drag **Setpoint Slider to 25°C**
   - Label updates to "25°C"

2. Click **"HEATING"** button
   - Slider stays at 25°C (sends 25°C setpoint to thermostat)

3. **Wait 10 seconds** - Slider should NOT reset

4. **Terminal 3 (Thermostat) Should Show:**

   ```
   [Thermostat] Received command: {"state":"HEATING","setpoint":25}
   ```

5. Drag Setpoint Slider to **20°C**

6. **Wait 10 seconds** - Slider should stay at 20°C (not jump back to database value)

7. Check **GUI "Setpoint" Display (right panel)** - Shows 25°C (actual thermostat setpoint)

8. The **Slider (left panel)** Shows 20°C (next value to send when AC button clicked)

✅ **Test Passed:** Slider is control-only input, independent of database updates

---

## Stress Testing

### Test: Sustained Operation

**Run system for 5 minutes:**

1. All 6 components running
2. Monitor CPU usage (should be <5%)
3. Monitor memory (should be stable ~50-100MB)
4. Check for crashes

**After 5 minutes, stop all and check database:**

```bash
sqlite3 db/smart_home.db "SELECT COUNT(*) FROM iot_data;"
```

Should show 100+ records without errors.

✅ **Expected:** No crashes, stable resource usage

---

## Failure Recovery Testing

### Test: Manager Crash & Recovery

**Step 1:** Stop manager (Ctrl+C in Terminal 1)

**Step 2:** Verify emulators still publishing

- Terminal 2, 3, etc. should still show publish messages

**Step 3:** Check GUI

- Data still visible (from database cache)
- "Disconnected" status appears

**Step 4:** Restart manager

```bash
python manager/data_manager.py
```

**Expected:**

- Manager catches up on missed messages
- New data resumes flowing to database
- GUI reconnects

✅ **Test Passed:** System recovers from component failure

---

## Checklist - All Tests Passing

- [x] Configuration values load correctly
- [x] Database creates and stores records
- [x] MQTT client initializes
- [x] Manager receives all sensor messages
- [x] Data stored in SQLite within 1 second
- [x] GUI connects to broker
- [x] GUI displays real-time sensor values
- [x] Manual AC control sends commands
- [x] Thermostat updates state
- [x] Alarms trigger on threshold
- [x] Database stores alarm records
- [x] Relay responds to control
- [x] System sustained for 5+ minutes
- [x] System recovers from component failure
- [x] Latency < 300ms
- [x] No database corruption

---

## Final Validation

### Full System Test Checklist

**Before demonstration, verify:**

1. ✅ All 6 terminals show "Connected" status
2. ✅ GUI displays live values
3. ✅ Database has >100 records
4. ✅ Alerts panel shows at least one message
5. ✅ Manual control works (setpoint change triggers response)
6. ✅ All components running for >2 minutes without errors

**If any check fails:**

- Review error messages in terminal
- Check config.py BROKER_SELECT setting
- Verify MQTT broker is running (if using localhost)
- Check database file exists: `db/smart_home.db`

---

## Clean Up After Testing

**Stop all components:**
Press **Ctrl+C** in each terminal

**To reset database:**

```bash
# Delete and recreate
del db\smart_home.db
python -c "from db.data_acq import da; print('Database reset')"
```

**To reset config:**

```python
# Edit config.py and restore:
BROKER_SELECT = 0  # localhost
DHT_TEMP_RANGE = (18, 30)  # normal range
```

---

**Testing Complete!** ✅ System Ready for Presentation
