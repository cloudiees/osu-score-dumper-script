"""
This file is used to create the database
"""

import sqlite3

con = sqlite3.connect("scoredump.db")
cur = con.cursor()

cur.execute("PRAGMA foreign_keys = ON;")

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS maps(
        id INTEGER PRIMARY KEY,
        map_id INTEGER UNIQUE NOT NULL,
        title TEXT NOT NULL,
        difficulty_name TEXT NOT NULL,
        ranked_status TEXT NOT NULL,
        artist TEXT NOT NULL
    );
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS scores(
        id INTEGER PRIMARY KEY,
        score_id INTEGER UNIQUE NOT NULL,
        pp REAL,
        accuracy REAL NOT NULL,
        total_score INTEGER NOT NULL,
        ended_at TEXT NOT NULL,
        star_rating REAL NOT NULL,
        mods TEXT NOT NULL,
        map_id INTEGER NOT NULL,
        lazer INTEGER NOT NULL,
        player INTEGER NOT NULL,
        FOREIGN KEY(map_id) REFERENCES maps(map_id)
    );
    """
)

con.commit()

con.close()
