"""
Main functionality of the dumper
"""

from ossapi import Ossapi, UserBeatmapType, GameMode, Score, BeatmapPlaycount, Mod
from ossapi.enums import RankStatus
import time, sqlite3, json, os
from concurrent.futures import ThreadPoolExecutor

map_executor = ThreadPoolExecutor(max_workers=10)
score_executor = ThreadPoolExecutor(max_workers=10)

client_id: int = None
client_secret: str = None
api: Ossapi = None
maps = []
user_id: int = None
DATA_PATH = "data.json"
SLEEP_DELAY = 0.06

# Used to get the enums to strings for adding to the db (because I hate having to reference a table to figure out what the numbers mean)
ranked_status_dict = {
    RankStatus.APPROVED: "approved",
    RankStatus.GRAVEYARD: "graveyard",
    RankStatus.LOVED: "loved",
    RankStatus.PENDING: "pending",
    RankStatus.QUALIFIED: "qualified",
    RankStatus.RANKED: "ranked",
    RankStatus.WIP: "wip",
}

VALID_STATUSES = {
    RankStatus.APPROVED,
    RankStatus.LOVED,
    RankStatus.QUALIFIED,
    RankStatus.RANKED
}

def insert_map(map: BeatmapPlaycount):
    """
    Inserts a given map into the database

    Parameters:
        map (ossapi.BeatmapPlaycount): beatmap to insert (note that this is NOT a Beatmap, but rather a BeatmapPlaycount which is returned by user_beatmaps when type is set to most played)

    Returns:
        None
    """
    maps.append(map.beatmap_id)
    try:
        with sqlite3.connect("scoredump.db") as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO maps (map_id, title, difficulty_name, ranked_status, artist)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    map.beatmap_id,
                    map.beatmapset.title,
                    map.beatmap().version,
                    ranked_status_dict[map.beatmap().status],
                    map.beatmapset.artist,
                ),
            )
            con.commit()
    except Exception as e:
        # If this exception executes I have no clue what broke, maybe the db is broken in some way?
        print(f"!!!!!!!!!!!ERROR: issue with inserting map: {e}")


def insert_score(score: Score, star_rating: float, mods: list[str]):
    """
    Inserts a given score and its associated star rating into the database

    Parameters:
        score (ossapi.Score): score to insert
        star_rating (float): star rating of the map after the mods for the given score is applied to the map
        mods (list[str]): list of mods in string format

    Returns:
        None
    """
    try:
        with sqlite3.connect("scoredump.db") as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO scores (score_id, pp, accuracy, total_score, ended_at, star_rating, map_id, mods, lazer, player)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    score.id,
                    score.pp,
                    score.accuracy,
                    score.total_score,
                    score.ended_at.isoformat(),
                    star_rating,
                    score.beatmap_id,
                    "".join(mods),
                    1 if score.started_at is not None else 0,
                    score.user_id,
                ),
            )
            con.commit()
    except Exception as e:
        # If this exception executes I have no clue what broke, maybe the db is broken in some way?
        print(f"!!!!!!!!!!!ERROR: issue with inserting score: {e}")


def get_maps():
    """
    Gets all the user's played maps and inserts them into the database

    Parameters:
        None

    Returns:
        None
    """
    # Have a count variable separate from the offset bc at the end it won't be a perfect 100, I could probably make them the same variable but I don't want to
    offset = 0
    count = 0
    while True:
        map_batch:list[BeatmapPlaycount] = api.user_beatmaps(
            user_id, UserBeatmapType.MOST_PLAYED, limit=100, offset=offset
        )
        if not map_batch:
            break
        for map in map_batch:
            # Make sure we don't add maps w/out leaderboards so we dont check them
            if map.beatmapset.status in VALID_STATUSES:
                map_executor.submit(insert_map, map)
        offset += 100
        count += len(map_batch)
        print(f"{count} maps scanned")
        if count == offset:
            time.sleep(SLEEP_DELAY)

    map_executor.shutdown()


def get_scores():
    """
    Gets all the user's recorded scores and inserts them into the database

    Parameters:
        None

    Returns:
        None
    """
    status = 0
    for map in maps:
        try:
            scores = api.beatmap_user_scores(
                beatmap_id=map, user_id=user_id, mode=GameMode.OSU
            )
        except Exception as e:
            # this exception is mainly for maps that don't records scores, like some loved maps or maps without leaderboards
            print(f"!!!!!!ERROR: {e}")
            status += 1
            print(f"{status}/{len(maps)}")
            time.sleep(SLEEP_DELAY)
            continue
        # Going through scores
        mod_combos = {}
        for score in scores:
            mod_list = []
            # Used for scores with settings in them, like rate change or CL with some settings
            invalid_score = False
            # Used to detect CL because ossapi's map attributes shits itself if it sees CL so I add it after
            has_cl = False
            for mod in score.mods:
                if mod.settings:
                    invalid_score = True
                    break
                if mod.acronym == "CL":
                    has_cl = True
                # I am like 90% sure this doesn't matter but leaving it here anyways
                elif mod.acronym == "NM":
                    break
                elif mod.acronym != "CL":
                    mod_list.append(mod.acronym)
            if invalid_score:
                continue
            try:
                api_cd_needed = False
                # Optimization B) (I forgot what this is called)
                # also surely sorting it doesnt make it more inefficent... right?
                mod_list.sort()
                mod_combo = "".join(mod_list)
                if mod_combo in mod_combos:
                    star_rating = mod_combos[mod_combo]
                else:
                    api_cd_needed = True
                    if mod_list == []:
                        star_rating = api.beatmap_attributes(
                            beatmap_id=map
                        ).attributes.star_rating
                    else:
                        star_rating = api.beatmap_attributes(
                            beatmap_id=map, mods=mod_list
                        ).attributes.star_rating
                # Adding CL to the list after bc above reasoning
                if has_cl:
                    mod_list.append("CL")
                # insert_score(score=score, star_rating=star_rating, mods=mod_list)
                score_executor.submit(insert_score, score, star_rating, mod_list)
            except Exception as e:
                print(f"!!!!!!!!!!!!error: {e}")
            if api_cd_needed:
                time.sleep(SLEEP_DELAY)
        status += 1
        print(f"{status}/{len(maps)}")
        time.sleep(SLEEP_DELAY)
    score_executor.shutdown()


def set_client():
    """
    Gets input from the user to set client_id, client_secret, and user_id to use for the current run and record it for later runs

    Parameters:
        None

    Returns:
        None
    """
    f = open(DATA_PATH, "w")
    global client_id, client_secret, user_id, api
    valid_input = False
    while not valid_input:
        client_id = input("Please enter your osu! OAuth client id: ")
        client_secret = input("Please enter the same osu! OAuth client's secret key: ")
        try:
            # Attempt to establish an api connection, if it works then the credentials were probably valid
            api = Ossapi(client_id=client_id, client_secret=client_secret)
            correct_user = False
            while not correct_user:
                user = input("Please enter either your username or user id: ")
                try:
                    # Mainly do this to double check the API is working correctly, and it's nice to have a safe guard just in case the user mistypes their username
                    user_info = api.user(user=user)
                    username = user_info.username
                    temp_user_id = user_info.id
                    response = ""
                    # Literally only did this bc someone (me) would probably spam Yes or No instead of y or n
                    while response not in ["y", "n"]:
                        response = (
                            input(
                                f"To confirm you are {username} with the user id of {temp_user_id}? [y/n]: "
                            )
                            .strip()
                            .lower()
                        )
                        if response not in ["y", "n"]:
                            print(
                                'Invalid response! (only valid responses are "y" and "n")'
                            )
                    if response == "y":
                        valid_input = True
                        correct_user = True
                        user_id = temp_user_id
                        break
                except Exception as e:
                    # There is a chance that this exception goes off cus the API poopied itself but surely that never happens
                    print(f"Error: {e}")
                    print(
                        f"{"Make sure you entered the username or user id correctly!" if api else "A valid user id was entered."}"
                    )
        except Exception as e:
            # I... Have no clue why I made the exception above and this an if else statement... oh well
            print(f"Error: {e}")
            print(
                f"{"Client id and secret key are both working!" if api else "Either the client id or secret key were incorrect or not working for some reason."}"
            )

    data_dict = {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_id": user_id,
    }
    json.dump(data_dict, f)
    f.close()
    print(f"Will dump {username}'s score data...")


def get_client():
    """
    Reads DATA_PATH to check if the user already inputted their data from a previous run and sets client_id, client_secret, and user_id from the json stored in DATA_PATH. Or if something is wrong with the json data (or no data is found), runs set_client() to ask the user for the data

    Parameters:
        None

    Returns:
        None
    """
    print("Attempting to get client")
    # Checking if the data exists
    if os.path.exists(DATA_PATH):
        f = open(DATA_PATH, "r")
        try:
            data = json.load(f)
        except Exception as e:
            # Something's messed up with the json, probably empty bc it was created but not written to
            print(f"ERROR: {e}")
            print(
                "Likely that setup was not completed successfully or somehow the json file got corrupted, so please re-enter your info."
            )
            f.close()
            set_client()
            return
        if (
            not data
            or "client_id" not in data
            or "client_secret" not in data
            or "user_id" not in data
        ):
            # there was a good json but didn't have the data we needed
            f.close()
            set_client()
            return
        else:
            global client_id, api, client_secret, user_id
            client_id = data["client_id"]
            client_secret = data["client_secret"]
            user_id = data["user_id"]
            try:
                # Verifying that everything works before we start
                api = Ossapi(client_id=client_id, client_secret=client_secret)
                username = api.user(user=user_id).username
                # Doing this as a way to change the person who you want to dump... and also reminded me to add the user id to the score just in case if someone wants multiple user's dumps in their database
                response = ""
                while response not in ["y", "n"]:
                    response = (
                        input(f"Do you want to dump {username}'s scores? [y/n]: ")
                        .strip()
                        .lower()
                    )
                    if response not in ["y", "n"]:
                        print(
                            'Invalid response! (only valid responses are "y" and "n")'
                        )
                if response == "n":
                    set_client()
                    return
                print(f"Will dump {username}'s score data...")
            except Exception as e:
                # This should never really happen unless the user manually fudged something up or the API is down
                print(f"ERROR: {e}")
                print(
                    "Something went wrong, please look at the error message above and verify that its due to the data and not the osu!API shitting itself.\nIf osu!API is shitting itself then please kill the program now, as it will ask you to re-enter your data."
                )
                set_client()
                return
    else:
        set_client()
        return


def dump_scores():
    """
    Records times and gets all maps and user scores and records them in the database

    Parameters:
        None

    Returns:
        None
    """
    get_client()
    start_time = time.time()
    print("Getting maps...")
    get_maps()
    mid_time = time.time()
    print(f"Completed getting all maps in {mid_time - start_time}s!\nGetting scores...")
    get_scores()
    final_time = time.time()
    print(
        f"Completed getting all scores in {final_time - mid_time}s!\nCompleted all tasks in {final_time - start_time}s!!!"
    )
