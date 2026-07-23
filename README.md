# SAILSAFE

Autonomous surface catamaran focused on control systems development.

## Overview
SAILSAFE is a personal engineering project focused on building an autonomous surface vehicle with differential propulsion, embedded control, and waypoint navigation. It is developed as a real-world platform for learning and applying control systems, embedded software and safety engineering.

## Current Phase
Phase 1 — software MVP validated in simulation; mechanical build in preparation (architecture v6.1).

## Current Status
- Raspberry Pi ↔ ESP32 command chain validated on the bench (USB serial, text protocol `L: x R: y`)
- State machine DISARMED ↔ ARMED / NAV with 5 Hz heartbeat; ESP32-side failsafe (~1 s timeout) confirmed with real hardware
- Heading hold (proportional controller) and waypoint navigation (haversine + bearing) validated in closed-loop simulation
- Per-session CSV logging with millisecond timestamps
- Mechanical architecture v6.1: batteries housed inside the hulls, IP66 electronics box at deck level
- Motors, ESCs and GPS integration pending (blocked on physical kill-switch chain — safety rule)

## Safety Design
- Boot always in a safe (DISARMED) state; STOP has absolute priority
- Two independent protection layers: Pi heartbeat + ESP32 failsafe-by-timeout
- Firmware-enforced 30% power ceiling for bench testing
- Manual power cut (XT90 loop key) required before any ESC/motor energisation; remote kill switch (2.4 GHz RC / LoRa) planned before autonomous operation

## Main Components
- Raspberry Pi 4 (high-level control, navigation, logging — Python)
- ESP32 (real-time motor control and failsafe — C++/Arduino)
- 2 brushless motors with ESCs (waterjets)
- GPS, IMU (BNO055), ADC (ADS1015)

## Repository Structure
- `docs/` → architecture and project documentation
- `hardware/` → electrical and mechanical files (schematics, blueprints, CAD)
- `software/esp32/` → ESP32 firmware
- `software/raspberry_pi/` → onboard software (communication, control, telemetry, tests)

## Running the software (bench)
```bash
# unit tests (no hardware needed)
python3 software/raspberry_pi/tests/test_heading.py
python3 software/raspberry_pi/tests/test_mixer.py
python3 software/raspberry_pi/tests/test_navigation.py

# main process (ESP32 over USB optional)
python3 software/raspberry_pi/main.py
```

## Documentation
- System architecture: `docs/SAILSAFE_Architecture_v1_12.docx`
- Engineering log: `Engineering_log.md`
- Mechanical blueprint: `hardware/mechanical/SAILSAFE_blueprint_madeira_v6_1.pdf`

## License
MIT — see `LICENSE`. Experimental project: build and operate at your own risk (see safety notice in the license file).

## Author
Gonçalo Martins da Silva
