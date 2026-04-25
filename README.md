# Standalone Submarine Arcade Game

**ECEG 201 Project** A fully self-contained, motion-controlled arcade game built on CircuitPython. Steer your submarine through a 2D ocean by physically tilting the controller. Dodge icebergs, collect coins, and survive as long as possible using a NeoPixel radar and a physical stepper motor compass!

---

## 🎮 How to Play

1. **Power On & Calibrate:** Place the controller flat on a table and plug it into power (or a USB battery bank). The screen will display `Calibrating... Keep Still!`. **Do not touch the controller** during this 2-second phase, as it maps the natural tilt of the table to create a perfect "Zero" point.
2. **Steer:** Tilt the controller left or right. The physical stepper motor arm acts as your submarine's heading. The game features a 10-degree deadzone and proportional velocity steering (tilt more to spin the arm faster).
3. **The Radar (NeoPixel Ring):** * 🟡 **Yellow Lights:** Coins. Steer towards them!
   * 🔵 **Blue Lights:** Icebergs. Steer away from them!
   * *Brightness indicates distance:* Dim lights are far away, bright lights are right next to you.
4. **Scoring:** The LCD screen keeps track of your survival time and collected coins. If you hit an iceberg, the screen flashes red and the game resets!

---

## 🛠️ Hardware Requirements

* **Microcontroller:** DAMNED Board (or equivalent CircuitPython-compatible board)
* **Motion Sensor:** Adafruit ICM20948 (STEMMA QT I2C - Address `0x69`)
* **Display:** 16x2 Character LCD Backpack (STEMMA QT I2C - Address `0x20`)
* **Motor:** I2C-controlled Stepper Motor
* **Radar Display:** NeoPixel Ring (24-LED)
* **Misc:** STEMMA QT cables, standard USB power source.

### 📌 Pinout & Wiring Configuration
| Component | Connection | Notes |
| :--- | :--- | :--- |
| **IMU (ICM20948)** | `board.I2C` | STEMMA QT chain |
| **Character LCD** | `board.I2C` | STEMMA QT chain |
| **Stepper Motor** | `board.I2C` | Addressed via motor library |
| **NeoPixel Ring** | `board.D5` | Brightness limited to 0.3 |
| **Hall Sensor** | `board.D16` | Homing switch for motor |

---

## 💻 Software & Libraries

This project uses **CircuitPython**. Make sure your board is updated to a compatible CircuitPython release.

### Required Adafruit Libraries
Download the [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries) and copy the following to your `lib/` folder:
* `adafruit_icm20x`
* `adafruit_character_lcd`

### Custom Project Files
Your `CIRCUITPY` drive should look like this:
```text
CIRCUITPY/
│
├── lib/
│   ├── adafruit_icm20x/
│   ├── adafruit_character_lcd/
│   ├── motorFunctions.py        # Custom motor driver
│   └── neoPixelFunctions.py     # Custom LED driver
│
├── submarine_engine.py          # 2D Arcade Game Logic & Object Tracking
└── code.py                      # Main Hardware Loop & Steering Math
