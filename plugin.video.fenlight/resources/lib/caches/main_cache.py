# -*- coding: utf-8 -*-
from caches.base_cache import BaseCache, get_timestamp
# from modules.kodi_utils import logger

GET_ALL = 'SELECT id FROM maincache'
DELETE_ALL = 'DELETE FROM maincache'
LIKE_SELECT = 'SELECT id from maincache where id LIKE %s'
LIKE_DELETE = 'DELETE FROM maincache WHERE id LIKE %s'
CLEAN = 'DELETE from maincache WHERE CAST(expires AS INT) <= ?'

class MainCache(BaseCache):
	def __init__(self):
		BaseCache.__init__(self, 'maincache_db', 'maincache')

	def delete_all(self):
		try:
			for i in self.dbcon.execute(GET_ALL): self.delete_memory_cache(str(i[0]))
			self.dbcon.execute(DELETE_ALL)
			self.dbcon.execute('VACUUM')
		except: return

	def delete_all_folderscrapers(self):
		remove_list = [str(i[0]) for i in self.dbcon.execute(LIKE_SELECT % "'FOLDERSCRAPER_%'").fetchall()]
		if not remove_list: return
		try:
			self.dbcon.execute(LIKE_DELETE % "'FOLDERSCRAPER_%'")
			self.dbcon.execute('VACUUM')
			for item in remove_list: self.delete_memory_cache(str(item))
		except: pass

	def clean_database(self):
		try:
			self.dbcon.execute(CLEAN, (get_timestamp(),))
			self.dbcon.execute('VACUUM')
			return True
		except: return False

main_cache = MainCache()

def cache_object(function, string, args, json=True, expiration=24):
	cache = main_cache.get(string)
	if cache is not None: return cache
	if isinstance(args, list): args = tuple(args)
	else: args = (args,)
	if json: result = function(*args).json()
	else: result = function(*args)
	main_cache.set(string, result, expiration=expiration)
	return result
