# -*- coding: utf-8 -*-

import sys, os, urllib, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from datetime import datetime
from cache import Cache
from common import log, notify

from PIL import Image
from StringIO import StringIO

# import selenium
ADDON = xbmcaddon.Addon()
sys.path.append(os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Browser:

    initial_width = 1152
    #initial_height = 648
    initial_height = 4096

    threshold_size = 400

    MODE_LINKLIST = 0
    MODE_DRILLDOWN = 1
    MODE_CAPTURE = 2

    def __init__(self, executable_path):
        # ウェブドライバを設定
        chrome_options = Options()
        chrome_options.add_argument('headless')
        chrome_options.add_argument('disable-gpu')
        chrome_options.add_argument('window-size=%d,%d' % (self.initial_width,self.initial_height))
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        # キャッシュディレクトリを作成
        self.cache = Cache()
        # セッションを特定するIDとして時刻を格納
        self.session = datetime.now().strftime('%s')

    def __capture(self, element, filepath):
        size = element.size
        width = size['width']
        height = size['height']
        if width > 0 and height > 0:
            location = element.location
            left = location['x']
            top = location['y']
            right = left + width
            bottom = top + height
            image = self.image.crop((int(left), int(top), int(right), int(bottom)))
            image.save(filepath)
            return filepath
        else:
            return None

    def __traverse(self, xpath):
        result = []
        elems = self.driver.find_elements_by_xpath(xpath+'/*')
        for i in range(0,len(elems)):
            # テキストが含まれるノードについて
            if elems[i].text:
                xpath1 = xpath + '/*[%d]' % (i+1)
                width = elems[i].size['width']
                height = elems[i].size['height']
                if height < self.threshold_size or width < self.threshold_size:
                    image = os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(xpath1).hexdigest()))
                    if self.__capture(elems[i], image):
                        # コンテクストメニュー設定
                        menu = []
                        values = {'action':'traverse', 'url':self.url, 'xpath':xpath1, 'mode':self.mode}
                        query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                        menu.append(('Drill down', query))
                        # リンクを抽出してコンテクストメニューに設定
                        for a in elems[i].find_elements_by_tag_name("a"):
                            text = a.text or a.get_attribute('title') or a.get_attribute('alt') or ''
                            text = text.replace('\n',' ')
                            href = a.get_attribute('href')
                            if len(text)>0 and href and href.find('http')==0:
                                values = {'action':'traverse', 'url':href, 'mode':self.mode}
                                query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                                menu.append(('[COLOR blue]%s[/COLOR]' % text, query))
                        # 抽出データを格納
                        elem = {
                            'index': i,
                            'node': elems[i],
                            'text': elems[i].text.replace('\n',' '),
                            'image': image,
                            'menu': menu,
                            'xpath': xpath1
                        }
                        result.append(elem)
                else:
                    # 閾値よりも大きい場合はさらに分割
                    result = result + self.__traverse(xpath1)
        return result

    def load(self, url, xpath, mode=MODE_LINKLIST):
        # ページ読み込み
        self.driver.implicitly_wait(10)
        self.driver.get(url)
        self.url = url
        self.mode = int(mode)
        # 全体をキャプチャ
        image = self.driver.get_screenshot_as_png()
        self.image = Image.open(StringIO(image))
        self.image_file = os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(url).hexdigest()))
        self.image.save(self.image_file)
        # 画面表示
        if not xpath: xpath = '//body'
        if self.mode == self.MODE_DRILLDOWN:
            self.load1(url, xpath)
        elif self.mode == self.MODE_LINKLIST:
            self.load2(url, xpath)
        elif self.mode == self.MODE_CAPTURE:
            self.load3(url, xpath)
        # ウェブドライバを終了
        self.driver.quit()

    def load1(self, url, xpath):
        # テキストを含むノードを抽出
        result = self.__traverse(xpath)
        while len(result) == 1:
            result = self.__traverse(result[0]['xpath'])
        # メニュー生成
        label = self.driver.title or '(Untitled)'
        item = xbmcgui.ListItem('[COLOR yellow]%s[/COLOR]' % label, iconImage=self.image_file, thumbnailImage=self.image_file)
        values = {'action':'showcapture', 'file':self.image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
    	for elem in result:
            item = xbmcgui.ListItem('[COLOR orange]%s[/COLOR]' % elem['text'], iconImage=elem['image'], thumbnailImage=elem['image'])
            item.addContextMenuItems(elem['menu'], replaceItems=True)
            values = {'action':'showcapture', 'file':elem['image']}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    def load2(self, url, xpath):
        # メニュー生成
        label = self.driver.title or '(Untitled)'
        item = xbmcgui.ListItem('[COLOR yellow]%s[/COLOR]' % label, iconImage=self.image_file, thumbnailImage=self.image_file)
        values = {'action':'showcapture', 'file':self.image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # リンクを追加
        for a in self.driver.find_elements_by_tag_name("a"):
            text = a.text or a.get_attribute('title') or a.get_attribute('alt') or ''
            text = text.replace('\n',' ')
            href = a.get_attribute('href')
            if len(text)>0 and href and href.find('http')==0:
                values = {'action':'traverse', 'url':href, 'mode':self.mode}
                query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                item = xbmcgui.ListItem('[COLOR blue]%s[/COLOR]' % text)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    def load3(self, url, xpath):
        #　指定したノードを抽出
        elem = self.driver.find_element_by_xpath(xpath)
        # 抽出部分をキャプチャ
        image = os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(xpath).hexdigest()))
        if self.__capture(elem, image):
            # キャプチャ画像を表示
            xbmc.executebuiltin('ShowPicture(%s)' % image)
