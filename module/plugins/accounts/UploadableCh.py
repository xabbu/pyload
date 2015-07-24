# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account


class UploadableCh(Account):
    __name__    = "UploadableCh"
    __type__    = "account"
    __version__ = "0.05"
    __status__  = "testing"

    __description__ = """Uploadable.ch account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Sasch", "gsasch@gmail.com")]


    def load_account_info(self, user, req):
        html = self.load("http://www.uploadable.ch/login.php")

        premium     = '<a href="/logout.php"' in html
        trafficleft = -1 if premium else None

        return {'validuntil': None, 'trafficleft': trafficleft, 'premium': premium}  #@TODO: validuntil


    def login(self, user, data, req):
        html = self.load("http://www.uploadable.ch/login.php",
                         post={'userName'     : user,
                               'userPassword' : data['password'],
                               'autoLogin'    : "1",
                               'action__login': "normalLogin"})

        if "Login failed" in html:
            self.wrong_password()
