import sys
import xbmc, xbmcaddon, xbmcplugin, xbmcgui

try:
    from urllib import quote  # Python 2
except ImportError:
    from urllib.parse import quote  # Python 3

trailer_addon_id = 'newf276.trailers'
addon_id = xbmcaddon.Addon().getAddonInfo('id')

url = sys.argv[0] + sys.argv[2]
new_url = 'plugin://newf276.trailers/redirect/?url=' + quote(url)
xbmc.log("{} - Re-routing {} -> {}".format(addon_id, url, new_url))

li = xbmcgui.ListItem(path=new_url)
xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
