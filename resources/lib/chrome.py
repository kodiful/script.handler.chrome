# -*- coding: utf-8 -*-

import os, sys
import json
import threading
import datetime
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from PIL import Image
from StringIO import StringIO

from common import log, notify

sys.path.append(os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#-------------------------------------------------------------------------------
class Session:

    def __init__(self, realm):
        # アドオン
        self.addon = xbmcaddon.Addon()
        addon_id = self.addon.getAddonInfo('id')
        addon_profile = self.addon.getAddonInfo('profile')
        # ディレクトリを作成
        self.dirpath = os.path.join(xbmc.translatePath(addon_profile), realm or addon_id)
        if not os.path.isdir(self.dirpath):
            os.makedirs(self.dirpath)
        # セッション情報を格納するファイルのパス
        self.filepath = os.path.join(self.dirpath, 'session.json')

    def read(self):
        # ファイルがあれば読み込む
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
        # タイムスタンプを設定
        data['timestamp'] = int(datetime.datetime.now().strftime('%s'))
        # ファイルへ書き込む
        f = open(self.filepath, 'w')
        f.write(json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2).encode('utf-8'))
        f.close()

    def save(self, driver, url=None):
        # セッション情報を保存する
        self.driver = driver
        self.url = url
        data = {'executor_url':self.driver.command_executor._url, 'session_id':self.driver.session_id, 'url':self.url}
        self.write(data)

    def restore(self, options):
        # セッション情報を読み込む
        data = self.read()
        # ウェブドライバを復元する
        if data:
            try:
                self.driver = webdriver.Remote(data['executor_url'], desired_capabilities=options.to_capabilities())
                self.driver.session_id = data['session_id']
                self.url = data['url']
                # タイムスタンプを更新する
                self.write(data)
            except:
                self.clear()
        else:
            self.clear()
        return self.driver

    def clear(self):
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)
        self.driver = None
        self.url = None

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

    def __init__(self, url, realm=None):
        # アドオン
        self.addon = xbmcaddon.Addon()
        # ユーザエージェント
        ua = self.addon.getSetting('ua')
        self.ua = self.USER_AGENT[ua]
        # オプション
        options = Options()
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        options.add_argument('user-agent=%s' % self.ua['user_agent'])
        # セッション情報
        self.session = Session(realm)
        # ウェブドライバを生成
        self.driver = self.session.restore(options)
        # 既存のウェブドライバがある場合
        if self.driver:
            # ページ遷移しない場合
            if url == self.session.url:
                # 既存のウェブドライバをそのまま使う
                self.renewed = False
                return
            # ページ遷移する場合
            else:
                # 既存のウェブドライバを破棄
                self.__close()
        # ウェブドライバを新規作成
        self.__new(options, realm)
        self.renewed = True
        # ページを開く
        self.__open(url)

    def __new(self, options, realm):
        # ウェブドライバを作成
        executable_path = self.addon.getSetting('chrome')
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=options)
        # セッション情報を保存
        self.session.save(self.driver)
        # セッションのメンテナンスを開始
        args = (self.driver.command_executor._url, self.driver.session_id, realm)
        threading.Thread(target=self.__watchdog, args=args).start()

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
        # セッション情報を保存
        self.session.save(self.driver, url)

    def __close(self):
        # ウェブドライバを閉じる
        self.driver.close()
        # セッション情報をクリア
        self.session.clear()

    def save_image(self, image_file, element=None, xpath=None):
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

    def save_text(self, text_file, element=None, xpath=None):
        # 指定部分を抽出
        if element:
            pass
        elif xpath:
            element = self.driver.find_element_by_xpath(xpath)
        # キャプチャ
        if element:
            f = open(text_file,'w')
            f.write(element.text.encode('utf-8'))
            f.close()

    def __watchdog(self, executor_url, session_id, realm):
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            # 停止を待機
            if monitor.waitForAbort(10): break
            # セッションをチェック
            data = Session(realm).read()
            if data is None:
                break
            elif data['executor_url'] != executor_url:
                break
            elif data['session_id'] != session_id:
                break
            elif data['timestamp'] + 180 < int(datetime.datetime.now().strftime('%s')):
                break
        # ウェブドライバを終了
        self.driver.quit()
