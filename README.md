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
- STOP retried until acknowledged by the ESP32; ARM/NAV refuse without proof the latch opened
- Control path independent of an interactive terminal (FIFO + `SIGUSR1`), so the process is
  commandable under systemd or `nohup`
- Per-session CSV logging with millisecond timestamps
- Mechanical architecture v6.1: batteries housed inside the hulls, IP66 electronics box at deck level
- Motors, ESCs and GPS integration pending (blocked on physical kill-switch chain — safety rule)

## Safety Design
- Boot always in a safe (DISARMED) state; STOP has absolute priority
- Two independent protection layers: Pi heartbeat + ESP32 failsafe-by-timeout
- Propulsion latch: the failsafe does not merely stop the motors, it locks propulsion.
  The lock only opens on an explicit `L: 0 R: 0`, so no path leads from "stopped by
  failure" back to "running" without passing through zero
- Confirmed STOP: the stop command is retried until the ESP32 acknowledges it, with the
  input buffer drained first so a stale ack cannot pass for a fresh confirmation. The
  whole budget (~0.24 s) sits well inside the 1 s failsafe timeout, so the two layers
  chain instead of competing. An unconfirmed STOP is loud and logged
- Arming requires proof: ARM and NAV only proceed if the ESP32 confirms the latch opened.
  No announcing ARMED without knowing propulsion is actually unlocked
- Control does not depend on a terminal: keyboard (when a tty exists), a control FIFO
  (`echo s > /tmp/sailsafe.ctl`) and `SIGUSR1` as STOP. The signal path is the only one
  that cannot be missing, which is why it carries the stop
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

python3 software/raspberry_pi/tests/test_real_heading.py
python3 software/raspberry_pi/tests/test_stop_confirmado.py
python3 software/raspberry_pi/tests/test_commands.py

# ESP32 safety logic (runs on a PC, no board needed)
g++ -std=c++11 -Wall -o /tmp/tms software/esp32/tests/test_motor_safety.cpp && /tmp/tms

# firmware syntax check against stub Arduino headers (no board, no ESP32 toolchain).
# Catches typos and signature drift; NOT a substitute for a real build.
sh software/esp32/tools/syntax_check.sh
arduino-cli compile --fqbn esp32:esp32:esp32 software/esp32   # the real thing

# main process (ESP32 over USB optional)
python3 software/raspberry_pi/main.py               # DISARMED/ARMED only
python3 software/raspberry_pi/main.py --sim         # NAV in simulation, no propulsion sent
python3 software/raspberry_pi/main.py --sim-motores # NAV in simulation, motors DO run
```

84 Python tests and 182 C++ checks, none of which need hardware.

### Commanding the process
`a`=ARM `n`=NAV `d`=DISARM `s`=STOP `q`=quit, over any of three paths:

```bash
# 1. keyboard, when a terminal is attached
# 2. control FIFO — works under systemd, nohup or a non-tty ssh
echo s > /tmp/sailsafe.ctl
# 3. signal — STOP only, and the one path that cannot be missing
kill -USR1 <pid>
```

The process prints its PID and the paths actually available at startup. Without a tty and
without a FIFO only STOP remains, so the boat cannot be armed — inert, which is the safe
direction to fail in.

`NAV` closes the control loop on a synthetic boat. Commanding real motors from it means
the physical boat follows a mission it has no knowledge of, so the mode refuses to start
unless the synthetic sources are declared on the command line. `--sim` computes and prints
the motor commands without sending them; `--sim-motores` actually drives the ESCs and is
only for a boat clamped to the bench, out of the water.

## Documentation
- System architecture: `docs/SAILSAFE_Architecture_v1_12.docx`
- Engineering log: `Engineering_log.md`
- Mechanical blueprint: `hardware/mechanical/SAILSAFE_blueprint_madeira_v6_1.pdf`

## License
MIT — see `LICENSE`. Experimental project: build and operate at your own risk (see safety notice in the license file).

## Author
Gonçalo Martins da Silva
