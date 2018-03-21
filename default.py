# -*- coding: utf-8 -*-

import urlparse, urllib
import sys, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from resources.lib.common import log, notify

# import selenium
ADDON = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver

#-------------------------------------------------------------------------------
class Browser:

    def __init__(self):
        self.driver = None
        self.cache_path = ''
        # ウェブドライバ
        if ADDON.getSetting('browser') == 'Chrome':
            path = ADDON.getSetting('chrome')
            if path:
                self.driver = webdriver.Chrome(executable_path=path)
            else:
                self.driver = webdriver.Chrome()
        elif ADDON.getSetting('browser') == 'Safari':
            self.driver = webdriver.Safari()
        # キャッシュ
        self.create_cache()

    def create_cache(self):
        # キャッシュディレクトリを作成
        self.cache_path = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), 'cache')
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)

    def clear_cache(self):
        # キャッシュディレクトリをクリア
        file_list = os.listdir(self.cache_path)
        for file_path in file_list:
            os.remove(os.path.join(self.cache_path, file_path))

    def capture_page(self, url):
        # ページ読み込み
        self.driver.maximize_window()
        self.driver.get(url)
        self.sections = []
        # ページの左上までスクロール
        self.driver.execute_script("window.scrollTo(0, 0);")
        # ページサイズ取得
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        total_width = self.driver.execute_script("return document.body.scrollWidth")
        # 画面サイズ取得
        view_width = self.driver.execute_script("return window.innerWidth")
        view_height = self.driver.execute_script("return window.innerHeight")
        # スクロールの処理
        scroll_height = 0
        while scroll_height < total_height:
            self.driver.execute_script("window.scrollTo(0, %d)" % (scroll_height))
            file_path = os.path.join(self.cache_path, '%05d.png' % (scroll_height))
            self.sections.append({'name':scroll_height, 'image':file_path, 'context_menu':[]})
            self.driver.get_screenshot_as_file(file_path)
            scroll_height += view_height
        # リンクの処理
        for a in self.driver.find_elements_by_tag_name("a"):
            text = a.text or a.get_attribute('title') or a.get_attribute('alt')
            href = a.get_attribute('href')
            pos = int(a.location['y'])/view_height
            if len(text)>0 and href.find('http')==0 and pos<len(sections):
                query = 'XBMC.Container.Update(%s?action=browse&url=%s)' % (sys.argv[0],urllib.quote_plus(href))
                self.sections[pos]['context_menu'].append((text,query))

    def create_menu(self, url):
        self.capture_page(url)
    	for section in self.sections:
            image_path = section['image']
            item = xbmcgui.ListItem('%05d' % section['name'], iconImage=image_path, thumbnailImage=image_path)
            item.addContextMenuItems(section['context_menu'], replaceItems=True)
            query = '%s?action=show&path=%s' % (sys.argv[0],urllib.quote_plus(image_path))
    	    xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

#-------------------------------------------------------------------------------
def main():
    # ブラウザ
    browser = Browser()
    if browser.driver is  None:
        addon.openSettings()
        return
    # パラメータ抽出
    args = urlparse.parse_qs(sys.argv[2][1:])
    action = args.get('action', None)
    url = args.get('url', None)
    path = args.get('path', None)
    # 処理
    if action is None:
        browser.create_menu('https://www.yahoo.co.jp/')
    elif action[0] == 'browse':
        browser.create_menu(url[0])
    elif action[0] == 'show':
        xbmc.executebuiltin('ShowPicture(%s)' % path[0])
    elif action[0] == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % addon.getAddonInfo('id'))

#-------------------------------------------------------------------------------
if __name__  == '__main__': main()
