# -*- coding: utf-8 -*-

import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

def show_image(image_file):
    xbmc.executebuiltin('ShowPicture(%s)' % image_file)

def show_text(text_file, title=None):
    # ファイル読み込み
    if os.path.isfile(text_file):
        f = open(text_file,'r')
        data = f.read()
        f.close()
    else:
        data = ''
    # テキストビューアに表示
    xbmcgui.Dialog().textviewer(title or '(Selected Node)', data)
