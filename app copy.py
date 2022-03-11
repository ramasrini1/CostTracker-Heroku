from flask import Flask, request, render_template,  redirect, flash, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, Events, Expenses, User
from forms import AddEventForm, AddExpenseForm, UserAddForm, LoginForm, AdminForm, ShowEventForm
from expenses import EvtExpenses
from venmo import Venmo
import os

app = Flask(__name__)

CURR_USER_KEY = "curr_user"
ACCESS_TOKEN = "acc_token"
db_url =  os.environ.get('DATABASE_URL')

if (db_url): 
    db_url = (db_url).replace("postgres://", "postgresql://", 1 )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///cost_tracker_db'



app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hellosecret1')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)
#db.create_all()

##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """
    if ( g.user ):
        flash(f"You are already logged in", "info")
        return redirect("/")

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    
    flash("You have successfully logged out.", 'success')
    return redirect("/login")

@app.route('/')
def home_page():
    """Render home page"""
    return render_template("/index.html")


##############################################################################
# Events Route

@app.route('/events/new', methods=["GET", "POST"])
def add_event():
    """Renders add event form (GET) or handles event form submission (POST)"""
    form = AddEventForm()
    
    if form.validate_on_submit():
        evt_name = form.evt_name.data
        event = Events( evt_name = evt_name )
        
        try:
            db.session.add(event)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            msg = f"Choose another name"
            flash(f"This event {evt_name} already exists.", "danger")
            return redirect("/events/new")
        
        return redirect('/events/list')
    
    return render_template("/events/add_event_form.html", form=form)

@app.route("/events/list")
def list_events():
    """Return all events in db."""
    events = Events.query.filter_by(evt_type = None)
    return render_template("/events/event_list.html", events=events)


##############################################################################
# Expenses Route
@app.route("/expenses/add_expense", methods=["GET", "POST"])
def add_expense():
    """Show Event Expense Form.
       Get method for showing form
       Post method for processing the form
    """
    
    if ( g.user is None ):
        msg = "Login First to enter report"
        return render_template("/message.html", msg=msg)

    form =  AddExpenseForm()
    event_form = ShowEventForm()
    evts = [ [event.id, event.evt_name] for event in Events.query.filter_by(evt_type = None)]
    friends = [ [user.username, user.username] for user in User.query.filter_by(role = None) ]
    
    
    form.evt.choices = evts
    event_form.event.choices = evts
    form.friend.choices = friends

    if form.validate_on_submit():
       
        cost = form.cost.data
        event_id = form.evt.data
        cost_info = form.cost_info.data
        username = form.friend.data

        exps = db.session.query(Expenses).filter(Expenses.event_id == event_id).filter( (Expenses.status == 'paid') | (Expenses.status== 'Request Sent') | (Expenses.status == 'No Action') )
        #If any of the expenses have been processed, no more expenses can be 
        # added for that event.
        
        if (exps.count() > 0):
            msg = "Deadline over expenses computed you can no longer add additional expenses"
            flash(f"Deadline over expenses computed you can no longer add additional expenses", "danger")
            return render_template("/message.html", msg=msg)

        expense = Expenses( username = username, event_id=event_id, cost=cost, cost_info=cost_info )
        
        try:
            db.session.add(expense)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            msg = "Integrity Error: You have entered your expense report"
            flash(f"Integrity Error: You have entered your expense report", "danger")
            return render_template("/message.html", msg=msg)
        
        flash(f"Friend {username} expense added", "info")
        #return redirect("/events/list")
        event = Events.query.get_or_404(event_id)
        evt_name = event.evt_name
        
        return render_template(f"/expenses/add_expense_form.html/", form=form, 
                                event_form = event_form, event_id=event_id, evt_name=evt_name)
    
    return render_template("/expenses/add_expense_form.html", form=form, event_form = event_form )


@app.route("/event/expenses/<int:event_id>", methods=["GET", "POST"])
def show_expenses(event_id):
    """Split Expenses For this event_id among friends
    """
    results = Expenses.query.filter_by(event_id=event_id)
    if (results.count() == 0):
        return render_template("/message.html", msg="No Expenses Entered")
    
    event = Events.query.get_or_404(event_id)
    event_name = event.evt_name

    exps = Expenses.query.filter_by(event_id=event_id).all()

    evtExpenses = EvtExpenses(exps)
   
    return render_template("/expenses/payment.html", 
                            payments=evtExpenses.payments, 
                            event_name=event_name,
                            event_id = event_id,
                            total_cost=evtExpenses.total_cost,
                            target=evtExpenses.target)

@app.route("/request_payment", methods=["GET", "POST"])
def request_payment():
    """Request Payment: Get payment details from get request
       Call Venmo api to make the payment request
    """
    amount = request.form['amt']
    amount = float(amount)
    user_name = request.form['user_name']
    event_id  = request.form['evt']
    event_id  = int(event_id)
   
    
    msg = f"Permission Denied Log In As Admin"

    if (g.user and is_admin(g.user.username)):
        msg = "Access_token not set"
        
        if ( ACCESS_TOKEN in session ):
            # get access token from session variable
            access_token = session[ACCESS_TOKEN]

            venmo = Venmo(access_token)
            user_id = venmo.get_user_id_by_username(user_name)

            event = Events.query.get_or_404(event_id)
            event_name = event.evt_name
            
            message = f"Request payment ${amount} for event {event_name}"
    
            success = venmo.request_money(amount, message, user_id)
    
            if (success):
             
                single_expense = Expenses.query.filter_by(event_id=event_id, username=user_name).first()
                
                single_expense.status = 'Request Sent'
                single_expense.payment_amt = amount
                db.session.commit()
                
                msg = f"{event_name}:Sent payment request to Venmo user_id: ({user_name})for ${amount}"
            else:
                msg = f"Unable to send payment request to user_id: {user_name}"
    
            return render_template("/message.html", msg=msg)

    return render_template("/message.html", msg=msg)


@app.route("/send_payment", methods=["GET", "POST"])
def send_payment():
    """Send Payment: Get payment details from Get request
        Call Venmo Api to send the payment
    """
    payment_amount = request.form['amt']
    payment_amount = float(payment_amount)
    user_name = request.form['user_name']
    event_id  = request.form['evt']
    event_id  = int(event_id)
  
    if (g.user and is_admin(g.user.username)):
      
        if ( ACCESS_TOKEN in session ):

            event = Events.query.get_or_404(event_id)
            event_name = event.evt_name
            
            access_token = session[ACCESS_TOKEN]
            venmo = Venmo(access_token)
            
            user_id = venmo.get_user_id_by_username(user_name)
            payment_note = f"{user_name}, Payment ${payment_amount} for event {event_name}"
    
            success = venmo.send_money(payment_amount, payment_note, user_id )

            if (success):
                single_expense = Expenses.query.filter_by(event_id=event_id, username=user_name).first()
                single_expense.status = 'Paid'
                single_expense.payment_amt = payment_amount
                db.session.commit()

                msg = f"{event_name}Sent payment to Venmo user_id: ({user_name})for ${payment_amount}"
            else:
                msg = f"Unable to send payment to user_id: {user_name}"
            
            return render_template("/message.html", msg=msg)
    
    msg = "Permission Denied Log In As Admin"
    return render_template("/message.html", msg=msg)

##############################################################################
# Admin Route

    
@app.route('/admin', methods=["GET", "POST"])
def admin():
    """Handle Admin Form
    """
    if( g.user and is_admin(g.user.username)):
        if  ACCESS_TOKEN in session:
            flash("Admin set up complete", "success")
    
    form = AdminForm()
    if (g.user and is_admin(g.user.username) ):

        if form.validate_on_submit():
        
            access_token = form.access_token.data
       
            session[ACCESS_TOKEN] = access_token
            flash("Admin set up complete")
            return redirect("/")

    return render_template('users/admin_form.html', form=form)

@app.route('/admin/remove', methods=["GET", "POST"])
def remove_token():
    if (g.user and is_admin(g.user.username)):
        
        if ACCESS_TOKEN in session:
            del session[ACCESS_TOKEN]
            return render_template("/message.html", msg="Removed Token From System")
    return render_template("/message.html", msg="Unable to Remove token From System")

def is_admin(username):
    user = User.query.filter_by(username=username).first()
    if ( user.role == 'admin'):
        return True
    return False

##############################################################################
# Demo Route
@app.route("/demo_app", methods=["GET", "POST"])
def demo_app():
    init_demo_data()
    form =  AddExpenseForm()
    event_form = ShowEventForm()
    
    evts = [ [event.id, event.evt_name] for event in Events.query.filter_by(evt_name = 'Mars Trip')]
    friends = [ [user.username, user.username] for user in User.query.filter_by(username = 'nemo') ]

    form.evt.choices = evts
    event_form.event.choices = evts
    form.friend.choices = friends

    return render_template("/expenses/add_expense_form.html", form=form, event_form = event_form )

    #return render_template("/message.html", msg="init demo data")
    
    # evts = [ [event.id, event.evt_name] for event in Events.query.filter_by(evt_type = 'demo')]
    # friends = [ [user.username, user.username] for user in User.query.filter_by(role = 'demo') ]

def init_demo_data():
    evt_name = "Mars Trip"
    demo = "demo"
  
    #Expenses.query.filter_by(username='nemo').delete()
    evt1 = Events(
     evt_name = evt_name,
     evt_type =  demo
    )
    try:
        event_id =  db.session.add(evt1)
        db.session.commit()
    except IntegrityError:
            db.session.rollback()

    f1 = User(
        username = "nemo",
        role = demo,
        password = "nemopass"
    )
    f2 = User(
        username = "jellyfish",
        role = demo,
        password = "jellypass"
    )
    f3 = User(
        username = "blueWhale",
        role = demo,
        password = "whalepass"
    )

    try:
        db.session.add_all([f1, f2, f3])
        db.session.commit()
    except IntegrityError:
            db.session.rollback()
    

    e1 = Expenses(
        username="nemo",
        event_id = event_id,
        cost=1,
        cost_info="Spent for hotel and gas"
    )

    e2 = Expenses(
        username="jelly-fish",
        event_id = event_id,
        cost=1,
        cost_info="Spent for hotel and gas"
    )

    try:
        db.session.add_all([e1, e2])
        db.session.commit()
    except IntegrityError:
            db.session.rollback()
    
