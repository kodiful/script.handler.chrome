# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse, urllib
import sys

from resources.lib.browser import Browser
from resources.lib.cache import Cache
from resources.lib.common import log, notify

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    addon = xbmcaddon.Addon()
    executable_path = addon.getSetting('chrome')
    if executable_path:
        # 引数
        args = urlparse.parse_qs(sys.argv[2][1:])
        action = args.get('action', None)
        url = args.get('url', None)
        xpath = args.get('xpath', ['//body'])
        mode = args.get('mode', [Browser.MODE_DRILLDOWN])
        file = args.get('file', None)
        # actionに応じて処理
        if action is None:
            # キャッシュをクリア
            Cache().clear()
            # スタート画面
            for url in ['https://www.yahoo.co.jp/','https://www.google.co.jp/','http://kodiful.com/']:
                item = xbmcgui.ListItem(url)
                values = {'action':'traverse', 'url':url, 'xpath':xpath[0], 'mode':mode[0]}
                query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
            xbmcplugin.endOfDirectory(int(sys.argv[1]), True)
        elif action[0] == 'traverse':
            Browser(executable_path).load(url=url[0], xpath=xpath[0], mode=mode[0])
        elif action[0] == 'capture':
            Browser(executable_path).load(url=url[0], xpath=xpath[0], mode=Browser.MODE_CAPTURE)
        elif action[0] == 'showcapture':
            xbmc.executebuiltin('ShowPicture(%s)' % file[0])
    else:
        addon.openSettings()
