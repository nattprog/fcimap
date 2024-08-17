from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/index/")
def home():
    return render_template("index.html", CurrentPage="index")

@app.route("/map/")
def map():
    return render_template("mmu.html", CurrentPage="map")

if __name__ == "__main__":
    app.run(debug=True)