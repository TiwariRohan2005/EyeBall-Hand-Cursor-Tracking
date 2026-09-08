# TrueEyeball

## Overview

TrueEyeball is an AI-powered, hands-free computer control system and administrative environment. Originally conceptualized as the "Eye Ball Motion Tracking System" (a spatial cursor simulation framework), the project has evolved into a fully unified **Dual-Role Application Desktop**.

By aggregating real-time facial recognition, computer vision eye tracking, semantic hand gesture kinematics, and biometric session security, TrueEyeball replaces traditional mouse-and-keyboard peripherals. It natively drives a complex application ecosystem—principally a robust Smart Library Management System and a decoupled Study Notes platform—all orchestrated through intelligent context-aware physical gestures securely governed by strict Role-Based Access Control (RBAC).

## Key Features

- **Advanced Computer Vision Modalities**
  - **Real-Time Eye Tracking & Blink Detection**: Parses precise facial landmarks and evaluates Eye Aspect Ratio (EAR) dynamically to map pupil coordinates.
  - **Kinematic Cursor Control**: Smooth, responsive on-screen cursor control reinforced by Exponential Moving Average (EMA) smoothing and velocity-based mapping algorithms.
  - **Hand Tracking & Gesture Recognition**: Detects sophisticated spatial signals (thumb up/down, swipes, pointing) coordinated through a robust gesture state machine.
- **Biometric Security Architecture**
  - **Face Authentication**: Mandatory encrypted biometric registration ensuring only registered faces unlock the application.
  - **Continuous Session Verification**: Implements real-time frame-by-frame user verification that instantly halts unauthorized interactions.
  - **Role-Based Access Control (OWNER/STAFF)**: Enforces hard ownership boundaries natively at the database level against gesture intents.
  - **Soft-Deletion User Management**: Staff accounts can be soft-deactivated securely by the Owner without breaking referenced constraints in the historical ledger.
- **Smart Library Management System**
  - **Inventory Subsystem**: Full CRUD operations executed over gestural selection matrices.
  - **Logical Book Lifecycles**: Strict issue and return operational constraints linked directly to the authenticated system operator.
  - **Transaction Ledger**: Historical tracking preserving system accountability.
- **Automated Reporting**
  - **Excel Generation**: Deep integration with OpenPyXL generating and intelligently updating `TrueEyeball_Library_Report.xlsx` dashboards conditionally depending on the requesting role.
- **Unified CustomTkinter Architecture**
  - Multi-threaded processing distributing CV camera pipelines and queue-based UI rendering without interface starvation.
  - Built-in comprehensive unit and integration **Testing** covering 100% of major logic paths.

## System Architecture

The core architecture operates serially through a robust pipeline decoupled for scale:

```text
 Webcam Feed
      ↓
 OpenCV Engine
      ↓
 MediaPipe Processors (Face Mesh + Hand Tracking)
      ↓
 Authentication Service (Continuous Identity Guard)
      ↓
 Gesture & Interaction Engine (EAR, Hand Signals, Smooth Cursor)
      ↓
 Context Intent Analyzer (Yields Command Instructions)
      ↓
 Command Registry (RBAC Filter)
      ↓
 Smart Library / Application GUI (CustomTkinter)
      ↓
 SQLite Database / OpenPyXL Reporting
```

## Technology Stack

The project relies strictly on a deterministic core layout without fragmented bloat:

- **Python 3.11** (Core Processing Logic)
- **OpenCV (`opencv-python`)** (Video I/O and frame transformation)
- **MediaPipe** (High-fidelity ML landmarker topology for eyes and hands)
- **CustomTkinter** (Modern, hardware-accelerated GUI development)
- **SQLite** (Embedded relational database framework)
- **OpenPyXL** (Static robust Excel `.xlsx` workbook manipulation)
- **NumPy** (High-performance array operations and geometric mathematics)
- **Cryptography** (Secure AES encryption mapping for biometric profiles)

## Project Structure

```text
TrueEyeballproject/
├── data/                       # Local SQLite DB and generated Excel reports
├── library_app/                # Application GUI, backend commands, and Repository
│   ├── commands/               # Command mappings for physical gestures
│   ├── database/               # Relational schemas and object handlers
│   ├── reports/                # Dynamic spreadsheet exporting logic
│   └── ui/                     # Decoupled application-specific custom widgets
├── modules/                    # Independent AI computer vision modules
│   ├── auth/                   # Face landmarker authentication manager
│   ├── context/                # Context-aware behavioral intent mapper
│   ├── evaluation/             # Specialized model benchmarking suite
│   └── ui/                     # Assistive interface systems (Virtual Keyboard)
├── tests/                      # Extensive PyTest integration suite
├── TrueEyeball_App.py          # Legacy entry wrapper
├── core_backend.py             # Global AI configuration processing thread
├── main.py                     # Entry point (Application Startup)
├── manage_users.py             # Administrative fallback CLI
├── register.py                 # Visual User Registration & Model capture
├── run.bat                     # Windows application launcher
├── run_tests.bat               # Headless automated testing runner
├── seed_books.py               # Pre-population database bootstrapping script
└── requirements.txt            # System dependencies
```
