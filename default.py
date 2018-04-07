# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse, urllib
import sys

from resources.lib.browser import Browser
from resources.lib.cache import Cache
from resources.lib.start import Start
from resources.lib.common import log, notify

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    addon = xbmcaddon.Addon()
    executable_path = addon.getSetting('chrome')
    if executable_path:
        # 引数
        args = urlparse.parse_qs(sys.argv[2][1:])
        action = args.get('action', [None])[0]
        label = args.get('label', [''])[0]
        url = args.get('url', [''])[0]
        xpath = args.get('xpath', [''])[0]
        mode = args.get('mode', [Browser.MODE_DRILLDOWN])[0]
        file = args.get('file', [''])[0]
        # actionに応じて処理
        if action is None:
            # キャッシュをクリア
            Cache().clear()
            # スタート画面を表示
            Start().show()
        elif action == 'traverse':
            Browser(executable_path).load(url=url, xpath=xpath, mode=mode)
        elif action == 'capture':
            Browser(executable_path).load(url=url, xpath=xpath, mode=Browser.MODE_CAPTURE)
        elif action == 'showcapture':
            xbmc.executebuiltin('ShowPicture(%s)' % file)
        elif action == 'editstart':
            Start().update()
        elif action == 'edititem':
            Start().edit(label, url, xpath, mode)
        elif action == 'deleteitem':
            Start().delete(url, xpath)
        # 設定画面をクリア
        '''addon.setSetting('url1', '')
        addon.setSetting('xpath1', '')
        addon.setSetting('url', 'http://')
        addon.setSetting('label', '')
        addon.setSetting('xpath', '')
        addon.setSetting('mode', '0')'''
    else:
        addon.openSettings()
