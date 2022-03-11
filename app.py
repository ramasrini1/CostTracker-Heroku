from flask import Flask, request, render_template,  redirect, flash, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, Groups, Expenses, User
from forms import AddGroupForm, AddExpenseForm, UserAddForm, LoginForm, AdminForm, ShowGroupForm
from expenses import GroupExpenses
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
# Groups Route

@app.route('/groups/new', methods=["GET", "POST"])
def add_group():
    """Renders add group form (GET) or handles event form submission (POST)"""
    form = AddGroupForm()
    
    if form.validate_on_submit():
        gp_name = form.gp_name.data
        group = Groups( gp_name = gp_name )
        
        try:
            db.session.add(group)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            msg = f"Choose another name"
            flash(f"This group {gp_name} already exists.", "danger")
            return redirect("/groups/new")
        
        return redirect('/groups/list')
    
    return render_template("/groups/add_group.html", form=form)

@app.route("/groups/list")
def list_groupss():
    """Return all groups in db."""
    groups = Groups.query.filter_by(gp_type = None)
    return render_template("/groups/group_list.html", groups=groups)


##############################################################################
# Expenses Route
@app.route("/expenses/add_expense", methods=["GET", "POST"])
def add_expense():
    """Show Groups Expense Form.
       Get method for showing form
       Post method for processing the form
    """
    
    if ( g.user is None ):
        msg = "Login First to enter report"
        return render_template("/message.html", msg=msg)

    form =  AddExpenseForm()
    
    groups = [ [group.gp_name, group.gp_name] for group in Groups.query.filter_by(gp_type = None)]
    friends = [ [user.username, user.username] for user in User.query.filter_by(role = None) ]

    friend_list = []

    form.gp.choices = groups
    form.friend.choices = friends

    if form.validate_on_submit():
       
        cost = form.cost.data
        group_name = form.gp.data
        cost_info = form.cost_info.data
        username = form.friend.data

        exps = db.session.query(Expenses).filter(Expenses.group_name == group_name).filter( (Expenses.status == 'paid') | (Expenses.status== 'Request Sent') | (Expenses.status == 'No Action') )
        #If any of the expenses have been processed, no more expenses can be 
        # added for that event.

        if (exps.count() > 0):
            flash(f"Deadline over expenses computed you can no longer add additional expenses", "danger")
            
            friend_list = get_friend_list(group_name)
            return render_template("/expenses/add_expense_form.html", form=form, 
                                    group_name=group_name, 
                                    friend_list=friend_list )
    
        expense = Expenses( username = username, group_name=group_name, cost=cost, cost_info=cost_info )
        
        try:
            db.session.add(expense)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
         
            flash(f"Integrity Error: You have entered your expense report", "danger")
            friend_list = get_friend_list(group_name)
            
            return render_template("/expenses/add_expense_form.html", form=form, 
                                    group_name=group_name, friend_list=friend_list )
           
        
        #Get Friends/usernames for the event from expense table
        friend_list = get_friend_list(group_name)
        
        flash(f"Friend {username} expense added", "info")

        return render_template(f"/expenses/add_expense_form.html/", form=form, 
                                  group_name=group_name, friend_list=friend_list)
    
    return render_template("/expenses/add_expense_form.html", form=form )

#Get Friends/usernames for the event from expense table
def get_friend_list(group_name):
    friend_list = []
    
    exp_list = Expenses.query.filter_by(group_name=group_name)
    if (exp_list.count() > 0):
        for e in exp_list:
            friend_list.append(e.username)
    return friend_list



@app.route("/groups/expenses/<group_name>", methods=["GET", "POST"])
def show_expenses(group_name):
    """Split Expenses For this group among friends
    """
    results = Expenses.query.filter_by(group_name=group_name)
    if (results.count() == 0):
        return render_template("/message.html", msg="No Expenses Entered")

    exps = Expenses.query.filter_by(group_name=group_name).all()

    gpExpenses = GroupExpenses(exps)
   
    return render_template("/expenses/payment.html", 
                            payments=gpExpenses.payments, 
                            group_name=group_name,
                            total_cost=gpExpenses.total_cost,
                            target=gpExpenses.target)

@app.route("/request_payment", methods=["GET", "POST"])
def request_payment():
    """Request Payment: Get payment details from get request
       Call Venmo api to make the payment request
    """
    amount = request.form['amt']
    amount = float(amount)
    user_name = request.form['user_name']
    gp_name  = request.form['gp']
    
    
    msg = f"Permission Denied Log In As Admin"

    if (g.user and is_admin(g.user.username)):
        msg = "Access_token not set"
        
        if ( ACCESS_TOKEN in session ):
            # get access token from session variable
            access_token = session[ACCESS_TOKEN]

            venmo = Venmo(access_token)
            user_id = venmo.get_user_id_by_username(user_name)
            
            message = f"Request payment ${amount} for event {gp_name}"
    
            success = venmo.request_money(amount, message, user_id)
    
            if (success):
             
                single_expense = Expenses.query.filter_by(group_name=gp_name, username=user_name).first()
                
                single_expense.status = 'Request Sent'
                single_expense.payment_amt = amount
                db.session.commit()
                
                msg = f"{gp_name}:Sent payment request to Venmo user_id: ({user_name})for ${amount}"
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
    group_name  = request.form['gp']
    
    if (g.user and is_admin(g.user.username)):
      
        if ( ACCESS_TOKEN in session ):
            
            access_token = session[ACCESS_TOKEN]
            venmo = Venmo(access_token)
            
            user_id = venmo.get_user_id_by_username(user_name)
            payment_note = f"{user_name}, Payment ${payment_amount} for event {group_name}"
    
            success = venmo.send_money(payment_amount, payment_note, user_id )

            if (success):
                single_expense = Expenses.query.filter_by(group_name=group_name, username=user_name).first()
                single_expense.status = 'Paid'
                single_expense.payment_amt = payment_amount
                db.session.commit()

                msg = f"{group_name}Sent payment to Venmo user_id: ({user_name})for ${payment_amount}"
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
@app.route("/demo/demo_app", methods=["GET", "POST"])
def demo_app():
    init_demo_data()
    gp_name = "Mars Trip"
    Expenses.query.filter_by(username='Nemo').delete()
    
    form =  AddExpenseForm()
    #group_form = ShowGroupForm()
    
    groups = [ [group.gp_name, group.gp_name] for group in Groups.query.filter_by(gp_name = gp_name)]
    friends = [ [user.username, user.username] for user in User.query.filter_by(username = 'Nemo') ]

    form.gp.choices = groups
    #event_form.event.choices = evts
    form.friend.choices = friends

    demo_gp = Groups.query.filter_by(gp_name = gp_name).first()
    friend_list = get_friend_list(demo_gp.gp_name)

    if form.validate_on_submit():
       
        cost = form.cost.data
        group_name = form.gp.data
        cost_info = form.cost_info.data
        username = form.friend.data

        # group = Groups.query.get_or_404(group_name)
        # evt_name = event.evt_name
        
        expense = Expenses( username = username, group_name=group_name, cost=cost, cost_info=cost_info )
        
        try:
            db.session.add(expense)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
         
            flash(f"Integrity Error: You have entered your expense report", "danger")
            return render_template("message.html", msg="Error")
        
        exps = Expenses.query.filter_by(group_name=group_name).all()
        friend_list = get_friend_list(group_name)
        
        gpExpenses = GroupExpenses(exps)
        flash(f"Splitting expenses between Nemo and friends. If action required, payment will be settled soon", "info")
   
        return render_template("/expenses/payment.html", 
                            payments=gpExpenses.payments, 
                            group_name=group_name,
                            total_cost=gpExpenses.total_cost,
                            target=gpExpenses.target)
        
    flash(f"This is a Demo of the CostTracker App!", "info")
    return render_template("/demo/demo_form.html", form=form, friend_list=friend_list, gp_name=gp_name )


def init_demo_data():
    gp_name = "Mars Trip"
    demo = "demo"
  
    gp1 = Groups(
     gp_name = gp_name,
     gp_type =  'demo'
    )
    try:
        id =  db.session.add(gp1)
        db.session.commit()
    except IntegrityError:
            db.session.rollback()

    f1 = User(
        username = "Nemo",
        role = demo,
        password = "nemopass"
    )
    f2 = User(
        username = "Jelly Fish",
        role = demo,
        password = "jellypass"
    )
    f3 = User(
        username = "Blue Whale",
        role = demo,
        password = "whalepass"
    )

    try:
        db.session.add(f1)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    try:
        jellyFishId =  db.session.add(f2)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    try:
        blueWhaleId = db.session.add(f3)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    #demo_gp = Groups.query.filter_by(gp_name=gp_name).first()

    e1 = Expenses(
        username="Blue Whale",
        group_name = gp_name,
        cost=1,
        cost_info="Hotel and gas"
    )

    e2 = Expenses(
        username="Jelly Fish",
        group_name = gp_name,
        cost=3,
        cost_info="Food and drinks"
    )

    try:
        db.session.add(e1)
        db.session.commit()
    except IntegrityError:
        print("err1")
        db.session.rollback()
    
    try:
        db.session.add(e2)
        db.session.commit()
    except IntegrityError:
        print("err2")
        db.session.rollback()
    
##############################################################################
# About Route
@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("/about.html")