# TrueEyeball OS Platform (Complete Edition)

An AI-powered hands-free computer control system that connects eye tracking, hand tracking, gesture recognition, and biometric authentication directly onto a secure, context-aware command registry managing complex desktop application state.

---

## PROJECT OVERVIEW

TrueEyeball evolved from a hardware-free spatial cursor simulation into a full Dual-Role Application Desktop. It operates an internal Database managing a secure inventory of Books, Transactions, Study Notes, and automated Excel analytical reporting, entirely navigable through secure gesture mappings mapped to active intelligent contexts (Library vs Notes).

## FEATURES

- **Face Authentication**: Continuous AI verification enforcing dual-roles (OWNER / STAFF).
- **Study Notes Mode**: Personal SQLite-persisted notebooks decoupled cleanly from the Library.
- **Library Manager**: Add, edit, remove, issue, and return books using gestural logic.
- **AI Command Center**: Real-time explainable tracking widget embedded rendering logic chains.
- **Automated Reporting**: Export robust `.xlsx` analytics dashboards instantly.
- **Database Engine**: Atomic constraints, indexed SQLite relational stability.

## ARCHITECTURE

Data flows sequentially:
`Camera -> Gesture AI -> Identity Authentication -> Context Engine -> Intent Registry -> Central Registry -> Permission Manager (Strict Roles) -> Database Service`

## REQUIREMENTS

- Python 3.11
- `face_landmarker.task` running on system.
- Webcam (Required for Authentication entry)

## INSTALLATION & VIRTUAL ENVIRONMENT

Start by spawning an optimized local machine environment:

```cmd
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install mediapipe==0.10.32
```

## FIRST OWNER REGISTRATION

The system denies access initially. Capture your biological identity safely:

```cmd
python register.py
```

_The very first user is permanently assigned `OWNER`._

## APPLICATION STARTUP

To launch the complete dual-pane system effortlessly:

```cmd
run.bat
```

Alternatively: `python main.py`

## LIBRARY MANAGEMENT (OWNER/STAFF)

- **Owners** have unrestricted Read, Write, Delete rights and global transaction history.
- **Staff** have Read, Issue, and self-Return rights. Editing books or generating bulk global reports is restricted. Attempted breaches emit `ACCESS_DENIED` exceptions in the AI loop.

## GESTURE CONTROLS & CONTEXT SWITCHING

Actions differ logically per active system.

- `BOTH THUMBS UP`: Flips active application state (`LIBRARY <-> STUDY_NOTES`).
- **In Library:** `RIGHT_THUMB_UP` == `ISSUE BOOK`. `SWIPE_LEFT` == `PREVIOUS_BOOK`.
- **In Study Notes:** `RIGHT_THUMB_UP` == `SAVE NOTE`.

## AI COMMAND CENTER

This visual side-panel monitors the AI engine in realtime showing exact pipeline states:

- Authenticated ID Role
- Raw Hand Gesture Detected
- Context Translation Intent
- Enforced Application command resulting

## TESTING & TROUBLESHOOTING

To run the master unit suite testing DB CRUD, permissions, intent logic, and command bindings:

```cmd
run_tests.bat
```

_(Runs: `python -m unittest discover tests` internally)._

## SHUTDOWN

Close cleanly via conventional window closing `X`. Background AI sensors tear down cleanly, releasing resources.

## PROJECT STRUCTURE

- `library_app/`: Application data logic, repository, and custom UI components (Dashboard).
- `modules/`: Headless AI subsystems managing prediction, calibration, kinematics, face identity, and Contextual Intent resolution.
- `data/`: Storage path for Local SQLite persistence and reports.
- `tests/`: End-to-end integration mapping layers.
