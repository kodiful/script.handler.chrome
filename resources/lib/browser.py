# -*- coding: utf-8 -*-

import sys, os, json, urllib, hashlib
import shutil
import traceback
import datetime
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from chrome import Chrome
from xpath import getPartialXPath, extractNodes
from common import log, notify
from utilities import show_image, show_text

from PIL import Image
from StringIO import StringIO

#-------------------------------------------------------------------------------
class Builder:

    def show_childnodes(self, xpath):
        label = self.addon.getLocalizedString(32914)
        values = {'action':'extract', 'url':self.url, 'xpath':xpath, 'target':Browser.TARGET_NODELIST}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        query = 'Container.Update(%s)' % query
        return (label, query)

    def show_links(self, xpath):
        label = self.addon.getLocalizedString(32915)
        values = {'action':'extract', 'url':self.url, 'xpath':xpath, 'target':Browser.TARGET_LINKLIST}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        query = 'Container.Update(%s)' % query
        return (label, query)

    def show_image(self, xpath):
        label = self.addon.getLocalizedString(32916)
        values = {'action':'extract', 'url':self.url, 'xpath':xpath, 'target':Browser.TARGET_CAPTURE}
        #values = {'action':'show_image', 'image_file':self.node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        query = 'RunPlugin(%s)' % query
        return (label, query)

    def show_text(self, xpath):
        label = self.addon.getLocalizedString(32917)
        values = {'action':'extract', 'url':self.url, 'xpath':xpath, 'target':Browser.TARGET_TEXT}
        #values = {'action':'show_text', 'text_file':self.node_text_file, 'title':self.driver.title.encode('utf-8')}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        query = 'RunPlugin(%s)' % query
        return (label, query)

    def play_wav(self, xpath):
        label = self.addon.getLocalizedString(32918)
        values = {'action':'extract', 'url':self.url, 'xpath':xpath, 'target':Browser.TARGET_WAV}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        query = 'RunPlugin(%s)' % query
        return (label, query)

    def add_to_top(self, xpath, content=None):
        label = self.addon.getLocalizedString(32919)
        title =  self.driver.title.encode('utf-8')
        if content:
            content = '%s - %s' % (content,title)
        else:
            content = title
        values = {'action':'append', 'label':content or self.driver.title.encode('utf-8'), 'url':self.url, 'xpath':xpath, 'target':self.target}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        query = 'RunPlugin(%s)' % query
        return (label, query)

    def extract_text_from_element(select, elem):
        if elem.text.replace(' ','').replace('\n',''):
            text = elem.text.replace('\n',' ').encode('utf-8')
        else:
            text = []
            imgs = elem.find_elements_by_xpath(".//img[@alt!='']")
            for img in imgs:
                alt = img.get_attribute('alt')
                if alt.replace(' ','').replace('\n',''):
                    text.append(alt.replace('\n',' ').encode('utf-8'))
            text = ' '.join(text)
        return text

    def current_page(self):
        # アイテムを作成
        content = self.driver.title.replace('\n',' ').encode('utf-8') or '(Selected Page)'
        label = '[COLOR white]%s[/COLOR]' % content
        page_image_file = self.page_image_file
        item = xbmcgui.ListItem(label, iconImage=page_image_file, thumbnailImage=page_image_file)
        # コンテクストメニューを設定
        context_menu = []
        item.addContextMenuItems(context_menu, replaceItems=True)
        # アイテムを追加
        values = {'action':'show_image', 'image_file':page_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)

    def parent_node(self):
        # 親ノードを抽出
        try:
            xpath = '%s/..' % self.xpath
            elem = self.elem.find_element_by_xpath("./..")
        except:
            # 親ノードがないルートノードはスキップ
            return
        # アイテムを作成
        text = self.extract_text_from_element(elem) or '(Parent Node)'
        label = '[COLOR khaki]%s[/COLOR]' % text
        node_image_file = os.path.join(self.cachedir, '%s_%s.png' % (self.driver.session_id,hashlib.md5(xpath).hexdigest()))
        if not os.path.isfile(node_image_file):
            self.chrome.save_image(node_image_file, element=elem)
        item = xbmcgui.ListItem(label, iconImage=node_image_file, thumbnailImage=node_image_file)
        # コンテクストメニュー
        context_menu = []
        #### ノードリストを表示する
        context_menu.append(self.show_childnodes(xpath))
        #### リンクリストを表示する
        context_menu.append(self.show_links(xpath))
        #### キャプチャを表示する
        context_menu.append(self.show_image(xpath))
        #### テキストを表示する
        context_menu.append(self.show_text(xpath))
        #### テキストを音声合成する
        if self.addon.getSetting('tts'):
            context_menu.append(self.play_wav(xpath))
        #### トップに追加する
        context_menu.append(self.add_to_top(xpath,text))
        # コンテクストメニューを設定
        item.addContextMenuItems(context_menu, replaceItems=True)
        # アイテムを追加
        values = {'action':'show_image', 'image_file':node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)

    def current_node(self):
        # アイテムを作成
        text = self.extract_text_from_element(self.elem) or '(Selected Node)'
        label = '[COLOR yellow]%s[/COLOR]' % text
        node_image_file = self.node_image_file
        item = xbmcgui.ListItem(label, iconImage=node_image_file, thumbnailImage=node_image_file)
        # コンテクストメニュー
        context_menu = []
        #### ノードリストを表示する
        context_menu.append(self.show_childnodes(self.xpath))
        #### リンクリストを表示する
        context_menu.append(self.show_links(self.xpath))
        #### キャプチャを表示する
        context_menu.append(self.show_image(self.xpath))
        #### テキストを表示する
        context_menu.append(self.show_text(self.xpath))
        #### テキストを音声合成する
        if self.addon.getSetting('tts'):
            context_menu.append(self.play_wav(self.xpath))
        #### トップに追加する
        context_menu.append(self.add_to_top(self.xpath,text))
        # コンテクストメニューを設定
        item.addContextMenuItems(context_menu, replaceItems=True)
        # アイテムを追加
        values = {'action':'show_image', 'image_file':node_image_file}
        query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, False)

    def nodelist(self, xpath):
        list = []
        ua_height = self.chrome.ua['height']
        ua_width = self.chrome.ua['width']
        elems = self.driver.find_elements_by_xpath('%s/*' % xpath)
        for i in range(0,len(elems)):
            xpath1 = xpath + "/*[%d]" % (i+1)
            width = elems[i].size['width']
            height = elems[i].size['height']
            if height>0 and width>0 and height<ua_height and width<ua_width and (height<ua_height/2 or width<ua_width/2):
                # 処理対象とするxpath
                xpath2 = xpath1
                # キャプチャを取得
                image_file = os.path.join(self.cachedir, '%s_%s.png' % (self.driver.session_id,hashlib.md5(xpath2).hexdigest()))
                if not os.path.isfile(image_file):
                    self.chrome.save_image(image_file, element=elems[i])
                # テキストを取得
                text_file = os.path.join(self.cachedir, '%s_%s.txt' % (self.driver.session_id,hashlib.md5(xpath2).hexdigest()))
                if not os.path.isfile(text_file):
                    self.chrome.save_text(text_file, element=elems[i])
                # ラベル
                text = self.extract_text_from_element(elems[i])
                if text:
                    # コンテクストメニュー設定
                    context_menu = []
                    #### ノードリストを表示する
                    context_menu.append(self.show_childnodes(xpath2))
                    #### リンクリストを表示する
                    context_menu.append(self.show_links(xpath2))
                    #### キャプチャを表示する
                    context_menu.append(self.show_image(xpath2))
                    #### テキストを表示する
                    context_menu.append(self.show_text(xpath2))
                    #### テキストを音声合成する
                    if self.addon.getSetting('tts'):
                        context_menu.append(self.play_wav(xpath2))
                    #### トップに追加する
                    context_menu.append(self.add_to_top(xpath2,text))
                    #### リンクを抽出してコンテクストメニューに設定
                    for (label, query) in self.linklist(elems[i]):
                        context_menu.append((label, 'Container.Update(%s)' % query))
                    # データを格納
                    label = '[COLOR orange]%s[/COLOR]' % text
                    values = {'action':'show_image', 'image_file':image_file}
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
        for a in elem.find_elements_by_xpath(".//a"):
            href = a.get_attribute('href')
            if href and href.find('http') == 0:
                # ラベル
                text = self.extract_text_from_element(a)
                if text:
                    label = '[COLOR blue]%s[/COLOR]' % text
                    values = {'action':'extract', 'url':href, 'target':Browser.TARGET_NODELIST}
                    query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
                    list.append((label, query))
        return list

#-------------------------------------------------------------------------------
class Google(Builder):

    def __init__(self):
        # アドオン
        self.addon = xbmcaddon.Addon()
        addon_id = self.addon.getAddonInfo('id')
        addon_profile = self.addon.getAddonInfo('profile')
        # キャッシュディレクトリを設定
        self.cachedir = os.path.join(xbmc.translatePath(addon_profile), addon_id, 'cache')
        if not os.path.isdir(self.cachedir): os.makedirs(self.cachedir)
        # ウェブドライバを設定
        url = 'https://www.google.co.jp/webhp'
        ua = 'iPad Pro'
        self.chrome = Chrome(url=url, realm=None, ua=ua, managed=False)
        self.driver = self.chrome.driver

    def extract(self, keyword):
        # 検索窓を抽出
        input = self.driver.find_element_by_xpath("//input[@name='q']")
        # キーワードを入力
        input.send_keys(keyword)
        input.send_keys(Chrome.KEYS_ENTER)
        # 検索結果を抽出
        heading = self.driver.find_elements_by_xpath("//a/div[@role='heading']")
        list = []
        for div in heading:
            a = div.find_element_by_xpath("./..")
            label = '[COLOR blue]%s[/COLOR]' % div.text.encode('utf-8')
            values = {'action':'extract', 'url':a.get_attribute('href'), 'target':Browser.TARGET_NODELIST}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            list.append((label, query))
        # 画面全体をキャプチャ
        self.page_image_file = os.path.join(self.cachedir, '%s.png' % (self.driver.session_id))
        if not os.path.isfile(self.page_image_file):
            self.chrome.save_image(self.page_image_file)
        # 親ページを表示する
        self.current_page()
        # リンクのリスト
        for (label, query) in list:
            item = xbmcgui.ListItem(label)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        # ウェブドライバを終了
        self.driver.close()

#-------------------------------------------------------------------------------
class Browser(Builder):

    TARGET_NODELIST = 0
    TARGET_LINKLIST = 1
    TARGET_CAPTURE = 2
    TARGET_TEXT = 3
    TARGET_WAV = 4
    TARGET_FILES = 99

    def __init__(self, url, realm=None):
        # アドオン
        self.addon = xbmcaddon.Addon()
        addon_id = self.addon.getAddonInfo('id')
        addon_profile = self.addon.getAddonInfo('profile')
        # キャッシュディレクトリを設定
        self.cachedir = os.path.join(xbmc.translatePath(addon_profile), realm or addon_id, 'cache')
        if not os.path.isdir(self.cachedir): os.makedirs(self.cachedir)
        # ウェブドライバを設定
        self.chrome = Chrome(url, realm)
        self.driver = self.chrome.driver
        self.url = url
        # ページ遷移した場合はキャッシュディレクトリをクリアする
        if self.chrome.renewed: self.clear()

    def clear(self):
        # キャッシュディレクトリをクリア
        for filename in os.listdir(self.cachedir):
            os.remove(os.path.join(self.cachedir, filename))

    def extract(self, xpath=None, target=None, image_file=None, text_file=None, wav_file=None):
        self.xpath = xpath or '//html'
        self.target = target and int(target)
        #log([self.url,self.xpath,self.target])
        # 画面全体をキャプチャ
        self.page_image_file = os.path.join(self.cachedir, '%s.png' % (self.driver.session_id))
        if not os.path.isfile(self.page_image_file):
            self.chrome.save_image(self.page_image_file)
        # 指定部分のエレメント
        self.elem = self.driver.find_element_by_xpath(self.xpath)
        # 指定部分をキャプチャ
        self.node_image_file = os.path.join(self.cachedir, '%s_%s.png' % (self.driver.session_id, hashlib.md5(self.xpath).hexdigest()))
        if not os.path.isfile(self.node_image_file):
            self.chrome.save_image(self.node_image_file, element=self.elem)
        # 指定部分のテキスト
        self.node_text_file = os.path.join(self.cachedir, '%s_%s.txt' % (self.driver.session_id, hashlib.md5(self.xpath).hexdigest()))
        if not os.path.isfile(self.node_text_file):
            self.chrome.save_text(self.node_text_file, element=self.elem)
        # 指定部分のテキストを音声合成（ファイルパスのみ設定）
        self.node_wav_file = os.path.join(self.cachedir, '%s_%s.wav' % (self.driver.session_id, hashlib.md5(self.xpath).hexdigest()))
        # 画面表示
        if self.target == self.TARGET_NODELIST:
            self.__extract_nodelist()
        elif self.target == self.TARGET_LINKLIST:
            self.__extract_linklist()
        elif self.target == self.TARGET_CAPTURE:
            self.__extract_image()
        elif self.target == self.TARGET_TEXT:
            self.__extract_text()
        elif self.target == self.TARGET_WAV:
            self.__extract_wav()
        elif self.target == self.TARGET_FILES:
            self.__extract_files(image_file, text_file, wav_file)
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
        self.parent_node()
        # 現ノードを表示する
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
        # 現ノードを表示する
        self.current_node()
        # リンクのリスト
        for (label, query) in self.linklist(self.elem):
            item = xbmcgui.ListItem(label)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __extract_image(self):
        show_image(self.node_image_file)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)

    def __extract_text(self):
        show_text(self.node_text_file, self.driver.title.encode('utf-8'))
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)

    def __extract_wav(self, play=True):
        # 指定部分のテキストから音声合成
        if not os.path.isfile(self.node_wav_file):
            # ファイル読み込み
            if os.path.isfile(self.node_text_file):
                f = open(self.node_text_file,'r')
                data = f.read()
                f.close()
            else:
                data = ''
            # 音声合成を実行
            values = {'text':data.replace('\n',' '), 'silent':'true', 'wavfile':self.node_wav_file}
            postdata = urllib.urlencode(values)
            xbmc.executebuiltin('RunPlugin(plugin://script.handler.tts/?%s)' % (postdata))
            # WAVFILEの生成を待機
            while not os.path.exists(self.node_wav_file):
                xbmc.sleep(1)
        if play:
            #show_image(self.node_image_file)
            show_text(self.node_text_file, self.driver.title.encode('utf-8'))
            xbmc.executebuiltin('PlayMedia(%s)' % self.node_wav_file)

    def __extract_search_results(self):
        # 親ページを表示する
        self.current_page()
        # 親ノードを表示する
        self.current_node()
        # リンクのリスト
        for (label, query) in self.linklist(self.elem):
            item = xbmcgui.ListItem(label)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def __extract_files(self, image_file=None, text_file=None, wav_file=None):
        if image_file and os.path.isfile(self.node_image_file):
            shutil.copyfile(self.node_image_file, image_file)
        if text_file and os.path.isfile(self.node_text_file):
            shutil.copyfile(self.node_text_file, text_file)
        if wav_file:
            self.__extract_wav(play=False)
            shutil.copyfile(self.node_wav_file, wav_file)
