from app import app
from models import db, Groups, Expenses, User

db.drop_all()
db.create_all()

#Some psql commands

#This empties table Model User
# db.session.query(User).delete()
# db.session.commit()


# evt1 = Events(
#     evt_name="Hawai Trip"
# )

# db.session.add_all([evt1])
# db.session.commit()

# e1 = Expenses(
#     username="sumana-srinivas",
#     event_id = 1,
#     cost=1,
#     cost_info="Spent for hotel and gas"
# )

# e2 = Expenses(
#     username="Anjana-Srinivas",
#     event_id=1,
#     cost=2,
#     cost_info="Spent for Mama's Grill"
# )


# db.session.add_all([e1, e2])
# db.session.commit()

# UPDATE users SET role = 'admin' WHERE username = 'rama-srinivas'

#from venmo_api import Client

# Get your access token. You will need to complete the 2FA process
#access_token = Client.get_access_token(username='ramasrini1@gmail.com', password='your_venmo_password')

#To drop a table
# DELETE FROM expenses;

#Delete a record from a table
#DELETE FROM users where username = 'tester';