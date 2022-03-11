from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app):
    db.app = app
    db.init_app(app)

# MODELS GO BELOW!

class Events(db.Model):
    """Events Model"""  
    __tablename__ = "events"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    evt_name = db.Column(db.Text, nullable=False, unique=True)
    evt_type = db.Column(db.Text, nullable=True)
    expenses = db.relationship("Expenses", backref="events")


class Expenses(db.Model):
    """Expenses Model"""  
    
    __tablename__ = "expenses"
    __table_args__ = (
        UniqueConstraint('username', 'event_id', name='username_evtid'),
    )
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column( 
        db.Text, 
        db.ForeignKey('users.username'), 
        nullable=False
    )
    event_id = db.Column(
        db.Integer, 
        db.ForeignKey('events.id'), 
        nullable=False
    )
    cost = db.Column(db.Integer, nullable=False)
    cost_info = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, nullable=False, default="Pending")
    payment_amt = db.Column(db.Float, nullable=True)
   

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    role = db.Column(
        db.Text,
        nullable=True,  
    )

    @classmethod
    def signup(cls, username, password ):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
