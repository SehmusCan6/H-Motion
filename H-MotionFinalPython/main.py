import cv2
import mediapipe as mp
import serial
import time
import math

# === SERIAL CONNECTION ===
try:
    ser = serial.Serial('/dev/cu.usbmodem1401', 9600)
    time.sleep(2)
    print("[Arduino] Connected.")
except:
    ser = None
    print("[Arduino] No connection!")

# === MEDIAPIPE ===
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# === BUTTON CLASS ===
class ToggleButton:
    def __init__(self, label, pos, cmd_on, cmd_off, group=None):
        self.label = label
        self.pos = pos
        self.cmd_on = cmd_on
        self.cmd_off = cmd_off
        self.group = group
        self.selected = False
        self.hovered = False

    def draw(self, frame, active):
        x, y = self.pos
        if not active:
            return  # don't draw if not active
        color = (0, 200, 0) if self.selected else (170, 170, 170)
        if self.hovered:
            color = (100, 200, 255)
        cv2.rectangle(frame, (x, y), (x + 160, y + 60), color, -1)
        cv2.putText(frame, self.label, (x + 10, y + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    def is_inside(self, cx, cy):
        x, y = self.pos
        return x <= cx <= x + 160 and y <= cy <= y + 60

    def toggle(self, btn_list):
        if self.group:
            for b in btn_list:
                if b.group == self.group:
                    b.selected = False
            self.selected = True
            cmd = self.cmd_on
        else:
            self.selected = not self.selected
            cmd = self.cmd_on if self.selected else self.cmd_off
        send(cmd)
        return cmd

# === SEND COMMAND ===
def send(cmd):
    if ser and ser.is_open:
        ser.write((cmd + '\n').encode())
        print(f"[SENT] {cmd}")

# === BUTTONS ===
buttons = [
    ToggleButton("SYSTEM", (480, 40), "SYSTEM ON", "SYSTEM OFF"),
    ToggleButton("FAN", (100, 150), "FAN_ON", "FAN_OFF"),
    ToggleButton("SERVO 0°", (850, 140), "SERVO:0", "", group="servo"),
    ToggleButton("SERVO 90°", (850, 220), "SERVO:90", "", group="servo"),
    ToggleButton("SERVO 180°", (850, 300), "SERVO:180", "", group="servo")
]

# === CAMERA ===
cap = cv2.VideoCapture(0)
cv2.namedWindow("Smart Control", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Smart Control", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

clicked = False
system_active = False
last_cmd = ""

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    cursor_pos = None

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            x1 = int(hand.landmark[8].x * w)
            y1 = int(hand.landmark[8].y * h)
            x2 = int(hand.landmark[4].x * w)
            y2 = int(hand.landmark[4].y * h)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            cursor_pos = (cx, cy)
            cv2.circle(frame, (cx, cy), 10, (255, 0, 255), -1)

            distance = math.hypot(x2 - x1, y2 - y1)
            if distance < 40 and not clicked:
                for b in buttons:
                    if b.is_inside(cx, cy):
                        if b.label == "SYSTEM":
                            b.selected = not b.selected
                            system_active = b.selected
                            cmd = b.cmd_on if b.selected else b.cmd_off
                            send(cmd)
                            last_cmd = cmd
                        elif system_active:
                            last_cmd = b.toggle(buttons)
                        clicked = True
                        break
            elif distance >= 40:
                clicked = False

    # === Hover control ===
    for b in buttons:
        b.hovered = cursor_pos and b.is_inside(*cursor_pos)

    # === DRAW BUTTONS ===
    for b in buttons:
        if b.label == "SYSTEM":
            b.draw(frame, active=True)
        else:
            b.draw(frame, active=system_active)

    cv2.putText(frame, f"Command: {last_cmd}", (50, h - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 50, 255), 2)

    cv2.imshow("Smart Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
