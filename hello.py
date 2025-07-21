#Make sure port is set to public in codespaces

from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def hello_world():
    print("it worked")
    return 'Hello World!'

@app.route('/webhook', methods=['POST'])
def webhook():
    print("Headers:", request.headers, flush=True)
    print("Body:", request.get_data(as_text=True), flush=True)
    return "OK", 200

if __name__ == '__main__':
     app.run()


