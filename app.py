from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "ok", "message": "Microservicio Flask listo"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)