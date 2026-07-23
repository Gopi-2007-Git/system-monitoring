import asyncio
import websockets
import cv2
import mss
import numpy as np
import aiohttp

student_id = input("Enter Student ID: ")
enable_webcam = input("Enable Webcam? (y/n): ").lower() == "y"

uri = f"ws://127.0.0.1:8000/ws/{student_id}"


async def stream_screen():

    async with websockets.connect(uri) as websocket:

        print(f"✅ Connected as {student_id}")

        with mss.mss() as sct:

            monitor = sct.monitors[1]

            while True:

                # Capture screen
                screenshot = sct.grab(monitor)

                frame = np.array(screenshot)

                # Convert BGRA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Resize (reduces bandwidth)
                frame = cv2.resize(frame, (960, 540))

                # Compress image as JPEG
                _, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 60]
                )

                # Send screen frame to backend via WebSocket
                await websocket.send(buffer.tobytes())

                # 5 FPS
                await asyncio.sleep(0.2)


async def stream_webcam():

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        print("❌ Webcam not found")

        return

    async with aiohttp.ClientSession() as session:

        while True:

            ret, frame = cap.read()

            if not ret:

                await asyncio.sleep(0.5)

                continue

            # Resize webcam image
            frame = cv2.resize(frame, (640, 480))

            # Compress as JPEG
            _, buffer = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 60]
            )

            # Create multipart form
            data = aiohttp.FormData()

            data.add_field(
                "file",
                buffer.tobytes(),
                filename="webcam.jpg",
                content_type="image/jpeg"
            )

            # Upload webcam frame
            await session.post(
                f"http://127.0.0.1:8000/webcam/{student_id}",
                data=data
            )

            # Upload one webcam image every second
            await asyncio.sleep(1)

    cap.release()


async def main():

    tasks = [stream_screen()]

    if enable_webcam:
        tasks.append(stream_webcam())

    await asyncio.gather(*tasks)
asyncio.run(main())