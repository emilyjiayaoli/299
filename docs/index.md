---
title: Vision & Voice-Controlled Robotic Arm
layout: default
---

# Vision & Voice-Controlled Robotic Arm

*Control a desktop robotic arm with your gestures and voice*

#### Emily Li (jiayaoli) and Anthony Bustamante (rbustama)

- [Source code](https://github.com/emilyjiayaoli/299)

## Demo Videos

- [Vision Control Video](https://drive.google.com/file/d/1e5foSXKJbEs6M6Z02uJfuhmo0NDN6i9H/preview)
- [Voice Control Video](https://drive.google.com/file/d/1mTg2Q8gx1zIK7Thece-NMjSh-V4eERII/preview)

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
```

> For Apple Silicon Macs, we use `mediapipe-silicon` which is already included in the `requirements.txt`.

### macOS USB HID Driver (xArm only)

If you're on **macOS**, install the HIDAPI library via Homebrew:

```bash
brew install hidapi
```

This is required to interface with the xArm over USB. If HID errors occur, verify this is installed and accessible in your environment.

### Additional Setup (Deepgram, OpenAI, LiveKit)

To enable voice control functionality, you'll need API keys and environment variables for third-party services:

```bash
# .env file format
OPENAI_API_KEY="your-openai-api-key"
DEEPGRAM_API_KEY="your-deepgram-api-key"
LIVEKIT_API_KEY="your-livekit-api-key"
LIVEKIT_SECRET="your-livekit-secret"
LIVEKIT_ENDPOINT="your-livekit-endpoint"
```

- **OpenAI**: [Sign up](https://platform.openai.com/signup) and obtain your key from the dashboard.
- **Deepgram**: [Create an account](https://console.deepgram.com/signup) and generate an API key.
- **LiveKit**: [Start here](https://cloud.livekit.io/) to create a project, and use the API key, secret, and endpoint provided.

Use a library like `python-dotenv` or load variables in your shell to access them in code.

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

> Note: Ensure your microphone is selected as the system default input or configure explicitly in the script.

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

* **Webcam → Pose**: MediaPipe tracks upper-body landmarks (~30 fps)
* **Pose → Angles**: Simple vector math for shoulder & elbow (no full IK)
* **Angles → Robot**: Streamed over USB HID to servos
* **Mic → Text**: Audio streamed via LiveKit → Deepgram/Whisper
* **Text → Intent**: OpenAI function-calling maps utterances to Python routines
* **[WIP] Task Planner**: E.g., break "Tidy the desk" into low-level calls

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
* **Throttling**: Add ~100ms delay between commands
* **Error Handling**: Arm may ignore rapid-fire commands

---

## Limitations & Opportunities for Improvement

While the system performs well in controlled conditions, there are several areas for future refinement:

- **Pose Estimation Accuracy**: Currently uses simplified IK and 2D keypoints; accuracy degrades in non-ideal lighting or occlusion.
- **Limited Voice Capabilities**: Only supports predefined routines; does not dynamically parse or compose new ones.
- **No Feedback Loop**: The system executes actions blindly without sensing success/failure or reacting to external disturbances.
- **Task Planning (WIP)**: LLM-based decomposition of abstract commands is not yet integrated.

### Suggested Future Improvements

- Implement full-body inverse kinematics using a learned model or additional sensors.
- Develop a real-time feedback loop using webcam input to detect action results.
- Extend LLM prompting to include multi-step plans with memory and error correction.
- Integrate a confidence-aware fallback system for voice misunderstanding.

---

## Next Steps

To extend this project further, we propose the following concrete improvements:

1. **Add Visual Feedback Loop**  
   Incorporate webcam-based state estimation to close the loop on task execution. This would allow the robot to adjust arm pose mid-task based on observed outcomes (e.g., object not grasped → retry).

2. **Hierarchical Planning via LLMs**  
   Train or prompt an LLM to deconstruct complex instructions like "organize the tools on the table" into sequences of existing motion routines (e.g., locate tool → move arm → pick → place).

3. **Continuous Control**  
   Move from single-trigger actions to streaming control based on continuous gesture or voice input.
