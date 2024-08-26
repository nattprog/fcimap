from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuring the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializing the database
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email address already registered."

        new_user = User(username=username, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('signup_success'))

    return render_template('signup.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the database and the tables
    app.run(debug=True, port=5001)