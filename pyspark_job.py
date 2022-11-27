import findspark
findspark.init()

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

sparkSession = SparkSession.builder.appName("transactions_user_aggregation").getOrCreate() 

transactions = sparkSession.read.option("header", True).csv('hdfs://localhost:9000/user/hduser/transactions.csv')
 
# Filtering successful & failed transactions separately
successful_transactions = transactions.filter(transactions.status == "Success")
failed_transactions = transactions.filter(transactions.status == "Failed")

# Counting failed transactions for each user
user_receiving_failed_transactions = failed_transactions.select(col("payment_to").alias("user_id"))
user_sending_failed_transactions = failed_transactions.select(col("payment_from").alias("user_id"))
user_all_failed_transactions = user_sending_failed_transactions.union(user_receiving_failed_transactions)
failed_transactions_per_user = user_all_failed_transactions.groupBy("user_id").count()
failed_transactions_per_user = failed_transactions_per_user.withColumnRenamed("count", "failed_txn")

# All sending transactions for each user
user_sending_transactions = successful_transactions.select(
    col("payment_from").alias("user_id"),
    (-1 * col("amount")).alias("amount"),
    col("payment_method"), 
    col("status")
)

# All receiving transactions for each user
user_receiving_transactions = successful_transactions.select(
    col("payment_to").alias("user_id"),
    col("amount"), 
    col("payment_method"), 
    col("status")
)

# User wise all successful transactions
user_all_successful_transactions = user_sending_transactions.union(user_receiving_transactions)

# Calculating avg/total amount transacted by each user
overall_transacted_per_user = user_all_successful_transactions.groupBy("user_id").agg(
    mean('amount').alias("avg_amount_transacted"), 
    sum('amount').alias("overall_amount_transacted")
)

# Calculating avg/total amount received by each user
overall_received_per_user = user_receiving_transactions.groupBy("user_id").agg(
    mean('amount').alias("avg_amount_received"), 
    sum('amount').alias("overall_amount_received")
)

# Counting successful transactions for each user
successful_transactions_per_user = user_all_successful_transactions.groupBy("user_id").count()
successful_transactions_per_user = successful_transactions_per_user.withColumnRenamed("count", "successful_txn")

# Getting the payment method for the highest amount transacted by each user
highest_transaction_per_user = user_all_successful_transactions.withColumn(
    "row_number", 
      row_number().
      over(
          Window.
          partitionBy("user_id").
          orderBy(col("amount").
            desc()
          )
      )
)

highest_transaction_per_user = highest_transaction_per_user.filter(
    highest_transaction_per_user.row_number == 1
)

highest_transaction_per_user = highest_transaction_per_user.select(
    col("user_id"), 
    col("payment_method").alias("highest_txn_method")
)

# Getting the payment method for the highest amount received by each user
highest_received_per_user = user_receiving_transactions.withColumn(
    "row_number", 
      row_number().
      over(
          Window.
          partitionBy("user_id").
          orderBy(col("amount").
            desc()
          )
      )
)

highest_received_per_user = highest_received_per_user.filter(
    highest_received_per_user.row_number == 1
)

highest_received_per_user = highest_received_per_user.select(
    col("user_id"), 
    col("payment_method").alias("highest_rcvd_method")
)

# Joining the individual dataframes to collate all the data together
overall_transacted_per_user = overall_transacted_per_user.withColumnRenamed("user_id", "base_user_id")

user_metrics = overall_transacted_per_user.join(
    overall_received_per_user, overall_transacted_per_user.base_user_id == overall_received_per_user.user_id, "left"
)
user_metrics = user_metrics.drop("user_id")

user_metrics = user_metrics.join(
    successful_transactions_per_user, user_metrics.base_user_id == successful_transactions_per_user.user_id, "left"
)
user_metrics = user_metrics.drop("user_id")

user_metrics = user_metrics.join(
    failed_transactions_per_user, user_metrics.base_user_id == failed_transactions_per_user.user_id, "left"
)
user_metrics = user_metrics.drop("user_id")

user_metrics = user_metrics.join(
    highest_transaction_per_user, user_metrics.base_user_id == highest_transaction_per_user.user_id, "left"
)
user_metrics = user_metrics.drop("user_id")

user_metrics = user_metrics.join(
    highest_received_per_user, user_metrics.base_user_id == highest_received_per_user.user_id, "left"
)
user_metrics = user_metrics.drop("user_id").withColumnRenamed("base_user_id", "user_id")

user_metrics.write.option("header", True).csv('hdfs://localhost:9000/user/hduser/user_txn_metrics.csv')
