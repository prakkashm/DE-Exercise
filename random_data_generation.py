# Libraries
import random
import pandas as pd
import pymysql
from sqlalchemy import create_engine

# Initializations
total_transactions = 10000
users = 200
max_amount = 1000000000
random_transactions = []

payment_method_list = ['UPI', 'Credit Card', 'Debit Card']
payment_status_list = ['Failed', 'Declined', 'Processing', 'Initiated', 'Success']
user_list = list(range(1, users + 1, 1))

def generate_random_transactions(payment_method_list, payment_status_list, user_list, payee_per_user = 1):
    transaction_list = []

    if payee_per_user == 0:
        payee_per_user = 1
    
    for payment_method in payment_method_list:
        for payment_status in payment_status_list:
            for user in user_list:
                other_users = user_list.copy()
                other_users.remove(user)      # Assuming a user cannot transact with themself
                
                payment_from = user
                payment_to = random.sample(other_users, payee_per_user) # Sampling other users to transact with
                amount = random.sample(range(1, max_amount, 1), payee_per_user) # Sampling amounts to transact worth
                
                for idx in range(payee_per_user):
                    current_transaction = [payment_method, payment_from, payment_to[idx], amount[idx], payment_status]
                    transaction_list.append(current_transaction)
    
    return transaction_list

# Generating all unique combinations of payment method, status & user in the transactions
payee_per_user = total_transactions//(len(payment_method_list) * len(payment_status_list) * len(user_list))
random_transactions = generate_random_transactions(payment_method_list, payment_status_list, user_list, payee_per_user)

payee_per_user = (total_transactions - len(random_transactions)) //(len(payment_method_list) * len(payment_status_list) * len(user_list))
random_transactions = random_transactions + generate_random_transactions(
    payment_method_list, payment_status_list, user_list, payee_per_user
)

random_transactions = random_transactions[0: total_transactions]
random_transactions_df = pd.DataFrame(random_transactions, 
    columns = ['payment_method', 'payment_from', 'payment_to', 'amount', 'status']
)
random_transactions_df.insert(0, 'id', range(len(random_transactions)))

# Connecting with the database to insert the generated data
user = 'root'
password = '' # Enter the password here
host = 'localhost'
port = 3306
database = '' # Enter the database name here

engine = create_engine(url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", echo = False)
random_transactions_df.to_sql(name = 'transactions', con = engine, if_exists = 'append', index = False)

