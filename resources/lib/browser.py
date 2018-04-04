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
    threshold_numder = 3

    def __init__(self, executable_path):
        # ウェブドライバを設定
        chrome_options = Options()
        chrome_options.add_argument('headless')
        chrome_options.add_argument('disable-gpu')
        chrome_options.add_argument('window-size=%d,%d' % (self.initial_width,self.initial_height))
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        # キャッシュディレクトリを作成
        self.cache = Cache()

    def __capture(self, element, filepath):
        size = element.size
        width = size['width']
        height = size['height']
        if width > 10 and height > 10:
            location = element.location
            left = location['x']
            top = location['y']
            right = left + width
            bottom = top + height
            if bottom < self.initial_height:
                image = self.image.crop((int(left), int(top), int(right), int(bottom)))
                image.save(filepath)
                return filepath
        return None

    def traverse(self, xpath):
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
                        menu.append(('Show thumbnail', 'ShowPicture(%s)' % image))
                        menu.append(('Show page', 'ShowPicture(%s)' % self.image_file))
                        # リンクを抽出してコンテクストメニューに設定
                        for a in elems[i].find_elements_by_tag_name("a"):
                            text = a.text or a.get_attribute('title') or a.get_attribute('alt') or ''
                            text = text.replace('\n',' ')
                            href = a.get_attribute('href')
                            if len(text)>0 and href and href.find('http')==0:
                                query = 'Container.Update(%s?url=%s)' % (sys.argv[0],urllib.quote_plus(href))
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
                    result = result + self.traverse(xpath1)
        return result

    def load(self, url, xpath='//body'):
        # ページ読み込み
        self.driver.implicitly_wait(10)
        self.driver.get(url)
        # セッションを特定するIDとして時刻を格納
        self.session = datetime.now().strftime('%s')
        # 全体をキャプチャ
        image = self.driver.get_screenshot_as_png()
        self.image = Image.open(StringIO(image))
        self.image_file = os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(url).hexdigest()))
        self.image.save(self.image_file)
        # メニュー生成
        self.load1(url, xpath)
        #self.load2()
        # ウェブドライバを終了
        self.driver.quit()

    def load1(self, url, xpath):
        # テキストを含むノードを抽出
        result = self.traverse(xpath)
        while len(result) == 1:
            result = self.traverse(result[0]['xpath'])
        # メニュー生成
        item = xbmcgui.ListItem(self.driver.title or '(Untitled)', iconImage=self.image_file, thumbnailImage=self.image_file)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), self.image_file, item, False)
    	for elem in result:
            item = xbmcgui.ListItem('[COLOR orange]%s[/COLOR]' % elem['text'], iconImage=elem['image'], thumbnailImage=elem['image'])
            item.addContextMenuItems(elem['menu'], replaceItems=True)
            values = {'url':url, 'xpath':elem['xpath']}
            postdata = urllib.urlencode(values)
            query = '%s?action=traverse&%s' % (sys.argv[0], postdata)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    def load2(self):
        # メニュー生成
        item = xbmcgui.ListItem(self.driver.title or '(Untitled)', iconImage=self.image_file, thumbnailImage=self.image_file)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), self.image_file, item, False)
        # リンクを追加
        for a in self.driver.find_elements_by_tag_name("a"):
            text = a.text or a.get_attribute('title') or a.get_attribute('alt') or ''
            text = text.replace('\n',' ')
            href = a.get_attribute('href')
            if len(text)>0 and href and href.find('http')==0:
                values = {'url':href}
                postdata = urllib.urlencode(values)
                query = '%s?action=traverse%s' % (sys.argv[0], postdata)
                item = xbmcgui.ListItem('[COLOR blue]%s[/COLOR]' % text)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)
