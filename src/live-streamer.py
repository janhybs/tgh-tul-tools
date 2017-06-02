import flask
import subprocess
import time          #You don't need this. Just included it so you can see the output stream.
from flask import render_template

app = flask.Flask(__name__)
debug_proc = None

@app.route('/debug')
def debug():
    proc = subprocess.Popen(['tgh-watchdog', 'stop']).wait()
    proc = subprocess.Popen(['tgh-service', 'stop']).wait()
    proc = subprocess.Popen(['ps', '-alu', 'tgh-worker']).wait()
    proc = subprocess.Popen(['pkill', '-u', 'tgh-worker']).wait()


    def inner():
        yield '<h1>live output</h1>'
        yield '<pre>'
        
        proc = subprocess.Popen(
            ['tgh-service', 'debug'],             #call something with a lot of output so we can see it
            # shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )


        for line in iter(proc.stdout.readline, ''):
            line = line.decode()
            if proc.poll() is not None:
                break
            yield line.rstrip() + '<br/>'
        yield '</pre>'
        yield '<h2>Process ended</h2>'
        return None
        raise StopIteration()

    return flask.Response(inner(), mimetype='text/html')  # text/html is required for most browsers to show th$

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/restart')
def restart():
    proc = subprocess.Popen(['tgh-watchdog', 'stop']).wait()
    proc = subprocess.Popen(['tgh-service', 'stop']).wait()
    proc = subprocess.Popen(['ps', '-alu', 'tgh-worker']).wait()
    proc = subprocess.Popen(['pkill', '-u', 'tgh-worker']).wait()
    proc = subprocess.Popen(['tgh-watchdog', 'start']).wait()
    
    return 'Restart complete'

@app.route('/stop')
def stop():
    proc = subprocess.Popen(['tgh-watchdog', 'stop']).wait()
    proc = subprocess.Popen(['tgh-service', 'stop']).wait()
    proc = subprocess.Popen(['ps', '-alu', 'tgh-worker']).wait()
    proc = subprocess.Popen(['pkill', '-u', 'tgh-worker']).wait()
    
    return 'Services stopped'


# import signal
# import sys
# def signal_handler(signal, frame):
#         print('You pressed Ctrl+C!')
#         sys.exit(0)
# signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# signal.pause()

app.run(debug=False, port=6789, host='0.0.0.0', threaded=True)
# ps -alu tgh-worker
# pkill -u tgh-worker