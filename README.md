# SAILSAFE

Autonomous surface catamaran focused on control systems development.

## Overview
SAILSAFE is a personal engineering project focused on building an autonomous surface vehicle with differential propulsion, embedded control, and waypoint navigation. It is developed as a real-world platform for learning and applying control systems, embedded software and safety engineering.

> **Project history.** SAILSAFE has been in development since February 2026. The git
> history in this repository starts later than that — it was re-initialised during a
> restructure — so commit dates are not a record of the project's timeline. The actual
> development record, with dated entries from the start, is in
> [`Engineering_log.md`](Engineering_log.md).

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
- **GPS validated on hardware** (15 Sep): NEO-8M on the Pi's GPIO UART, 2 600 frames
  without a single bad checksum, fix with 8 satellites and HDOP 1.05. Short-term
  wander measured at ~30 cm over 10 s; slow drift over 10 min reached a 31 m × 4 m
  box at a window sill, with half the sky blocked — a pessimistic bound, to be
  re-measured on open water before the waypoint arrival radius is fixed
- **Heading blocked**: the BNO055 module is faulty (internal rail at 2.7 V with 4.7 V
  in, and ~0.4 mA of leakage on SDA, which poisoned the whole I2C bus). Replacement
  ordered; see `Engineering_log.md` for the diagnosis
- Power sense (ADS1015) written and covered by tests, and the chip answers reliably on
  the bus, but the dividers are not built yet — the PGA correction and the divider
  ratios stay theory until they are
- Mechanical architecture v6.1: batteries housed inside the hulls, IP66 electronics box at deck level
- Motors and ESCs pending (blocked on physical kill-switch chain — safety rule)
- GPS wiring closed (OPEN-005): NMEA on the Pi's GPIO UART, `/dev/serial0` at 9600
- Return point defined (closes OPEN-006 on the point): the position recorded once at ARM,
  averaged over validated fixes and never rewritten; straight-line return, which is only
  admissible on open water within sight of the operator

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
- Return trigger on the electronics battery: it drains on the clock rather than on
  thrust, and when it goes, radio, logging and control go together. The guard latches —
  a battery that recovers voltage once the load drops does not un-abort a mission — and
  refuses to decide at all on uncalibrated readings
- Manual power cut (XT90 loop key) required before any ESC/motor energisation; remote kill switch (2.4 GHz RC / LoRa) planned before autonomous operation

## Main Components
- Raspberry Pi 4 (high-level control, navigation, logging — Python)
- ESP32 (real-time motor control and failsafe — C++/Arduino)
- 2 brushless motors with ESCs (waterjets)
- GPS NEO-8M, IMU BNO055, ADC ADS1015 — all three on the Pi (GPS on UART, the other two on I2C)

## Repository Structure
- `docs/` → architecture and project documentation
- `hardware/` → electrical and mechanical files (schematics, blueprints, CAD)
- `software/esp32/` → ESP32 firmware
- `software/raspberry_pi/` → onboard software (communication, control, sensors, safety, telemetry, tests)

## Raspberry Pi setup
Two firmware parameters are conditions for the system to work at all, not bench tweaks.
A reinstall without them gives a boat with no heading and no sense, and nothing reports
an error that points at the cause.

```
# /boot/firmware/config.txt
dtparam=i2c_arm=on              # without it /dev/i2c-1 does not exist
dtparam=i2c_arm_baudrate=10000  # the BNO055 clock-stretches and the Broadcom I2C
                                # controller mishandles it: corrupted reads, no error
enable_uart=1                   # without it /dev/serial0 does not exist
dtoverlay=disable-bt            # puts the PL011 on the GPIO; the mini-UART's baud rate
                                # follows the core clock and drifts with CPU load
```

Also, in `raspi-config` → Interface Options → Serial Port: login shell over serial **no**,
serial hardware **yes**. Verify what actually took effect, because a parameter that lands
inside a conditional section of `config.txt` is ignored in silence:

```bash
ls -l /dev/serial0     # must point at ttyAMA0, not ttyS0
i2cdetect -y 1         # 0x28 (BNO055) and 0x48 (ADS1015)
for f in /proc/device-tree/soc/i2c@*/clock-frequency; do
  echo -n "$f: "; od -An -tx1 "$f" | tr -d " \n"; echo
done                   # i2c@7e804000 must read 00002710 (10000)
```

Both I2C devices need their address pin tied by a wire — `ADD` to GND on the BNO055
(0x28), `ADDR` to GND on the ADS1015 (0x48). A floating address pin does not fail: it
gives an address that changes, and a device that appears and disappears.

Dependencies on the Pi:

```bash
pip install smbus2 pyserial adafruit-circuitpython-bno055 --break-system-packages
```

## Running the software (bench)
```bash
# unit tests (no hardware needed)
python3 software/raspberry_pi/tests/test_heading.py
python3 software/raspberry_pi/tests/test_mixer.py
python3 software/raspberry_pi/tests/test_navigation.py

python3 software/raspberry_pi/tests/test_real_heading.py
python3 software/raspberry_pi/tests/test_stop_confirmado.py
python3 software/raspberry_pi/tests/test_commands.py
python3 software/raspberry_pi/tests/test_sense.py
python3 software/raspberry_pi/tests/test_battery_guard.py
python3 software/raspberry_pi/tests/test_real_position.py

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

153 Python tests and 182 C++ checks, none of which need hardware.

### Bench tools
Each one exercises exactly one sensor and sends nothing to the ESP32.

```bash
cd software/raspberry_pi
python3 -m tools.heading_bench --fake     # BNO055: heading hold, turned by hand
python3 -m tools.sense_bench --fake       # ADS1015: channels, and one-point calibration
python3 -m tools.sense_bench --ganho-errado   # shows the saturation the wrong PGA causes
python3 -m tools.gps_bench --fake         # NEO-8M: fix quality, not just "has a position"
python3 -m tools.gps_bench --cru          # shows every frame, and whether it parsed
```

Drop `--fake` for the real sensor. `sense_bench --calibrar a2 12.60` stores the scale
factor for one channel against a multimeter reading; without that file the readings are
produced but marked uncalibrated, and the return trigger refuses to act on them.

`gps_bench` reports four counters rather than one, because "this frame produced no
position" has causes with opposite remedies: **bad checksum** means corruption (baud,
wiring, ground); **no fix** means an intact frame that carries no position, which during a
cold start is every frame for minutes and is not a fault at all; **rejected** means a
position that failed the satellite, HDOP or null-island criteria; **accepted** means a
usable fix. Collapsing them into one number makes a normal cold start look like a wiring
failure.

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
- System architecture: `docs/SAILSAFE_Architecture_v1_13.docx`
- Engineering log: `Engineering_log.md`
- Bench procedure (sensors): `docs/SAILSAFE_procedimento_sensores_v1.pdf`
- Mechanical blueprint: `hardware/mechanical/SAILSAFE_blueprint_madeira_v6_1.pdf`

## License
MIT — see `LICENSE`. Experimental project: build and operate at your own risk (see safety notice in the license file).

## Author
Gonçalo Martins da Silva
