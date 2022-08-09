# Flask Package
from flask import Flask, abort, flash, redirect, render_template, request, url_for

# SQLAlchemy for ORM in Flask
from flask_sqlalchemy import SQLAlchemy

# flask_wft for login page Form and Validaiton
from flask_wtf import FlaskForm
from sqlalchemy import null
from wtforms.validators import InputRequired, Length, EqualTo, DataRequired, Regexp
from wtforms import StringField, BooleanField, RadioField, TextAreaField, SelectField, DateField

# flask_login for Authenitcation
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# OS for database in filepath
import os

# Flask Bootstrap Design
from flask_bootstrap import Bootstrap

# Datetime for Summary Page
import datetime
from datetime import datetime, timedelta, date


#initializing the flask 
app = Flask(__name__)


# db_path in root directory, which stores the values in store.db
db_path = os.path.join(os.path.dirname(__file__), 'store.db')

# db_url for sqlite
db_uri = 'sqlite:///{}'.format(db_path)

# secret_key which used for session Management
app.config['SECRET_KEY'] = 'MySecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initializing the bootstrap and SQLAlchemy in the flask app
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


# Login Manager
Login_Manager = LoginManager()
Login_Manager.init_app(app)
Login_Manager.login_view = 'login'

# User Model
class User(UserMixin ,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True) # User ID
    username = db.Column(db.String(20), unique=True) # User Name with Unique
    lists = db.relationship('List', backref='user', lazy=True)


# List Model
class List(db.Model):
    __tablename__ = 'list'
    id = db.Column(db.Integer, primary_key=True) # List ID
    name = db.Column(db.String(20), unique=False) # List Name
    description = db.Column(db.String(200), unique=False) # List Descriptiion
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=False)
    cards = db.relationship('Card', backref='list', lazy=True)

# Card Model
class Card(db.Model):
    __table_name__ = 'card'
    id = db.Column(db.Integer, primary_key=True) # Card ID
    title = db.Column(db.String(50), nullable=False, unique=False) # Card title
    content = db.Column(db.String(200), nullable=False, unique=False) # Card Content
    date = db.Column(db.String(10), nullable=False, unique=False) # Card ExpiryDate
    complete = db.Column(db.String(10), nullable=True, unique=False) # Card Status
    is_deadline = db.Column(db.String(10), nullable = True) # Card Deadline
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=False)
       

@Login_Manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Login Form
class LoginForm(FlaskForm):
    username =  StringField('Username', validators=[Regexp(r'^[\w]+$'), InputRequired(), Length(min=4, max=20)])
    remember = BooleanField('Remember me')

# SignUp Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])

# List Form
class ListForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=4, max=25)])
    description = TextAreaField('Description', validators=[InputRequired(), Length(min=6, max=100)])

# Card Form
class CardForm(FlaskForm):
    title = StringField('title', validators=[InputRequired()])
    content = StringField('description', validators=[InputRequired()])
    date = StringField('date',validators=[InputRequired(), Length(min=6, max=100)])
    complete = StringField('Mark as Complete')
    list = SelectField('List', choices=[], validators=[DataRequired()])

# Home Page
@app.route("/",  methods=['GET', 'POST'])
def login():    
    
    form = LoginForm()

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        else:
            return render_template('index.html', error='User not exist in our Database', form=form)
    
    return render_template('index.html', form=form)


# SignUp Route 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if form.validate_on_submit():
        new_user = User(username=form.username.data)
        check_user = User.query.filter_by(username = form.username.data).all()
        if check_user:
            return render_template("signup.html", form = form , error = 'User already exist in our database')
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


# Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
# Authorization Login Required
@login_required
def dashboard():
    
    id = current_user.id
    list = List.query.filter_by(user_id=id).all()
    card = Card.query.filter_by(user_id=id).all()
    date_object = date.today()
    d = datetime.strptime(str(date_object), "%Y-%m-%d").date()
    
    for c in card:
        d1 = datetime.strptime(str(c.date), "%Y-%m-%d").date()
        if d > d1:
            c.is_deadline = True
        
    db.session.commit()

    return render_template('dashboard.html', name = current_user.username, list = list, card = card)


# AddList Page Route
@app.route('/addList', methods=['GET', 'POST'])
# Authorization Login Required
@login_required
def addList():
    form = ListForm(request.form)

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        new_list = List(name=name, description=description, user_id=current_user.id)
        db.session.add(new_list)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('addList.html', form=form)


# AddCard Page
@app.route('/addCard/<id>', methods=['GET', 'POST'])
@login_required
def addCard(id):
    list = List.query.get(id)
    if list.user != current_user:
        abort(403)
    form = CardForm(list=list.id)
    form.list.choices = [(list.id, list.name) for list in current_user.lists]
    if form.validate_on_submit():
        complete = form.complete.data
        if complete == None:
            complete = 'False'
        card = Card(title = form.title.data, content = form.content.data, date=form.date.data, complete=complete, list_id = form.list.data, user_id = current_user.id)
        date_object = date.today()
        d = datetime.strptime(str(date_object), "%Y-%m-%d").date()
        d1 = datetime.strptime(str(card.date), "%Y-%m-%d").date()
        if d > d1:
            card.is_deadline = True
        else:
            card.is_deadline = False

        db.session.add(card)
        db.session.commit()
        flash(f'Card has been successfully edited', 'success')
        return redirect(url_for('dashboard'))
    list = List.query.filter_by(user_id=current_user.id).all()
    return render_template('addCard.html', form = form, list=list)

      
# EditList Page
@app.route('/editList/<id>', methods=['GET', 'POST'])
@login_required
def editList(id):
    if request.method == 'GET':
        list = List.query.filter_by(id=id, user_id=current_user.id).all()   
        form = ListForm(instance=list)
        print(form)
        return render_template('editList.html', form = form, list = list)

    if request.method == 'POST':
        form = ListForm(request.form)
        if form.validate_on_submit():
            name = form.name.data
            description = form.description.data
            list = List.query.filter_by(id=int(id)).first()
            list.name = name
            list.description = description                
            db.session.commit()
            return redirect(url_for('dashboard'))

# Edit Card Page
@app.route('/editCard/<id>', methods=['GET', 'POST'])
def editCard(id):
    card = Card.query.get(id)
    list = card.list
    if list.user != current_user:
        abort(403)
    form = CardForm(title=card.title, content=card.content, date=card.date, complete=card.complete, list=list.id)
    form.list.choices = [(list.id, list.name) for list in current_user.lists]
    if form.validate_on_submit():
        card.title = form.title.data
        card.content = form.content.data
        card.date = form.date.data
        complete = form.complete.data
        print(complete)
        if complete == None:
            complete = 'False'
        card.complete = complete
        card.list_id = form.list.data
        date_object = date.today()
        d = datetime.strptime(str(date_object), "%Y-%m-%d").date()
        d1 = datetime.strptime(str(form.date.data), "%Y-%m-%d").date()
        if d > d1:
            card.is_deadline = True
        else:
            card.is_deadline = False

        db.session.add(card)
        db.session.commit()
        flash(f'Card has been successfully edited', 'success')
        return redirect(url_for('dashboard'))
    card = Card.query.filter_by(id=id)
    return render_template('editCard.html', form = form,card = card)

# Delete List Route
@app.route("/deleteList/<id>", methods=['GET', 'POST'])
@login_required
def deleteList(id):
    list = List.query.get_or_404(id)
    print(list)
    if list.user != current_user:
        abort(403)
    for card in list.cards:
        db.session.delete(card)
    db.session.delete(list)
    db.session.commit()

    return redirect(url_for('dashboard')) 


# DeleteCard Route
@app.route("/deleteCard/<id>", methods=['GET', 'POST'])
@login_required
def deleteCard(id):
    delete = Card.query.filter_by(id=int(id)).first()
    db.session.delete(delete)
    db.session.commit()

    return redirect(url_for('dashboard'))   

  
# Summary Page
@app.route('/summary')
# Auth
@login_required
def summary():
    dates = []
    now = datetime.now()
    for x in range(10):
        d = now - timedelta(days=x)
        y = d.strftime("%Y-%m-%d")
        z = datetime.strptime(y, "%Y-%m-%d").date().strftime("%B")
        b = str(d)[8:-16]+"/"+z
        dates.append(b)
    dates.reverse()
    
    id  = current_user.id
    list = List.query.filter_by(user_id = id).all()
    date_object = date.today()
    da = datetime.strptime(str(date_object), "%Y-%m-%d").date()
    details = []
    labels = []
    expired_cards = []
    completed_cards =[]
    for i in range(0,10):
        labels.append(str(date_object))
        date_object = date_object - timedelta(days=1)

    print(date_object)

    for list in list:
        data = {}
        completed_days = [0,0,0,0,0,0,0,0,0,0]
        data['id'] = list.id
        data['list_title'] = list.name
        completed = 0
        expired = 0
        cards = list.cards
        data['no_of_cards'] = len(cards)
        for card in cards:
            d1 = datetime.strptime(str(card.date), "%Y-%m-%d").date()
            if d1 <da and card.complete == 'False' :
                expired+=1
            if card.complete == 'on':
                completed+=1
            if card.complete == 'on' and d1 <=da:
                days = (da - d1).days
                if(days == 0):
                    completed_days[9] += 1 
                if(days == 1):
                    completed_days[9] += 1 
                if(days == 2):
                    completed_days[8] += 1 
                if(days == 3):
                    completed_days[7] += 1 
                if(days == 4):
                    completed_days[6] += 1 
                if(days == 5):
                    completed_days[5] += 1 
                if(days == 6):
                    completed_days[4] += 1 
                if(days == 7):
                    completed_days[3] += 1 
                if(days == 8):
                    completed_days[2] += 1 
                if(days == 9):
                    completed_days[1] += 1 
        expired_cards.append(expired)
        completed_cards.append(completed)
        data['expired_cards'] = expired
        data['completed_cards'] = completed
        data['completed_days'] = completed_days
        details.append(data)
    
    print(details)
    return render_template('summary.html',name = current_user.username, list = list, dates = dates, details = details)

#Logout Page Route
@app.route('/logout')
# Authorization Login Required then they could logout successfully
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run()
