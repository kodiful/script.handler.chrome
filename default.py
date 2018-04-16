# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse, urllib
import sys, os, json

from resources.lib.browser import Browser
from resources.lib.cache import Cache
from resources.lib.common import log, notify
from resources.lib.utilities import show_image, show_text

#-------------------------------------------------------------------------------
class Settings:

    def __init__(self, keys):
        self.addon = xbmcaddon.Addon()
        self.data = {}
        for key in keys:
            self.data[key] = self.addon.getSetting(key)

    def clear(self):
        for key in self.data.keys():
            self.addon.setSetting(key, '')
        return self.data

#-------------------------------------------------------------------------------
class Main:

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
        # 設定を取得
        url1 = settings['url1']
        xpath1 = settings['xpath1']
        url = settings['url']
        label = settings['label']
        xpath = settings['xpath']
        mode = settings['mode']
        # 設定更新
        self.append(label, url, xpath, mode, url1, xpath1)

    def append(self, label, url, xpath, mode, url1=None, xpath1=None):
        addon = xbmcaddon.Addon()
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
                # 更新フラグを設定
                data['flag'] = True
                break
            elif url == data['url'] and xpath == data['xpath']:
                # 重複する設定を更新
                data['url'] = url
                data['label'] = label
                data['xpath'] = xpath
                data['mode'] = int(mode)
                # 更新フラグを設定
                data['flag'] = True
                break
        else:
            # 追加情報を取得
            info = Browser(url).extract(xpath)
            # 設定を追加
            data = {}
            data['url'] = url
            data['mode'] = int(mode)
            # ラベルを補完
            data['label'] = label or info['title'] or '(Untitled)'
            # XPATHを最適化
            data['xpath'] = info['optimized_xpath']
            # 更新フラグを設定
            data['flag'] = True
            self.data.append(data)
        # ファイル書き込み
        self.write()
        # スタート画面を更新
        xbmc.executebuiltin('Container.Update(plugin://%s)' % addon.getAddonInfo('id'))

    def show(self):
        addon = xbmcaddon.Addon()
        # 表示
        for data in self.data:
            url = data['url']
            label = data['label']
            xpath = data['xpath']
            mode = data['mode']
            # フラグ
            flag = data.get('flag',False)
            if flag:
                data['flag'] = False
                # ファイル書き込み
                self.write()
            # コンテクストメニュー
            menu = []
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'mode':Browser.MODE_NODELIST}
            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32922), query))
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'mode':Browser.MODE_LINKLIST}
            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32921), query))
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'mode':Browser.MODE_CAPTURE}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32923), query))
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'mode':Browser.MODE_TEXT}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32924), query))
            values = {'action':'edit', 'label':label.encode('utf-8'), 'url':url, 'xpath':xpath, 'mode':mode}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32911), query))
            values = {'action':'delete', 'url':url, 'xpath':xpath}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((addon.getLocalizedString(32912), query))
            menu.append((addon.getLocalizedString(32913), 'Addon.OpenSettings(%s)' % addon.getAddonInfo('id')))
            # アイテム追加
            if flag:
                item = xbmcgui.ListItem('[COLOR yellow]%s[/COLOR]' % (label or url))
            else:
                item = xbmcgui.ListItem(label or url)
            item.addContextMenuItems(menu, replaceItems=True)
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'mode':mode, 'renew':True}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, mode in (Browser.MODE_NODELIST, Browser.MODE_LINKLIST))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    addon = xbmcaddon.Addon()
    if addon.getSetting('chrome'):
        # 引数
        log(sys.argv)
        args = urlparse.parse_qs(sys.argv[2][1:])
        action = args.get('action', [None])[0]
        label = args.get('label', [''])[0]
        url = args.get('url', [''])[0]
        xpath = args.get('xpath', [''])[0]
        mode = args.get('mode', [''])[0]
        renew = args.get('renew', [False])[0]
        image_file = args.get('image_file', [''])[0]
        text_file = args.get('text_file', [''])[0]
        title = args.get('title', [''])[0]
        output_file = args.get('output_file', [None])[0]
        # アドオン設定
        settings = Settings(('url1','xpath1','url','label','xpath','mode')).clear()
        # actionに応じて処理
        if action is None:
            # スタート画面を表示
            Main().show()
        elif action == 'extract':
            if renew:
                Browser(url).extract(xpath, mode)
            else:
                Browser().extract(xpath, mode)
        elif action == 'append':
            Main().append(label, url, xpath, mode)
        elif action == 'edit':
            Main().edit(label, url, xpath, mode)
        elif action == 'edited':
            Main().edited(settings)
        elif action == 'delete':
            Main().delete(url, xpath)
        # following actions requires isFoldert=False
        elif action == 'show_image':
            show_image(image_file)
        elif action == 'show_text':
            show_text(text_file, title)
        elif action == 'extract_image':
            Browser(url).extract(xpath, mode=Browser.MODE_CAPTURE, output_file=output_file)
        elif action == 'extract_text':
            Browser(url).extract(xpath, mode=Browser.MODE_TEXT, output_file=output_file)
    else:
        addon.openSettings()
