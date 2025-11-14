## Overview
This is a simple terminal based Python script that dumps all of a user's osu! scores recorded on bancho into a sqlite database. 

## Requirements:
- an osu! Account
- Python 3.12.12
- ossapi 5.3.3

## How To Use:
1. Make sure you have all the requirements setup
2. Run main.py (google it or gpt it)
2. Enter in your osu! OAuth credentials
    - To get your osu! OAuth credentials go to your settings page on osu! scroll down to OAuth ([or click here](https://osu.ppy.sh/home/account/edit#oauth)) and click "New OAuth Application"
    - Name it whatever you want then click "Register application" (don't worry about the callback URLs)
    - When the application asks you for your client id copy the "Client ID" key
    - When the application asks you for your client secret click "Show client secret" and copy and the "Client Secret" key
3. Enter either your username or osu! user id (the numbers in your profile url after the "/user/")
4. Wait
    - If you want to get a little dangerous you can go into "dump_scores.py" and find all the "sleep()" calls and reduce the time it takes so the application runs faster at your own risk, don't blame me if the API blacklists you are something 
5. Profit (idk have fun with your data)

## Limitations
This script will not track the following:
- Scores using Lazer exclusive mods
- Scores using Lazer mod settings (ex: rate change)
- Maps without score submission
    - Graveyard maps, unsubmitted maps, pending maps, loved maps with leaderboard submission disabled, etc.
