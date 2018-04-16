# -*- coding: utf-8 -*-

import sys, os, json, urllib, hashlib
import traceback
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from datetime import datetime
from chrome import Chrome
from xpath import getPartialXPath, extractNodes
from common import log, notify
from utilities import show_image, show_text

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
class Builder:

    def current_page(self):
        # アイテムを作成
        label = '[COLOR white]%s[/COLOR]' % self.driver.title.replace('\n',' ').encode('utf-8') or '(Untitled)'
        page_image_file = self.page_image_file
        item = xbmcgui.ListItem(label, iconImage=page_image_file, thumbnailImage=page_image_file)
        # コンテクストメニューを設定
        menu = []
        item.addContextMenuItems(menu, replaceItems=True)
        # アイテムを追加
        values = {'action':'showimage', 'image_file':page_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)

    def current_node(self):
        # アイテムを作成
        label = '[COLOR yellow]%s[/COLOR]' % self.elem.text.replace('\n',' ').encode('utf-8') or '(Untitled)'
        node_image_file = self.node_image_file
        item = xbmcgui.ListItem(label, iconImage=node_image_file, thumbnailImage=node_image_file)
        # コンテクストメニューを設定
        menu = []
        #### ノードリストを表示する
        (label, query) = self.show_childnodes(self.xpath)
        menu.append((label, 'Container.Update(%s)' % query))
        #### リンクリストを表示する
        (label, query) = self.show_links(self.xpath)
        menu.append((label, 'Container.Update(%s)' % query))
        #### キャプチャを表示する
        (label, query) = self.show_image(self.xpath)
        menu.append((label, 'RunPlugin(%s)' % query))
        #### テキストを表示する
        (label, query) = self.show_text(self.xpath)
        menu.append((label, 'RunPlugin(%s)' % query))
        #### トップに追加する
        (label, query) = self.add_to_top(self.xpath)
        menu.append((label, 'Container.Update(%s)' % query))
        item.addContextMenuItems(menu, replaceItems=True)
        # アイテムを追加
        values = {'action':'showimage', 'image_file':node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)

    def show_childnodes(self, xpath):
        label = self.addon.getLocalizedString(32914)
        values = {'action':'traverse', 'url':self.url, 'xpath':xpath, 'mode':Browser.MODE_NODELIST}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        return (label, query)

    def show_links(self, xpath):
        label = self.addon.getLocalizedString(32915)
        values = {'action':'traverse', 'url':self.url, 'xpath':xpath, 'mode':Browser.MODE_LINKLIST}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        return (label, query)

    def show_image(self, xpath):
        label = self.addon.getLocalizedString(32916)
        #values = {'action':'traverse', 'url':self.url, 'xpath':xpath, 'mode':Browser.MODE_CAPTURE}
        values = {'action':'showimage', 'image_file':self.node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        return (label, query)

    def show_text(self, xpath):
        label = self.addon.getLocalizedString(32917)
        #values = {'action':'traverse', 'url':self.url, 'xpath':xpath, 'mode':Browser.MODE_TEXT}
        values = {'action':'showtext', 'text_file':self.node_text_file, 'title':self.driver.title.encode('utf-8')}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        return (label, query)

    def add_to_top(self, xpath):
        label = self.addon.getLocalizedString(32918)
        values = {'action':'append', 'label':self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'mode':self.mode}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        return (label, query)

    def nodelist(self, xpath):
        list = []
        ua_height = self.chrome.ua['height']
        ua_width = self.chrome.ua['width']
        elems = self.driver.find_elements_by_xpath('%s/*' % xpath)
        for i in range(0,len(elems)):
            # スペース、改行以外のテキストを含むノードについて
            if elems[i].text.replace(' ','').replace('\n',''):
                xpath1 = xpath + "/*[%d]" % (i+1)
                width = elems[i].size['width']
                height = elems[i].size['height']
                if height>0 and width>0 and height<ua_height and width<ua_width and (height<ua_height/2 or width<ua_width/2):
                    # 処理対象とするxpath
                    xpath2 = xpath1
                    # キャプチャを取得
                    image_file = os.path.join(self.cache.dirpath, '%s_%s.png' % (self.driver.session_id,hashlib.md5(xpath2).hexdigest()))
                    if not os.path.isfile(image_file):
                        self.chrome.save_image(image_file, element=elems[i])
                    # テキストを取得
                    text_file = os.path.join(self.cache.dirpath, '%s_%s.txt' % (self.driver.session_id,hashlib.md5(xpath2).hexdigest()))
                    if not os.path.isfile(text_file):
                        self.chrome.save_text(text_file, element=elems[i])
                    # コンテクストメニュー設定
                    context_menu = []
                    #### ノードリストを表示する
                    (label, query) = self.show_childnodes(xpath2)
                    context_menu.append((label, 'Container.Update(%s)' % query))
                    #### リンクリストを表示する
                    (label, query) = self.show_links(xpath2)
                    context_menu.append((label, 'Container.Update(%s)' % query))
                    #### キャプチャを表示する
                    (label, query) = self.show_image(xpath2)
                    context_menu.append((label, 'RunPlugin(%s)' % query))
                    #### テキストを表示する
                    (label, query) = self.show_text(xpath2)
                    context_menu.append((label, 'RunPlugin(%s)' % query))
                    #### トップに追加する
                    (label, query) = self.add_to_top(xpath2)
                    context_menu.append((label, 'Container.Update(%s)' % query))
                    #### リンクを抽出してコンテクストメニューに設定
                    for (label, query) in self.linklist(elems[i]):
                        context_menu.append((label, 'Container.Update(%s)' % query))
                    # データを格納
                    label = '[COLOR orange]%s[/COLOR]' % elems[i].text.replace('\n',' ')
                    values = {'action':'showimage', 'image_file':image_file}
                    query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                    list.append((label, query, image_file, text_file, context_menu))
                else:
                    # サイズが対象外の場合は、子ノードに対して処理した結果を加える
                    list = list + self.nodelist(xpath1)
        if len(list) == 1:
            # 抽出ノード数が1の場合は、子ノードに対して処理した結果で置換する
            list = self.nodelist(xpath2)
        return list

    def linklist(self, elem):
        list = []
        for a in elem.find_elements_by_xpath(".//a[starts-with(@href,'http')]"):
            if a.text.replace(' ','').replace('\n',''):
                label = '[COLOR blue]%s[/COLOR]' % a.text.replace('\n',' ')
                values = {'action':'traverse', 'url':a.get_attribute('href'), 'mode':Browser.MODE_NODELIST, 'renew':True}
                query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                list.append((label, query))
        return list

#-------------------------------------------------------------------------------
class Browser(Builder):

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

    def extract(self, url=None, xpath=None, mode=None):
        self.url = url
        self.xpath = xpath or '//html'
        self.mode = mode and int(mode)
        log([self.url,self.xpath,self.mode])
        # 画面全体をキャプチャ
        self.page_image_file = os.path.join(self.cache.dirpath, '%s_%s.png' % (self.driver.session_id,hashlib.md5(self.url).hexdigest()))
        if not os.path.isfile(self.page_image_file):
            self.chrome.save_image(self.page_image_file)
        # 指定部分のエレメント
        self.elem = self.driver.find_element_by_xpath(self.xpath)
        # 指定部分をキャプチャ
        self.node_image_file = os.path.join(self.cache.dirpath, '%s_%s.png' % (self.driver.session_id,hashlib.md5(self.xpath).hexdigest()))
        if not os.path.isfile(self.node_image_file):
            self.chrome.save_image(self.node_image_file, element=self.elem)
        # 指定部分のテキスト
        self.node_text_file = os.path.join(self.cache.dirpath, '%s_%s.txt' % (self.driver.session_id,hashlib.md5(self.xpath).hexdigest()))
        if not os.path.isfile(self.node_text_file):
            self.chrome.save_text(self.node_text_file, element=self.elem)
        # 画面表示
        if self.mode == self.MODE_NODELIST:
            self.__extract_nodelist()
        elif self.mode == self.MODE_LINKLIST:
            self.__extract_linklist()
        elif self.mode == self.MODE_CAPTURE:
            self.__extract_image()
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
            'node_text_file': self.node_text_file
        }

    def __extract_nodelist(self):
        # 親ページを表示する
        self.current_page()
        # 親ノードを表示する
        self.current_node()
        # 子ノードのリスト
    	for (label, query, image_file, text_file, context_menu) in self.nodelist(self.xpath):
            item = xbmcgui.ListItem(label, iconImage=image_file, thumbnailImage=image_file)
            item.addContextMenuItems(context_menu, replaceItems=True)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __extract_linklist(self):
        # 親ページを表示する
        self.current_page()
        # 親ノードを表示する
        self.current_node()
        # リンクのリスト
        for (label, query) in self.linklist(self.elem):
            item = xbmcgui.ListItem(label)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __extract_image(self):
        show_image(self.node_image_file)

    def __extract_text(self):
        show_text(self.node_text_file, self.driver.title.encode('utf-8'))
