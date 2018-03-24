# -*- coding: utf-8 -*-

import sys, os
import datetime, re, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from common import log, notify
from datelabel import datelabel

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
talkroom = 'ウッチー'

class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

    def onSettingsChanged(self):
        log('settings changed')

    def onScreensaverActivated(self):
        log('screensaver activated')

    def onScreensaverDeactivated(self):
        log('screensaver deactivated')

class Line:

    def __init__(self, executable_path):
        # ウェブドライバを設定
        chrome_options = Options()
        chrome_options.add_extension(extension_path)
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)

    def start(self):
        # ページ読み込み
        self.driver.implicitly_wait(10)
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
        self.driver.implicitly_wait(60)
        elem = self.driver.find_element_by_xpath("//li[@title='%s']" % talkroom)
        elem.click()
        # メッセージ検索
        messages = self.watch()
        # メッセージ検索
        '''monitor = Monitor()
        hash = None
        while not monitor.abortRequested():
            if monitor.waitForAbort(3): break
            messages = self.watch()
            hash1 = hashlib.md5(str(messages)).hexdigest()
            if hash != hash1:
                if hash and len(messages)>0: notify('%04d-%02d-%02d %02d:%02d %s' % messages[-1])
                hash = hash1'''
        # 終了
        self.driver.close()
        # メニュー生成
    	for message in messages:
            (year,month,day,hour,minute,src,msg) = message
            # 日時
            dstr = datelabel(year,month,day,hour,minute)
            # メッセージ
            mstr = msg
            if src == '>':
                mstr = '[COLOR yellow]%s[/COLOR]' % msg
            # メニュー
            item = xbmcgui.ListItem('%s %s' % (dstr,mstr))
            #item.addContextMenuItems(context_menu, replaceItems=True)
    	    xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    def watch(self):
        # メッセージ
        messages = []
        elems = self.driver.find_elements_by_xpath("//div[@class='mdRGT07Msg mdRGT07Text' or @class='MdRGT10Notice mdRGT07Other mdRGT10Date']")
        for elem in elems:
            date = elem.get_attribute('data-local-id')
            if date:
                # 日付
                d = datetime.datetime.fromtimestamp(int(date)/1000)
            else:
                # メッセージ
                elem1 = elem.find_element_by_xpath(".//span[@class='mdRGT07MsgTextInner']")
                msg = elem1.text.replace('\n', ' ')
                # 時刻
                elem2 = elem.find_element_by_xpath(".//p[@class='mdRGT07Date']")
                match = re.match(r'(AM|PM) (1?[0-9])\:([0-9][0-9])', elem2.text)
                hour = int(match.group(2))
                minute = int(match.group(3))
                if match.group(1) == 'PM': hour += 12
                # 親エレメント
                elem3 = elem1.find_element_by_xpath("../../../..")
                cls = elem3.get_attribute('class')
                if cls == 'MdRGT07Cont mdRGT07Own':
                    src = '<'
                elif cls == 'MdRGT07Cont mdRGT07Other':
                    src = '>'
                else:
                    src = ''
                # 格納
                messages.append((d.year,d.month,d.day,hour,minute,src,msg))
                #log('%04d-%02d-%02d %02d:%02d %s %s' % (d.year,d.month,d.day,hour,minute,src,msg))
        return messages
