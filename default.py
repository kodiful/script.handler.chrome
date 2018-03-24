# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse
import sys

from resources.lib.browser import Browser
from resources.lib.line import Line
from resources.lib.common import log, notify

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    addon = xbmcaddon.Addon()
    executable_path = addon.getSetting('chrome')
    if executable_path:
        # 引数
        args = urlparse.parse_qs(sys.argv[2][1:])
        url = args.get('url', [''])
        # ブラウザ
        #browser = Browser(executable_path)
        #browser.load(url[0] or 'https://www.yahoo.co.jp/')
        # LINE
        line = Line(executable_path)
        line.start()
    else:
        ADDON.openSettings()
