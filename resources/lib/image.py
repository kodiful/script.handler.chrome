# -*- coding: utf-8 -*-

import os

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

class Image:

    ADDON_PATH = xbmcaddon.Addon().getAddonInfo('path')
    IMAGE_PATH = os.path.join(ADDON_PATH,'resources','media','image')

    LINK100 = os.path.join(IMAGE_PATH,'icons8-internet-30.png')
    LINK500 = os.path.join(IMAGE_PATH,'icons8-internet-480.png')

    INFO100 = os.path.join(IMAGE_PATH,'icons8-search-property-30.png')
    INFO500 = os.path.join(IMAGE_PATH,'icons8-search-property-480.png')
