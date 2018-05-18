# -*- coding: utf-8 -*-

import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

def show_image(imgfile):
    xbmc.executebuiltin('ShowPicture(%s)' % imgfile)

def show_text(txtfile, title=None):
    # ファイル読み込み
    if os.path.isfile(txtfile):
        f = open(txtfile,'r')
        data = f.read()
        f.close()
    else:
        data = ''
    # テキストビューアに表示
    xbmcgui.Dialog().textviewer(title or '(Selected Node)', data)
