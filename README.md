# Data Engineering Exercise

- *installation_steps* contains the command execute the different softwares.
- After the installation, the database & table can be created through the DDL statements present in *db_table_creation*.
- Once the table is created, *random_data_generation.py* should be run to generate random transactions data in the table. A small subset of this data is also exported in the file *transactions.csv* (just to get a visual understanding of how the randomly generated data looks like).
- After setting up hadoop & sqoop (instructions in installation_steps), *sqoop_job* is the command that generates the desired job for incremental updates.
