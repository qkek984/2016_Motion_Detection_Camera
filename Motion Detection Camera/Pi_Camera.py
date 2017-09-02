import time, os, io

import random, pickle
import picamera
from PIL import Image
import numpy as np
import subprocess
#
import signal,time
from threading import Lock
import glob
#
global mode
mode=None
global minPixelsChanged
lck = Lock()

prior_image = None
effect = None

width = 1280
height = 720
threshold=30
minPixelsChanged = width * height * 1.7 / 100 # % change  # how many pixels must change to begin a save sequence

camera = picamera.PiCamera()
camera.resolution = (width, height)
stream = picamera.PiCameraCircularIO(camera, seconds=10)
camera.start_recording(stream, format='h264')



# TODO: 이 프로세스의 PID를 특정 파일에 저장하여, 시그널을 보낼 프로그램(ipcam_config.py)이 PID를 알 수 있도록 한다.
print 'PID:', os.getpid()
pp = os.getpid()
pid = open('pid.txt','w')
pickle.dump(pp,pid)
pid.close()

def signal_handler(signum, frame):
        global mode
        global minPixelsChanged
        print 'Signal handler called with signal', signum
        # TODO: ipcam_config.py 가 새로 저장한 설정을 읽어서 설정 변수를 변경한다.
        f = open('set.txt','r')
        mode = pickle.load(f).strip()
        mode = int(mode)
        effect = pickle.load(f)
        annotate = pickle.load(f)
        camera.annotate_text = annotate
        print effect,mode


        
        f.close()
        
        if(effect == "0"):
                camera.image_effect = 'none'
                minPixelsChanged = width * height * 1.7 / 100
        elif(effect == "1"):
                camera.image_effect = 'colorswap'
                minPixelsChanged = width * height * 1.5 / 100
        elif(effect == "2"):
                camera.image_effect = 'emboss'
                minPixelsChanged = width * height * 1.2 / 100
        else:
                camera.image_effect = 'sketch'
                minPixelsChanged = width * height * 1.7 / 100

def detect_motion(camera):
    global prior_image
    stream = io.BytesIO()
    camera.capture(stream, format='rgba', use_video_port=True)
    stream.seek(0)
    
    if prior_image is None:
        prior_image = np.fromstring(stream.getvalue(), dtype=np.uint8)
        return False
    else:
        current_image = np.fromstring(stream.getvalue(), dtype=np.uint8) 
        data3 = np.abs(prior_image - current_image)  
        numTriggers = np.count_nonzero(data3 > threshold) / 4 / threshold 

        print("Trigger cnt=",numTriggers)
        print("M=",minPixelsChanged)
        prior_image = current_image
        if numTriggers > minPixelsChanged:
            #print ('change!')
            return True
        else:
            #print ('non change')
            return False
signal.signal(signal.SIGUSR1, signal_handler)

while True:
        
        if mode==0 or mode==None:
        
                f = open("filename.txt",'a')
                camera.wait_recording(1)
                if detect_motion(camera):
                        print('############## Motion detected! ##########')
                        fname = time.strftime("%Y%m%d_%H%M%S",time.localtime())
                        camera.split_recording(fname+'after.h264')
                        print fname
                        # Write the 10 seconds "before" motion to disk as well
                        stream.copy_to(fname+'before.h264', seconds=10)
                        #os.system('MP4Box -fps 30 -add after.h264 sample.mp4')
                        cmd = ["MP4Box", "-fps", "30", "-add", fname+"before.h264", fname+"before.mp4"]
                        popen = subprocess.Popen(cmd)
                        f.write(fname+'before.mp4'+ "\n")
                        stream.clear()
                        camera.wait_recording(5)
                        # Wait until motion is no longer detected, then split
                        # recording back to the in-memory circular buffer
                        while detect_motion(camera):
                                camera.wait_recording(1)
                        print('==============Motion stopped!==============')
                        cmd = ["MP4Box", "-fps", "30", "-add", fname+"after.h264", fname+"after.mp4"]
                        popen = subprocess.Popen(cmd)
                        f.write(fname+'after.mp4'+ "\n")
                        camera.split_recording(stream)
        else:
                time.sleep(1)
                camera.capture('capture.jpg')
        
        
