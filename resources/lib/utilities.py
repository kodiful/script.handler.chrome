# -*- coding: utf-8 -*-

import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

def show_image(image_file):
    xbmc.executebuiltin('ShowPicture(%s)' % image_file)

def show_text(text_file, title=None):
    # ファイル読み込み
    if os.path.isfile(text_file):
        f = open(text_file,'r')
        data = f.read().decode('utf-8')
        f.close()
    else:
        data = ''
    # テキストビューア
    viewer_id = 10147
    # ウィンドウを開く
    xbmc.executebuiltin('ActivateWindow(%s)' % viewer_id)
    # ウィンドウの用意ができるまで1秒待つ
    xbmc.sleep(1000)
    # ウィンドウへ書き込む
    viewer = xbmcgui.Window(viewer_id)
    viewer.getControl(1).setLabel(title or '(Untitled)')
    viewer.getControl(5).setText(data)
