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
        print("# * * * * * * * * * * * * * * * * * * #")
        print("# IMAGE POI FINDER")
        print("# * * * * * * * * * * * * * * * * * * #")

    def Run(
            self    
        ) -> int:
        try:
            # 
            # Introduce how prompting is done
            # 
            self.TextToSpeech("During program, whenever prompted to speak, please wait until after the beep.")
            # 
            # Does the user want to capture an image now?
            # 
            user_has_confirmed = False
            confirm_fail_count = 0
            while not user_has_confirmed:
                self.TextToSpeech("Would you like to capture image now?")
                should_capture_now = self.SpeechToText()
                # 
                # If the user answers yes, then break
                # 
                if should_capture_now.lower() == "yes":
                    user_has_confirmed = True
                # 
                # If the user doesn't answer yes, after 5 fails exit the program
                # 
                else:
                    confirm_fail_count += 1
                    user_has_confirmed = False
                    if confirm_fail_count >= 5:
                        self.TextToSpeech("Confirmation not received after five attempts. Exiting program.")
                        return -1
            # 
            # Capture the image
            # 
            self.CaptureImage()
            self.TextToSpeech("Image captured.")
            self.TextToSpeech("Detecting objects in the captured image.")
            # 
            # Detect objects in captured image
            # 
            detections = self.DetectObjects()
            if len(detections) > 0:
                # 
                # Have the user specify a class of objects to look for. If there are none, list all objects
                # 
                self.TextToSpeech("What object do you want to detect?")
                object_to_detect = self.SpeechToText()
                if object_to_detect != "":
                    matching_detections = [d for d in detections if d.get(object_to_detect)]
                    if len(matching_detections) > 0:
                        detections = matching_detections
                    else:
                        self.TextToSpeech(f"{object_to_detect} is not in the object")
                self.TextToSpeech(f"{len(detections)} objects found in the image.")
            else:
                self.TextToSpeech("No objects found in the image. Would you like to take another image?")
                take_another_image = self.SpeechToText()
                if take_another_image == "yes":
                    self.Run()
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            print(e)
            return -1
        
    def CaptureImage(
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
        try:
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
        except Exception as e:
            return -1

    def DetectObjects(
            self,
            input_image_path: str = "assets/images/captured_frame.jpg",
            output_image_path: str = "assets/images/annotated_image.jpg",
            yolo_model: str = "yolov8n.pt"
        ) -> list[dict]:
        """Detect objects in image and return the image with bounding boxes

        Args:
            input_image_path (str, optional): path of image to detect. Defaults to "assets/images/captured_frame.jpg".
            output_image_path (str, optional): path to output bounding box image to. Defaults to "assets/images/annotated_image.jpg".
            yolo_model (str, optional): model to use for detection. Defaults to "yolov8n.pt".

        Returns:
            str: path of bb image
        """
        try:
            model = ultralytics.YOLO(
                model=yolo_model
            )
            results = model(
                source=input_image_path
            )
            
            result = results[0]

            result.save(filename=output_image_path)

            img_height, img_width = result.orig_shape

            detections = []
            for box in result.boxes:
                # [x_min, y_min, x_max, y_max]
                box_range = box.xyxy[0].tolist()

                # [x_center, y_center, width, height]
                xywh = box.xywh[0].tolist()
                center_coords = (xywh[0], xywh[1])
                #
                # Get box label
                #
                class_id = int(box.cls[0].item())
                label = result.names[class_id]
                quadrants = self.GetBbQuadPercentages(
                    box_range=box_range,
                    img_width=img_width,
                    img_height=img_height
                )
                detections.append(
                    {
                        "label": label,
                        "center": center_coords,
                        "quadrants": quadrants
                    }
                )
            return detections
        except Exception as e:
            return ""
        
    def GetBbQuadPercentages(
            self, 
            box_range: list[int],
            img_width: int,
            img_height: int
        ):
        x_min, y_min, x_max, y_max = box_range
        box_area = (x_max - x_min) * (y_max - y_min)

        if box_area <= 0:
            return {
                "top_left": 0.0,
                "top_right": 0.0,
                "bottom_left": 0.0,
                "bottom_right": 0.0,
            }

        mid_x = img_width / 2.0
        mid_y = img_height / 2.0
        # 
        # Quadrant boundaries: (x_start, x_end, y_start, y_end)
        # 
        quadrants = {
            "top_left": (0, mid_x, 0, mid_y),
            "top_right": (mid_x, img_width, 0, mid_y),
            "bottom_left": (0, mid_x, mid_y, img_height),
            "bottom_right": (mid_x, img_width, mid_y, img_height),
        }

        percentages = {}
        for quad_name, (q_x_min, q_x_max, q_y_min, q_y_max) in quadrants.items():
            # 
            # Find width and height of the overlapping rectangle
            # 
            overlap_width = max(0.0, min(x_max, q_x_max) - max(x_min, q_x_min))
            overlap_height = max(0.0, min(y_max, q_y_max) - max(y_min, q_y_min))
            inter_area = overlap_width * overlap_height
            # 
            # Calculate percentage of total box area
            # 
            percentages[quad_name] = round((inter_area / box_area) * 100, 2)

        return percentages

    def TextToSpeech(
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

    def SpeechToText(
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

            playsound.playsound(sound=BEEP)

            sounddevice.wait()

            audio = speech_recognition.AudioData(
                recording.tobytes(),
                sample_rate,
                2
            )

            try:
                text = recognizer.recognize_google(audio)
                return str(text).lower().strip()

            except speech_recognition.UnknownValueError:
                self.TextToSpeech("Could not understand. Please speak again after the beep.")

def main():
    image_poi_finder = ImagePoiFinder()
    image_poi_finder.DetectObjects(input_image_path="assets/images/doggie.png")
    # image_poi_finder.run()

if __name__ == "__main__":
    main()


# pip install opencv-python pyttsx3 sounddevice SpeechRecognition ultralytics
