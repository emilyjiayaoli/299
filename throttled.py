# user for demo vid (iphone)
import cv2
import time
from pose_estimation import PoseDetector
from xarm import Controller, Servo

# ─── ROBOT SETUP ────────────────────────────────────────────────────────────────
arm = Controller('USB')

# Servo behavior:
# 1 (claw): bigger = closed
# 2 (angle): bigger = right      (unused)
# 3 (elbow): smaller = forward
# 4 (shoulder): smaller = back
# 5 (always 500): bigger = back  (unused)
# 6 (base): bigger = rotate left (unused)

# hardware ranges
range_map = {
    1: (0,   700),   # claw
    2: (500, 500),   # angle axis
    3: (0,  1000),   # elbow
    4: (150, 850),   # shoulder
    5: (500, 500),   # fixed
    6: (500, 500),   # fixed
}

opened = 0
closed = 700

# track current positions
current_positions = {j: 500 for j in range(1, 7)}

def clamp(j, p):
    lo, hi = range_map[j]
    return max(lo, min(hi, p))

def move_all(jpos, duration=1000):
    servos = [Servo(j, p) for j, p in jpos.items()]
    arm.setPosition(servos, duration=duration, wait=True)
    time.sleep(0.5)

def set_claw(position, duration=1000):
    p = clamp(1, position)
    current_positions[1] = p
    move_all(current_positions, duration)

def human_angle_to_servo(joint, angle_deg):
    lo, hi = range_map[joint]
    span = hi - lo
    return int(lo + (angle_deg / 180.0) * span)

def go_to_pose(shoulder_angle, elbow_angle, hand_closed):
    # shoulder → servo 4
    sh_p = clamp(4, human_angle_to_servo(4, shoulder_angle))
    # elbow    → servo 3
    el_p = clamp(3, human_angle_to_servo(3, elbow_angle))
    current_positions[4] = sh_p
    current_positions[3] = el_p

    # apply
    move_all(current_positions)

    # claw
    set_claw(closed if hand_closed else opened)



def main():
    cap = cv2.VideoCapture(0)
    detector = PoseDetector()

    # Neutral start (as before)
    current_positions.update({2:500, 5:500, 6:500})
    current_positions[3] = int((range_map[3][0] + range_map[3][1]) / 2)
    current_positions[4] = int((range_map[4][0] + range_map[4][1]) / 2)
    current_positions[1] = opened
    move_all(current_positions)

    # ---- set up your throttling / dead‑zone logic ----
    last_sent_time   = 0.0
    min_interval     = 0.5    # seconds between updates
    angle_threshold  = 5.0    # only send if >5° change
    last_sh, last_el = None, None
    last_hand       = None

    while True:
        ret, img = cap.read()
        if not ret:
            break

        img = detector.find_pose(img)
        pose_lms, hand_lms = detector.find_position(img)

        sh_ang = el_ang = None
        hand_closed = False

        if all(i in [lm[0] for lm in pose_lms] for i in (11,13,15,23)):
            l_sh  = next(lm for lm in pose_lms if lm[0]==11)
            l_el  = next(lm for lm in pose_lms if lm[0]==13)
            l_wr  = next(lm for lm in pose_lms if lm[0]==15)
            l_hip = next(lm for lm in pose_lms if lm[0]==23)

            sh_ang = detector.calculate_angle(l_hip, l_sh, l_el)
            el_ang = detector.calculate_angle(l_sh, l_el, l_wr)
            hand_closed, _ = detector.is_hand_closed(hand_lms, img.shape)

            # draw feedback (optional) …
            cv2.putText(img, f"S:{sh_ang:.0f}° E:{el_ang:.0f}°", (20,60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0),2)
            cv2.putText(img, "FIST" if hand_closed else "OPEN", (20,110),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0,0,255) if hand_closed else (0,255,0), 2)

            # decide if we should send a new command:
            now = time.time()
            moved_enough = (
                last_sh is None
                or abs(sh_ang - last_sh) > angle_threshold
                or abs(el_ang - last_el) > angle_threshold
                or (hand_closed != last_hand)
            )
            if moved_enough and (now - last_sent_time) > min_interval:
                go_to_pose(sh_ang, el_ang, hand_closed)
                last_sent_time = now
                last_sh, last_el, last_hand = sh_ang, el_ang, hand_closed

        cv2.imshow("Auto‑Follow Pose", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
