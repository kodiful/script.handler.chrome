# -*- coding: utf-8 -*-

import urlparse, urllib
import sys, re
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from resources.lib.common import log, notify

#-------------------------------------------------------------------------------
def main():
    # アドオン設定を確認
    addon = xbmcaddon.Addon()
    browser = addon.getSetting('browser')
    if browser == 'Chrome':
        driver = addon.getSetting('chrome')
    elif browser == 'Firefox':
        driver = addon.getSetting('firefox')
    else:
        driver = None
    if browser and driver:
        pass
    else:
        addon.openSettings()
        return

    # パラメータ抽出
    args = urlparse.parse_qs(sys.argv[2][1:])
    action = args.get('action', None)

    if action is None:
        pass
    elif action[0] == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % addon.getAddonInfo('id'))

#-------------------------------------------------------------------------------
if __name__  == '__main__': main()
