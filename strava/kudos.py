'''
    File name: kudos.py
    Author: Andrew Grabbs
    Date created: 4/5/2021
    Date last modified: 4/5/2021
    Python Version: 2.7+
'''

import requests
import time
import sys
import re
from getpass import getpass

USER = raw_input("Strava Email: ")
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
    while len(self.activities) > 0:
      for x in self.activities:
        # Give Kudos
        self.give_kudos(x)
      self.get_activities()


  # Refresh List
  def get_activities(self):
    r = self.s.get('{}/dashboard/feed?feed_type=following&athlete_id={}&before={}&cursor={}'.format(BASE, self.athlete_id, self.cursors['before'], self.cursors['cursor']))
    self.get_cursors(r.content)
    self.activities = re.findall('js-add-kudo\' data-entry=\'\[&quot;Activity&quot;,(.*?)\]', r.content)

  # Sending Kudos
  def give_kudos(self, activity):
    payload = {}
    r = self.s.post('{}/feed/activity/{}/kudo'.format(BASE, activity), data = payload, headers = { 'x-csrf-token': self.payload['authenticity_token'] })
    print(r.content)
    if r.content == '{"success":"true"}':
      print('Gave {} Kudos!'.format(activity))
      return True
    else:
      print('Failed giving kudos to {}!'.format(activity))
      return False

  # Get Cursors
  def get_cursors(self, html):
    match = re.findall('data-rank=\'(.*?)\' data-updated-at=\'(.*?)\'', html)
    if match is not None:
      self.cursors['before'] = match[0][1]
      self.cursors['cursor'] = match[len(match)-1][0]
      return True
    else:
      self.cursors['before'] = None
      self.cursors['cursor'] = None
      return False

  # Login
  def auth(self):
    r = self.s.get('{}/login'.format(BASE))

    # Get CSRF Token
    match = re.search('csrf-token" content="(.*?)"', r.content)
    if match is not None:
      self.payload['authenticity_token'] = match.group(1)
      r = self.s.post('{}/session'.format(BASE), data = self.payload)
      match = re.search('Access to this account is temporarily suspended. Please try again later.', r.content)
      if match is not None:
        print('Whoops, we\'ve been temporarily suspended.') 
        sys.exit()

      # Get Athlete ID & Confirm Logged In
      match = re.search('currentAthleteId =\s+(.*?);', r.content)
      if match is not None:
        print('match is not None!')
        self.athlete_id = match.group(1)
      else:
        print('Error logging in. Exited.')
        sys.exit()

      # Get Initial Activities
      self.get_cursors(r.content)
      self.activities = re.findall('js-add-kudo\' data-entry=\'\[&quot;Activity&quot;,(.*?)\]', r.content)

    else:
      print('Error! Unable to get CSRF Token.')
      sys.exit()

if __name__ == '__main__':
  strava = strava()
