import cv2
import mediapipe as mp
import numpy as np
import math

class PoseDetector:
    def __init__(self, mode=False, complexity=1, smooth_landmarks=True,
                 enable_segmentation=False, smooth_segmentation=True,
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        
        self.mode = mode
        self.complexity = complexity
        self.smooth_landmarks = smooth_landmarks
        self.enable_segmentation = enable_segmentation
        self.smooth_segmentation = smooth_segmentation
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=self.mode,
            model_complexity=self.complexity,
            smooth_landmarks=self.smooth_landmarks,
            enable_segmentation=self.enable_segmentation,
            smooth_segmentation=self.smooth_segmentation,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize holistic model for hand landmarks
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=self.mode,
            model_complexity=self.complexity,
            smooth_landmarks=self.smooth_landmarks,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
    
    def find_pose(self, img, draw=True):
        # Flip the image horizontally for a later selfie-view display
        # This ensures left appears as left, right as right
        img = cv2.flip(img, 1)
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(img_rgb)
        self.holistic_results = self.holistic.process(img_rgb)
        
        if self.results.pose_landmarks and draw:
            self.mp_draw.draw_landmarks(
                img, 
                self.results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
            # Draw left hand landmarks if available - since we flipped the image
            # what appears on screen as left is actually detected as right by MediaPipe
            if self.holistic_results.left_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img,
                    self.holistic_results.left_hand_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS
                )
        
        return img
    
    def find_position(self, img, draw=True):
        pose_landmark_list = []
        left_hand_landmark_list = []  # This will now be filled with right hand landmarks
                                        # since we've flipped the image
        
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                pose_landmark_list.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        
        # Process left hand landmarks as "left" since we flipped the image
        if self.holistic_results.left_hand_landmarks:
            for id, lm in enumerate(self.holistic_results.left_hand_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                left_hand_landmark_list.append([id, cx, cy])
                
        return pose_landmark_list, left_hand_landmark_list
    
    def calculate_angle(self, p1, p2, p3):
        """
        Calculate angle between three points
        p1: First point [x, y]
        p2: Mid point [x, y] (the joint)
        p3: End point [x, y]
        """
        # Get vectors
        a = np.array([p1[1], p1[2]]) # First point
        b = np.array([p2[1], p2[2]]) # Mid point
        c = np.array([p3[1], p3[2]]) # End point
        
        # Calculate vectors from points
        ba = a - b
        bc = c - b
        
        # Calculate angle using dot product
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        # Ensure the value is in valid range for arccos
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        
        # Convert to degrees
        angle = np.degrees(angle)
        
        return angle

    def is_hand_closed(self, hand_landmarks, img_shape):
        """
        Detect whether the hand is closed (fist) or open
        Uses the distance between fingertips and wrist
        """
        if not hand_landmarks or len(hand_landmarks) < 21:
            return False, 0  # Not enough landmarks to determine

        # MediaPipe hand landmark indices:
        # Wrist: 0
        # Fingertips: 4 (thumb), 8 (index), 12 (middle), 16 (ring), 20 (pinky)
        wrist = next((lm for lm in hand_landmarks if lm[0] == 0), None)
        if not wrist:
            return False, 0

        # Get fingertip landmarks
        fingertips = []
        for tip_id in [4, 8, 12, 16, 20]:
            tip = next((lm for lm in hand_landmarks if lm[0] == tip_id), None)
            if tip:
                fingertips.append(tip)

        if len(fingertips) < 5:
            return False, 0

        # Calculate distance from each fingertip to wrist
        distances = []
        for tip in fingertips:
            dist = np.sqrt((tip[1] - wrist[1])**2 + (tip[2] - wrist[2])**2)
            # Normalize by image width for consistency
            normalized_dist = dist / img_shape[1]
            distances.append(normalized_dist)

        # Average normalized distance
        avg_distance = sum(distances) / len(distances)
        
        # Determine if hand is closed based on average distance
        # This threshold might need adjustment based on testing
        threshold = 0.12
        is_closed = avg_distance < threshold
        
        return is_closed, avg_distance

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    detector = PoseDetector()
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame from camera.")
            break
            
        # Find pose - image is flipped inside this function
        img = detector.find_pose(img)
        pose_landmarks, left_hand_landmarks = detector.find_position(img)
        
        if len(pose_landmarks) > 0:
            # Left arm angles - in the flipped image, what looks like left to the user
            # is detected as right by MediaPipe (11: right shoulder)
            # 11: right shoulder (appears as left on screen), 13: right elbow, 15: right wrist
            # 23: right hip
            if all(i in [lm[0] for lm in pose_landmarks] for i in [11, 13, 15, 23]):
                left_shoulder = next(lm for lm in pose_landmarks if lm[0] == 11)
                left_elbow = next(lm for lm in pose_landmarks if lm[0] == 13)
                left_wrist = next(lm for lm in pose_landmarks if lm[0] == 15)
                left_hip = next(lm for lm in pose_landmarks if lm[0] == 23)
                
                # Calculate shoulder angle (hip-shoulder-elbow)
                left_shoulder_angle = detector.calculate_angle(left_hip, left_shoulder, left_elbow)
                
                # Calculate elbow angle (shoulder-elbow-wrist)
                left_elbow_angle = detector.calculate_angle(left_shoulder, left_elbow, left_wrist)
                
                # Display angles with larger text
                cv2.putText(img, f"L Shoulder: {int(left_shoulder_angle)}°", 
                            (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                cv2.putText(img, f"L Elbow: {int(left_elbow_angle)}°", 
                            (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                
                # Draw angle lines
                cv2.line(img, (left_hip[1], left_hip[2]), 
                         (left_shoulder[1], left_shoulder[2]), (255, 255, 0), 3)
                cv2.line(img, (left_shoulder[1], left_shoulder[2]), 
                         (left_elbow[1], left_elbow[2]), (255, 255, 0), 3)
                cv2.line(img, (left_elbow[1], left_elbow[2]), 
                         (left_wrist[1], left_wrist[2]), (255, 255, 0), 3)
                
                # Check if hand is closed (fist) or open
                is_closed, distance = detector.is_hand_closed(left_hand_landmarks, img.shape)
                hand_status = "FIST" if is_closed else "OPEN"
                color = (0, 0, 255) if is_closed else (0, 255, 0)
                
                # Display hand status with larger text
                cv2.putText(img, f"Hand: {hand_status}", 
                            (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        
        # Display quit message
        cv2.putText(img, f"Press 'q' to quit", (10, img.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        
        # Show image
        cv2.imshow("Left Arm Pose Estimation", img)
        
        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 