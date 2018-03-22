# -*- coding: utf-8 -*-

import sys, os, urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from datetime import datetime
from cache import Cache
from common import log, notify

# import selenium
ADDON = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Browser:

    def __init__(self, executable_path):
        # ウェブドライバを設定
        chrome_options = Options()
        chrome_options.add_argument('headless')
        chrome_options.add_argument('disable-gpu')
        chrome_options.add_argument('window-size=1152,648')
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        # キャッシュディレクトリを作成
        self.cache = Cache()

    def load(self, url):
        # ページ読み込み
        self.driver.implicitly_wait(10)
        self.driver.get(url)
        # ページの左上までスクロール
        self.driver.execute_script("window.scrollTo(0, 0);")
        # ページサイズ取得
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        total_width = self.driver.execute_script("return document.body.scrollWidth")
        # 画面サイズ取得
        view_width = self.driver.execute_script("return window.innerWidth")
        view_height = self.driver.execute_script("return window.innerHeight")
        # ページを画面サイズに分割
        self.sections = []
        for pos in range(0,total_height/view_height+1):
            self.sections.append({'name':'', 'image':'', 'context_menu':[]})
        # リンクの処理
        for a in self.driver.find_elements_by_tag_name("a"):
            text = a.text or a.get_attribute('title') or a.get_attribute('alt') or ''
            text = text.replace('\n',' ')
            href = a.get_attribute('href')
            pos = int(a.location['y'])/view_height
            if len(text)>0 and href and href.find('http')==0 and pos<len(self.sections):
                query = 'XBMC.Container.Update(%s?action=browse&url=%s)' % (sys.argv[0],urllib.quote_plus(href))
                self.sections[pos]['context_menu'].append((text,query))
        # スクロールの処理
        for scroll_height in range(0,total_height,view_height):
            self.driver.execute_script("window.scrollTo(0, %d)" % (scroll_height))
            xbmc.sleep(1000)
            path = os.path.join(self.cache.path, '%s.png' % datetime.now().strftime('%s'))
            pos = scroll_height/view_height
            self.sections[pos]['name'] = '%s [%d]' % (self.driver.title, scroll_height)
            self.sections[pos]['image'] = path
            self.driver.get_screenshot_as_file(path)
        # 終了
        self.driver.close()
        # メニュー生成
    	for section in self.sections:
            image_path = section['image']
            item = xbmcgui.ListItem(section['name'], iconImage=image_path, thumbnailImage=image_path)
            item.addContextMenuItems(section['context_menu'], replaceItems=True)
    	    xbmcplugin.addDirectoryItem(int(sys.argv[1]), image_path, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)
