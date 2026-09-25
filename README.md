# SAILSAFE

Autonomous surface catamaran focused on control systems development.

## Overview
SAILSAFE is a personal engineering project focused on building an autonomous surface vehicle with differential propulsion, embedded control, and waypoint navigation. It is developed as a real-world platform for learning and applying control systems, embedded software and safety engineering.

> **Project history.** SAILSAFE has been in development since February 2026. The git
> history in this repository starts later than that — it was re-initialised during a
> restructure — so commit dates are not a record of the project's timeline. The actual
> development record, with dated entries from the start, is in
> [`Engineering_log.md`](Engineering_log.md).

> **On authorship.** The system design, the safety decisions, the hardware and the bench
> work are mine. The code is written with AI assistance and held to the same standard as
> everything else here: a regression suite that runs without hardware, and figures that
> come from measurements on the bench rather than from datasheets. The engineering log and
> the commit messages are also written with AI assistance, from my decisions and
> measurements. The log records those decisions and their reasoning — including the times
> a generated tool was wrong and the bench proved it.

## Current Phase
Phase 1 — software MVP validated in simulation, GPS integrated and validated on hardware. Propulsion on the bench next; mechanical build held until the structure is weighed (blueprint v6.1, CAD v6.4). **Where things stand and what comes next: see [Next steps](#next-steps) below and the latest entries of `Engineering_log.md`.**

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
- **GPS integrated into the main process** (17 Sep, `--gps`): position read and
  logged in every state, not just NAV, so an ordinary bench session produces the
  dispersion data a separate script used to be needed for. Losing position in NAV
  leads to a safe state after a short tolerance; the return point is recorded at
  ARM. Rehearsed end to end against fake serial hardware (`tools/system_bench.py`),
  never yet against the real receiver
- **Heading blocked**: the BNO055 module is faulty (internal rail at 2.7 V with 4.7 V
  in, and ~0.4 mA of leakage on SDA, which poisoned the whole I2C bus). Replacement
  ordered; see `Engineering_log.md` for the diagnosis
- Power sense (ADS1015) written and covered by tests, and the chip answers reliably on
  the bus, but the dividers are not built yet — the PGA correction and the divider
  ratios stay theory until they are
- Mechanical architecture v6.1: batteries housed inside the hulls, IP66 electronics box at deck level
- Motors and ESCs in hand (each motor and waterjet is a single 107 g unit); loop key and fuse soldered. Bench test with the units **uncoupled** is next. Running them on water stays gated by the remote kill switch
- **Components weighed (25 Sep):** ~2.0 kg for everything except the structure, against 3.2 kg assumed by the CAD. The structure is still unweighed, so the total sits between 5.3 and 10.4 kg (waterline 33–65 mm). Battery bay floors raised from z=45 to **z=80**, which clears the whole range. Lighter propulsion may move the CG forward of the LCB and flip the trim to the bow, which would move the battery bays aft — to be decided after weighing the structure
- **30% throttle ceiling is per phase, not a constant:** bench 30%; tethered on water, higher; free running only with the remote kill switch. 30% throttle is roughly 30% of top speed (~0.5 m/s by a rough estimate), which a 1-knot current cancels
- GPS wiring closed (OPEN-005): NMEA on the Pi's GPIO UART, `/dev/serial0` at 9600
- Return point implemented (closes OPEN-006 on the point): the position is recorded
  once at ARM, averaged over validated fixes in a sliding window, and never rewritten.
  With `--gps`, ARM is refused without it. Straight-line return, which is only
  admissible on open water within sight of the operator. Recorded but not yet
  consumed — there is no return mode yet
- **Arrival radius is in debt to the GPS rate.** At 1 Hz, a position may legitimately
  be 2.5 s old; at the 3 m/s design speed that is 7.5 m of uncertainty, against a 4 m
  arrival radius. No staleness budget fixes this — raising the module to 5 Hz
  (`UBX-CFG-RATE`) is the condition for tightening the radius

## Next steps
*Updated 2026-09-25. The reasoning behind each item is in `Engineering_log.md`.*

1. **Bench test of ESCs and motors, uncoupled from the jets.** 5 A fuse (not 30 A — the
   fuse holder's thin pigtail would melt first), 2–3 s pulses at 10–15%. Check rotation
   direction *before* coupling and mark the phase order. Measure the current. First run of
   the latch, failsafe, ceiling and confirmed STOP against real actuators.
2. **Thrust test in a tub**, jet submerged so the cooling loop primes, pulling on a spring
   scale. Replaces the speed estimate with a number.
3. **Weigh the structure** — a 3 mm okoumé offcut of known area, and the XPS. Then correct
   the mass table in `verify_concept.py` with measured values, recompute the CG, and
   decide the battery bay X position, confirm z=80, and the motor access hatch.
4. **Find the blueprint generator (OPEN-016)** and apply the changes to the drawing. Only
   then do the drawings go to the carpenter.

In parallel: run `main.py --gps --sim` on the Pi with the real receiver.
Blocked, nothing to do: replacement BNO055 board; remote kill switch (budget).

Open items: OPEN-014 (dead reckoning as observer, never actuator), OPEN-015 (bilge water
sensor per hull — the cooling loop puts pressurised water inside the hull), OPEN-016
(blueprint has no generator in the repo).

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
- Losing position stops the boat, it does not send it home by dead reckoning. Retracing
  the outbound path blind was considered and declined: with no speed sensor and a
  magnetometer sitting next to the motors, the estimate would be steered by the least
  trustworthy sensor in the system with nothing left to check it against — and GPS error
  is bounded where dead-reckoning error is not. The decisive argument was that the
  condition making a blind return safe (a working radio link) is the same one that makes
  it unnecessary, since the operator can then simply drive the boat back. Dead reckoning
  is still worth running as an *observer*, so its error can be measured against GPS and
  reported; that is OPEN-014, and it never steers. Reasoning in `Engineering_log.md`
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
python3 software/raspberry_pi/tests/test_return_point.py

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

186 Python tests and 182 C++ checks, none of which need hardware.

There is also an end-to-end rehearsal of the whole process against fake serial
hardware — two pseudo-terminals, one feeding NMEA as the NEO-8M, the other
answering STOP as the ESP32:

```bash
cd software/raspberry_pi
python3 -m tools.system_bench
```

It walks ARM-too-early → ARM → NAV → GPS going silent, and checks that each step
does the safe thing. Unit tests cover the pieces; this one covers the seams
between them, which is where the last three defects were.

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

```bash
# main process with the real GPS (position real, heading still synthetic)
python3 main.py --gps --sim
```

With `--gps` the position comes from the NEO-8M and is logged in every state. If the
port does not open the process **exits** rather than quietly falling back to the
synthetic boat — running a different system than the one that was asked for is the
failure nobody notices. Heading is still synthetic, so `nav_guard` keeps refusing
propulsion: `--gps --sim` is an observation mode, not a mission.

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

Serial ports can be named explicitly: `--esp32-port /dev/serial/by-id/...` and
`--gps-port`. A stable `by-id` name is worth the typing — two USB devices swap
`/dev/ttyUSB*` numbers between boots, and nothing warns you.

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
