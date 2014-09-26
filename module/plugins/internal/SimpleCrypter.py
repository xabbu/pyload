# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter
from module.plugins.internal.SimpleHoster import PluginParseError, replace_patterns, set_cookies
from module.utils import html_unescape


class SimpleCrypter(Crypter):
    __name__ = "SimpleCrypter"
    __type__ = "crypter"
    __version__ = "0.11"

    __pattern__ = None

    __description__ = """Simple decrypter plugin"""
    __author_name__ = ("stickell", "zoidberg", "Walter Purcaro")
    __author_mail__ = ("l.stickell@yahoo.it", "zoidberg@mujmail.cz", "vuolter@gmail.com")

    """
    Following patterns should be defined by each crypter:

      LINK_PATTERN: group(1) must be a download link or a regex to catch more links
        example: LINK_PATTERN = r'<div class="link"><a href="(http://speedload.org/\w+)'

      TITLE_PATTERN: (optional) The group defined by 'title' should be the folder name or the webpage title
        example: TITLE_PATTERN = r'<title>Files of: (?P<title>[^<]+) folder</title>'

      OFFLINE_PATTERN: (optional) Checks if the file is yet available online
        example: OFFLINE_PATTERN = r'File (deleted|not found)'

      TEMP_OFFLINE_PATTERN: (optional) Checks if the file is temporarily offline
        example: TEMP_OFFLINE_PATTERN = r'Server maintainance'


    You can override the getLinks method if you need a more sophisticated way to extract the links.


    If the links are splitted on multiple pages you can define the PAGES_PATTERN regex:

      PAGES_PATTERN: (optional) The group defined by 'pages' should be the number of overall pages containing the links
        example: PAGES_PATTERN = r'Pages: (?P<pages>\d+)'

    and its loadPage method:

      def loadPage(self, page_n):
          return the html of the page number page_n
    """


    URL_REPLACEMENTS = []

    SH_BROKEN_ENCODING = False  #: Set to True or encoding name if encoding in http header is not correct
    SH_COOKIES = True  #: or False or list of tuples [(domain, name, value)]

    LOGIN_ACCOUNT = False
    LOGIN_PREMIUM = False


    def setup(self):
        if isinstance(self.SH_COOKIES, list):
            set_cookies(self.req.cj, self.SH_COOKIES)


    def decrypt(self, pyfile):
        if self.LOGIN_ACCOUNT and not self.account:
            self.fail('Required account not found!')

        if self.LOGIN_PREMIUM and not self.premium:
            self.fail('Required premium account not found!')

        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)

        self.html = self.load(pyfile.url, decode=not self.SH_BROKEN_ENCODING, cookies=self.SH_COOKIES)

        self.checkOnline()

        package_name, folder_name = self.getPackageNameAndFolder()

        self.package_links = self.getLinks()

        if hasattr(self, 'PAGES_PATTERN') and hasattr(self, 'loadPage'):
            self.handleMultiPages()

        self.logDebug('Package has %d links' % len(self.package_links))

        if self.package_links:
            self.packages = [(package_name, self.package_links, folder_name)]
        else:
            self.fail('Could not extract any links')


    def getLinks(self):
        """
        Returns the links extracted from self.html
        You should override this only if it's impossible to extract links using only the LINK_PATTERN.
        """
        return re.findall(self.LINK_PATTERN, self.html)


    def checkOnline(self):
        if hasattr(self, "OFFLINE_PATTERN") and re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()
        elif hasattr(self, "TEMP_OFFLINE_PATTERN") and re.search(self.TEMP_OFFLINE_PATTERN, self.html):
            self.tempOffline()


    def getPackageNameAndFolder(self):
        if hasattr(self, 'TITLE_PATTERN'):
            m = re.search(self.TITLE_PATTERN, self.html)
            if m:
                name = folder = html_unescape(m.group('title').strip())
                self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
                return name, folder

        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder


    def handleMultiPages(self):
        pages = re.search(self.PAGES_PATTERN, self.html)
        if pages:
            pages = int(pages.group('pages'))
        else:
            pages = 1

        for p in xrange(2, pages + 1):
            self.html = self.loadPage(p)
            self.package_links += self.getLinks()


    def parseError(self, msg):
        raise PluginParseError(msg)
