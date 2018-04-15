# -*- coding: utf-8 -*-

import os, sys
import json
import threading
import datetime
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from PIL import Image
from StringIO import StringIO

from resources.lib.common import log, notify

addon = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(addon.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#-------------------------------------------------------------------------------
class Session:

    def __init__(self):
        addon = xbmcaddon.Addon()
        # ディレクトリを作成
        self.dirpath = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), 'session')
        if not os.path.isdir(self.dirpath):
            os.makedirs(self.dirpath)
        # セッション情報を格納するファイルのパス
        self.appid = addon.getAddonInfo('id')
        self.filepath = os.path.join(self.dirpath, self.appid)

    def read(self):
        if os.path.isfile(self.filepath):
            try:
                f = open(self.filepath, 'r')
                data = json.loads(f.read(), 'utf-8')
                f.close()
            except ValueError:
                log('broken json: %s' % self.filepath)
                data = None
        else:
            data = None
        return data

    def write(self, data):
        f = open(self.filepath, 'w')
        f.write(json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2).encode('utf-8'))
        f.close()

    def save(self, driver):
        # セッション情報を保存する
        self.driver = driver
        data = {'executor_url':self.driver.command_executor._url, 'session_id':self.driver.session_id}
        self.write(data)

    def restore(self, options):
        # セッション情報を読み込む
        data = self.read()
        # ウェブドライバを復元する
        if data:
            try:
                self.driver = webdriver.Remote(data['executor_url'], desired_capabilities=options.to_capabilities())
                self.driver.session_id = data['session_id']
            except:
                self.clear()
        else:
            self.clear()
        return self.driver

    def clear(self):
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)
        self.driver = None

#-------------------------------------------------------------------------------
class Chrome:

    USER_AGENT = {
        'iPhone 6/7/8': {
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'width': 375,
            'height': 667
        },
        'iPhone 6/7/8 Plus': {
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'width': 414,
            'height': 736
        },
        'iPad': {
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
            'width': 768,
            'height': 1024
        },
        'iPad Pro': {
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
            'width': 1024,
            'height': 1366
        }
    }

    def __init__(self, url=None):
        # ユーザエージェント
        ua = xbmcaddon.Addon().getSetting('ua')
        self.ua = self.USER_AGENT[ua]
        self.block_size = min(self.ua['width']/2, self.ua['height']/2)
        # オプション
        options = Options()
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        options.add_argument('user-agent=%s' % self.ua['user_agent'])
        # セッション情報
        self.session = Session()
        # ウェブドライバを生成
        self.driver = self.session.restore(options)
        if url:
            # ページ遷移する場合は既存のウェブドライバを破棄して新規作成
            if self.driver: self.__close()
            self.__new(options)
            # ページを開く
            self.__open(url)
        elif self.driver is None:
            # 既存のウェブドライバがない場合は新規作成
            self.__new(options)

    def __new(self, options):
        # ウェブドライバを作成
        executable_path = xbmcaddon.Addon().getSetting('chrome')
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=options)
        # セッション情報を保存
        self.session.save(self.driver)
        # セッションのメンテナンスを開始
        args = (self.driver.command_executor._url, self.driver.session_id)
        threading.Thread(target=self.watchdog, args=args).start()

    def __open(self, url):
        # ウィンドウサイズをリセット
        self.driver.set_window_size(self.ua['width'],self.ua['height'])
        # ページ読み込み
        self.driver.get(url)
        # コンテンツサイズを取得
        width = self.driver.execute_script("return document.documentElement.scrollWidth")
        height = self.driver.execute_script("return document.documentElement.scrollHeight")
        # ウィンドウサイズをアジャスト
        self.driver.set_window_size(width,height)

    def __close(self):
        # ウェブドライバを閉じる
        self.driver.close()
        # セッション情報をクリア
        self.session.clear()

    def capture(self, image_file, element=None, xpath=None):
        # 画面全体のイメージを取得
        screenshot = self.driver.get_screenshot_as_png()
        image = Image.open(StringIO(screenshot))
        # 指定部分を抽出
        if element:
            pass
        elif xpath:
            element = self.driver.find_element_by_xpath(xpath)
        # キャプチャ
        if element:
            # 指定部分
            size = element.size
            location = element.location
            window = self.driver.get_window_size()
            left = min(location['x'], window['width'])
            top = min(location['y'], window['height'])
            right = min(location['x']+size['width'], window['width'])
            bottom = min(location['y']+size['height'], window['height'])
            if bottom > top and right > left:
                image.crop((int(left), int(top), int(right), int(bottom))).save(image_file)
        else:
            # 画面全体
            image.save(image_file)

    def watchdog(self, executor_url, session_id):
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            # 停止を待機
            if monitor.waitForAbort(10): break
            # セッションをチェック
            data = Session().read()
            if (executor_url,session_id) != (data['executor_url'],data['session_id']): break
        # ウェブドライバを終了
        self.driver.quit()
