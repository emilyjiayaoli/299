---
title: Vision & Voice-Controlled Robotic Arm
layout: default
---

# Vision & Voice-Controlled Robotic Arm

*Control a desktop robotic arm with your gestures and voice*

#### Emily Li (jiayaoli) and Anthony Bustamante (rbustama)

[Source code](https://github.com/emilyjiayaoli/299)


## Demo Videos

| Vision Control | Voice Control |
|----------------|---------------|
| <iframe src="https://drive.google.com/file/d/1e5foSXKJbEs6M6Z02uJfuhmo0NDN6i9H/preview" width="320" height="240" frameborder="0" allowfullscreen></iframe> | <iframe src="https://drive.google.com/file/d/1mTg2Q8gx1zIK7Thece-NMjSh-V4eERII/preview" width="320" height="240" frameborder="0" allowfullscreen></iframe> |

---

## Goals

- Combine vision (MediaPipe) and natural language (OpenAI) for multi-modal control.
- Enable intuitive gesture & voice interaction instead of code.
- Prototype the future of everyday human–robot collaboration.

## Target Use-Cases

- **Accessibility** — hands-free, code-free control.
- **Lightweight automation** — pick-and-place, drawing, tidying.
- **Education** — approachable intro to computer vision, speech, robotics.

---

## Materials

| Qty | Item                            | Notes                                  |
|-----|----------------------------------|----------------------------------------|
| 1   | UFACTORY **xArm** or similar     | Any USB HID positional arm works       |
| 1   | Laptop with webcam & mic         | Tested on macOS M-series + Python 3.9  |
| –   | Python 3.7+                      | `pyenv` recommended                    |
| –   | (Optional) USB microphone        | Better speech recognition              |

---

## Software Stack

| Layer           | Tech                                       |
|----------------|--------------------------------------------|
| Vision          | MediaPipe Pose / Holistic                  |
| Speech-to-Text  | LiveKit stream → Deepgram / OpenAI Whisper |
| NLU / Planner   | OpenAI Function-Calling *(WIP)*            |
| Robot I/O       | USB HID serial (xArm SDK)                  |

---

## Getting Started with the xArm

### Hardware Setup

1. **Assemble the xArm** according to the manufacturer's instructions.
2. **Connect via USB** to your computer.
3. **Power on** the arm with the provided power supply.

### Software Installation

```bash
# 1. Clone the repository
git clone https://github.com/emilyjiayaoli/299
cd 299/

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
````

> For Apple Silicon Macs, we use `mediapipe-silicon` which is already included in the `requirements.txt`.

---

## xArm Library

This project uses the **Hiwonder-xArm1S** library for controlling the robotic arm.

**Key features:**

* Control servos with `setposition` using values from 0–1000.
* Automatically interpolates a smooth path to the target position.
* Built-in support for coordinated multi-servo movement.

**Important:** Sending commands too rapidly can cause the servo to freeze. This happens because each command restarts the smooth path calculation from a stopped state. We implement **throttling** in code to prevent this.

---

## Basic Usage

### Vision Control

```bash
python pose_estimation.py
```

* Opens webcam
* Tracks arm movements using MediaPipe
* Mirrors shoulder/elbow positions on the robot
* Press `Q` to quit

### Voice Control

```bash
python demo1.py
```

* Listens for voice commands via mic
* Processes speech using Deepgram/Whisper
* Executes commands like “Do a dance” or “Pick up the cup”
* Supports multi-turn conversations

---

## Project Structure

```
├── pose_estimation.py   # MediaPipe + IK-lite
├── demo1.py             # Voice pipeline & function calls
├── pickup_move.py       # Pre-defined robot routines
├── return_neutral.py    # Helper to reset pose
├── requirements.txt
└── docs/                # GitHub Pages site (this file)
```

---

## Technical Details

### How It Works

* **Webcam → Pose**: MediaPipe tracks upper-body landmarks (\~30 fps)
* **Pose → Angles**: Simple vector math for shoulder & elbow (no full IK)
* **Angles → Robot**: Streamed over USB HID to servos
* **Mic → Text**: Audio streamed via LiveKit → Deepgram/Whisper
* **Text → Intent**: OpenAI function-calling maps utterances to Python routines
* **\[WIP] Task Planner**: E.g., break "Tidy the desk" into low-level calls

---

## xArm Programming Details

The xArm uses a serial protocol to communicate with the servos. Each servo has a unique ID and can be controlled individually or in groups.

```python
# Control a single servo
arm.setposition(1, 500, 1000)  # Servo ID 1, position 500, time 1000ms

# Control multiple servos together
arm.setpositions([
    (1, 500),  # Servo ID 1
    (2, 300),  # Servo ID 2
    (3, 700)   # Servo ID 3
], 1000)  # All move in 1000ms
```

### Servo Control Tips

* **Position Range**: 0–1000 (mapped to 0–240°)
* **Time Parameter**: Controls movement speed (in ms)
* **Throttling**: Add \~100ms delay between commands
* **Error Handling**: Arm may ignore rapid-fire commands
