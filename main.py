import cv2
import mediapipe as mp
import pyautogui
import threading
from queue import Queue
import numpy as np
import pyopencl as cl
import torch

class GPUAccelerator:
    def __init__(self):
        # Disable GPU for now since it's causing issues
        self.gpu_enabled = False
        print("GPU acceleration disabled to prevent errors")

    def to_gpu(self, arr):
        if self.gpu_enabled:
            return cl.Buffer(
                self.ctx,
                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                hostbuf=arr.astype(np.float32)
            )
        return arr

    def to_cpu(self, buf, shape):
        if self.gpu_enabled:
            result = np.empty(shape, dtype=np.float32)
            cl.enqueue_copy(self.queue, result, buf)
            return result
        return buf

class HandProcessor:
    def __init__(self, frame_queue, result_queue):
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.stopped = False
        
        # Configuration pour MediaPipe
        self.hand_detector = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            model_complexity=1
        )
        
        # Initialisation de l'accélérateur GPU
        self.gpu = GPUAccelerator()
        
    def process_frame_gpu(self, frame):
        # Simplify to just use CPU processing for now
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def process(self):
        while not self.stopped:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                
                # Traitement GPU
                rgb_frame = self.process_frame_gpu(frame)
                
                # Détection des mains avec MediaPipe
                output = self.hand_detector.process(rgb_frame)
                
                if output.multi_hand_landmarks:
                    # Traitement des landmarks sur GPU si possible
                    for hand_landmarks in output.multi_hand_landmarks:
                        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
                        if self.gpu.gpu_enabled:
                            landmarks_gpu = self.gpu.to_gpu(landmarks)
                            # Ici on pourrait ajouter des calculs supplémentaires sur GPU
                            landmarks = self.gpu.to_cpu(landmarks_gpu, landmarks.shape)
                
                self.result_queue.put((frame, output))
    
    def start(self):
        thread = threading.Thread(target=self.process, args=())
        thread.daemon = True
        thread.start()
        return self
    
    def stop(self):
        self.stopped = True

# Modification de la fonction get_screen_coordinates pour utiliser GPU
def get_screen_coordinates(landmark, frame_width, frame_height, screen_width, screen_height):
    x = landmark.x * frame_width * (screen_width/frame_width)
    y = landmark.y * frame_height * (screen_height/frame_height)
    return x, y

# Configuration initiale
def initialize_capture():
    cap = cv2.VideoCapture(0)
    hand_detector = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,  # Limite à une seule main pour optimiser
        min_detection_confidence=0.7
    )
    return cap, hand_detector

def process_hand_landmarks(frame, hands, screen_width, screen_height):
    frame_height, frame_width, _ = frame.shape
    index_y = thumb_y = None
    
    for hand in hands:
        landmarks = hand.landmark
        
        # Récupération des points d'intérêt (index et pouce)
        index_point = landmarks[8]
        thumb_point = landmarks[4]
        
        # Calcul des coordonnées
        index_x, index_y = get_screen_coordinates(index_point, frame_width, frame_height, screen_width, screen_height)
        thumb_x, thumb_y = get_screen_coordinates(thumb_point, frame_width, frame_height, screen_width, screen_height)
        
        # Dessin des points
        draw_landmark_point(frame, index_point, frame_width, frame_height)
        draw_landmark_point(frame, thumb_point, frame_width, frame_height)
        
        # Déplacement et clic
        pyautogui.moveTo(index_x, index_y)
        if thumb_y and abs(index_y - thumb_y) < 150:
            pyautogui.click()
            pyautogui.sleep(1)

def draw_landmark_point(frame, landmark, frame_width, frame_height):
    x = int(landmark.x * frame_width)
    y = int(landmark.y * frame_height)
    cv2.circle(img=frame, center=(x,y), radius=10, color=(0, 255, 255))

class VideoGet:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        
    def start(self):
        thread = threading.Thread(target=self.get, args=())
        thread.daemon = True
        thread.start()
        return self
        
    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                self.grabbed, self.frame = self.stream.read()
                
    def stop(self):
        self.stopped = True
        self.stream.release()

def main():
    # Vérification du support OpenCL
    try:
        platforms = cl.get_platforms()
        devices = platforms[0].get_devices(device_type=cl.device_type.GPU)
        print(f"OpenCL GPU available: {devices[0].name}")
    except:
        print("OpenCL GPU not available, using CPU")
    
    # Initialisation des queues pour la communication entre threads
    frame_queue = Queue(maxsize=2)
    result_queue = Queue(maxsize=2)
    
    # Démarrage des threads
    video_getter = VideoGet().start()
    hand_processor = HandProcessor(frame_queue, result_queue).start()
    
    drawing_utils = mp.solutions.drawing_utils
    screen_width, screen_height = pyautogui.size()
    
    try:
        while True:
            if video_getter.stopped:
                break
                
            frame = video_getter.frame
            frame = cv2.flip(frame, 1)
            
            # Envoi du frame pour traitement
            if not frame_queue.full():
                frame_queue.put(frame)
            
            # Traitement des résultats
            if not result_queue.empty():
                processed_frame, output = result_queue.get()
                
                if output and output.multi_hand_landmarks:
                    for hand in output.multi_hand_landmarks:
                        drawing_utils.draw_landmarks(processed_frame, hand)
                        process_hand_landmarks(processed_frame, [hand], screen_width, screen_height)
                
                cv2.imshow('Fingclick', processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # Nettoyage
        video_getter.stop()
        hand_processor.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()