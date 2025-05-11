import cv2
import threading
import queue
import time
import numpy as np
from xarm import Controller, Servo
import mediapipe as mp

# ─── ROBOT SETUP ────────────────────────────────────────────────────────────────
arm = Controller('USB')

# Servo behavior:
# 1 (claw): bigger = closed
# 3 (elbow): smaller = forward
# 4 (shoulder): smaller = back
# 2,5,6 remain fixed at 500

range_map = {
    1: (0,   700),
    2: (500, 500),
    3: (0,  1000),
    4: (150,850),
    5: (500, 500),
    6: (500, 500),
}
opened, closed = 0, 700
current_positions = {j:500 for j in range(1,7)}

def clamp(j, p):
    lo, hi = range_map[j]
    return max(lo, min(hi, p))

def move_all(jpos, duration=1000):
    servos = [Servo(j, p) for j,p in jpos.items()]
    arm.setPosition(servos, duration=duration, wait=True)
    time.sleep(0.5)

def set_claw(pos):
    p = clamp(1, pos)
    current_positions[1] = p
    move_all(current_positions)

def human_angle_to_servo(joint, angle):
    lo, hi = range_map[joint]
    return int(lo + (angle/180)* (hi-lo))

def go_to_pose(sh_ang, el_ang, hand_closed):
    current_positions[4] = clamp(4, human_angle_to_servo(4, sh_ang))
    current_positions[3] = clamp(3, human_angle_to_servo(3, el_ang))
    move_all(current_positions)
    set_claw(closed if hand_closed else opened)

# ─── MEDIAPIPE DETECTOR ─────────────────────────────────────────────────────────
class PoseDetector:
    def __init__(self):
        # pose detector
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # hand detector
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def find_pose(self, img, draw=False):
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.pose_res = self.pose.process(img_rgb)
        self.hand_res = self.hands.process(img_rgb)
        # optionally draw landmarks
        if draw and self.pose_res.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                img, self.pose_res.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
        return img

    def find_position(self, img):
        pose_list, hand_list = [], None
        # pose landmarks
        if self.pose_res.pose_landmarks:
            h, w, _ = img.shape
            for id, lm in enumerate(self.pose_res.pose_landmarks.landmark):
                pose_list.append([id, int(lm.x*w), int(lm.y*h)])
        # hand landmarks (single hand)
        if self.hand_res.multi_hand_landmarks:
            h, w, _ = img.shape
            hand_list = []
            for id, lm in enumerate(self.hand_res.multi_hand_landmarks[0].landmark):
                hand_list.append([id, int(lm.x*w), int(lm.y*h)])
        return pose_list, hand_list

    def calculate_angle(self, p1, p2, p3):
        a = np.array([p1[1], p1[2]]) - np.array([p2[1], p2[2]])
        b = np.array([p3[1], p3[2]]) - np.array([p2[1], p2[2]])
        cos = np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))
        return np.degrees(np.arccos(np.clip(cos, -1, 1)))

    def is_hand_closed(self, hand_landmarks):
        if not hand_landmarks:
            return False
        # count extended fingers
        tips = [4,8,12,16,20]
        pips = [3,6,10,14,18]
        ext = 0
        for t, p in zip(tips, pips):
            tip_y = hand_landmarks[t][2]
            pip_y = hand_landmarks[p][2]
            if tip_y < pip_y:
                ext += 1
        # closed if at most 1 finger extended
        return ext <= 1

# ─── CAMERA THREAD ───────────────────────────────────────────────────────────────
def camera_thread(src, q):
    cap = cv2.VideoCapture(src)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    while True:
        ret, frame = cap.read()
        if not ret: break
        if not q.empty():
            try: q.get_nowait()
            except: pass
        q.put(frame)
    cap.release()

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    q = queue.Queue(maxsize=1)
    threading.Thread(target=camera_thread, args=(0,q), daemon=True).start()
    detector = PoseDetector()

    # neutral pose
    current_positions.update({2:500,5:500,6:500,3:500,4:500,1:opened})
    move_all(current_positions)

    while True:
        if q.empty():
            time.sleep(0.005)
            continue
        img = q.get()
        img = detector.find_pose(img)
        pose_lms, hand_lms = detector.find_position(img)

        sh = el = None
        closed = False
        ids = {11,13,15,23}
        if ids.issubset({lm[0] for lm in pose_lms}):
            l_sh  = next(x for x in pose_lms if x[0]==11)
            l_el  = next(x for x in pose_lms if x[0]==13)
            l_wr  = next(x for x in pose_lms if x[0]==15)
            l_hip = next(x for x in pose_lms if x[0]==23)
            sh = detector.calculate_angle(l_hip, l_sh, l_el)
            el = detector.calculate_angle(l_sh, l_el, l_wr)
            closed = detector.is_hand_closed(hand_lms)

            cv2.putText(img, f"S:{int(sh)} E:{int(el)}", (20,40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0),2)
            cv2.putText(img, "FIST" if closed else "OPEN", (20,80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0,0,255) if closed else (0,255,0),2)
            go_to_pose(sh, el, closed)

        cv2.imshow("Live Pose", img)
        if cv2.waitKey(1)&0xFF==ord('q'): break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
