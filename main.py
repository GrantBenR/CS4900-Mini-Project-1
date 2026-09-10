import cv2
import pyttsx3
import winsound
import sounddevice as sd
import speech_recognition as sr
from ultralytics import YOLO


def capture_image():
    camera = cv2.VideoCapture(0)

    success, frame = camera.read()

    if success:
        cv2.imwrite("captured_frame.jpg", frame)
    camera.release()

    cv2.destroyAllWindows()

def detect_objects():
    model = YOLO("yolov8n.pt")
    results = model("captured_frame.jpg")
    results[0].save(filename="annotated_image.jpg")

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.say(text)
    engine.runAndWait()

def speech_to_text():
    recognizer = sr.Recognizer()

    sample_rate = 44100
    seconds = 3

    while True:
        recording = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        winsound.Beep(1000, 200)

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
