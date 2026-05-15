# AC Unit State Machine Diagram

## Thermostat State Transitions

```mermaid
stateDiagram-v2
    [*] --> OFF

    OFF --> HEATING: User/GUI selects<br/>HEATING mode
    OFF --> COOLING: User/GUI selects<br/>COOLING mode
    OFF --> OFF: No action / Timeout

    HEATING --> ON: Temperature reaches<br/>setpoint
    HEATING --> OFF: User turns OFF /<br/>Timeout
    HEATING --> COOLING: User switches mode

    COOLING --> ON: Temperature reaches<br/>setpoint
    COOLING --> OFF: User turns OFF /<br/>Timeout
    COOLING --> HEATING: User switches mode

    ON --> OFF: Setpoint reached /<br/>User command
    ON --> HEATING: Temperature drops<br/>below setpoint
    ON --> COOLING: Temperature rises<br/>above setpoint

    note right of OFF
        Unit is powered off
        No heating or cooling
        Thermostat in standby
    end note

    note right of HEATING
        Unit actively heating
        Target: Raise temperature
        to setpoint value
    end note

    note right of COOLING
        Unit actively cooling
        Target: Lower temperature
        to setpoint value
    end note

    note right of ON
        Unit reached target
        Maintaining setpoint
        Minimal energy use
    end note
```

## AC Relay Control Flow

```mermaid
flowchart TD
    A["User Adjusts AC<br/>Setpoint or Mode<br/>in GUI"] --> B["GUI Creates<br/>Control Command<br/>JSON"]

    B --> C["Publish to<br/>home/ac/control"]

    C --> D["Thermostat<br/>Receives Command<br/>on MQTT"]

    D --> E{"Validate<br/>Command"}

    E -->|Invalid| F["Log Error<br/>No State Change"]
    E -->|Valid| G["Update Internal<br/>State & Setpoint"]

    G --> H["Simulate AC<br/>Response (0.5s delay)"]

    H --> I["Publish New State to<br/>home/thermostat/status"]

    I --> J["Manager Receives<br/>State Update"]

    J --> K["Store in Database"]

    K --> L["GUI Updates Display<br/>& Acknowledges Change"]

    F --> M["Manager Logs<br/>Alarm"]

    M --> N["GUI Displays<br/>Error Message"]

    style A fill:#fce4ec
    style G fill:#fff3e0
    style I fill:#e3f2fd
    style L fill:#e8f5e9
```

## GUI Control Interface

```mermaid
flowchart LR
    subgraph GUI["GUI Dashboard"]
        direction LR
        S["Setpoint<br/>Slider<br/>16-30°C"]
        B1["OFF<br/>Button"]
        B2["HEATING<br/>Button"]
        B3["COOLING<br/>Button"]
    end

    S -->|Value Change| CMD["Create<br/>Command<br/>JSON"]
    B1 -->|Click| CMD
    B2 -->|Click| CMD
    B3 -->|Click| CMD

    CMD --> MQTT["Publish to<br/>home/ac/control"]

    MQTT --> THERM["Thermostat<br/>Processes"]
    THERM --> RELAY["Relay<br/>Executes"]
    RELAY --> ACU["Physical AC<br/>Unit"]

    ACU -.->|Feedback| MQTT
    MQTT -.->|Status Update| GUI

    style S fill:#bbdefb
    style B1 fill:#ffcccc
    style B2 fill:#ffe0b2
    style B3 fill:#c8e6c9
    style MQTT fill:#fff9c4
    style ACU fill:#f0f4c3
```

## Setpoint Adjustment Timeline

```mermaid
timeline
    title Temperature Control Timeline (Setpoint 22°C)

    section Initial State
        14:30:00 : Unit OFF : No heating/cooling

    section User Action
        14:30:05 : User sets HEATING mode in GUI
        14:30:05 : Setpoint set to 22°C

    section Command Transmission
        14:30:06 : Command published to MQTT
        14:30:06 : Thermostat receives command

    section AC Response
        14:30:06.5 : Thermostat confirms state change
        14:30:07 : AC unit relay activated (ON)
        14:30:07 : Physical heating begins

    section Monitoring
        14:30:10 : Temperature: 18°C (below target, heating)
        14:30:15 : Temperature: 19°C
        14:30:20 : Temperature: 20°C
        14:30:25 : Temperature: 21°C
        14:30:30 : Temperature: 22°C (target reached!)

    section Steady State
        14:30:35 : Unit ON (maintaining 22°C)
        14:30:40 : Unit ON
        14:31:00 : Unit ON (still holding)
```
