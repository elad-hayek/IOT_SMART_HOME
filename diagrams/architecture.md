# Architecture Diagram - Smart Home Climate Control System

## System Architecture

```mermaid
graph TB
    subgraph Emulators["🌡️ DATA PRODUCERS (Emulators)"]
        DHT1["DHT Sensor<br/>Living Room<br/>(Temp/Humidity)"]
        DHT2["DHT Sensor<br/>Bedroom<br/>(Temp/Humidity)"]
        THERM["Thermostat<br/>Controller<br/>(State/Setpoint)"]
        RELAY["AC Relay<br/>Switch<br/>(ON/OFF)"]
    end

    subgraph Broker["🔄 MQTT MESSAGE BROKER<br/>(localhost:1883)"]
        MQTT["Mosquitto<br/>Message Hub"]
    end

    subgraph Manager["📊 DATA MANAGER<br/>(Central Processing)"]
        LISTENER["MQTT Listener<br/>(Subscribe All Topics)"]
        PARSER["Message Parser<br/>(JSON)"]
        ALARMS["Alarm Logic<br/>(Thresholds)"]
        WRITER["Database Writer"]
    end

    subgraph Database["💾 DATA STORAGE"]
        SQLITE["SQLite Database<br/>smart_home.db"]
        TABLE["iot_data Table<br/>(Timestamp, Device, Value)"]
    end

    subgraph GUI["🖥️ USER INTERFACE<br/>(Real-time Dashboard)"]
        MONITOR["Live Sensor Display"]
        CONTROL["Manual AC Control"]
        ALERTS["Alert Panel"]
        CHARTS["Temperature Trends"]
    end

    DHT1 -->|Publish| MQTT
    DHT2 -->|Publish| MQTT
    THERM -->|Publish| MQTT
    RELAY -->|Publish| MQTT

    MQTT -->|Subscribe All| LISTENER
    LISTENER -->|Parse| PARSER
    PARSER -->|Check| ALARMS
    PARSER -->|Insert| WRITER
    ALARMS -->|Alert| MQTT

    WRITER -->|Store| SQLITE
    SQLITE -->|Schema| TABLE

    MQTT -->|Subscribe| GUI
    TABLE -->|Query| GUI

    GUI -->|Command| MQTT
    GUI -->|AC Control| MQTT

    MQTT -->|Relay ON/OFF| RELAY
    MQTT -->|Setpoint| THERM

    style Emulators fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style Broker fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style Manager fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style Database fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style GUI fill:#fce4ec,stroke:#880e4f,stroke-width:2px
```

## Key Components

| Component         | Role                             | Protocol              |
| ----------------- | -------------------------------- | --------------------- |
| **Emulators**     | Simulate IoT sensors & actuators | MQTT Pub/Sub          |
| **MQTT Broker**   | Central message hub              | TCP/1883              |
| **Data Manager**  | Listens, parses, stores, alerts  | MQTT Subscribe        |
| **SQLite DB**     | Persistent data storage          | SQL                   |
| **GUI Dashboard** | Real-time monitoring & control   | MQTT + Database Query |

## Data Flow

1. **Emulator → Broker**: DHT/Thermostat/Relay publish sensor readings (every 5-15 sec)
2. **Broker → Manager**: Manager subscribes to `home/#` receives all messages
3. **Manager → Database**: Parses JSON, inserts into SQLite with timestamp
4. **Manager → Alerts**: Checks temperature thresholds, publishes alerts if exceeded
5. **Manager → Broker**: Alert messages published to `home/alerts/temperature`
6. **Broker → GUI**: GUI subscribes to alerts and all home topics
7. **GUI → Database**: Queries latest sensor values every 1 second
8. **GUI → Broker**: User sends AC commands back to broker
9. **Broker → Thermostat**: Thermostat receives and processes control commands

## Network Topics

```
home/
├── living_room/
│   └── dht              # {"temperature": 22.5, "humidity": 55, ...}
├── bedroom/
│   └── dht              # {"temperature": 21.0, "humidity": 60, ...}
├── thermostat/
│   └── status           # {"state": "HEATING", "setpoint": 22, ...}
├── ac/
│   ├── relay/
│   │   ├── status       # {"relay_state": "ON", ...}
│   │   └── command      # {"state": "ON"} (from GUI)
│   └── control          # {"state": "HEATING", "setpoint": 22} (from GUI)
└── alerts/
    └── temperature      # {"severity": "warning", "device": "...", ...}
```
