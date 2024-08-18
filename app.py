from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def homepage():
    return redirect("/index/")

@app.route("/index/")
def index():
    return render_template("index.html", CurrentPage="index")

@app.route("/map/")
def map():
    return render_template("mmu.html", CurrentPage="map")

@app.route("/rick/")
def rick():
    return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

if __name__ == "__main__":
    app.run(debug=True)