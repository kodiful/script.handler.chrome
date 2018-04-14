# -*- coding: utf-8 -*-

import sys, os, json, urllib, hashlib
import traceback
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from datetime import datetime
from chrome import Chrome
from xpath import getPartialXPath, extractNodes
from common import log, notify

from PIL import Image
from StringIO import StringIO

#-------------------------------------------------------------------------------
class Cache:

    def __init__(self):
        # ディレクトリを作成
        addon = xbmcaddon.Addon()
        self.dirpath = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), 'cache')
        if not os.path.isdir(self.dirpath):
            os.makedirs(self.dirpath)

    def clear(self):
        # ディレクトリをクリア
        for filename in os.listdir(self.dirpath):
            os.remove(os.path.join(self.dirpath, filename))

#-------------------------------------------------------------------------------
class Browser:

    MODE_NODELIST = 0
    MODE_LINKLIST = 1
    MODE_CAPTURE = 2
    MODE_TEXT = 3

    def __init__(self, url=None):
        # アドオン
        self.addon = xbmcaddon.Addon()
        # キャッシュディレクトリを作成
        self.cache = Cache()
        if url: self.cache.clear()
        # ウェブドライバを設定
        self.chrome = Chrome(url)
        self.driver = self.chrome.driver

    def __traverse(self, xpath):
        result = []
        elems = self.driver.find_elements_by_xpath('%s/*' % xpath)
        for i in range(0,len(elems)):
            # テキストが含まれるノードについて
            content = elems[i].text
            if content:
                xpath1 = xpath + "/*[%d]" % (i+1)
                width = elems[i].size['width']
                height = elems[i].size['height']
                if height > 0 and width > 0 and (height < self.chrome.block_size or width < self.chrome.block_size):
                    # 画像を取得
                    image_file = os.path.join(self.cache.dirpath, '%s_%s.png' % (self.driver.session_id,hashlib.md5(xpath1).hexdigest()))
                    self.chrome.capture(image_file, element=elems[i])
                    # コンテクストメニュー設定
                    menu = []
                    # ノードリストを表示する
                    values = {'action':'traverse', 'xpath':xpath1, 'mode':self.MODE_NODELIST}
                    query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                    menu.append((self.addon.getLocalizedString(32914), query))
                    # リンクリストを表示する
                    values = {'action':'traverse', 'xpath':xpath1, 'mode':self.MODE_LINKLIST}
                    query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                    menu.append((self.addon.getLocalizedString(32915), query))
                    # トップに追加する
                    values = {'action':'append', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath1, 'mode':self.mode}
                    query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                    menu.append((self.addon.getLocalizedString(32916), query))
                    # リンクを抽出してコンテクストメニューに設定
                    for a in elems[i].find_elements_by_xpath(".//a[starts-with(@href,'http')]"):
                        href = a.get_attribute('href')
                        text = a.text.replace('\n',' ')
                        if text:
                            values = {'action':'traverse', 'url':href, 'mode':self.mode}
                            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                            menu.append(('[COLOR blue]%s[/COLOR]' % text, query))
                    # 抽出データを格納
                    elem = {
                        'index': i,
                        'node': elems[i],
                        'text': content.replace('\n',' '),
                        'image': image_file,
                        'menu': menu,
                        'xpath': xpath1
                    }
                    result.append(elem)
                else:
                    result = result + self.__traverse(xpath1)
        return result

    def extract(self, url=None, xpath=None, mode=None):
        self.url = url
        self.xpath = xpath or '//html'
        self.mode = mode and int(mode)
        # 画面全体をキャプチャ
        self.page_image_file = os.path.join(self.cache.dirpath, '%s_%s.png' % (self.driver.session_id,hashlib.md5(self.url).hexdigest()))
        if not os.path.isdir(self.page_image_file):
            self.chrome.capture(self.page_image_file)
        # 指定部分をキャプチャ
        self.node_image_file = os.path.join(self.cache.dirpath, '%s_%s.png' % (self.driver.session_id,hashlib.md5(self.xpath).hexdigest()))
        if not os.path.isdir(self.node_image_file):
            self.chrome.capture(self.node_image_file, xpath=self.xpath)
        # 指定部分のエレメント
        self.elem = self.driver.find_element_by_xpath(self.xpath)
        # 指定部分のテキスト
        self.node_text = self.elem.text
        # 画面表示
        if self.mode == self.MODE_NODELIST:
            self.__extract_nodelist(self.url, self.xpath)
        elif self.mode == self.MODE_LINKLIST:
            self.__extract_linklist(self.url, self.xpath)
        elif self.mode == self.MODE_CAPTURE:
            self.__extract_capture()
        elif self.mode == self.MODE_TEXT:
            self.__extract_text()
        # ノード情報を返す
        return {
            'url': self.url,
            'xpath': self.xpath,
            'optimized_xpath': self.driver.execute_script(getPartialXPath, self.elem),
            'title': self.driver.title,
            'page_image_file': self.page_image_file,
            'node_image_file': self.node_image_file,
            'node_text': self.node_text
        }

    def __extract_nodelist(self, url, xpath):
        # テキストを含むノードを抽出
        result = self.__traverse(xpath)
        while len(result) == 1:
            result = self.__traverse(result[0]['xpath'])
        # 親ページの項目を追加
        label = self.driver.title.encode('utf-8') or '(Untitled)'
        item = xbmcgui.ListItem('[COLOR yellow]\xe2\x97\x80\xe2\x97\x80 %s[/COLOR]' % label, iconImage=self.page_image_file, thumbnailImage=self.page_image_file)
        values = {'action':'showcapture', 'file':self.page_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # コンテクストメニュー
        menu = []
        # リンクリストを表示する
        values = {'action':'traverse', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'mode':self.MODE_LINKLIST}
        query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
        menu.append((self.addon.getLocalizedString(32915), query))
        # トップに追加する
        values = {'action':'append', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'mode':self.mode}
        query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
        menu.append((self.addon.getLocalizedString(32916), query))
        # 親ノードの項目を追加
        label = '[COLOR orange]\xe2\x97\x80 %s[/COLOR]' % self.node_text.replace('\n',' ').encode('utf-8')
        item = xbmcgui.ListItem(label, iconImage=self.node_image_file, thumbnailImage=self.node_image_file)
        item.addContextMenuItems(menu, replaceItems=True)
        values = {'action':'showcapture', 'file':self.node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # 子ノードのリスト
    	for elem in result:
            label = '[COLOR orange]%s[/COLOR]' % elem['text'].encode('utf-8')
            item = xbmcgui.ListItem(label, iconImage=elem['image'], thumbnailImage=elem['image'])
            item.addContextMenuItems(elem['menu'], replaceItems=True)
            values = {'action':'showcapture', 'file':elem['image']}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __extract_linklist(self, url, xpath):
        # 親ページの項目を追加
        label = self.driver.title.encode('utf-8') or '(Untitled)'
        item = xbmcgui.ListItem('[COLOR yellow]\xe2\x97\x80\xe2\x97\x80 %s[/COLOR]' % label, iconImage=self.page_image_file, thumbnailImage=self.page_image_file)
        values = {'action':'showcapture', 'file':self.page_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # コンテクストメニュー
        menu = []
        # ノードリストを表示する
        values = {'action':'traverse', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'mode':self.MODE_NODELIST}
        query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
        menu.append((self.addon.getLocalizedString(32914), query))
        # トップに追加する
        values = {'action':'append', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'mode':self.mode}
        query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
        menu.append((self.addon.getLocalizedString(32916), query))
        # 親ノードの項目を追加
        label = '[COLOR orange]\xe2\x97\x80 %s[/COLOR]' % self.node_text.replace('\n',' ').encode('utf-8')
        item = xbmcgui.ListItem(label, iconImage=self.node_image_file, thumbnailImage=self.node_image_file)
        item.addContextMenuItems(menu, replaceItems=True)
        values = {'action':'showcapture', 'file':self.node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)
        # リンクのリスト
        for a in self.elem.find_elements_by_xpath(".//a[starts-with(@href,'http')]"):
            href = a.get_attribute('href')
            text = a.text.replace('\n',' ')
            if text:
                values = {'action':'traverse', 'url':href, 'mode':self.mode, 'renew':True}
                query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                item = xbmcgui.ListItem('[COLOR blue]%s[/COLOR]' % text)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __extract_capture(self):
        # キャプチャ画像を表示
        xbmc.executebuiltin('ShowPicture(%s)' % self.node_image_file)

    def __extract_text(self):
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
