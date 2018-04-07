# -*- coding: utf-8 -*-

import sys, os, json
import urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from browser import Browser
from common import log

#-------------------------------------------------------------------------------
class Start:

    filepath = None
    data = None

    def __init__(self, filename='start.json'):
        addon = xbmcaddon.Addon()
        profile = xbmc.translatePath(addon.getAddonInfo('profile'))
        self.filename = filename
        self.filepath = os.path.join(profile, filename)
        self.read()

    def read(self):
        if os.path.isfile(self.filepath):
            try:
                f = open(self.filepath,'r')
                self.data = json.loads(f.read(), 'utf-8')
                f.close()
            except ValueError:
                log('broken json: %s' % self.filepath)
                self.data = []
        else:
            self.data = []
        return self.data

    def write(self):
        self.data = sorted(self.data, key=lambda elem: elem['label'] or elem['url'])
        f = open(self.filepath,'w')
        f.write(json.dumps(self.data, sort_keys=True, ensure_ascii=False, indent=2).encode('utf-8'))
        f.close()

    def clear(self):
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)
        self.data = []
        self.write()

    def delete(self, url, xpath):
        addon = xbmcaddon.Addon()
        data1 = []
        for data in self.data:
            if url == data['url'] and xpath == data['xpath']:
                pass
            else:
                data1.append(data)
        self.data = data1
        self.write()
        # スタート画面を更新
        xbmc.executebuiltin('Container.Update(plugin://%s)' % addon.getAddonInfo('id'))

    def edit(self, label, url, xpath, mode):
        addon = xbmcaddon.Addon()
        # 設定画面に反映
        addon.setSetting('url1', url)
        addon.setSetting('xpath1', xpath)
        addon.setSetting('url', url)
        addon.setSetting('label', label)
        addon.setSetting('xpath', xpath)
        addon.setSetting('mode', mode)
        # 設定画面を開く
        addon.openSettings()

    def edited(self, settings):
        addon = xbmcaddon.Addon()
        # 設定を取得
        url1 = settings['url1']
        xpath1 = settings['xpath1']
        url = settings['url']
        label = settings['label']
        xpath = settings['xpath']
        mode = settings['mode']
        # 文字コード変換
        if isinstance(label, str): label = label.decode('utf-8')
        if isinstance(url, str): url = url.decode('utf-8')
        if isinstance(xpath, str): xpath = xpath.decode('utf-8')
        if isinstance(mode, str): mode = mode.decode('utf-8')
        # 設定更新
        for data in self.data:
            if url1 == data['url'] and xpath1 == data['xpath']:
                # 既存の設定を更新
                data['url'] = url
                data['label'] = label
                data['xpath'] = xpath
                data['mode'] = int(mode)
                break
            elif url == data['url'] and xpath == data['xpath']:
                # 重複する設定を更新
                data['url'] = url
                data['label'] = label
                data['xpath'] = xpath
                data['mode'] = int(mode)
                break
        else:
            # 設定を追加
            data = {}
            data['label'] = label
            data['url'] = url
            data['xpath'] = xpath
            data['mode'] = int(mode)
            self.data.append(data)
        # ファイル書き込み
        self.write()
        # スタート画面を更新
        xbmc.executebuiltin('Container.Update(plugin://%s)' % addon.getAddonInfo('id'))

    def show(self, executable_path=None):
        addon = xbmcaddon.Addon()
        # タイトル補完
        for data in self.data:
            if data['label'] == '':
                data['label'] = Browser(executable_path).load(data['url'], data['xpath'], mode=Browser.MODE_TITLE)
        self.write()
        # 表示
        for data in self.data:
            url = data['url']
            label = data['label']
            xpath = data['xpath']
            mode = data['mode']
            # コンテクストメニュー
            menu = []
            values = {'action':'edit', 'label':label.encode('utf-8'), 'url':url, 'xpath':xpath, 'mode':mode}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32911), query))
            values = {'action':'delete', 'url':url, 'xpath':xpath}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32912), query))
            menu.append((addon.getLocalizedString(32913), 'Addon.OpenSettings(%s)' % addon.getAddonInfo('id')))
            # アイテム追加
            item = xbmcgui.ListItem(label or url)
            item.addContextMenuItems(menu, replaceItems=True)
            values = {'action':'traverse', 'url':url, 'xpath':xpath, 'mode':mode}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)
