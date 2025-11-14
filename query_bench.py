"""
Use this file to play around with the data you got from the dump
Do note you need to run main.py and wait for it to complete before you do anything else
"""

import sqlite3

with sqlite3.connect("scoredump.db") as con:
    cur = con.cursor()
    # This query gets your top 5 highest star rating non NF passes on stable
    cur.execute(
        """
        SELECT DISTINCT
            maps.map_id,
            maps.title,
            maps.difficulty_name,
            maps.artist,
            scores.star_rating
        FROM maps
        JOIN scores ON scores.map_id = maps.map_id
        WHERE scores.lazer = 0
          AND scores.mods NOT LIKE '%NF%'
          AND maps.ranked_status = "ranked"
        ORDER BY scores.star_rating DESC
        LIMIT 5;
    """
    )

    top_maps = cur.fetchall()

print(top_maps)
