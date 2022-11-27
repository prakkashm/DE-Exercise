# Libraries 
import random
import pandas as pd
import pymysql
import sqlalchemy as sa

# Initializations
total_transactions = 10000
users = 200
max_amount = 1000000
random_transactions = []

# Connecting with the database
user = 'root'
password = 'mysql_PM_EC2_1' # Enter the password here
host = 'localhost'
port = 3306
database = 'epifi' # Enter the database name here
table = 'transactions'

engine = sa.create_engine(url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}", echo = False)
db_connection = engine.connect()

def get_enum_values(enum_string):
    return str(enum_string).replace('enum', '').replace('(', '').replace(')', '').replace('\'', '').split(",")

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

if __name__ == "__main__":
    # Getting table schema
    table_schema = db_connection.execute('DESCRIBE transactions;')

    # Truncating the table to test this script again and again
    # db_connection.execute('TRUNCATE TABLE transactions;')

    table_columns = []

    for row in table_schema:
        if row[0] == 'payment_method':
            payment_method_list = get_enum_values(row[1])
            
        if row[0] == 'status':
            payment_status_list = get_enum_values(row[1])
            
        table_columns.append(row[0])
    
    table_columns.remove('id')
    table_columns.remove('updated_at') 
    user_list = list(range(1, users + 1, 1))
    
    # Generating all unique combinations of payment method, status & user in the transactions
    payee_per_user = total_transactions//(len(payment_method_list) * len(payment_status_list) * len(user_list))
    random_transactions = generate_random_transactions(payment_method_list, payment_status_list, user_list, payee_per_user)

    payee_per_user = (total_transactions - len(random_transactions)) //(len(payment_method_list) * len(payment_status_list) * len(user_list))
    random_transactions = random_transactions + generate_random_transactions(
        payment_method_list, payment_status_list, user_list, payee_per_user
    )

    random_transactions = random_transactions[0: total_transactions]
    random_transactions_df = pd.DataFrame(random_transactions, columns = table_columns)

    random_transactions_df.to_sql(name = table, con = db_connection, if_exists = 'append', index = False)
    
    data_population_check = db_connection.execute('SELECT COUNT(id) AS row_count, MIN(id) AS min_id, MAX(id) AS max_id, COUNT(DISTINCT(payment_from)) AS user_count, COUNT(DISTINCT(payment_method)) AS payment_methods, COUNT(DISTINCT(status)) AS statuses FROM transactions;')

    print(f"Data populated in '{database}.{table}' successfully!")
    for row in data_population_check:
        print("Table rows: ", row[0])
        print("Table least id: ", row[1])
        print("Table highest id: ", row[2])
        print("Unique combinations: ", row[3], " users * ", row[4], " payment methods * ", row[5], " payment status values")

    table_dump = db_connection.execute('SELECT * FROM transactions LIMIT 500;')

    final_dump = pd.DataFrame(table_dump.fetchall())
    final_dump.columns = table_dump.keys()

    print(f"\n'{database}.{table}' looks like: ")
    print(final_dump.head(5).to_string(index = False))

    final_dump.to_csv('transactions.csv', index = False)
    
