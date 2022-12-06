'''
    File name: kudos.py
    Author: Andrew Grabbs
    Date created: 4/5/2021
    Date last modified: 4/26/2022
    Python Version: 3+
'''

import re
import os
import sys
import json
import time
import requests
import datetime
from getpass import getpass

USER = input("Strava Email: ")
PASS = getpass()
BASE = 'https://www.strava.com'

# Set Epoch to PST 
os.environ['TZ'] = 'US/Pacific'
time.tzset()

class strava(object):
  def __init__(self):
    self.athlete_id = None
    self.end_of_the_line = False
    self.activities = list()
    self.payload = {
        'utf8': u'\u2713',
        'plan': None,
        'authenticity_token': None,
        'email': USER,
        'password': PASS
    }
    self.cursors = {
      'before': None,
      'cursor': None
    }
    self.s = requests.Session()
    self.auth()
    print(datetime.datetime.now())
    while len(self.activities) > 0:
      for x in self.activities:
        # Give Kudos
        self.give_kudos(x)
      self.get_activities()
    print(datetime.datetime.now())

  # Refresh List
  def get_activities(self):
    r = self.s.get(f'{BASE}/dashboard/feed?feed_type=following&athlete_id={self.athlete_id}&before={self.cursors["before"]}&cursor={self.cursors["cursor"]}')
    self.get_cursors(r.text)
    match = [x for x in json.loads(r.text)['entries'] if x['entity'] in ['Activity', 'GroupActivity']]
    for x in match:
        if x['entity'] == 'Activity' and x['activity']['kudosAndComments']['canKudo'] == True and x['activity']['kudosAndComments']['hasKudoed'] == False:
            self.activities.append(x['activity']['id'])
        elif x['entity'] == 'GroupActivity':
            for k, v in x['kudosAndComments'].items():
                if v['canKudo'] == True and v['hasKudoed'] == False:
                    self.activities.append(k)
        else:
            print('uh oh')

  # Sending Kudos
  def give_kudos(self, activity):
    payload = {}
    r = self.s.post(f'{BASE}/feed/activity/{activity}/kudo', data = payload, headers = { 'x-csrf-token': self.payload['authenticity_token'] })
    if r.text == '{"success":"true"}':
      print(f'Gave {activity} Kudos!')
      return True
    else:
      print(r.text)
      print(f'Failed giving kudos to {activity}!')
      return False

  # Get Cursors
  def get_cursors(self, data):
    match = [x for x in json.loads(data)['entries'] if x['entity'] == 'Activity']
    if len(match) > 0:
      self.cursors['before'] = match[0]['cursorData']['updated_at']
      self.cursors['cursor'] = match[-1]['cursorData']['rank']
      return True
    else:
      print(match)
      self.cursors['before'] = None
      self.cursors['cursor'] = None
      return False

  # Login
  def auth(self):
    r = self.s.get('{}/login'.format(BASE))

    # Get CSRF Token
    match = re.search('csrf-token" content="(.*?)"', r.text)
    if match is not None:
      self.payload['authenticity_token'] = match.group(1)
      r = self.s.post('{}/session'.format(BASE), data = self.payload)
      match = re.search('Access to this account is temporarily suspended. Please try again later.', r.text)
      if match is not None:
        print('Whoops, we\'ve been temporarily suspended.')
        sys.exit()

      # Get Athlete ID & Confirm Logged In
      match = re.search('Strava.Models.CurrentAthlete\({"id":(.*?),', r.text)
      if match is not None:
        self.athlete_id = match.group(1)
      else:
        print('Error logging in. Exited.')
        sys.exit()

      # Get Pre-Fetched Activities
      self.cursors['before'] = time.time() - 259200
      self.cursors['cursor'] = time.time()
      self.get_activities()

    else:
      print('Error! Unable to get CSRF Token.')
      sys.exit()

if __name__ == '__main__':
  try:
    strava = strava()
  except Exception as e:
    print(f'ERROR: {e}`')
