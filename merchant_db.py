# merchant_db.py

import sqlite3
from datetime import datetime

class MerchantDB:
    # Class to handle database operations for merchants

    def __init__(self, db_file):
        self.conn = self.create_connection(db_file) # Establish a database connection
        self.create_tables() # Create necessary tables if they don't exist

    def create_connection(self, db_file):
        # Create a SQLite database connection
        return sqlite3.connect(db_file)

    def create_tables(self):
        # Create the tables for closed merchants and logging actions
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS ClosedMerchant (
                                    MerchantUUID TEXT PRIMARY KEY,
                                    Status TEXT,
                                    AreaID TEXT,
                                    LastUpdated TIMESTAMP
                                );''')

            self.conn.execute('''CREATE TABLE IF NOT EXISTS Logging (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    Timestamp TIMESTAMP,
                                    Action TEXT,
                                    MerchantUUID TEXT,
                                    AreaID TEXT,
                                    AreaName TEXT
                                );''')

    def add_merchant(self, merchant_uuid, area_info):
        # Add or update a merchant as closed in the ClosedMerchant table
        with self.conn:
            self.conn.execute('''
                INSERT INTO ClosedMerchant (MerchantUUID, Status, AreaID, LastUpdated)
                VALUES (?, 'Closed', ?, ?)
                ON CONFLICT(MerchantUUID) 
                DO UPDATE SET Status='Closed', LastUpdated=excluded.LastUpdated;''',
                         (merchant_uuid, area_info['area_id'], datetime.now()))

            self.conn.execute('''
                INSERT INTO Logging (Timestamp, Action, MerchantUUID, AreaID, AreaName)
                VALUES (?, 'Closed', ?, ?, ?);''',
                         (datetime.now(), merchant_uuid, area_info['area_id'], area_info['area_name']))

    def remove_merchant(self, merchant_uuid, area_info):
        # Remove a merchant from the ClosedMerchant table and log the opening action
        with self.conn:
            self.conn.execute('''
                DELETE FROM ClosedMerchant WHERE MerchantUUID=?;''', (merchant_uuid,))
            self.conn.execute('''
                INSERT INTO Logging (Timestamp, Action, MerchantUUID, AreaID, AreaName)
                VALUES (?, 'Opened', ?, ?, ?);''', (datetime.now(), merchant_uuid, area_info['area_id'], area_info['area_name']))

    def close(self):
        # Close the database connection
        self.conn.close()
