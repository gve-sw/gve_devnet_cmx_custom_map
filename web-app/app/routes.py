#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2022 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2022 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


from distinctipy import distinctipy
from flask import render_template, request, session, flash, redirect, url_for
from collections import defaultdict
from passlib.hash import sha256_crypt
from app import app
from DETAILS import *
from functools import wraps
import datetime
import logging.handlers
import logging
import pprint
import requests
import json
import simplejson
import re

pp = pprint.PrettyPrinter(indent=2)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
base_handler = logging.handlers.RotatingFileHandler('app.log', mode='a', maxBytes=10000000, backupCount=999)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
base_handler.setFormatter(formatter)
base_logger = logging.getLogger('')
base_logger.setLevel(logging.DEBUG)
base_logger.addHandler(base_handler)

# Logger maker
def setup_logger(name, file, level=logging.DEBUG):
    handler = logging.handlers.RotatingFileHandler(file, mode='a', maxBytes=10000000, backupCount=999)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

rbac = setup_logger('rbac', 'rbac.log', level=logging.INFO)
search_log = setup_logger('search_log', 'search.log', level=logging.INFO)


if LOCAL_JSON:
    with open('file.json', 'r') as file:
        data = file.read()
        local_json = simplejson.loads(data)
        # pp.pprint(local_json[0])
with open('groups.json', 'r') as file:
    data = file.read()
    groups_json = simplejson.loads(data)
    # pp.pprint(local_json[0])
with open('names.json', 'r') as file:
    data = file.read()
    names_json = simplejson.loads(data)
    # pp.pprint(local_json[0])
with open('users.json', 'r') as file:
    data = file.read()
    users_json = simplejson.loads(data)
    # pp.pprint(local_json[0])


# access
def restricted():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'logged_in' in session:
                return func(*args, **kwargs)
            else:
                flash('You need to login first')
                return redirect(url_for('login'))

        return wrapper
    return decorator


@app.template_filter()
def regex_replace(s):
    """Replace only with alphanumeric"""
    return str(re.sub(r'\W+', '', s))


@app.template_filter()
def name_check(s):
    """Replace only with caps and no colons"""
    return str(re.sub(r'\W+', '', s.upper()))


class CMX:
    def __init__(self, username, password, url):
        """
        Initiate CMX connector object
        Uses config information to log in the user and perform API the api request

        Parameters
        ----------
            username : str
                CMX Username
            password : str
                CMX Password
            url : str
                CMX URL
        """
        self.cmx_url = f"https://{url}"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.auth = requests.auth.HTTPBasicAuth(username,password)

    def basic_get_call(self, endpoint):
        get_url = f"{self.cmx_url}/api/{endpoint}"
        print(get_url)
        received = requests.request('GET', get_url, headers=self.headers, verify=False, auth=self.auth)
        return received

    def get_active_clients(self):
        endpoint = "location/v1/clients"
        return self.basic_get_call(endpoint).json()


cmx = CMX(CMX_USERNAME, CMX_PASSWORD, CMX_URL)


# Mode Selection
# @app.route('/map/<map_id>', methods=['GET', 'POST'])
# def data(map_id):
@app.route('/', methods=['GET', 'POST'])
@restricted()
def data():
    now = datetime.datetime.utcnow().toordinal()
    start_date = datetime.datetime.combine(datetime.date.today().replace(day=1), datetime.datetime.min.time())
    end_date = datetime.datetime.combine(datetime.date(datetime.datetime.now().year + (datetime.datetime.now().month == 12),
                (datetime.datetime.now().month + 1 if datetime.datetime.now().month < 12 else 1), 1) - datetime.timedelta(1), datetime.datetime.max.time())
    endpoint_data = []
    rgb_colours = []
    colours = {}

    if LOCAL_JSON:
        endpoint_data = local_json
    else:
        endpoint_data = cmx.get_active_clients()


    # groups = [
    #     "Computer",
    #     "Printer"
    # ]
    macs = sorted([entry["macAddress"] for entry in endpoint_data], key=str.lower)
    groups = groups_json.keys()
    manufacturers = sorted(set([entry["manufacturer"] for entry in endpoint_data if entry["manufacturer"]]),
                           key=str.lower)
    N = len(manufacturers) + 1
    gen_colours = distinctipy.get_colors(N)
    for (r, g, b) in gen_colours:
        rgb_colours.append({
            "r": int(r*255),
            "g": int(g*255),
            "b": int(b*255)
        })
    i = 0
    for manufacturer in manufacturers:
        # pp.pprint(manufacturer)
        colours[regex_replace(manufacturer)] = rgb_colours[i]
        i += 1
    colours["None"] = rgb_colours[i]
    # pp.pprint(colours)
    temp = []
    for device in endpoint_data:
        try:
            device['name'] = names_json[name_check(device["macAddress"])]['Device Number']
        except:
            device['name'] = ""
        temp.append(device)
    endpoint_data = temp
    names = sorted([entry["name"] for entry in endpoint_data if entry['name']], key=str.lower)
    if request.method == 'POST':
        data = request.form.to_dict()
        data.pop('_csrf_token')
        search_log.info(f'{session["USERNAME"]} searched for {data}')
        if data['mac']:
            temp_macs = data['mac'].split(',')
            endpoint_data = [entry for entry in endpoint_data if any(addr in entry['macAddress'] for addr in temp_macs)]
        else:
            if data['name']:
                temp_names = data['name'].split(',')
                endpoint_data = [entry for entry in endpoint_data if any(addr in entry['name'] for addr in temp_names)]
            else:
                if data['manufacturer'] == "All":
                    endpoint_data = endpoint_data
                elif data['manufacturer'] == "None":
                    endpoint_data = [entry for entry in endpoint_data if entry['manufacturer'] is None]
                else:
                    endpoint_data = [entry for entry in endpoint_data if entry['manufacturer'] == data['manufacturer']]
    else:
        rbac.info(f'{session["USERNAME"]} opened the website')
    # pp.pprint(names)
    return render_template('data.html', title='Endpoint Locator',
                           entries=endpoint_data, start_date=start_date.date(), end_date=end_date.date(),
                           dateString=DATESTRING, groups=groups, manufacturers=manufacturers, macs=macs,
                           colours=colours, names=names)


# Login Selection
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', title='Sign In')
    elif request.method == 'POST':
        details = request.form
        logging.debug(details)
        users = users_json
        for user in users:
            if user['username'] == details['username']:
                password = sha256_crypt.encrypt(details['password'])
                # if user['password'] == details['password']:
                if sha256_crypt.verify(details['password'], user['password']):
                    rbac.info(f"{details['username']} logged in")
                    session['USERNAME'] = user['username']
                    session['logged_in'] = True
                    return redirect(url_for('data'))
                else:
                    pass
            else:
                pass
        return "Invalid credentials!", 404


# Logout Selection
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))
