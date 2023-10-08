import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import paho.mqtt.client as mqtt
from random import uniform
import time
import cv2
import numpy as np

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/server.html')
            self.end_headers()
        elif self.path == '/server.html':
            with open('server.html', 'rb') as file:
                content = file.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                self.handle_streaming()
            except ConnectionResetError:
                logging.warning('Connection reset by client')
                camera_stream.stop()
            except Exception as e:
                logging.warning('Exception occurred in streaming: %s', str(e))
                camera_stream.stop()
        else:
            self.send_error(404)
            self.end_headers()

    def handle_streaming(self):
        while True:
            with camera_stream.output.condition:
                camera_stream.output.condition.wait()
                frame = camera_stream.output.frame
            try:
                # Perform face detection on the frame
                frame_with_faces = detect_faces(frame)

                self.wfile.write(b'--FRAME\r\n')
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(frame_with_faces))
                self.end_headers()
                self.wfile.write(frame_with_faces)
                self.wfile.write(b'\r\n')
                self.wfile.flush()
            except BrokenPipeError:
                logging.warning('Broken pipe error occurred')
                camera_stream.stop()
                break

def detect_faces(frame):
    nparr = np.frombuffer(frame, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        print("Error: Image decoding failed.")
        return frame  # Return the original frame if decoding fails

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        # Wenn Gesichter erkannt wurden
        print(f"{len(faces)} face(s) detected.")
        # Führe Aktionen aus, wenn Gesicht(er) erkannt wurde(n)
        # Zum Beispiel:
        # Hier könntest du Code hinzufügen, um eine Aktion auszuführen,
        # wenn ein Gesicht erkannt wurde.
    else:
        # Wenn keine Gesichter erkannt wurden
        print("No faces detected.")
        # Führe Aktionen aus, wenn keine Gesichter erkannt wurden.
        # Zum Beispiel:
        # Hier könntest du Code hinzufügen, um eine Aktion auszuführen,
        # wenn kein Gesicht erkannt wurde.

    # Zeichne Rechtecke um die erkannten Gesichter
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class CameraStream(object):
    def __init__(self):
        self.camera = picamera.PiCamera(resolution='640x480', framerate=24)
        self.output = StreamingOutput()
        self.server = None
        self.is_streaming = False

    def start(self):
        print("is Starting")
        self.camera.start_recording(self.output, format='mjpeg')
        address = ('', 8000)
        self.server = StreamingServer(address, StreamingHandler)
        self.server.serve_forever()

    def stop(self):
        if self.camera.recording:
            self.camera.stop_recording()
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.is_streaming = False

def on_connect(client, userdata, flags, rc):
    print("Client connected")
    client.subscribe("camera/control")

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received message: ", message)
    if message == "start":
        print("Starting camera...")
        if not camera_stream.is_streaming:
            camera_stream.start()
            camera_stream.is_streaming = True
    elif message == "stop":
        print("Stopping camera...")
        if camera_stream.is_streaming:
            camera_stream.stop()
            camera_stream.is_streaming = False

# Load the face cascade classifier
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

client = mqtt.Client("Camera_Streaming_Server")
client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.eclipseprojects.io")

camera_stream = CameraStream()

camera_stream.start()

client.loop_forever()
