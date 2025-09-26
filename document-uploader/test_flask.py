from flask import Flask

app = Flask(__name__)

@app.route('/test-upload', methods=['POST'])
def test_upload():
    print("TEST UPLOAD FUNCTION CALLED", flush=True)
    return "Test upload successful!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
