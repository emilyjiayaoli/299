from xarm import Controller, Servo
import time

arm = Controller('USB')

# Servo behavior:
# 1 (claw): bigger number = closed
# 2 (angle): bigger number = right
# 3 (wrist): smaller number = forward
# 4 (elbow): smaller number = back
# 5 (shoulder): bigger number = back
# 6 (base): bigger number = rotate left

range_map = {
    1: (0, 700),
    2: (0, 1000),
    3: (0, 1000),
    4: (0, 1000),
    5: (0, 850),
    6: (0, 1000)
}

opened = 0
closed = 700

current_positions = {i: 500 for i in range(1, 7)}

def clamp(joint, pos):
    lo, hi = range_map[joint]
    return max(lo, min(pos, hi))

def move_all(joint_positions, duration=2000):
    servos = [Servo(joint, pos) for joint, pos in joint_positions.items()]
    arm.setPosition(servos, duration=duration, wait=True)
    time.sleep(1)

def reset():
    print("[INFO] Resetting full arm including claw...")
    for j in current_positions:
        current_positions[j] = 500
    move_all(current_positions)
    print("[INFO] Full reset complete.")

def return_home():
    print("[INFO] Returning joints to home (claw untouched)...")
    for j in current_positions:
        if j != claw:
            current_positions[j] = 500
    move_all(current_positions)
    print("[INFO] Joints returned to home.")

def move_joint(joint_number, position, duration=1000):
    old = current_positions[joint_number]
    new = clamp(joint_number, position)
    print(f"[INFO] Moving joint {joint_number} from {old} to {new}...")
    current_positions[joint_number] = new
    move_all(current_positions, duration)
    time.sleep(0.5)
    print(f"[INFO] Joint {joint_number} now at {new}.")

def set_claw(position, duration=1000):
    target = clamp(claw, position)
    move_joint(claw, target, duration)

def bend_and_pick():
    print("[INFO] Performing bend and pick sequence...")
    set_claw(opened)
    target_positions = {
        shoulder: 575,
        elbow: 930,
        wrist: 200
    }
    for joint, pos in target_positions.items():
        current_positions[joint] = clamp(joint, pos)
    move_all(current_positions)
    time.sleep(0.5)
    set_claw(closed)
    print("[INFO] Pick sequence complete.")

def bend_and_drop():
    print("[INFO] Performing bend and drop sequence...")
    target_positions = {
        shoulder: 575,
        elbow: 930,
        wrist: 200,
        base: 100 # rotate right
    }
    for joint, pos in target_positions.items():
        current_positions[joint] = clamp(joint, pos)
    move_all(current_positions)
    time.sleep(0.5)
    set_claw(opened)
    print("[INFO] Drop sequence complete.")

claw = 1
hand = claw
angle = 2
wrist = 3
elbow = 4
shoulder = 5
base = 6
bottom = base

if __name__ == "__main__":
    reset()
    bend_and_pick()
    return_home()
    bend_and_drop()
    return_home()