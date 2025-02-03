from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello from minimal Flask!"

if __name__ == "__main__":
    print("DEBUG: test_flask.py is actually running.")
    app.run(debug=True)
