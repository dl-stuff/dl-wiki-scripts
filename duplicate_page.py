#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    duplicate_page.py
    MediaWiki API
"""

import requests
import time
import io

S = requests.Session()
URL = "https://dragalialost.gamepedia.com/api.php"

# Retrieve login token first
PARAMS_0 = {
    'action': "query",
    'meta': "tokens",
    'type': "login",
    'format': "json"
}

R = S.get(url=URL, params=PARAMS_0)
DATA = R.json()

LOGIN_TOKEN = DATA['query']['tokens']['logintoken']

print(LOGIN_TOKEN)

PARAMS_1 = {
    'action': "login",
    'lgname': "BOT NAME",
    'lgpassword': "BOT PASSWORD",
    'lgtoken': LOGIN_TOKEN,
    'format': "json"
}

R = S.post(URL, data=PARAMS_1)
DATA = R.json()

print(DATA)

PARAMS_2 = {
    "action": "query",
    "meta": "tokens",
    "format": "json"
}

R = S.get(url=URL, params=PARAMS_2)
DATA = R.json()

CSRF_TOKEN = DATA['query']['tokens']['csrftoken']

queryPARAMS = {
    'action': "query",
    'prop': "revisions",
    'rvslots': "*",
    'rvprop': "content",
    'formatversion': "2",
    'format': "json"
}

editPARAMS = {
    'action': "edit",
    'summary': "Creating archived page",
    'token': CSRF_TOKEN,
    'bot': "1",
    'format': "json",
    'createonly': "1"
}


def archive_group(filepath, wikipath):
    with io.open(filepath, 'rt', encoding='utf8') as file:
        for line in file:
            old_title = line.replace("\n", "")
            queryPARAMS['titles'] = old_title
            print("Fetching ", old_title)
            json = S.get(url=URL, params=queryPARAMS)
            archive_data = json.json()
            pages = archive_data['query']["pages"]
            content = pages[0]['revisions'][0]['slots']['main']['content']
            new_title = wikipath.format(old_title)
            editPARAMS['title'] = new_title
            editPARAMS['text'] = content
            print("Posting ", new_title)
            json = S.post(URL, data=editPARAMS)
            archive_data = json.json()
            print(archive_data)
            time.sleep(5)


archive_group("C:/Users/Canim/Documents/Weapon List.txt", "Weapons/Archive/Version 1.23.1/{}")
archive_group("C:/Users/Canim/Documents/Wyrmprint List.txt", "Wyrmprints/Archive/Version 1.23.1/{}")

# Step 4: Send a POST request to logout
PARAMS_3 = {
    "action": "logout",
    "token": CSRF_TOKEN,
    "format": "json"
}

R = S.post(URL, data=PARAMS_3)
DATA = R.json()

print(DATA)
