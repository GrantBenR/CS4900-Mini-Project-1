import cv2
import pyttsx3
from playsound import playsound
import sounddevice as sd
import speech_recognition as sr
from ultralytics import YOLO


def capture_image(
        camera_device_id: int = 0,
        capture_path: str = "captured_frame.jpg"
    ):
    camera = cv2.VideoCapture(0)

    success, frame = camera.read()

    if success:
        cv2.imwrite(capture_path, frame)
    camera.release()

    cv2.destroyAllWindows()

def detect_objects(
        input_image_path: str = "captured_frame.jpg",
        output_image_path: str = "annotated_image.jpg",
        yolo_model: str = "yolov8n.pt"
    ) -> str:
    model = YOLO(
        model=yolo_model
    )
    results = model(
        source=input_image_path
    )
    return results[0].save(filename=output_image_path)

def text_to_speech(
        text: str
    ):
    engine = pyttsx3.init()
    engine.setProperty(
        name="rate", 
        value=150
    )
    engine.say(text)
    engine.runAndWait()

def speech_to_text(
        sample_rate: int = 44100,
        seconds: int = 3
    ):
    recognizer = sr.Recognizer()

    while True:
        recording = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        playsound("assets/audio/beep.mp3")

        sd.wait()

        audio = sr.AudioData(
            recording.tobytes(),
            sample_rate,
            2
        )

        try:
            text = recognizer.recognize_google(audio)
            return text

        except sr.UnknownValueError:
            text_to_speech("Could not understand. Please speak again after the beep.")

def main():

    text_to_speech("During program, whenever prompted to speak, please wait until after the beep.")
    text_to_speech("Would you like to capture image now?")
    text = speech_to_text()

    if text.lower() == "yes":
        capture_image()
        text_to_speech("Image captured.")
        text_to_speech("Detecting objects in the captured image.")
        detect_objects()

    text_to_speech("What object do you want to detect?")
    text = speech_to_text()
    if text != "":
        text_to_speech(f"You want to detect: {text}")

    

if __name__ == "__main__":
    main()


# pip install opencv-python pyttsx3 sounddevice SpeechRecognition ultralytics
