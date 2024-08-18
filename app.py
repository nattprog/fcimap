from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def homepage():
    return redirect(url_for("index"))

@app.route("/index/")
def index():
    return render_template("index.html", ActivePage="index")

@app.route("/map/")
def map():
    return render_template("mmu.html", ActivePage="map")

@app.route("/meow/")
def meow():
    return render_template("index.html", ActivePage ="meow", Meow = True)

if __name__ == "__main__":
    app.run(debug=True)