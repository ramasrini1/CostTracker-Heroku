from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app):
    db.app = app
    db.init_app(app)

# MODELS GO BELOW!

class Groups(db.Model):
    """Groups Model"""  
    __tablename__ = "groups"
    
    gp_name = db.Column(db.Text, nullable=False, primary_key=True, unique=True)
    gp_type = db.Column(db.Text, nullable=True)
    gp_owner = db.Column(
        db.Text,   
        db.ForeignKey('users.username', ondelete='CASCADE'),  
      nullable=False
    )

    
  
class Expenses(db.Model):
    """Expenses Model"""  
    
    __tablename__ = "expenses"
    __table_args__ = (
        UniqueConstraint('username', 'group_name', name='username_group'),
    )
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column( 
        db.Text, 
        db.ForeignKey('users.username', ondelete='CASCADE'), 
        nullable=False
    )
    group_name = db.Column(
        db.String, 
        db.ForeignKey('groups.gp_name', ondelete='CASCADE'), 
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

class Message(db.Model):
    """An individual message ("from groups")."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    username = db.Column(
        db.Text,
        db.ForeignKey('users.username', ondelete='CASCADE'),
        nullable=False,
    )

    group_name = db.Column(
        db.Text,
        db.ForeignKey('groups.gp_name', ondelete='CASCADE'),
        nullable=False,
    )

    category = db.Column(
        db.String(30),
    )

   

class Subscribers(db.Model):
    """Users subscribed to the group."""
    
    __tablename__ = 'subscribers'

    __table_args__ = (
        UniqueConstraint('username', 'group_name', name='u_g'),
    )
   
    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    username = db.Column(
        db.Text,
        db.ForeignKey('users.username', ondelete='CASCADE'),
        nullable=False,
    )
    group_name = db.Column(
        db.Text,
        db.ForeignKey('groups.gp_name', ondelete='CASCADE'),
        nullable=False,
    )
