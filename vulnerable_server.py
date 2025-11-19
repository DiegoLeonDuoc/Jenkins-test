from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to the vulnerable app!"


@app.route('/hello', methods=['GET'])
def hello():
    name = request.args.get('name')
    return f'Hello, {name}!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
