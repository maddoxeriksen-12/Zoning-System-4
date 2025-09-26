from flask import Flask, request

app = Flask(__name__)

@app.route('/test', methods=['POST'])
def test():
    with open('/app/minimal_debug.log', 'a') as f:
        f.write("MINIMAL TEST CALLED\n")
        f.flush()
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)
