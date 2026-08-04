# TrueEyeball Project

An AI-powered hands-free computer control system that combines eye tracking, hand tracking, gesture recognition, and biometric authentication for secure and intelligent human-computer interaction.

---

# Features

- 👁️ Eye tracking for click detection
- ✋ Hand tracking for cursor movement
- 🖱️ Left eye blink → Left Click
- 🖱️ Right eye blink → Right Click
- ⏸️ Both eyes closed → Pause Cursor
- 🔐 Face Recognition Authentication
- 👤 Face Enrollment System
- 🔄 Continuous User Verification
- 📋 User Management Utility
- 📊 Session Logging

---

# Project Roadmap

## ✅ Phase 1 — AI Processing Layer

- Cursor Intelligence
- EMA Cursor Smoothing
- Velocity Mapping

**Status:** Completed

---

## ✅ Phase 2 — Adaptive Blink Intelligence

- Dynamic Blink Threshold
- Blink Confidence Scoring
- Blink Debounce
- Automatic Calibration

**Status:** Completed

---

## ✅ Phase 3 — Gesture Recognition Engine

- Gesture Recognition
- Gesture Confidence Scoring
- Gesture Stabilization
- Gesture State Machine

**Status:** Completed

---

## ✅ Phase 4 — Secure Authentication

- Face Enrollment
- Face Recognition
- Continuous Verification
- Session Management
- Activity Logging

**Status:** Completed

---

# Tech Stack

- Python 3.11
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI
- Face Recognition
- Machine Learning

---

# Requirements

- Python 3.11
- `face_landmarker.task` in the project root

---

# Installation

```bash
py -3.11 -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

pip install mediapipe==0.10.32
```

---

# Running the Application

```bash
python main.py
```

---

# User Registration

Register a new user before using the application.

```bash
python register.py
```

---

# User Management

### List Registered Users

```bash
python manage_users.py list
```

### Rename User

```bash
python manage_users.py rename "Old_Name" "New_Name"
```

### Revoke User

```bash
python manage_users.py revoke "User_Name"
```

---

# Project Workflow

1. Register a new face using `register.py`.
2. Manage registered users with `manage_users.py`.
3. Launch the application using `main.py`.
4. Authentication is performed automatically.
5. Cursor control begins after successful verification.
6. Continuous verification ensures only authorized users retain access.

---

# Controls

| Action           | Control               |
| ---------------- | --------------------- |
| Cursor Movement  | Hand Movement         |
| Left Click       | Left Eye Blink        |
| Right Click      | Right Eye Blink       |
| Pause Cursor     | Both Eyes Closed      |
| Exit Application | Press**Q** or **ESC** |

---

# Security Features

- Secure biometric enrollment
- Authorized-user-only access
- Continuous identity verification
- Session management
- User registration and revocation
- Activity logging

---

# Future Enhancements

- Voice Commands
- Multi-user Profiles
- Head Pose Tracking
- Custom Gesture Training
- AI-based Personalization
- Desktop Installer
- Cross-platform Support

---

# License

This project is intended for educational and research purpose
