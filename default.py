# -*- coding: utf-8 -*-

import urlparse, urllib
import sys, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from resources.lib.common import log, notify

# import selenium
addon = xbmcaddon.Addon()
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
sys.path.append(os.path.join(addon_path, 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver

#-------------------------------------------------------------------------------
def main():
    # アドオン設定を確認
    browser = addon.getSetting('browser')
    if browser == 'Chrome':
        path = addon.getSetting('chrome')
        if path:
            driver = webdriver.Chrome(path)
        else:
            driver = webdriver.Chrome()
    elif browser == 'Safari':
        driver = webdriver.Safari()
    else:
        addon.openSettings()
        return

    # パラメータ抽出
    args = urlparse.parse_qs(sys.argv[2][1:])
    action = args.get('action', None)

    if action is None:
        url = 'https://www.yahoo.co.jp/'
        filepath = '/tmp/selenium.png'

        driver.maximize_window()
        driver.get(url)
        driver.save_screenshot(filepath)
        xbmc.executebuiltin('ShowPicture(%s)' % filepath)
    elif action[0] == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % addon.getAddonInfo('id'))

#-------------------------------------------------------------------------------
if __name__  == '__main__': main()
