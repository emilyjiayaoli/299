# Arm Pose Estimation

This project uses OpenCV and MediaPipe to detect arm poses and calculate joint angles in real-time using your webcam.

## Features

- Real-time arm pose detection
- Joint angle calculations:
  - Shoulder angles (between torso and upper arm)
  - Elbow angles (between upper arm and forearm)
  - Wrist angles (between forearm and hand)
- Visual overlay of pose landmarks and angles
- Displays measurements for both left and right arms

## Requirements

- Python 3.7+
- Webcam

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pnpm dlx pip install -r requirements.txt
```

### Notes for macOS M1/M2/M3 (Apple Silicon) Users:
The requirements file uses `mediapipe-silicon` which is a fork of MediaPipe compatible with Apple Silicon. If you encounter any issues, you can try installing MediaPipe using:

```bash
pip install mediapipe-silicon
```

## Usage

Run the pose estimation script:

```bash
python pose_estimation.py
```

- Press 'q' to exit the application

## How it works

The application uses:
- MediaPipe's pose detection and holistic models to identify body and hand landmarks
- OpenCV for camera access and drawing the visual output
- Vector mathematics to calculate angles between joints

## Angle Measurements

The following angles are measured:
- **Shoulder angle**: The angle between hip, shoulder, and elbow points
- **Elbow angle**: The angle between shoulder, elbow, and wrist points
- **Wrist angle**: The angle between elbow, wrist, and index finger (or alternate reference point)

## Landmark Reference

MediaPipe identifies the following key landmarks for angle calculation:
- 0: Nose
- 11: Right shoulder
- 12: Left shoulder
- 13: Right elbow
- 14: Left elbow
- 15: Right wrist
- 16: Left wrist
- 23: Right hip
- 24: Left hip

For wrist angles, the system attempts to use hand landmarks from the MediaPipe Holistic model when available. 