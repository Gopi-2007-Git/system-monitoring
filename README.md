# Multi-Agent Secure Exam Monitoring System

A real-time exam proctoring system. A **student agent** streams the student's
screen (and optionally webcam) over WebSocket/HTTP to a **FastAPI backend**,
which runs YOLOv8 object detection on incoming webcam frames to flag phones,
missing students, or multiple people in frame, and shows live status on an
admin **dashboard**.

## Project Structure

```
Multi-Agent-Secure-Exam-System/
├── backend/
│   ├── app.py                  # FastAPI app: routes, WebSocket, YOLO inference
│   ├── ai/                     # (reserved) face/phone/eye/screen analysis modules
│   ├── managers/                # (reserved) frame/connection manager modules
│   ├── models/                  # (reserved) data models
│   ├── routes/                  # (reserved) dashboard route module
│   ├── static/                  # static assets served at /static
│   └── templates/
│       └── dashboard.html       # live admin dashboard UI
├── student/
│   └── agents/streaming/
│       ├── screen_capture.py    # standalone screen-capture preview tool
│       └── stream_client.py     # student agent: streams screen + webcam to backend
├── yolov8n.pt                   # pretrained YOLOv8 nano weights
└── requirements.txt
```

> Note: `backend/ai`, `backend/managers`, `backend/models`, and `backend/routes`
> currently contain empty placeholder modules reserved for splitting the
> monolithic `app.py` logic (face detection, phone detection, eye tracking,
> screen analysis, connection/frame management) into separate agents later.

## Requirements

- Python 3.10+ (project was built/tested on Python 3.12)
- [uv](https://docs.astral.sh/uv/) installed
- A webcam (for webcam monitoring) and a display (for screen streaming)

## 1. Setup

Clone/unzip the project, then from the project root (`Multi-Agent-Secure-Exam-System/`):

```bash
uv sync
```

(or `uv pip install -r requirements.txt` if you're not using a `uv` project/lockfile)

This installs FastAPI, Uvicorn, OpenCV, NumPy, Ultralytics (YOLOv8, pulls in
PyTorch automatically), websockets, aiohttp, and mss.

## 2. Run the Backend Server

Run this from the **project root** (not from inside `backend/`), since paths
like `backend/static` and `backend/templates` are relative to it:

```bash
uv run uvicorn backend.app:app --reload
```

- Backend root check: http://127.0.0.1:8000/
- Admin dashboard: http://127.0.0.1:8000/dashboard
- Student list API: http://127.0.0.1:8000/students

Leave this running in its own terminal.

## 3. Run a Student Agent

In a **separate terminal**, from the project root:

```bash
uv run student/agents/streaming/stream_client.py
```

You'll be prompted:
```
Enter Student ID: student1
Enable Webcam? (y/n): y
```

- Enter any unique student ID (used to identify the student on the dashboard).
- Choose `y` to also stream webcam frames for YOLO-based monitoring (phone /
  no-person / multiple-person detection), or `n` to stream screen only.

Repeat this command (with a different Student ID) in additional terminals to
simulate multiple students connecting at once.

## 4. (Optional) Preview Screen Capture Standalone

To just test screen capture locally without connecting to the backend:

```bash
uv run student/agents/streaming/screen_capture.py
```

Press `q` in the preview window to quit.

## API Reference

| Method | Endpoint                  | Description                                   |
|--------|----------------------------|------------------------------------------------|
| GET    | `/`                        | Health check                                   |
| GET    | `/dashboard`                | Live admin dashboard (HTML)                    |
| GET    | `/students`                 | JSON list of connected students + statuses     |
| GET    | `/frame/{student_id}`       | Latest screen frame (JPEG) for a student       |
| GET    | `/webcam_frame/{student_id}`| Latest YOLO-annotated webcam frame (JPEG)      |
| POST   | `/webcam/{student_id}`      | Upload a webcam frame for YOLO analysis        |
| WS     | `/ws/{student_id}`          | WebSocket for continuous screen frame stream   |

## Troubleshooting

- **`ModuleNotFoundError`**: make sure `uv sync` (or `uv pip install -r requirements.txt`)
  completed without errors.
- **Static files error on startup**: ensure you run uvicorn from the project
  root so `backend/static` and `backend/templates` resolve correctly.
- **Webcam not found**: check no other application is using the webcam and
  that camera permissions are granted to your terminal/Python.
- **Slow first run**: the first YOLO inference call downloads/loads model
  weights (`yolov8n.pt` is bundled already) and may take a few seconds.
