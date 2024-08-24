from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'passcodesecretkey'

# Database for block, floor and number of rooms.
class fci_room(db.Model):
        __tablename__ = "fci_room"
        id = db.Column(db.Integer, primary_key=True, nullable=False)
        building_block = db.Column(db.String(50), primary_key =True, nullable=False)
        room_floor = db.Column(db.Integer, nullable=False)
        room_number = db.Column(db.Integer, nullable=False)
        def __repr__(self, id, building_block, room_floor, room_number):
             self.id = id
             self.building_block = building_block
             self.room_floor = room_floor
             self.room_number = room_number

@app.route("/")
def RedirectHome():
    return redirect("/map/0")

@app.route("/map/<floor>/", methods=["GET", "POST"])
def home(floor):
    search = None
    if request.method == "POST":
        search = request.form["search"]
        session["search"] = search
        return redirect(f"/search/{search}")
    else:
        return render_template("index.html", ActivePage="index", ActiveFloor = floor, search = search)

@app.route("/roompage/<block>/<floor>/<room>")
def roompage(block, floor, room):
    roomID = fci_room.query.filter_by(building_block = block, room_floor = floor, room_number = room).first_or_404()
    if roomID:
        return render_template("roompage.html", building_block = roomID.building_block, room_floor = roomID.room_floor, room_number = roomID.room_number)
    

@app.route("/account/")
def account():
    return render_template("account.html", ActivePage = "account")

@app.route("/search/<search>")
def search(search):
    search = session["search"]
    search = list(search)
    building_block = search[2]
    room_floor = search[4]
    room_number = search[7]
    roomID = fci_room.query.filter_by(building_block = building_block, room_floor = room_floor, room_number = room_number).first_or_404
    return render_template("search", roomID = roomID.room_number)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)