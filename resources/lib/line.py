# -*- coding: utf-8 -*-

import sys, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from common import log, notify

# import selenium
ADDON = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Line:

    def __init__(self, executable_path):
        # ウェブドライバを設定
        chrome_options = Options()
        extension_path = '/Users/uchiyama/Library/Application Support/Google/Chrome/Default/Extensions/ophjlpahpchlmihnnnihgmmeilfjmjjc/2.1.3_0.crx'
        chrome_options.add_extension(extension_path)
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)

    def load(self):
        # ページ読み込み
        self.driver.implicitly_wait(60)
        self.driver.get('chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html')
        # メールアドレス
        elem = self.driver.find_element_by_id('line_login_email')
        elem.send_keys('uchiyama@mac.com')
        # パスワード
        elem = self.driver.find_element_by_id('line_login_pwd')
        elem.send_keys('57577sss')
        # ログイン
        elem = self.driver.find_element_by_id('login_btn')
        elem.click()
        # 本人確認コード
        elem = self.driver.find_element_by_xpath("//div[@class='mdCMN01Code']")
        notify('Enter %s' % elem.text)
        # チャットリスト
        elem = self.driver.find_element_by_xpath("//li[@title='LINE Notify']")
        elem.click()
