# * * * * * * * * * * * * * * * * * * #
# EXTERNAL IMPORTS
# * * * * * * * * * * * * * * * * * * #
import cv2
import pyttsx3
import playsound
import sounddevice
import speech_recognition
import ultralytics
import os
from datetime import datetime


import tkinter
from tkinter import scrolledtext
from PIL import ImageTk, Image, ImageDraw
from PIL.ImageFile import ImageFile
import threading

BEEP = str("assets/audio/beep.mp3")


class ImagePoiFinder():

    def __init__(
            self
        ):
        self.root = tkinter.Tk()
        self.root.title("CS4900 - Image POI Finder")
        # 
        # Default window size
        # 
        self.root.geometry("700x700")
        # 
        # Set image properties
        # 
        self.current_raw_image = None 
        self.last_window_width = 0
        self.last_window_height = 0
        self.image_label = tkinter.Label(
            self.root, 
            text="Awaiting Capture...", 
            bg="black", 
            fg="white"
        )
        #
        # Make image responsive to changing window size
        # 
        self.image_label.pack(
            padx=20, 
            pady=20, 
            fill=tkinter.BOTH, 
            expand=True
        )

        # 
        # Scrollable text output
        # 
        self.log_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tkinter.WORD, 
            width=70, 
            height=12
        )
        self.log_area.pack(
            padx=20, 
            pady=(0, 20), 
            fill=tkinter.X
        )
        self.log_area.configure(
            state='disabled', 
            font=("Consolas", 10), 
            bg="#1e1e1e", 
            fg="#d4d4d4"
        )
        # 
        # Bind window resize event
        # 
        self.root.bind(
            sequence="<Configure>", 
            func=self._OnWindowResize
        )

        self.root.after_idle(
            func=self._RunThreaded
        )
        self.root.mainloop()

    def blue(
            self,
            text: str
        ) -> str:
        return "\033[34m" + text + "\033[0m"

    def _RunThreaded(self):
        """
        """
        threading.Thread(
            target=self.Run, 
            daemon=True
        ).start()

    
    def PrintToGui(
            self, 
            text: str
        ):
        """Print text content to gui text field

        Args:
            text (str): text to print
        """
        self.log_area.configure(state='normal')
        self.log_area.insert(tkinter.END, text + "\n")
        self.log_area.see(tkinter.END) # Auto-scrolls to the bottom
        self.log_area.configure(state='disabled')

    def DisplayImageToGui(
            self, 
            image_path: str,
            detections: list[dict] = None,
            center_ratio: float = 0.50
        ) -> None:
        """Open image from path, mark detection center points, and render it to gui.

        Args:
            image_path (str): path to image
            detections (list[dict], optional): list of detection dicts containing 'position' tuples
        """
        def _update():
            try:
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    #
                    # Draw center points if detections are passed
                    #
                    if detections:
                        draw = ImageDraw.Draw(img)
                        img_width, img_height = img.size
                        margin_x = (img_width * (1.0 - center_ratio)) / 2.0
                        margin_y = (img_height * (1.0 - center_ratio)) / 2.0

                        cx_min, cx_max = margin_x, img_width - margin_x
                        cy_min, cy_max = margin_y, img_height - margin_y
                        mid_x, mid_y = img_width / 2.0, img_height / 2.0

                        line_color = "cyan"
                        line_width = 2
                        #
                        # Draw Central Region Box
                        #
                        draw.rectangle(
                            [cx_min, cy_min, cx_max, cy_max], 
                            outline=line_color, 
                            width=line_width
                        )
                        #
                        # Draw Outer Quadrant Dividers
                        #
                        draw.line([(mid_x, 0), (mid_x, cy_min)], fill=line_color, width=line_width)          # Top divider
                        draw.line([(mid_x, cy_max), (mid_x, img_height)], fill=line_color, width=line_width) # Bottom divider
                        draw.line([(0, mid_y), (cx_min, mid_y)], fill=line_color, width=line_width)          # Left divider
                        draw.line([(cx_max, mid_y), (img_width, mid_y)], fill=line_color, width=line_width)  # Right divider

                        for det in detections:
                            pos = det.get("position")
                            if pos:
                                cx, cy = pos
                                #
                                # crosshairs around the center point of bounding box
                                # 
                                ch_len = 10
                                draw.line([(cx - ch_len, cy), (cx + ch_len, cy)], fill="yellow", width=2)
                                draw.line([(cx, cy - ch_len), (cx, cy + ch_len)], fill="yellow", width=2)

                    self.current_raw_image = img
                    self._render_scaled_image(
                        image_to_render=self.current_raw_image
                    )
            except Exception as e:
                self.PrintToGui(f"GUI Error loading image: {e}")

        self.root.after(0, _update)

    def _OnWindowResize(
            self, 
            event
        ) -> None:
        """Fired on window movement and resizing."""
        # Guard clause: Only trigger on root window events (ignore child widget events)
        if event.widget != self.root:
            return

        # Guard clause: Prevent infinite loops by checking if dimensions actually changed
        if (event.width == self.last_window_width and 
            event.height == self.last_window_height):
            return

        self.last_window_width = event.width
        self.last_window_height = event.height

        # Re-render image if one is loaded
        if self.current_raw_image is not None:
            self._render_scaled_image(
                image_to_render=self.current_raw_image
            )

    def _render_scaled_image(
            self,
            image_to_render: ImageFile
        ):
        """Rescales the current raw image to fit the label's current size."""
        if image_to_render is None:
            return

        # Get current available dimensions of the label
        target_w = max(self.image_label.winfo_width(), 100)
        target_h = max(self.image_label.winfo_height(), 100)

        # Make a copy of the original raw image to resize
        img_copy = image_to_render.copy()
        
        # Scale while preserving aspect ratio
        img_copy.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

        self.photo = ImageTk.PhotoImage(
            image=img_copy
        )
        self.image_label.configure(
            image=self.photo, 
            text=""
        )

    def Run(
            self,
            captures_dir: str = "images/captures",
            annotations_dir: str = "images/annotated",
            label_to_target: str | None = None
        ) -> int:
        try:
            # 
            # Introduce how prompting is done
            # 
            if not label_to_target:
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
                if "yes" in should_capture_now:
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
            capture_time = datetime.now().strftime("%y%m%d_%H%M%S")
            os.makedirs(name=captures_dir, exist_ok=True)
            capture_path = f"{captures_dir}/capture_{capture_time}.jpg"
            os.makedirs(name=annotations_dir, exist_ok=True)
            annotated_capture_path = f"{annotations_dir}/annotated_{capture_time}.jpg"
            capture_status = self.CaptureImage(capture_path=capture_path)
            if capture_status != 0:
                self.TextToSpeech("Image failed to capture. Exiting program.")
                return -1
            self.TextToSpeech("Image captured.")
            self.TextToSpeech("Detecting objects in the captured image.")
            # 
            # Detect objects in captured image
            # 
            detections = self.DetectObjects(
                input_image_path=capture_path,
                output_image_path=annotated_capture_path
            )
            if len(detections) > 0:
                # 
                # Have the user specify a class of objects to look for. If there are none, list all objects
                # 
                if not label_to_target:
                    self.TextToSpeech("What object do you want to detect?")
                    object_to_detect = self.SpeechToText()
                else:
                    object_to_detect = label_to_target
                if object_to_detect != "":
                    # 
                    # If the user says a label that is in the detections list, replace the full list with just the matches.
                    # 
                    matching_detections = []
                    for detection in detections:
                        if str(detection.get("label")) in object_to_detect:
                            matching_detections.append(detection)
                    if len(matching_detections) > 0:
                        detections = matching_detections
                    else:
                        self.TextToSpeech(f"'{object_to_detect}' is not in the image.")
                
                if len(detections) == 1:
                    self.TextToSpeech(f"{len(detections)} object found in the image.")
                else:
                    self.TextToSpeech(f"{len(detections)} objects found in the image.")
                for detection in detections:
                    self.TextToSpeech(f"There is a {detection["label"]} at the {detection["region"]}")
                # 
                # Ask if the user wants to take another capture
                # 
                self.TextToSpeech(f"Would you like to adjust the camera and take a new photo?")
                take_another_image = self.SpeechToText()
                if "yes" in take_another_image:
                    # self.TextToSpeech(f"Captures saved to {captures_dir}.")
                    self.Run(label_to_target=object_to_detect)
                    return 0
                else:
                    self.TextToSpeech(f"Exiting program. Image saved to file.")
                    return 0
            else:
                self.TextToSpeech("No objects found in the image. Would you like to take another image?")
                take_another_image = self.SpeechToText()
                if "yes" in take_another_image:
                    self.Run()
                    return 0
                else:
                    self.TextToSpeech(f"Exiting program. Image saved to file.")
                    return 0
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
            int: return value
        """
        try:
            return_code = 0
            camera = cv2.VideoCapture(0)

            success, frame = camera.read()

            if success:
                print(capture_path)
                cv2.imwrite(capture_path, frame)
                self.root.after(0, self.DisplayImageToGui, capture_path)

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
                region = self.GetBbRegion(
                    center_coords=center_coords,
                    img_width=img_width,
                    img_height=img_height
                )
                # quadrants = self.GetBbQuadPercentages(
                #     box_range=box_range,
                #     img_width=img_width,
                #     img_height=img_height
                # )
                detections.append(
                    {
                        "label": label,
                        "position": center_coords,
                        "region": region
                        # "quadrants": quadrants
                    }
                )
            print(detections)
            result.save(filename=output_image_path)
            
            self.DisplayImageToGui(
                image_path=output_image_path,
                detections=detections
            )
            return detections
        except Exception as e:
            return ""

    def GetBbRegion(
            self,
            center_coords: list[int], 
            img_width: int, 
            img_height: int,
            center_ratio: float = 0.50
        ) -> str:
        center_x, center_y = center_coords

        margin_x = (img_width * (1.0 - center_ratio)) / 2.0
        margin_y = (img_height * (1.0 - center_ratio)) / 2.0

        center_x_min = margin_x
        center_x_max = img_width - margin_x
        center_y_min = margin_y
        center_y_max = img_height - margin_y
        #
        # Check if center point falls inside the expanded center zone
        #
        if (center_x_min <= center_x <= center_x_max) and (
            center_y_min <= center_y <= center_y_max
        ):
            return "center"
        #
        # Otherwise, assign quadrant label based on frame midpoints
        #
        mid_x = img_width / 2.0
        mid_y = img_height / 2.0

        if center_x < mid_x and center_y < mid_y:
            return "top left. Move the camera up and right."
        elif center_x >= mid_x and center_y < mid_y:
            return "top right. Move the camera up and left."
        elif center_x < mid_x and center_y >= mid_y:
            return "bottom left. Move the camera down and right."
        else:
            return "bottom right. Move the camera down and left."
        
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
                "bottom_right": 0.0
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
            text_to_print = f"Assistant: {text}"
            print(text_to_print)
            self.PrintToGui(text_to_print)
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
                text = str(text).lower().strip()
                self.PrintToGui(
                    text=f"> {text}"
                )
                return text

            except speech_recognition.UnknownValueError:
                self.TextToSpeech("Could not understand. Please speak again after the beep.")

def main():
    image_poi_finder = ImagePoiFinder()
    # image_poi_finder.DetectObjects(input_image_path="assets/images/doggie.png")

if __name__ == "__main__":
    main()


# pip install opencv-python pyttsx3 sounddevice SpeechRecognition ultralytics
