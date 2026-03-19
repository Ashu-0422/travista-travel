from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/preference")
def preference():
    return render_template("preference.html")

if __name__ == "__main__":
    app.run(debug=True)
