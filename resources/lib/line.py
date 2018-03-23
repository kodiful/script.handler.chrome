# -*- coding: utf-8 -*-

import sys, os
import datetime, re
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from common import log, notify

# import selenium
ADDON = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# settings
extension_path = '/Users/uchiyama/Library/Application Support/Google/Chrome/Default/Extensions/ophjlpahpchlmihnnnihgmmeilfjmjjc/2.1.3_0.crx'
appid = 'ophjlpahpchlmihnnnihgmmeilfjmjjc'
email = 'uchiyama@mac.com'
password = '57577sss'
#talkroom = 'LINE Notify'
talkroom = 'ウッチー'

class Line:

    def __init__(self, executable_path):
        # ウェブドライバを設定
        chrome_options = Options()
        chrome_options.add_extension(extension_path)
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)

    def load(self):
        # ページ読み込み
        self.driver.implicitly_wait(60)
        self.driver.get('chrome-extension://%s/index.html' % appid)
        # メールアドレス
        elem = self.driver.find_element_by_id('line_login_email')
        elem.send_keys(email)
        # パスワード
        elem = self.driver.find_element_by_id('line_login_pwd')
        elem.send_keys(password)
        # ログイン
        elem = self.driver.find_element_by_id('login_btn')
        elem.click()
        # 本人確認コード
        elem = self.driver.find_element_by_xpath("//div[@class='mdCMN01Code']")
        notify('Enter %s' % elem.text)
        # トークルーム
        elem = self.driver.find_element_by_xpath("//li[@title='%s']" % talkroom)
        elem.click()
        # メッセージ検索
        self.search()

    def search(self):
        # メッセージ
        elems = self.driver.find_elements_by_xpath("//div[@class='mdRGT07Msg mdRGT07Text' or @class='MdRGT10Notice mdRGT07Other mdRGT10Date']")
        for elem in elems:
            date = elem.get_attribute('data-local-id')
            if date:
                d = datetime.datetime.fromtimestamp(int(date)/1000)
            else:
                # メッセージ
                elem1 = elem.find_element_by_xpath(".//span[@class='mdRGT07MsgTextInner']")
                msg = elem1.text.replace('\n', ' ')
                # 時刻
                elem1 = elem.find_element_by_xpath(".//p[@class='mdRGT07Date']")
                match = re.match(r'(AM|PM) (1?[0-9])\:([0-9][0-9])', elem1.text)
                hour = int(match.group(2))
                minute = int(match.group(3))
                if match.group(1) == 'PM': hour += 12
                log('%04d-%02d-%02d %02d:%02d %s' % (d.year,d.month,d.day,hour,minute,msg))
