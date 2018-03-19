# -*- coding: utf-8 -*-

import urlparse, urllib
import sys, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from resources.lib.common import log, notify

# import selenium
addon = xbmcaddon.Addon()
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
sys.path.append(os.path.join(addon_path, 'resources', 'lib', 'selenium-3.11.0'))
from selenium import webdriver

#-------------------------------------------------------------------------------
def main():
    # アドオン設定を確認
    path = addon.getSetting('chrome')
    if path:
        driver = webdriver.Chrome(path)
    else:
        addon.openSettings()
        return

    # パラメータ抽出
    args = urlparse.parse_qs(sys.argv[2][1:])
    action = args.get('action', None)

    if action is None:
        driver.get('https://www.yahoo.co.jp/')
        #text = driver.find_element_by_id("srchAssistTxt").text
        text = driver.title
        log(text)
        notify(text)
    elif action[0] == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % addon.getAddonInfo('id'))

#-------------------------------------------------------------------------------
if __name__  == '__main__': main()
