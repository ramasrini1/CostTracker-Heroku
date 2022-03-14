from models import Groups, Expenses, User, Message, Subscribers

def getUserByUsername(username):
  return User.query.filter_by(username = username)

def getExpenses(group_name):
  return Expenses.query.filter_by(group_name=group_name).all()

def getExpensesByGpAndUserNames(group_name, user_name):
  return Expenses.query.filter_by(group_name=group_name, username=user_name).first()

def getGroupsByGpType(gp_type):
  return Groups.query.filter_by(gp_type = gp_type)

def getGroupByGpName(gp_name):
  return Groups.query.filter_by(gp_name = gp_name)
                
def get_msg_groups():
  msg_groups = [ [group.gp_name, group.gp_name] for group in Groups.query.all()]
  return msg_groups

def get_msg_byId(id):
  return Message.query.get(id)

def get_friend_list(group_name):
  friend_list = []
    
  exp_list = Expenses.query.filter_by(group_name=group_name)
  if (exp_list.count() > 0):
      for e in exp_list:
        friend_list.append(e.username)
  return friend_list

def format_messages(messages):
  lst = []
  msg_lst = []
  msg_blk = {}

  for msg in messages:
    gp_name = msg.group_name
    l = {'username': msg.username, 'date': msg.timestamp, 'text': msg.text, 
          'group_name': msg.group_name, 'msg_id':msg.id }
    msg_lst.append(l)
    
  return msg_lst

def getGroupsTuple():
  groups = [ [group.gp_name, group.gp_name] for group in Groups.query.filter_by(gp_type = None)]
  return groups

def getFriendsTuple():
  friends = [ [user.username, user.username] for user in User.query.filter_by(role = None) ]
  return friends

def getExpensesBasedOnStatus(group_name):
  exps = Expenses.query.filter(Expenses.group_name == group_name).filter( (Expenses.status == 'paid') | (Expenses.status== 'Request Sent') | (Expenses.status == 'No Action') )
  return exps
    
def get_chat_msg(username):
  messages = Message.query.all()
  return(format_messages(messages))
  # sub_list = Subscribers.query.filter_by(username = username)
  # lst = []
  # for sub in sub_list:
  #   group_name = sub.group_name
  #   messages = Message.query.filter_by(group_name=group_name)

  # return(format_messages(messages))
    