

from flask import Flask, send_file, render_template, request
from picamera import PiCamera
import pickle, os, signal

app = Flask(__name__)

global lists_index
lists_index=None
@app.route('/')
def index():
        f = open("filename.txt",'r')
        play_array =f.read()
        line = play_array.split('\n')
        f.close
        return render_template('config.html', line = line) # config.html은 templates/config.html 에 위치해야 함.

@app.route('/config')
def config():
        global lists_index
        
        mode = request.args.get('mode', '')
        effect = request.args.get('effect', '')
        annotate = request.args.get('annotate', '')
        lists_index = request.args.get('lists', '')
        
        
        print  mode,effect, annotate, lists_index
        f = open("set.txt",'w')
        
        pickle.dump(mode, f)
        pickle.dump(effect, f)
        pickle.dump(annotate, f)
        pickle.dump(lists_index, f)
        
        f.close
        p = open('pid.txt','r')
        pid = pickle.load(p)
        p.close
        os.kill(pid, signal.SIGUSR1)        
        return 'OK'

@app.route('/stream')
def stream():
        f = open("filename.txt",'r')
        play_array =f.readlines()
        if(lists_index==None or lists_index.strip()=="default"):
                play=play_array[len(play_array)-1].strip()
                print lists_index
        else:
                print int(lists_index)
                if int(lists_index)==1:
                        print "true!"
                else:
                        print "lie"
                play=play_array[int(lists_index)].strip()
               
        print "play file : "+play
        f.close
        return send_file(play) # 캡쳐 프로그램이 캡쳐한 파일 전송

@app.route('/capture')
def capture():
       
        return send_file('capture.jpg') # 캡쳐 프로그램이 캡쳐한 파일 전송

if __name__ == '__main__':
        #app.run('0.0.0.0')
        app.run(host='0.0.0.0',port=5001, threaded=True)
