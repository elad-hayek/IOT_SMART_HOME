# Data Flow Diagram - Message Processing

## Complete Message Flow

## Complete Message Flow

```mermaid
sequenceDiagram
    participant DHT as DHT Sensor<br/>(Living Room)
    participant BR as MQTT Broker<br/>(localhost:1883)
    participant THERMO as Thermostat<br/>Emulator
    participant MG as Data Manager<br/>(Central Processing)
    participant RELAY as AC Relay
    participant DB as SQLite<br/>Database
    participant GUI as GUI Dashboard

    Note over DHT,GUI: Step 1: User Control
    GUI->>BR: Publish: home/ac/control<br/>{"state":"HEATING","setpoint":28}

    Note over DHT,GUI: Step 2: Thermostat Receives Command
    BR->>THERMO: Control message delivered
    THERMO->>THERMO: Update state to HEATING
    THERMO->>BR: Publish: home/thermostat/status<br/>{"state":"HEATING","setpoint":28}

    Note over DHT,GUI: Step 3: Manager Detects State Change & Controls Relay
    BR->>MG: Thermostat status message
    MG->>MG: Detect state change (OFF → HEATING)
    MG->>BR: Publish: home/ac/relay/command<br/>{"state":"ON"}
    BR->>RELAY: Relay command delivered
    RELAY->>RELAY: Activate relay (ON)
    RELAY->>BR: Publish: home/ac/relay/status<br/>{"relay_state":"ON"}

    Note over DHT,GUI: Step 4: DHT Responds to AC State
    BR->>DHT: Thermostat status subscribed
    DHT->>DHT: Detect HEATING mode + setpoint 28°C
    DHT->>DHT: Begin heating simulation
    DHT->>BR: Publish: home/living_room/dht<br/>{"temperature":23.2,"humidity":55}

    Note over DHT,GUI: Step 5: Manager Stores All Data
    BR->>MG: DHT temperature readings
    MG->>DB: INSERT iot_data (temperature: 23.2°C)
    MG->>DB: INSERT iot_data (thermostat state: HEATING)
    MG->>DB: INSERT iot_data (relay state: ON)

    Note over DHT,GUI: Step 6: GUI Updates Display (1Hz Timer)
    GUI->>DB: Query latest sensor values
    DB->>GUI: Return DHT_Living_Room, Thermostat, Relay data
    GUI->>GUI: Update temperature label (23.2°C)
    GUI->>GUI: Update thermostat state (HEATING)
    GUI->>GUI: Update relay state (ON)
```

## Temperature Threshold Check Logic

```mermaid
flowchart TD
    A["Manager Receives<br/>Temperature Reading"] --> B{"Check Value<br/>Against Thresholds"}

    B -->|temp < 16°C| C["🔴 CRITICAL<br/>ALERT"]
    B -->|16°C ≤ temp < 18°C| D["🟠 WARNING"]
    B -->|18°C ≤ temp ≤ 28°C| E["🟢 NORMAL"]
    B -->|28°C < temp ≤ 32°C| F["🟠 WARNING"]
    B -->|temp > 32°C| G["🔴 CRITICAL<br/>ALERT"]

    C --> H["Log to Database<br/>with severity=alert"]
    D --> H
    E --> H
    F --> H
    G --> H

    C --> I["Publish Alert to<br/>home/alerts/temperature"]
    D --> I
    F --> I
    G --> I

    I --> J["GUI Receives Alert<br/>& Displays Message"]

    style C fill:#ff4444,color:#fff
    style D fill:#ffaa00,color:#000
    style E fill:#44aa44,color:#fff
    style F fill:#ffaa00,color:#000
    style G fill:#ff4444,color:#fff
```

## Database Schema

```mermaid
erDiagram
    IOT_DATA {
        int id PK "Primary Key - Auto Increment"
        string timestamp "ISO Format - 2026-05-10T14:30:45.123456"
        string device_name "DHT_Living_Room, DHT_Bedroom, Thermostat, AC_Relay"
        string sensor_type "temperature, humidity, state, setpoint, relay_state"
        real value "Numeric value (temp in C, humidity in %)"
        string unit "°C, %, ON/OFF"
        string severity "normal, warning, alert"
    }
```

## Example Data Records

```
id | timestamp                  | device_name        | sensor_type | value  | unit | severity
---|----------------------------|-------------------|-------------|--------|------|----------
 1 | 2026-05-10T14:30:45.123456 | DHT_Living_Room    | temperature | 22.5   | °C   | normal
 2 | 2026-05-10T14:30:45.234567 | DHT_Living_Room    | humidity    | 55.0   | %    | normal
 3 | 2026-05-10T14:30:50.345678 | DHT_Bedroom        | temperature | 20.8   | °C   | normal
 4 | 2026-05-10T14:30:50.456789 | DHT_Bedroom        | humidity    | 60.5   | %    | normal
 5 | 2026-05-10T14:30:55.567890 | Thermostat         | setpoint    | 22.0   | °C   | normal
 6 | 2026-05-10T14:30:55.678901 | AC_Relay           | relay_state | 0      | ON   | normal
 7 | 2026-05-10T14:30:50.000000 | ALERT_SYSTEM       | temperature_alarm | 0 | DHT_Bedroom | warning
```

## Latency Analysis

| Operation                              | Latency    | Notes                    |
| -------------------------------------- | ---------- | ------------------------ |
| Sensor → Broker                        | ~50ms      | Local network            |
| Broker → Manager                       | <10ms      | Instant subscription     |
| Manager Processing                     | ~20ms      | JSON parsing + DB insert |
| DB Storage                             | ~5ms       | SQLite write             |
| **Total: Sensor to DB**                | **~85ms**  | Sub-100ms storage        |
| GUI Query                              | ~10ms      | Simple SELECT query      |
| GUI Display Update                     | ~100ms     | PyQt5 render             |
| **Total: Sensor to GUI**               | **~195ms** | Sub-200ms visibility     |
| User Command to Relay                  | ~150ms     | Publish + receive        |
| **Total E2E: User Action to Actuator** | **~250ms** | Real-time control        |
