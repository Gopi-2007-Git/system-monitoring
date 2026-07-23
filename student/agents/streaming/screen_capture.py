import cv2
import numpy as np
import mss


def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor

        while True:
            screenshot = sct.grab(monitor)

            frame = np.array(screenshot)

            # Convert BGRA → BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            cv2.imshow("Student Screen Capture", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    capture_screen()