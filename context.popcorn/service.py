import xbmc
import xbmcaddon

properties = [
    "context.popcorn.quickResume",
    "context.popcorn.shuffle",
    "context.popcorn.playFromRandomPoint",
    "context.popcorn.rescrape",
    "context.popcorn.rescrape_ss",
    "context.popcorn.sourceSelect",
    "context.popcorn.findSimilar",
    "context.popcorn.browseShow",
    "context.popcorn.browseSeason",
    "context.popcorn.traktManager",
]


class PropertiesUpdater(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.addon = xbmcaddon.Addon()
        self._update_window_properties()

    def __del__(self):
        del self.addon

    def onSettingsChanged(self):
        self._update_window_properties()

    def _update_window_properties(self):
        for prop in properties:
            setting = self.addon.getSetting(prop)
            if setting == "false":
                xbmc.executebuiltin(f"SetProperty({prop},{setting},home)")
            else:
                xbmc.executebuiltin(f"ClearProperty({prop},home)")
            xbmc.log(f'Context menu item {"disabled" if setting == "false" else "enabled"}: {prop}')


xbmc.log("context.popcorn service: starting", xbmc.LOGINFO)

try:
    # start monitoring settings changes events
    properties_monitor = PropertiesUpdater()

    # wait until abort is requested
    properties_monitor.waitForAbort()
except Exception as e:
    xbmc.log(f"context.popcorn service: error - {e}", xbmc.LOGERROR)
finally:
    del properties_monitor

xbmc.log("context.popcorn service: stopped", xbmc.LOGINFO)
