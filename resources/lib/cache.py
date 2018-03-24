# -*- coding: utf-8 -*-

import os, datetime, hashlib
import xbmc, xbmcaddon

class Cache:

    def __init__(self):
        # キャッシュディレクトリを作成
        addon = xbmcaddon.Addon()
        self.path = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')), 'cache')
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def clear(self):
        # キャッシュディレクトリをクリア
        file_list = os.listdir(self.path)
        for file_path in file_list:
            os.remove(os.path.join(self.path, file_path))

    def filename(self, key=None, ext='txt'):
        if key:
            filename = '%s.%s' % (hashlib.md5(key).hexdigest(), ext)
        else:
            filename = '%s.%s' % (datetime.now().strftime('%s'), ext)
        return os.path.join(self.path, filename)
