

#https://github.com/waveform80/picamera/blob/master/docs/examples/web_streaming.py



import argparse
from os.path import expanduser
import datetime

# Streaming video imports
import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

# Video analysis imports
import numpy as np
import cv2

# HTML source
from htmlsrc import PAGE, STOPPED_PAGE

# Video defaults
record_reso    = 1280,720
#record_reso    = 320,240
stream_reso    = 320,240
cam_strm_port  = 2
fps            = 10
highlightcolor = 'black'
record_time    = 10
num_files      = 5
cam_web_port   = 8000

home = expanduser("~")
print(home)
picture_folder = home + '/backyardsentry/'

# Video analysis defaults
write_frame=False

def parse_cmd_line_args():
   parser = argparse.ArgumentParser()
   parser.add_argument("-t", "--record_time", help=",the duration of the video segments to record in seconds", type=int, required=False)
   parser.add_argument("-nf", "--num_files", help=",the number of separate video files to record", type=int, required=False)
   parser.add_argument("-fps", "--frames_per_second", help="the number of frames per second to record", required=False)
   args = parser.parse_args()

   if args.record_time:
       record_time = args.record_time

   if args.num_files:
       num_files = args.num_files

class StreamingOutput(object):
    min_area = 1000
    frame_count = 0

    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()
        self.fgbg = cv2.createBackgroundSubtractorMOG2(25, 16, False)
        self.motionDetected = False

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

    def detectMotion(self):
        frameDecoded = cv2.imdecode(np.fromstring(self.frame, dtype=np.int8), 1)
        fgmask = output.fgbg.apply(frameDecoded)
        thresh = cv2.threshold(fgmask, 55, 255, cv2.THRESH_BINARY)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
               cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0]
        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if (cv2.contourArea(c) < self.min_area):
               continue
            else:
               self.motionDetected = True
               # compute the bounding box for the contour, draw it on the frame,
               (x, y, w, h) = cv2.boundingRect(c)
               cv2.rectangle(frameDecoded, (x, y), (x + w, y + h), (0, 255, 0), 2)
               cv2.rectangle(frameDecoded, (0, 0), (100, 100), (0, 255, 0), 2)

        if self.motionDetected is True:
           outputfile = picture_folder + str(datetime.datetime.now()) + ".jpg"
           print(outputfile)
           cv2.imwrite(outputfile, frameDecoded)
           self.motionDetected = False

        # Encode as jpg again for browser display
        self.img_str = cv2.imencode('.jpg', frameDecoded)[1].tostring()
 

class StreamingHandler(server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
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
                while True:
                    with output.condition:
                         output.condition.wait()
                         output.frame_count += 1
                         output.detectMotion()
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(output.img_str))
                    self.end_headers()
                    self.wfile.write(output.img_str)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == '/stop_streaming':
            content = STOPPED_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            if camera.recording:
               camera.stop_recording(splitter_port=cam_strm_port)
               camera.stop_recording()
        elif self.path == '/start_streaming':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            if not camera.recording:
               camera.start_recording(output, format='mjpeg')
               camera.start_recording(filenm, splitter_port=cam_strm_port)
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__=="__main__":
   parse_cmd_line_args() 

   with picamera.PiCamera(resolution=record_reso, framerate=fps) as camera:
       output = StreamingOutput()

       camera.start_recording(output, format='mjpeg')
       #camera.start_recording(output, format='rgb')
       camera.start_recording('lowres.h264', splitter_port=2, resize=(320, 240))
       try:
           address = ('', 8000)
           server = StreamingServer(address, StreamingHandler)
           print("Streaming now active.")
           server.serve_forever()
       finally:
           camera.stop_recording(splitter_port=2)
           camera.stop_recording()
