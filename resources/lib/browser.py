# -*- coding: utf-8 -*-

import sys, os, urllib, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from datetime import datetime
from cache import Cache
from common import log, notify

from PIL import Image
from StringIO import StringIO

class Browser:

    initial_width = 1152
    #initial_height = 648
    #initial_height = 4096
    initial_height = 8192

    threshold_size = 400

    MODE_NODELIST = 0
    MODE_LINKLIST = 1
    MODE_CAPTURE = 2
    MODE_TEXT = 3

    def __init__(self, executable_path):
        # アドオン
        self.addon = xbmcaddon.Addon()
        sys.path.append(os.path.join(xbmc.translatePath(self.addon.getAddonInfo('path')), 'resources', 'lib', 'selenium-3.9.0'))
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        # ウェブドライバを設定
        chrome_options = Options()
        chrome_options.add_argument('headless')
        chrome_options.add_argument('disable-gpu')
        chrome_options.add_argument('window-size=%d,%d' % (self.initial_width,self.initial_height))
        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        # キャッシュディレクトリを作成
        self.cache = Cache()
        # セッションIDとして時刻を格納
        self.session = datetime.now().strftime('%s')

    def __capture(self, element, filepath):
        size = element.size
        location = element.location
        width = size['width']
        height = size['height']
        left = location['x']
        top = location['y']
        right = left + width
        bottom = top + height
        image = self.image.crop((int(left), int(top), int(right), int(bottom)))
        image.save(filepath)

    def __traverse(self, xpath):
        result = []
        elems = self.driver.find_elements_by_xpath(xpath+'/*')
        for i in range(0,len(elems)):
            # テキストが含まれるノードについて
            if elems[i].text:
                xpath1 = xpath + '/*[%d]' % (i+1)
                width = elems[i].size['width']
                height = elems[i].size['height']
                if height > 0 and width > 0 and (height < self.threshold_size or width < self.threshold_size):
                    # 画像を取得
                    image = os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(xpath1).hexdigest()))
                    self.__capture(elems[i], image)
                    # コンテクストメニュー設定
                    menu = []
                    values = {'action':'traverse', 'url':self.url, 'xpath':xpath1, 'mode':self.mode}
                    query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                    menu.append((self.addon.getLocalizedString(32914), query))
                    values = {'action':'append', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath1, 'mode':self.mode}
                    query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                    menu.append((self.addon.getLocalizedString(32915), query))
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
                    result = result + self.__traverse(xpath1)
        return result

    def load(self, url, xpath=None, mode=None, page_image_file=None, node_image_file=None):
        # ページ読み込み
        self.driver.implicitly_wait(10)
        self.driver.get(url)
        self.url = url
        self.xpath = xpath or '//body'
        self.mode = mode and int(mode)
        # 全体をキャプチャ
        image = self.driver.get_screenshot_as_png()
        self.image = Image.open(StringIO(image))
        self.page_image_file = page_image_file or os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(self.url).hexdigest()))
        self.image.save(self.page_image_file)
        # 指定部分をキャプチャ
        self.elem = self.driver.find_element_by_xpath(self.xpath)
        self.node_image_file = node_image_file or os.path.join(self.cache.path, '%s_%s.png' % (self.session,hashlib.md5(self.xpath).hexdigest()))
        self.__capture(self.elem, self.node_image_file)
        self.node_text = self.elem.text
        # 返り値
        info = {
            'url': self.url,
            'xpath': self.xpath,
            'title': self.driver.title,
            'page_image_file': self.page_image_file,
            'node_image_file': self.node_image_file,
            'node_text': self.node_text
        }
        # 画面表示
        if self.mode == self.MODE_NODELIST:
            self.load_nodelist(url, self.xpath)
        elif self.mode == self.MODE_LINKLIST:
            self.load_linklist(url, self.xpath)
        elif self.mode == self.MODE_CAPTURE:
            self.load_capture(url, self.xpath)
        elif self.mode == self.MODE_TEXT:
            self.load_text(url, self.xpath)
        # ウェブドライバを終了
        self.driver.quit()
        return info

    def load_nodelist(self, url, xpath):
        # テキストを含むノードを抽出
        result = self.__traverse(xpath)
        while len(result) == 1:
            result = self.__traverse(result[0]['xpath'])
        # 親ページ
        label = self.driver.title or '(Untitled)'
        item = xbmcgui.ListItem('[COLOR yellow]%s[/COLOR]' % label, iconImage=self.page_image_file, thumbnailImage=self.page_image_file)
        values = {'action':'showcapture', 'file':self.page_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # 親ノード
        menu = []
        values = {'action':'append', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'mode':self.mode}
        query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
        menu.append((self.addon.getLocalizedString(32915), query))
        label = '[COLOR yellow]\xe2\x96\xb6 %s[/COLOR]' % self.node_text.replace('\n',' ').encode('utf-8')
        item = xbmcgui.ListItem(label, iconImage=self.node_image_file, thumbnailImage=self.node_image_file)
        item.addContextMenuItems(menu, replaceItems=True)
        values = {'action':'showcapture', 'file':self.node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # 子ノードのリスト
    	for elem in result:
            label = '[COLOR orange]\xe2\x96\xb6\xe2\x96\xb6 %s[/COLOR]' % elem['text'].encode('utf-8')
            item = xbmcgui.ListItem(label, iconImage=elem['image'], thumbnailImage=elem['image'])
            item.addContextMenuItems(elem['menu'], replaceItems=True)
            values = {'action':'showcapture', 'file':elem['image']}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def load_linklist(self, url, xpath):
        # メニュー生成
        label = self.driver.title or '(Untitled)'
        item = xbmcgui.ListItem('[COLOR yellow]%s[/COLOR]' % label, iconImage=self.page_image_file, thumbnailImage=self.page_image_file)
        values = {'action':'showcapture', 'file':self.page_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # リンクを追加
        for a in self.elem.find_elements_by_tag_name("a"):
            text = a.text or a.get_attribute('title') or a.get_attribute('alt') or ''
            text = text.replace('\n',' ')
            href = a.get_attribute('href')
            if len(text)>0 and href and href.find('http')==0:
                values = {'action':'traverse', 'url':href, 'mode':self.mode}
                query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                item = xbmcgui.ListItem('[COLOR blue]%s[/COLOR]' % text)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def load_capture(self, url, xpath):
        # キャプチャ画像を表示
        xbmc.executebuiltin('ShowPicture(%s)' % self.node_image_file)

    def load_text(self, url, xpath):
        # テキストビューア
        viewer_id = 10147
        # ウィンドウを開く
        xbmc.executebuiltin('ActivateWindow(%s)' % viewer_id)
        # ウィンドウの用意ができるまで1秒待つ
        xbmc.sleep(1000)
        # ウィンドウへ書き込む
        viewer = xbmcgui.Window(viewer_id)
        viewer.getControl(1).setLabel(self.driver.title or '(Untitled)')
        viewer.getControl(5).setText(self.node_text)
