# -*- coding: utf-8 -*-
from caches.base_cache import connect_database
# from modules.kodi_utils import logger

INSERT_FAV = 'INSERT INTO favourites VALUES (?, ?, ?)'
DELETE_FAV = 'DELETE FROM favourites where db_type=? and tmdb_id=?'
SELECT_FAV = 'SELECT tmdb_id, title FROM favourites WHERE db_type=?'
DELETE_TYPE = 'DELETE FROM favourites WHERE db_type=?'

class FavoritesCache:
	def __init__(self):
		self.dbcon = connect_database('favorites_db')

	def set_favourite(self, media_type, tmdb_id, title):
		try:
			self.dbcon.execute(INSERT_FAV, (media_type, str(tmdb_id), title))
			return True
		except: return False

	def delete_favourite(self, media_type, tmdb_id, title):
		try:
			self.dbcon.execute(DELETE_FAV, (media_type, str(tmdb_id)))
			return True
		except: return False

	def get_favorites(self, media_type):
		return [{'tmdb_id': str(i[0]), 'title': str(i[1])} for i in self.dbcon.execute(SELECT_FAV, (media_type,)).fetchall()]

	def clear_favorites(self, media_type):
		self.dbcon.execute(DELETE_TYPE, (media_type,))
		self.dbcon.execute('VACUUM')

favorites_cache = FavoritesCache()
