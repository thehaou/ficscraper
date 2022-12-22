import os.path
import unittest

import configparser
import requests
from bs4 import BeautifulSoup

from scrapers.ao3 import constants
from scrapers.ao3.utils_requests import read_credentials
from sqlite.constants import ROOT_DIR


class AO3ConnectionTest(unittest.TestCase):
    def testCredentialsFileExists(self):
        self.assertTrue(os.path.exists(ROOT_DIR + '/SETUP.INI'),
                        msg='Please make a copy of SETUP.INI_TEMPLATE called SETUP.INI.')

    def testReadCredentials(self):
        username, password = read_credentials()
        self.assertNotEqual(username, 'your_username_here',
                            msg='Please replace the username field in SETUP.INI with your username.')
        self.assertNotEqual(password, 'your_password_here',
                            msg='Please replace the password field in SETUP.INI with your password.')

    def testLogin(self):
        username, password = read_credentials()
        homepage_url = constants.homepage_url
        login_url = constants.login_url

        sess = requests.Session()
        req = sess.get(homepage_url)
        soup = BeautifulSoup(req.text, features='html.parser')

        authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']

        req = sess.post(login_url, params={
            'authenticity_token': authenticity_token,  # csrf token
            'user[login]': username,
            'user[password]': password,
            'commit': 'Log in'
        })

        login_fail = 'Please try again' in req.text
        self.assertFalse(login_fail,
                         msg='Please check that you can log into AO3 on browser right now '
                             'with the credentials you provided.')
