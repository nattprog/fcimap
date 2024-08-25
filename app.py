from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'passcodesecretkey'
search = None

# Database for block, floor and number of rooms.
class fci_room(db.Model):
        __tablename__ = "fci_room"
        id = db.Column(db.Integer, primary_key=True, nullable=False)
        room_code = db.Column(db.String(50), nullable=False)
        room_block = db.Column(db.String(1), nullable=False)
        room_floor = db.Column(db.Integer, nullable=False)
        room_number = db.Column(db.Integer, nullable=False)
        def __repr__(self, id, room_code, room_block, room_floor, room_number):
            self.id = id
            self.room_code = room_code
            self.room_block = room_block
            self.room_floor = room_floor
            self.room_number = room_number


    

@app.route("/")
def redirect_home():
    return redirect("/map/0")

@app.route("/map/<floor>/", methods=["GET", "POST"])
def home(floor):
    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("index.html", ActivePage="index", ActiveFloor = floor)

@app.route("/roompage/<room_code>", methods=["GET", "POST"])
def room_page(room_code):
    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("roompage.html")
    

@app.route("/account/", methods=["GET", "POST"])
def account():
    return render_template("account.html", ActivePage = "account")

@app.route("/search/<search>", methods=["GET", "POST"])
def search(search):
    session["search"] = search

    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")    
    return render_template("search.html", ActivePage = "search", search_result = session["search"])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)