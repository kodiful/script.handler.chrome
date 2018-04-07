# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse, urllib
import sys

from resources.lib.browser import Browser
from resources.lib.cache import Cache
from resources.lib.start import Start
from resources.lib.common import log, notify

#-------------------------------------------------------------------------------
class Settings:

    def __init__(self, keys):
        self.addon = xbmcaddon.Addon()
        self.data = {}
        for key in keys:
            self.data[key] = self.addon.getSetting(key)

    def clear(self):
        for key in self.data.keys():
            self.addon.setSetting(key, '')
        return self.data

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
        # アドオン設定
        settings = Settings(('url1','xpath1','url','label','xpath','mode')).clear()
        # actionに応じて処理
        if action is None:
            # キャッシュをクリア
            Cache().clear()
            # スタート画面を表示
            Start().show(executable_path)
        elif action == 'traverse':
            Browser(executable_path).load(url=url, xpath=xpath, mode=mode)
        elif action == 'capture':
            Browser(executable_path).load(url=url, xpath=xpath, mode=Browser.MODE_CAPTURE)
        elif action == 'showcapture':
            xbmc.executebuiltin('ShowPicture(%s)' % file)
        elif action == 'append':
            Start().append(label, url, xpath, mode)
        elif action == 'edit':
            Start().edit(label, url, xpath, mode)
        elif action == 'edited':
            Start().edited(settings)
        elif action == 'delete':
            Start().delete(url, xpath)
    else:
        addon.openSettings()
