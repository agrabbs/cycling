'''
    File name: kudos.py
    Author: Andrew Grabbs
    Date created: 4/5/2021
    Date last modified: 8/2/2021
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

USER = raw_input("Strava Email: ")
PASS = getpass()
BASE = 'https://www.strava.com'

class strava(object):
  def __init__(self):
    print(datetime.datetime.now())
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
    while len(self.activities) > 0:
      for x in self.activities:
        # Give Kudos
        self.give_kudos(x)
      self.get_activities()

  # Refresh List
  def get_activities(self):
    r = self.s.get('{}/dashboard/feed?feed_type=following&athlete_id={}&before={}&cursor={}'.format(BASE, self.athlete_id, self.cursors['before'], self.cursors['cursor']))
    self.get_cursors(r.text)
    match = [json.loads(html.unescape(x))['activity'] for x in re.findall('data-react-class="Activity" data-react-props="(.*?)"', r.text)]
    self.activities = [x['id'] for x in match if x['kudosAndComments']['canKudo'] == True and x['kudosAndComments']['hasKudoed'] == False]

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
    match = [json.loads(html.unescape(x)) for x in re.findall('data-react-class="Activity" data-react-props="(.*?)"', data)]
    if match is not None:
      self.cursors['before'] = match[0]['cursorData']['updated_at']
      self.cursors['cursor'] = match[len(match)-1]['cursorData']['updated_at']
      return True
    else:
      self.cursors['before'] = None
      self.cursors['cursor'] = None
      return False
    print(f'Got Cursors! {self.cursors}')

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
      match = re.search('currentAthleteId =\s+(.*?);', r.text)
      if match is not None:
        self.athlete_id = match.group(1)
      else:
        print('Error logging in. Exited.')
        sys.exit()

      # Get Initial Activities
      self.get_cursors(r.text)
      match = [json.loads(html.unescape(x))['activity'] for x in re.findall('data-react-class="Activity" data-react-props="(.*?)"', r.text)]
      self.activities = [x['id'] for x in match if x['kudosAndComments']['canKudo'] == True and x['kudosAndComments']['hasKudoed'] == False]

    else:
      print('Error! Unable to get CSRF Token.')
      sys.exit()

if __name__ == '__main__':
  strava = strava()
