# * * * * * * * * * * * * * * * * * * #
# EXTERNAL IMPORTS
# * * * * * * * * * * * * * * * * * * #
import cv2
import pyttsx3
import playsound
import sounddevice
import speech_recognition
import ultralytics

BEEP = str("assets/audio/beep.mp3")

class ImagePoiFinder():
    def __init__(self):
        self.text_to_speech("During program, whenever prompted to speak, please wait until after the beep.")
        self.text_to_speech("Would you like to capture image now?")
        should_capture_now = self.speech_to_text()
    
        if should_capture_now.lower() == "yes":
            self.capture_image()
            self.text_to_speech("Image captured.")
            self.text_to_speech("Detecting objects in the captured image.")
            self.detect_objects()
        
        self.text_to_speech("What object do you want to detect?")
        object_to_detect = self.speech_to_text()
        if object_to_detect != "":
            self.text_to_speech(f"You want to detect: {object_to_detect}")

    def capture_image(
            self,
            camera_device_id: int = 0,
            capture_path: str = "assets/images/captured_frame.jpg"
        ) -> int:
        """Capture image from device

        Args:
            camera_device_id (int, optional): camera device id. Defaults to 0.
            capture_path (str, optional): path to save capture to. Defaults to "captured_frame.jpg".

        Returns:
            int: _description_
        """
        return_code = 0
        camera = cv2.VideoCapture(0)

        success, frame = camera.read()

        if success:
            cv2.imwrite(capture_path, frame)
        else:
            return_code = -1
        camera.release()

        cv2.destroyAllWindows()
        return return_code

    def detect_objects(
            self,
            input_image_path: str = "assets/images/captured_frame.jpg",
            output_image_path: str = "assets/images/annotated_image.jpg",
            yolo_model: str = "yolov8n.pt"
        ) -> str:
        """Detect objects in image and return the image with bounding boxes

        Args:
            input_image_path (str, optional): path of image to detect. Defaults to "assets/images/captured_frame.jpg".
            output_image_path (str, optional): path to output bounding box image to. Defaults to "assets/images/annotated_image.jpg".
            yolo_model (str, optional): model to use for detection. Defaults to "yolov8n.pt".

        Returns:
            str: path of bb image
        """
        model = ultralytics.YOLO(
            model=yolo_model
        )
        results = model(
            source=input_image_path
        )
        return results[0].save(filename=output_image_path)

    def text_to_speech(
            self,
            text: str
        ) -> int:
        """Convert text to speech

        Args:
            text (str): text to convert to speech

        Returns:
            int: return code. 0 if successful
        """
        try:
            print(f"- {text}")
            engine = pyttsx3.init()
            engine.setProperty(
                name="rate", 
                value=150
            )
            engine.say(text)
            engine.runAndWait()
            return 0
        except Exception as e:
            print(e)
            return -1

    def speech_to_text(
            self,
            sample_rate: int = 44100,
            seconds: int = 3
        ) -> str:
        """Convert speech input to text

        Args:
            sample_rate (int, optional): sample rate for recording. Defaults to 44100.
            seconds (int, optional): seconds for recording_. Defaults to 3.

        Returns:
            str: text string of speech input
        """
        recognizer = speech_recognition.Recognizer()

        while True:
            recording = sounddevice.rec(
                int(seconds * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16"
            )

            playsound.playsound(BEEP)

            sounddevice.wait()

            audio = speech_recognition.AudioData(
                recording.tobytes(),
                sample_rate,
                2
            )

            try:
                text = recognizer.recognize_google(audio)
                return text

            except speech_recognition.UnknownValueError:
                self.text_to_speech("Could not understand. Please speak again after the beep.")

def main():
    ImagePoiFinder()

if __name__ == "__main__":
    main()


# pip install opencv-python pyttsx3 sounddevice SpeechRecognition ultralytics
