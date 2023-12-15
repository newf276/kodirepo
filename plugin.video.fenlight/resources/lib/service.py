# -*- coding: utf-8 -*-
from modules import service_functions
from modules.kodi_utils import Thread, xbmc_monitor, set_property, kodi_refresh, services_finished_prop, sleep, logger

on_notification_actions = service_functions.OnNotificationActions()

class FenLightMonitor(xbmc_monitor):
	def __init__ (self):
		xbmc_monitor.__init__(self)
		self.startServices()
		self.finishServices()

	def startServices(self):
		try:
			set_property(services_finished_prop, 'false')
			service_functions.CheckSettings().run()
			service_functions.TraktSync().run()
			Thread(target=service_functions.CustomActions().run).start()
			Thread(target=service_functions.CustomFonts().run).start()
			service_functions.RemoveOldDatabases().run()
			Thread(target=service_functions.TraktMonitor().run).start()
			Thread(target=service_functions.UpdateCheck().run).start()
		except: pass

	def finishServices(self):
		set_property(services_finished_prop, 'true')
		sleep(100)
		kodi_refresh()

	def onNotification(self, sender, method, data):
		on_notification_actions.run(sender, method, data)

logger('Fen Light', 'Main Monitor Service Starting')
FenLightMonitor().waitForAbort()
logger('Fen Light', 'Main Monitor Service Finished')