from fastapi import FastAPI, WebSocket, UploadFile, File, Request
from fastapi.responses import JSONResponse, Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ultralytics import YOLO

import cv2
import numpy as np


app = FastAPI(
    title="Multi-Agent Secure Exam Monitoring System",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory="backend/static"),
    name="static"
)

templates = Jinja2Templates(directory="backend/templates")

# ----------------------------
# Global Variables
# ----------------------------

students = {}

# Load YOLO model only once
model = YOLO("yolov8n.pt")
def raise_alert(student, alert_key, alert_message):

    if not student[alert_key]:

        student["alert_count"] += 1
        student["last_alert"] = alert_message
        student[alert_key] = True


# ----------------------------
# Dashboard
# ----------------------------

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={}
    )


# ----------------------------
# Home
# ----------------------------

@app.get("/")
def home():

    return {
        "message": "Backend Running Successfully 🚀"
    }


# ----------------------------
# Students API
# ----------------------------

@app.get("/students")
def get_students():

    return [

        {
            "id": student_id,
            "status": data["status"],
            "ai_status": data["ai_status"],
            "alert_count": data["alert_count"],
            "last_alert": data["last_alert"]
        }

        for student_id, data in students.items()

    ]


# ----------------------------
# Live Screen
# ----------------------------

@app.get("/frame/{student_id}")
def get_frame(student_id: str):

    if student_id not in students:

        return JSONResponse(
            {"error": "Student Not Found"},
            status_code=404
        )

    frame = students[student_id]["latest_frame"]

    if frame is None:

        return JSONResponse(
            {"error": "Frame Not Available"},
            status_code=404
        )

    _, jpeg = cv2.imencode(".jpg", frame)

    return Response(
        content=jpeg.tobytes(),
        media_type="image/jpeg"
    )
@app.get("/webcam_frame/{student_id}")
def get_webcam_frame(student_id: str):

    if student_id not in students:

        return JSONResponse(
            {"error": "Student Not Found"},
            status_code=404
        )

    frame = students[student_id]["processed_webcam"]

    if frame is None:

        return JSONResponse(
            {"error": "Frame Not Available"},
            status_code=404
        )

    _, jpeg = cv2.imencode(".jpg", frame)

    return Response(
        content=jpeg.tobytes(),
        media_type="image/jpeg"
    )


# ----------------------------
# Webcam Upload + YOLO
# ----------------------------

@app.post("/webcam/{student_id}")
async def upload_webcam(student_id: str, file: UploadFile = File(...)):

    if student_id not in students:

        return {"status": "student not found"}

    # Read webcam image

    image_bytes = await file.read()

    students[student_id]["latest_webcam"] = image_bytes

    # Convert bytes to OpenCV image

    np_array = np.frombuffer(image_bytes, np.uint8)

    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if frame is None:

        return {"status": "invalid image"}

    # -------------------------
    # YOLO Detection
    # -------------------------

    results = model(frame, verbose=False)
    annotated_frame = results[0].plot()
    students[student_id]["processed_webcam"] = annotated_frame

    phone_detected = False
    person_count = 0

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            class_name = model.names[class_id]

            if class_name == "cell phone":

                phone_detected = True

            elif class_name == "person":

                person_count += 1

# -------------------------
# Update AI Status
# -------------------------

    student = students[student_id]

    if phone_detected:

        student["ai_status"] = "🔴 Phone Detected"

        raise_alert(student, "phone_alert_active", "Phone Detected")

        student["multiple_person_active"] = False
        student["no_person_active"] = False

    elif person_count == 0:

        student["ai_status"] = "🟡 No Person"

        raise_alert(student, "no_person_active", "No Person")

        student["phone_alert_active"] = False
        student["multiple_person_active"] = False

    elif person_count > 1:

        student["ai_status"] = "🟠 Multiple Persons"

        raise_alert(student, "multiple_person_active", "Multiple Persons")

        student["phone_alert_active"] = False
        student["no_person_active"] = False

    else:

        student["ai_status"] = "🟢 Safe"

        student["last_alert"] = None

        student["phone_alert_active"] = False
        student["multiple_person_active"] = False
        student["no_person_active"] = False

    print(
        f"{student_id} | Persons: {person_count} | Phone: {phone_detected}"
    )

    return {"status": "ok"}

# ----------------------------
# WebSocket
# ----------------------------

@app.websocket("/ws/{student_id}")
async def websocket_endpoint(websocket: WebSocket, student_id: str):

    await websocket.accept()

    students[student_id] = {

    "websocket": websocket,

    "latest_frame": None,

    "latest_webcam": None,

    "processed_webcam": None,

    "status": "online",

    "ai_status": "🟢 Safe",

    "alert_count": 0,

    "last_alert": None,

    # Violation States
    "phone_alert_active": False,
    "multiple_person_active": False,
    "no_person_active": False
}

    print(f"✅ {student_id} Connected")

    try:

        while True:

            data = await websocket.receive_bytes()

            np_arr = np.frombuffer(data, np.uint8)

            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            students[student_id]["latest_frame"] = frame

    except Exception:

        print(f"❌ {student_id} Disconnected")

        students.pop(student_id, None)