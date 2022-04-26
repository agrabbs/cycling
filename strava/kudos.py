'''
    File name: kudos.py
    Author: Andrew Grabbs
    Date created: 4/5/2021
    Date last modified: 4/26/2022
    Python Version: 3+
'''

import requests
import time
import datetime
import sys
import re
import html
import json
from getpass import getpass

USER = input("Strava Email: ")
PASS = getpass()
BASE = 'https://www.strava.com'

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
    r = self.s.get('{}/dashboard/feed?feed_type=following&athlete_id={}&before={}&cursor={}'.format(BASE, self.athlete_id, self.cursors['before'], self.cursors['cursor']))
    self.get_cursors(r.text)
    match = [x for x in json.loads(r.text)['entries'] if x['entity'] == 'Activity']
    self.activities = [x['activity']['id'] for x in match if x['activity']['kudosAndComments']['canKudo'] == True and x['activity']['kudosAndComments']['hasKudoed'] == False]

  # Sending Kudos
  def give_kudos(self, activity):
    payload = {}
    r = self.s.post('{}/feed/activity/{}/kudo'.format(BASE, activity), data = payload, headers = { 'x-csrf-token': self.payload['authenticity_token'] })
    if r.text == '{"success":"true"}':
      print('Gave {} Kudos!'.format(activity))
      return True
    else:
      print(r.text)
      print('Failed giving kudos to {}!'.format(activity))
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
      match = [x for x in json.loads(html.unescape(re.findall('data-react-class="FeedRouter" data-react-props="(.*?)"', r.text)[0]))['preFetchedEntries'] if x['entity'] == 'Activity']
      self.activities = [x['activity']['id'] for x in match if x['activity']['kudosAndComments']['canKudo'] == True and x['activity']['kudosAndComments']['hasKudoed'] == False]
      self.cursors['before'] = match[0]['cursorData']['updated_at']
      self.cursors['cursor'] = match[-1]['cursorData']['rank']

    else:
      print('Error! Unable to get CSRF Token.')
      sys.exit()

if __name__ == '__main__':
  strava = strava()
