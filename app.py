from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'passcodesecretkey'

class fci_room(db.Model):
        __tablename__ = "fci_room"
        id = db.Column(db.Integer, primary_key=True, nullable=False)
        BuildingBlock = db.Column(db.String(50), primary_key =True, nullable=False)
        RoomFloor = db.Column(db.Integer, nullable=False)
        RoomNumber = db.Column(db.Integer, nullable=False)

@app.route("/")
def RedirectHome():
    return redirect(url_for("home"))

@app.route("/home/")
def home():
    return render_template("index.html", ActivePage="index")

@app.route("/home/<path>")
def floor(path):
    return render_template("index.html", ActivePage="index", ActiveFloor = path)

@app.route("/home/<path>/<room>")
def room(path, room):
    roomID = fci_room.query.filter_by(BuildingBlock = "CQAR")
     
    return render_template("index.html", ActivePage="index", ActiveFloor = path, roomID = roomID.id)

@app.route("/account/")
def account():
    return render_template("account.html", ActivePage = "account")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)