"""
Use this file to play around with the data you got from the dump
Do note you need to run main.py and wait for it to complete before you do anything else
"""

import sqlite3

with sqlite3.connect("scoredump.db") as con:
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            maps.map_id,
            maps.title,
            maps.difficulty_name,
            maps.artist,
            MAX(scores.star_rating) AS star_rating,
            maps.ranked_status
        FROM maps
        JOIN scores ON scores.map_id = maps.map_id
        WHERE scores.lazer = 0
        AND scores.mods NOT LIKE '%NF%'
        AND maps.ranked_status IN ('ranked', 'approved')
        AND scores.star_rating >= 10
        GROUP BY maps.map_id
        ORDER BY star_rating DESC;

    """
    )

    top_maps = cur.fetchall()

for map in top_maps:
    print(f"{map[3]} - {map[1]} [{map[2]}] {map[4]:.2f}* ({map[5]})")
    print()
print(len(top_maps))
