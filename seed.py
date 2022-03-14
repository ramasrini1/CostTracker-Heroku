from app import app
from models import db, Groups, Expenses, User, Subscribers, Message
#from models import db, Groups, Expenses

db.drop_all()
db.create_all()

demo = "demo"

#Create demo users
f1 = User(
    username = "demo_user",
    role = demo,
    password = "demo_user"
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

try:
    nemoId = db.session.add(f1)
    db.session.commit()
except IntegrityError:
    db.session.rollback()

#Create General gp for all groups chat
# name = "General"
# g = Groups(
#   gp_name = name,
#   gp_type = name,
#   gp_owner = 'demo_user'

# )
# try:
#     id =  db.session.add(g)
#     db.session.commit()
# except IntegrityError:
#         db.session.rollback()


# #Create Demo Group
gp_name = "Demo Group"

gp1 = Groups(
  gp_name = gp_name,
  gp_type =  demo,
  gp_owner = 'demo_user'
)
try:
    id =  db.session.add(gp1)
    db.session.commit()
except IntegrityError:
        db.session.rollback()


#   #demo_gp = Groups.query.filter_by(gp_name=gp_name).first()

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


#Some psql commands

#This empties table Model User
# db.session.query(User).delete()
# db.session.commit()

# UPDATE users SET role = 'admin' WHERE username = 'rama-srinivas'

#from venmo_api import Client

# Get your access token. You will need to complete the 2FA process
#access_token = Client.get_access_token(username='ramasrini1@gmail.com', password='your_venmo_password')

#To drop a table
# DELETE FROM expenses;

#Delete a record from a table
#DELETE FROM users where username = 'tester';