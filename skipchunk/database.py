"""
Manages a simple database to store concepts for existing preflabel lookup.
Should be kept in skipchunk_data for easy backup
"""

import sqlite3


class Database:

    def get_concept(self,key):
        # Gets the preflabel for the key
        self.c.execute('''SELECT preflabel FROM concepts WHERE key=?''', (key,))
        preflabel = self.c.fetchone()
        if preflabel and len(preflabel):
            #result is a tuple, just grab the value
            preflabel = preflabel[0]
        return preflabel

    def add_concept(self,concept):
        # Insert a new concept
        self.c.execute('''INSERT INTO concepts VALUES (?,?,?,datetime('now'))''', (concept.key, concept.preflabel, concept.total,))
        self.conn.commit()
        return concept

    def update_concept(self,concept):
        # Update the total
        self.c.execute('''UPDATE concepts SET total=total+? WHERE key=?''', (concept.total,concept.key,))
        self.conn.commit()
        return concept

    def upsert_concept(self,concept):
        # Creates a concept if it doesnt exist, updates the total if it does
        preflabel = self.get_concept(concept.key)

        if not preflabel:
            #Add to the table
            self.add_concept(concept)
            preflabel = concept.preflabel

        else:
            #Update the total
            self.update_concept(concept)

        return preflabel

    def create(self):

        # Create table
        self.c.execute('''
                CREATE TABLE concepts (
                    key text NOT NULL PRIMARY KEY,
                    preflabel text NOT NULL, 
                    total int DEFAULT 0,
                    date text NOT NULL
                )
            ''')

        # Save (commit) the changes
        self.conn.commit()

    def exists(self):
        #Does the database exist and is it healthy?
        OK = False

        self.c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='concepts' ''')
        name = self.c.fetchone()
        if name and len(name):
            OK = True

        return OK

    def delete(self):
        #Delete the concepts table.  USE AT YOUR OWN RISK!
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute('''DROP TABLE IF EXISTS concepts''')
        conn.commit()
        conn.close()

    def open(self):
        #Opens a connection, and creates the table if it doesn't exit
        self.conn = sqlite3.connect(self.database)
        self.c = self.conn.cursor()
        if not self.exists():
            self.create()

    def close(self):
        #Bye bye
        self.conn.close()

    def __init__(self,database,delete=False):
        #Database is the full path of the sqlite database file
        self.database = database

        if delete: 
            self.delete()

        self.open()
