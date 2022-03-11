class GroupExpenses:
    def __init__(self, expenses):
        self.expenses = expenses
        self.friends = []
        self.total_cost = 0
        self.cost_list = []
        self.cost_info = []
        self.status = []
        self.payments = []
        self.target = 0
        self.split_expenses()
    
    def unpack_data(self):
        sum_cost = 0
       
        for exp in self.expenses:
            #print(f"expense from db: {exp.username} {exp.event_id} {exp.cost}")
            self.friends.append(exp.username)
            sum_cost = exp.cost + sum_cost
            self.cost_list.append(exp.cost)
            self.cost_info.append(exp.cost_info)
            self.status.append(exp.status)
            sum_cost = round(sum_cost, 2)
            self.total_cost = sum_cost
            num_friends = len(self.friends)
            self.target = self.total_cost/num_friends
            self.target = round(self.target, 2)
    
    def getPaymentData(self, username, amt, cost, info, status, act):
        payment_data = {"user_name": username, "amt":amt, "cost":cost, 
                        "cost_info":info, "status":status, "act":act}
        return payment_data

    
    def split_expenses(self):
        self.unpack_data()
        amt = 0
        num_friends = len(self.friends)
        target = self.target

        rows, cols = (num_friends, 3)
        arr = [[0 for i in range(cols)] for j in range(rows)]

        for i in range(rows):
            arr[i][0] = self.cost_list[i]
            #print(f"cost for {self.friends[i]} is {arr[i][0]}")
        
        for i in range(rows):
            arr[i][1] = arr[i][0] - target
            #print(f"target for {self.friends[i]} is {arr[i][1]}")
            
        for i in range(rows):
            username = self.friends[i]
            cost = arr[i][0]
            info = self.cost_info[i]
            status = self.status[i]
            
            e = {}
                
            if arr[i][1] > 0:
                amt = arr[i][1]
                amt = round(amt, 2)
                act = 'Get'
                e = self.getPaymentData(username, amt, cost, info, status, act )
                #e = {"user_name": username, "amt":amt, "cost":cost, 
                #       "cost_info":info, "status":status, "act":'Get'}
                
            if arr[i][1] < 0:
                amt = abs(arr[i][1])
                amt = round(amt, 2)
                act = 'Send'
                e = self.getPaymentData(username, amt, cost, info, status, act )
                
                
            if arr[i][1] == 0:
                amt = abs(arr[i][1])
                amt = round(amt, 2)
                act = "No Action"
                status = "No Action"
                e = self.getPaymentData(username, amt, cost, info, status, act )
               
            self.payments.append(e)
            
        
        # for i in range(rows):
        #     arr[i][2] = arr[i][0] - arr[i][1]
           

    
 
 
 
 
 