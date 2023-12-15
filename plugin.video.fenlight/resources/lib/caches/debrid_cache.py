# -*- coding: utf-8 -*-
from caches.base_cache import connect_database, get_timestamp
# from modules.kodi_utils import logger

GET_MANY = 'SELECT * FROM debrid_data WHERE hash in (%s)'
SET_MANY = 'INSERT INTO debrid_data VALUES (?, ?, ?, ?)'
REMOVE_MANY = 'DELETE FROM debrid_data WHERE hash=?'
CLEAR = 'DELETE FROM debrid_data'
CLEAR_DEBRID = 'DELETE FROM debrid_data WHERE debrid=?'
CLEAN = 'DELETE from debrid_data WHERE CAST(expires AS INT) <= ?'

class DebridCache:
	def __init__(self):
		self.dbcon = connect_database('debridcache_db')

	def get_many(self, hash_list):
		result = None
		try:
			current_time = get_timestamp()
			cache_data = self.dbcon.execute(GET_MANY % (', '.join('?' for _ in hash_list)), hash_list).fetchall()
			if cache_data:
				if cache_data[0][3] > current_time: result = cache_data
				else: self.remove_many(cache_data)
		except: pass
		return result

	def set_many(self, hash_list, debrid):
		try:
			expires = get_timestamp(24)
			insert_list = [(i[0], debrid, i[1], expires) for i in hash_list]
			self.dbcon.executemany(SET_MANY, insert_list)
		except: pass

	def remove_many(self, old_cached_data):
		try:
			old_cached_data = [(str(i[0]),) for i in old_cached_data]
			self.dbcon.executemany(REMOVE_MANY, old_cached_data)
		except: pass

	def clear_debrid_results(self, debrid):
		try:
			self.dbcon.execute(CLEAR_DEBRID, (debrid,))
			self.dbcon.execute('VACUUM')
			return True
		except: return False
	
	def clear_database(self):
		try:
			self.dbcon.execute(CLEAR)
			self.dbcon.execute('VACUUM')
			return 'success'
		except: return 'failure'

	def clean_database(self):
		try:
			self.dbcon.execute(CLEAN, (get_timestamp(),))
			self.dbcon.execute('VACUUM')
			return True
		except: return False

debrid_cache = DebridCache()