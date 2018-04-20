# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

import urlparse, urllib
import sys, os, json
import datetime

from resources.lib.browser import Browser
from resources.lib.common import log, notify
from resources.lib.utilities import show_image, show_text

#-------------------------------------------------------------------------------
class Settings:

    DEFAULT = {
        'itemid':       '',
        'url':          'http://',
        'label':        '',
        'xpath':        '//html',
        'target1':       '0',
        'target2':       '0',
    }

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.data = {}
        for key in self.DEFAULT.keys():
            self.data[key] = self.addon.getSetting(key)

    def values(self):
        for key in self.DEFAULT.keys():
            self.addon.setSetting(key, self.DEFAULT[key])
        return self.data

#-------------------------------------------------------------------------------
class Arguments:

    DEFAULT = {
        'action':       None,
        'label':        '',
        'url':          '',
        'xpath':        '',
        'target':       '',
        'itemid':       '',
        'renew':        '',
        'image_file':   '',
        'text_file':    '',
        'title':        '',
        'wav_file':     '',
    }

    def __init__(self):
        args = urlparse.parse_qs(sys.argv[2][1:])
        self.data = {}
        for key in self.DEFAULT.keys():
            self.data[key] = args.get(key, [self.DEFAULT[key]])[0]

    def values(self):
        args = []
        for key in ('action','label','url','xpath','target','itemid','renew','image_file','text_file','title','wav_file'):
            args.append(self.data[key])
        return args

#-------------------------------------------------------------------------------
class Main:

    filepath = None
    data = None

    def __init__(self, filename='start.json'):
        self.addon = xbmcaddon.Addon()
        profile = xbmc.translatePath(self.addon.getAddonInfo('profile'))
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

    def delete(self, itemid):
        data1 = []
        for data in self.data:
            if itemid != data['itemid']:
                data1.append(data)
        self.data = data1
        self.write()
        # スタート画面を更新
        xbmc.executebuiltin('Container.Update(plugin://%s)' % self.addon.getAddonInfo('id'))

    def edit(self, label, url, xpath, target, itemid):
        # 設定画面に反映
        self.addon.setSetting('itemid', itemid)
        self.addon.setSetting('url', url)
        self.addon.setSetting('label', label)
        self.addon.setSetting('xpath', xpath)
        self.addon.setSetting('target1', target)
        self.addon.setSetting('target2', target)
        # 設定画面を開く
        self.addon.openSettings()

    def edited(self, settings):
        # 設定を取得
        itemid = settings['itemid']
        url = settings['url']
        label = settings['label']
        xpath = settings['xpath']
        if self.addon.getSetting('tts'):
            target = settings['target2']
        else:
            target = settings['target1']
        # 設定更新
        self.append(label, url, xpath, target, itemid)

    def append(self, label, url, xpath, target, itemid):
        # 文字コード変換
        if isinstance(label, str): label = label.decode('utf-8')
        if isinstance(url, str): url = url.decode('utf-8')
        if isinstance(xpath, str): xpath = xpath.decode('utf-8')
        if isinstance(target, str): target = target.decode('utf-8')
        # 設定更新
        for data in self.data:
            if itemid == data['itemid']:
                # 既存の設定を更新
                data['url'] = url
                data['label'] = label
                data['xpath'] = xpath
                data['target'] = int(target)
                # 更新フラグを設定
                data['flag'] = True
                break
        else:
            # 追加情報を取得
            info = Browser(url).extract(xpath)
            # 設定を追加
            data = {}
            data['itemid'] = datetime.datetime.now().strftime('%s')
            data['url'] = url
            data['label'] = label or info['title'] or '(Untitled)'
            data['xpath'] = info['optimized_xpath']
            data['target'] = int(target)
            # 更新フラグを設定
            data['flag'] = True
            self.data.append(data)
        # ファイル書き込み
        self.write()
        # スタート画面を更新
        xbmc.executebuiltin('Container.Update(plugin://%s)' % self.addon.getAddonInfo('id'))

    def show(self):
        # 表示
        for data in self.data:
            url = data['url']
            label = data['label']
            xpath = data['xpath']
            target = data['target']
            itemid = data['itemid']
            # フラグ
            flag = data.get('flag',False)
            if flag:
                data['flag'] = False
                # ファイル書き込み
                self.write()
            # コンテクストメニュー
            menu = []
            #### ノードリストを表示する
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'target':Browser.TARGET_NODELIST, 'renew':True}
            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((self.addon.getLocalizedString(32922), query))
            #### リンクリストを表示する
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'target':Browser.TARGET_LINKLIST, 'renew':True}
            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((self.addon.getLocalizedString(32921), query))
            #### キャプチャを表示する
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'target':Browser.TARGET_CAPTURE, 'renew':True}
            #query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((self.addon.getLocalizedString(32923), query))
            #### テキストを表示する
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'target':Browser.TARGET_TEXT, 'renew':True}
            #query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            #### テキストを音声合成する
            menu.append((self.addon.getLocalizedString(32924), query))
            if self.addon.getSetting('tts'):
                values = {'action':'extract', 'url':url, 'xpath':xpath, 'target':Browser.TARGET_WAV, 'renew':True}
                #query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                query = 'Container.Update(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
                menu.append((self.addon.getLocalizedString(32925), query))
            #### この項目を設定する
            values = {'action':'edit', 'label':label.encode('utf-8'), 'url':url, 'xpath':xpath, 'target':target, 'itemid':itemid}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((self.addon.getLocalizedString(32911), query))
            #### この項目を削除する
            values = {'action':'delete', 'itemid':itemid}
            query = 'RunPlugin(%s?%s)' % (sys.argv[0], urllib.urlencode(values))
            menu.append((self.addon.getLocalizedString(32912), query))
            #### アドオン設定
            menu.append((self.addon.getLocalizedString(32913), 'Addon.OpenSettings(%s)' % self.addon.getAddonInfo('id')))
            # アイテム追加
            if flag:
                item = xbmcgui.ListItem('[COLOR yellow]%s[/COLOR]' % (label or url))
            else:
                item = xbmcgui.ListItem(label or url)
            item.addContextMenuItems(menu, replaceItems=True)
            values = {'action':'extract', 'url':url, 'xpath':xpath, 'target':target, 'renew':True}
            query = '%s?%s' % (sys.argv[0], urllib.urlencode(values))
            #xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, target in (Browser.TARGET_NODELIST, Browser.TARGET_LINKLIST))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), query, item, True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

#-------------------------------------------------------------------------------
if __name__  == '__main__':
    # アドオン
    addon = xbmcaddon.Addon()
    # 音声合成アドオンの有無を確認
    try:
        tts = 'script.handler.tts'
        xbmcaddon.Addon(tts)
        addon.setSetting('tts', tts)
    except:
        addon.setSetting('tts', '')
    # chromedriverの設定を確認
    if addon.getSetting('chrome'):
        # 引数
        (action,label,url,xpath,target,itemid,renew,image_file,text_file,title,wav_file) = Arguments().values()
        # アドオン設定
        settings = Settings().values()
        # actionに応じて処理
        if action is None:
            # スタート画面を表示
            Main().show()
        elif action == 'extract':
            if renew:
                Browser(url).extract(xpath, target)
            else:
                Browser().extract(xpath, target)
        elif action == 'append':
            Main().append(label, url, xpath, target, itemid)
        elif action == 'edit':
            Main().edit(label, url, xpath, target, itemid)
        elif action == 'edited':
            Main().edited(settings)
        elif action == 'delete':
            Main().delete(itemid)
        elif action == 'show_image':
            show_image(image_file)
        elif action == 'show_text':
            show_text(text_file, title)
        # for plugin execution
        elif action == 'files':
            Browser(url).extract(xpath, target=Browser.TARGET_FILES, image_file=image_file, text_file=text_file, wav_file=wav_file)
    else:
        addon.openSettings()
