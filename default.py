# -*- coding: utf-8 -*-

import urlparse, urllib
import sys, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from datetime import datetime
from resources.lib.common import log, notify

# import selenium
ADDON = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#-------------------------------------------------------------------------------
class Browser:

    def __init__(self):
        self.driver = None
        self.cache_path = ''
        # ウェブドライバを設定
        executable_path = ADDON.getSetting('chrome')
        if executable_path:
            # オプション設定
            chrome_options = Options()
            chrome_options.add_argument('headless')
            chrome_options.add_argument('disable-gpu')
            chrome_options.add_argument('window-size=1152,648')
            #extension_path = '/Users/uchiyama/Library/Application Support/Google/Chrome/Default/Extensions/ophjlpahpchlmihnnnihgmmeilfjmjjc/2.1.3_0.crx'
            #chrome_options.add_extension(extension_path)
            self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
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

    def kodify_page(self, url):
        # ページ読み込み
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
            path = os.path.join(self.cache_path, '%s.png' % datetime.now().strftime('%s'))
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

    def line_login(self):
        # ページ読み込み
        self.driver.implicitly_wait(10)
        self.driver.get('chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html')
        # メールアドレス
        email = self.driver.find_element_by_id('line_login_email')
        email.send_keys('uchiyama@mac.com')
        # パスワード
        pwd = self.driver.find_element_by_id('line_login_pwd')
        pwd.send_keys('57577sss')
        # ログイン
        btn = self.driver.find_element_by_id('login_btn')
        btn.click()
        # 本人確認コード
        code = self.driver.find_element_by_xpath("//div[@class='mdCMN01Code']").text
        notify('Enter %s' % code)
        # チャットリスト
        chat = self.driver.find_element_by_xpath("//li[@title='LINE Notify']")
        chat.click()

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    browser = Browser()
    if browser.driver:
        args = urlparse.parse_qs(sys.argv[2][1:])
        url = args.get('url', None)
        if url:
            browser.kodify_page(url[0])
        else:
            browser.clear_cache()
            browser.kodify_page('https://www.yahoo.co.jp/')
            #browser.line_login()
    else:
        ADDON.openSettings()
