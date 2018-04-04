# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse, urllib
import sys

from resources.lib.browser import Browser
from resources.lib.common import log, notify

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    addon = xbmcaddon.Addon()
    executable_path = addon.getSetting('chrome')
    if executable_path:
        args = urlparse.parse_qs(sys.argv[2][1:])
        url = args.get('url', ['https://www.yahoo.co.jp/'])
        xpath = args.get('xpath', None)
        action = args.get('action', None)
        if action:
            if action[0] == 'traverse':
                if xpath:
                    values = {'url':url[0], 'xpath':xpath[0]}
                else:
                    values = {'url':url[0]}
                postdata = urllib.urlencode(values)
                xbmc.executebuiltin('Container.Update(%s?%s)' % (sys.argv[0], postdata))
        else:
            if xpath:
                Browser(executable_path).load(url[0], xpath[0])
            else:
                Browser(executable_path).load(url[0])
    else:
        addon.openSettings()
