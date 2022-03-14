from flask import Flask, request, render_template,  redirect, flash, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, Groups, Expenses, User, Message, Subscribers
from forms import (
    AddGroupForm, AddExpenseForm, UserAddForm, LoginForm, 
    AdminForm, ShowGroupForm, AddGroupsForm, MessageForm )

from expenses import GroupExpenses
import queries

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

demo_user = 'demo_user'
demo_group = 'Demo Group'

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
        join_chat_group("general")

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

def join_chat_group(gp_name):
    g.user = User.query.get(session[CURR_USER_KEY])
    username = g.user.username
   
    s1 = Subscribers(username=username, group_name=gp_name)
    try:
        db.session.add(s1)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

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
    if (g.user is None):
        msg = "Need to login"
        flash("Need to login or signup to add a group", "danger")
        return render_template("/message.html", msg=msg)
       
    
    if ( g.user.username == demo_user):
        msg = f"Please Sign up to access all the features of this app !"
        flash("Access Denied for demo users", "danger")
        return render_template("/message.html", msg=msg)
    
    form = AddGroupForm()
    
    if form.validate_on_submit():
        gp_name = form.gp_name.data
        group = Groups( gp_name = gp_name, gp_owner=g.user.username )
        
        try:
            db.session.add(group)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"This group {gp_name} already exists.", "danger")
            return redirect("/groups/new")
        
        return redirect('/groups/list')
    
    return render_template("/groups/add_group.html", form=form)


@app.route("/groups/list")
def list_groups():
    """Return all groups in db."""
    groups = Groups.query.filter_by(gp_type = None)
    return render_template("/groups/group_list.html", groups=groups)

## ToDo Feature
@app.route("/groups/join",  methods=["GET", "POST"])
def join_groups():

    if ( g.user is None ):
        return render_template("/message.html", msg="You need to login to join a group")
    
    form = AddGroupsForm()
    form.msg_groups.choices =  queries.get_msg_groups()

    if form.validate_on_submit():
        group_names = form.msg_groups.data
        
        for group_name in group_names:
            print(f"groupname is {group_name}")
            s = Subscribers(username=g.user.username, group_name=group_name)
            try:
                db.session.add(s)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(f"You have already subscribed to this group", "danger")
                return render_template("/messages/subscribe.html", form=form)
            
        return render_template("/message.html", msg="Thank you for joining the group")
    
    return render_template("/messages/subscribe.html", form=form)


##############################################################################
# Expenses Route
@app.route("/expenses/add_expense", methods=["GET", "POST"])
def add_expense():
    """Show Groups Expense Form.
       Get method for showing form
       Post method for processing the form
    """
    
    if ( g.user is None ):
        msg = "Sign up/Login First to enter report"
        return render_template("/message.html", msg=msg)
    
    if ( g.user.username == demo_user):
        msg = f"Please Sign up to access all the features of this app !"
        flash("Access Denied for demo users", "danger")
        return render_template("/message.html", msg=msg)
  

    friend_list = []
    form =  AddExpenseForm()
    
    form.gp.choices = queries.getGroupsTuple()
    form.friend.choices = queries.getFriendsTuple()

    if form.validate_on_submit():
       
        cost = form.cost.data
        group_name = form.gp.data
        cost_info = form.cost_info.data
        username = form.friend.data

        #Get expenses of the group whose status is 'Paid' or 'Request Sent' or 'No Action'
        exps = queries.getExpensesBasedOnStatus(group_name)
        
        #If any of the expenses have been processed, no more expenses can be 
        # added for that group.

        if (exps.count() > 0):
            flash(f"Deadline over expenses computed you can no longer add additional expenses", "danger")
            
            friend_list = queries.get_friend_list(group_name)
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
            friend_list = queries.get_friend_list(group_name)
            
            return render_template("/expenses/add_expense_form.html", form=form, 
                                    group_name=group_name, friend_list=friend_list )
           
        
        #Get Friends/usernames for the Group from Expense table
        friend_list = queries.get_friend_list(group_name)
        
        flash(f"Friend {username} expense added", "info")

        return render_template(f"/expenses/add_expense_form.html/", form=form, 
                                  group_name=group_name, friend_list=friend_list)
    
    return render_template("/expenses/add_expense_form.html", form=form )


@app.route("/groups/expenses/<group_name>", methods=["GET", "POST"])
def show_expenses(group_name):
    """Split Expenses For this group among friends
    """
   
    results = Expenses.query.filter_by(group_name=group_name)
    
    if (results.count() == 0):
        return render_template("/message.html", msg="No Expenses Entered")
    
    exps = queries.getExpenses(group_name)

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
    group_name  = request.form['gp']
    
    
    msg = f"Permission Denied Log In As Admin"

    if (g.user and is_admin(g.user.username)):
        msg = "Access_token not set"
        
        if ( ACCESS_TOKEN in session ):
            # get access token from session variable
            access_token = session[ACCESS_TOKEN]

            venmo = Venmo(access_token)
            user_id = venmo.get_user_id_by_username(user_name)
            
            message = f"Request payment ${amount} for event {group_name}"
    
            success = venmo.request_money(amount, message, user_id)
    
            if (success):
                single_expense = queries.getExpensesByGpAndUserNames(group_name, user_name)
                #single_expense = Expenses.query.filter_by(group_name=gp_name, username=user_name).first()
                
                single_expense.status = 'Request Sent'
                single_expense.payment_amt = amount
                db.session.commit()
                
                msg = f"{group_name}:Sent payment request to Venmo user_id: ({user_name})for ${amount}"
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
                single_expense = queries.getExpensesByGpAndUserNames(group_name, user_name)
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
    return render_template("/message.html", msg="Unable to Remove token From System.")

def is_admin(username):
    user = User.query.filter_by(username=username).first()
    if ( user.role == 'admin'):
        return True
    return False

@app.route('/admin/addGp', methods=["GET", "POST"])
def addGp():
    msg = "Not Valid user"
    name = "General"
    if (g.user and is_admin(g.user.username)):
        msg = "valid user"
        #Create General gp for all groups chat
        gp = Groups( gp_name = name, gp_type = name, gp_owner = g.user.username )
        try:
            id =  db.session.add(gp)
            db.session.commit()
            msg = "General gp created"
        except IntegrityError:
            msg = "IntegrityError, Group Exists"
            db.session.rollback()
        
    return render_template("/message.html", msg=msg)
    
   

##############################################################################
# Demo Route
@app.route("/demo/demo_app", methods=["GET", "POST"])
def demo_app():
  
    gp_name =  demo_group
    username = demo_user
    Expenses.query.filter_by(username = username).delete()
    db.session.commit()
    #Expenses.query.filter_by(username='Nemo').delete()
    user = User.query.filter_by(username=username).first()
    
    do_login(user)

    return redirect("/demo/expense")


@app.route("/demo/expense", methods=["GET", "POST"])
def demo_expense():
    gp_name =  demo_group
    username = demo_user

    form =  AddExpenseForm()
   
    groups = [ [group.gp_name, group.gp_name] for group in queries.getGroupByGpName(gp_name)]
    friends = [ [user.username, user.username] for user in queries.getUserByUsername(username) ]

    form.gp.choices = groups
    form.friend.choices = friends

    demo_gp = Groups.query.filter_by(gp_name = gp_name).first()
    friend_list = queries.get_friend_list(demo_gp.gp_name)

    if form.validate_on_submit():
       
        cost = form.cost.data
        group_name = form.gp.data
        cost_info = form.cost_info.data
        username = form.friend.data
      
        expense = Expenses( username = username, group_name=group_name, cost=cost, cost_info=cost_info )
        
        try:
            db.session.add(expense)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
         
            flash(f"Integrity Error: You have entered your expense report", "danger")
            return render_template("message.html", msg="Error")
        
        exps = queries.getExpenses(group_name)
        friend_list = queries.get_friend_list(group_name)
        
        gpExpenses = GroupExpenses(exps)
        flash(f"Splitting expenses between demo_user and friends. If action required, payment will be settled soon", "info")
       
        return render_template("/expenses/payment.html", 
                            payments=gpExpenses.payments, 
                            group_name=group_name,
                            total_cost=gpExpenses.total_cost,
                            target=gpExpenses.target)
        
    flash(f"This is a Demo of the Cost Tracker App!", "info")
    return render_template("/demo/demo_form.html", form=form, friend_list=friend_list, gp_name=gp_name )

  
    
##############################################################################
# About Route
@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("/about.html")


##############################################################################
# Message Route
@app.route("/messages/<username>", methods=["GET", "POST"])
def message(username):
    
    #Check if username is logged in before seeing or sending messages
    
    if (g.user.username != username):
        flash("Login with correct credential to view the chat", "info")
        return redirect("/")
    
    form = MessageForm()
    form.msg_group.choices =  queries.get_msg_groups()
    # get chat messages for the user
    msg_lst = queries.get_chat_msg(g.user.username)
 

    if form.validate_on_submit():
        group_name = form.msg_group.data
        text = form.text.data
        m = Message(group_name=group_name, username=g.user.username, text=text)
        db.session.add(m)
        db.session.commit()
        flash("Your message has been added", "success")
        msg_lst = queries.get_chat_msg(g.user.username)
       
    
    return render_template("/messages/msg_board.html", form=form, msg_lst=msg_lst)


@app.route("/messages/<int:msg_id>/delete", methods=["GET", "POST"])
def delete_message(msg_id):
    msg = queries.get_msg_byId(msg_id)
    
    if ( msg.username != g.user.username):
        flash("You don't have permissions to delete", "danger")
        return redirect(f"/messages/{g.user.username}")
    
    Message.query.filter_by(id = msg_id).delete()
    db.session.commit()
    flash("Message deleted", "info")
    return redirect(f"/messages/{g.user.username}")
    