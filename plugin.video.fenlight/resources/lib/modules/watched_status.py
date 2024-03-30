# -*- coding: utf-8 -*-
from datetime import datetime
from apis.trakt_api import trakt_watched_status_mark, trakt_official_status, trakt_progress, trakt_get_hidden_items
from caches.base_cache import connect_database, database
from caches.main_cache import main_cache
from caches.trakt_cache import clear_trakt_collection_watchlist_data
from modules import kodi_utils, settings, metadata
from modules.utils import get_datetime, adjust_premiered_date, sort_for_article, make_thread_list
# logger = kodi_utils.logger

sleep, progressDialogBG, Thread, get_video_database_path = kodi_utils.sleep, kodi_utils.progressDialogBG, kodi_utils.Thread, kodi_utils.get_video_database_path
watched_indicators_function, lists_sort_order, date_offset, truncate_watched = settings.watched_indicators, settings.lists_sort_order, settings.date_offset, settings.truncate_watched
get_property, set_property, clear_property = kodi_utils.get_property, kodi_utils.set_property, kodi_utils.clear_property
notification, kodi_refresh = kodi_utils.notification, kodi_utils.kodi_refresh
progress_db_string = 'fenlight_hidden_progress_items'
indicators_dict = {0: 'watched_db', 1: 'trakt_db'}
watched_prop_str, progress_prop_string = '%s_%s_%s_%s_watched', '%s_%s_%s_%s_progress'

def clear_watched_property(watched_indicators=None, media_type=None, truncate_watched_info=None, remove_hidden=True):
	watched_ind = watched_indicators or watched_indicators_function()
	watched_truncate = truncate_watched_info or truncate_watched()
	if not media_type:
		clear_property(watched_prop_str % (watched_ind, 'movie', watched_truncate, remove_hidden))
		clear_property(watched_prop_str % (watched_ind, 'episode', watched_truncate, remove_hidden))
	else:
		clear_property(watched_prop_str % (watched_ind, media_type, watched_truncate, remove_hidden))

def clear_progress_property(watched_indicators=None, media_type=None, truncate_watched_info=None, remove_hidden=True):
	watched_ind = watched_indicators or watched_indicators_function()
	watched_truncate = truncate_watched_info or truncate_watched()
	if not media_type:
		clear_property(progress_prop_string % (watched_ind, 'movie', watched_truncate, remove_hidden))
		clear_property(progress_prop_string % (watched_ind, 'episode', watched_truncate, remove_hidden))
	else:
		clear_property(progress_prop_string % (watched_ind, media_type, watched_truncate, remove_hidden))

def get_media_info(watched_indicators, media_type, include_progress=False, progress_only=False, remove_hidden=True):
	dbcon = None
	truncate_watched_info = truncate_watched()
	if not progress_only:
		try:
			prop_string = watched_prop_str % (watched_indicators, media_type, truncate_watched_info, remove_hidden)
			try: watched_info = eval(get_property(prop_string))
			except:
				dbcon = get_database(watched_indicators)
				watched_info = dbcon.execute("SELECT media_id, season, episode, title, last_played FROM watched WHERE db_type = ?", (media_type,)).fetchall()
				if media_type == 'episode' and remove_hidden:
					hidden_list = get_hidden_progress_items(watched_indicators)
					watched_info = [i for i in watched_info if not int(i[0]) in hidden_list]
				if truncate_watched_info:
					try:
						if media_type == 'movie': watched_info = sorted(watched_info, key=lambda x: x[4], reverse=True)[:50]
						else:
							seen = set()
							includes = [i[0] for i in sorted(watched_info, key=lambda x: (x[4], x[0], x[1], x[2]), reverse=True) if not (i[0] in seen or seen.add(i[0]))][:20]
							watched_info = [i for i in watched_info if i[0] in includes]
					except: pass
				set_property(prop_string, repr(watched_info))
		except: watched_indicators = []
	if include_progress:
		try:
			prop_string = progress_prop_string % (watched_indicators, media_type, truncate_watched_info)
			try: progress_info = eval(get_property(prop_string))
			except:
				if not dbcon: dbcon = get_database(watched_indicators)
				progress_info = dbcon.execute("SELECT media_id, resume_point, curr_time, season, episode, resume_id, last_played, title FROM progress WHERE db_type = ?",
											(media_type,)).fetchall()
				if media_type == 'episode' and remove_hidden:
					hidden_list = get_hidden_progress_items(watched_indicators)
					progress_info = [i for i in progress_info if not int(i[0]) in hidden_list]
				if truncate_watched_info: progress_info = progress_info[:50 if media_type == 'movie' else 20]
				set_property(prop_string, repr(progress_info))
		except: progress_info = []
		if progress_only: return progress_info
		return watched_info, progress_info
	return watched_info

def get_hidden_progress_items(watched_indicators):
	try:
		if watched_indicators == 0: return main_cache.get(progress_db_string) or []
		else: return trakt_get_hidden_items('progress_watched')
	except: return []

def hide_unhide_progress_items(params):
	action, tmdb_id = params['action'], int(params.get('media_id', '0'))
	clear_watched_property(media_type='episode')
	current_items = main_cache.get(progress_db_string) or []
	if action == 'hide': current_items.append(tmdb_id)
	else: current_items.remove(tmdb_id)
	main_cache.set(progress_db_string, current_items, 1825)
	return kodi_refresh()

def get_database(watched_indicators=None):
	return connect_database(indicators_dict[watched_indicators or watched_indicators_function()])

def get_next_episodes(watched_info):
	seen = set()
	watched_info = [i for i in watched_info if not i[0] is None]
	watched_info.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
	return [{'media_ids': {'tmdb': int(i[0])}, 'season': int(i[1]), 'episode': int(i[2]), 'title': i[3], 'last_played': i[4]} \
							for i in watched_info if not (i[0] in seen or seen.add(i[0]))]

def get_recently_watched(media_type, short_list=1, dummy1=None):
	watched_indicators = watched_indicators_function()
	watched_info = get_media_info(watched_indicators, media_type)
	if media_type == 'movie':
		data = sorted([{'media_id': i[0], 'title': i[3], 'last_played': i[4]} for i in watched_info], key=lambda x: x['last_played'], reverse=True)
	else:
		if short_list:
			data = sorted([{'media_ids': {'tmdb': int(i[0])}, 'season': int(i[1]), 'episode': int(i[2]), 'title': i[3], 'last_played': i[4]}
						for i in watched_info], key=lambda x: (x['last_played'], x['media_ids']['tmdb'], x['season'], x['episode']), reverse=True)
		else:
			seen = set()
			data = sorted([{'media_ids': {'tmdb': int(i[0])}, 'season': int(i[1]), 'episode': int(i[2]), 'title': i[3], 'last_played': i[4]}
						for i in sorted(watched_info, key=lambda x: (x[4], x[0], x[1], x[2]), reverse=True) if not (i[0] in seen or seen.add(i[0]))],
						key=lambda x: (x['last_played'], x['media_ids']['tmdb'], x['season'], x['episode']), reverse=True)
	if short_list: return data[0:20]
	else: return data

def get_progress_percent(bookmarks, tmdb_id, season='', episode=''):
	try: percent = str(round(float(detect_bookmark(bookmarks, tmdb_id, season, episode)[0])))
	except: percent = None
	return percent

def detect_bookmark(bookmarks, tmdb_id, season='', episode=''):
	return [(i[1], i[2], i[5]) for i in bookmarks if i[0] == str(tmdb_id) and i[3] == season and i[4] == episode][0]

def get_bookmarks(watched_indicators, media_type):
	try:
		dbcon = get_database(watched_indicators)
		info = dbcon.execute("SELECT media_id, resume_point, curr_time, season, episode, resume_id FROM progress WHERE db_type = ?", (media_type,)).fetchall()
	except: info = []
	return info

def erase_bookmark(media_type, tmdb_id, season='', episode='', refresh='false'):
	try:
		watched_indicators = watched_indicators_function()
		clear_watched_property(watched_indicators, media_type)
		clear_progress_property(watched_indicators, media_type)
		bookmarks = get_bookmarks(watched_indicators, media_type)
		if media_type == 'episode': season, episode = int(season), int(episode)
		try: resume_id = detect_bookmark(bookmarks, tmdb_id, season, episode)[2]
		except: return
		if watched_indicators == 1:
			sleep(1000)
			trakt_progress('clear_progress', media_type, tmdb_id, 0, season, episode, resume_id)
		dbcon = get_database()
		dbcon.execute("DELETE FROM progress where db_type = ? and media_id = ? and season = ? and episode = ?", (media_type, tmdb_id, season, episode))
		refresh_container(refresh == 'true')
	except: pass

def batch_erase_bookmark(watched_indicators, insert_list, action):
	try:
		clear_watched_property(watched_indicators)
		clear_progress_property(watched_indicators)
		if action == 'mark_as_watched': modified_list = [(i[0], i[1], i[2], i[3]) for i in insert_list]
		else: modified_list = insert_list
		if watched_indicators == 1:
			def _process():
				media_type, tmdb_id = insert_list[0][0], insert_list[0][1]
				bookmarks = get_bookmarks(watched_indicators, media_type)
				for i in insert_list:
					try: resume_point, curr_time, resume_id = detect_bookmark(bookmarks, tmdb_id, i[2], i[3])
					except: continue
					try:
						sleep(1100)
						trakt_progress('clear_progress', i[0], i[1], 0, i[2], i[3], resume_id)
					except: pass
			Thread(target=_process).start()
		dbcon = get_database(watched_indicators)
		dbcon.executemany("DELETE FROM progress where db_type = ? and media_id = ? and season = ? and episode = ?", modified_list)
	except: pass

def set_bookmark(params):
	try:
		watched_indicators = watched_indicators_function()
		media_type, tmdb_id, curr_time, total_time = params.get('media_type'), params.get('tmdb_id'), params.get('curr_time'), params.get('total_time')
		clear_watched_property(watched_indicators, media_type)
		clear_progress_property(watched_indicators, media_type)
		refresh = False if params.get('from_playback', 'false') == 'true' else True
		title, season, episode = params.get('title'), params.get('season'), params.get('episode')
		adjusted_current_time = float(curr_time) - 5
		resume_point = round(adjusted_current_time/float(total_time)*100,1)
		if watched_indicators == 1:
			if trakt_official_status(media_type) == False: return
			else: trakt_progress('set_progress', media_type, tmdb_id, resume_point, season, episode, refresh_trakt=True)
		else:
			erase_bookmark(media_type, tmdb_id, season, episode)
			last_played = get_last_played_value(watched_indicators)
			dbcon = get_database(watched_indicators)
			dbcon.execute("INSERT OR REPLACE INTO progress VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
						(media_type, tmdb_id, season, episode, str(resume_point), str(curr_time), last_played, 0, title))
		refresh_container(refresh)
	except: pass

def get_in_progress_movies(dummy_arg, page_no):
	data = [{'media_id': i[0], 'title': i[1], 'last_played': i[2]} for i in get_media_info(watched_indicators_function(), 'movie', True, True) if not i[0] == '']
	if lists_sort_order('progress') == 0: data = sort_for_article(data, 'title')
	else: data = sorted(data, key=lambda x: x['last_played'], reverse=True)
	return data

def get_in_progress_tvshows(dummy_arg, page_no):
	def _process(item):
		tmdb_id = item['media_id']
		meta = metadata.tvshow_meta('tmdb_id', tmdb_id, get_datetime())
		watched_status = get_watched_status_tvshow(watched_info, tmdb_id, meta.get('total_aired_eps'))
		status = meta.get('status', '')
		if watched_status[0] == 0: data_append(item)
	data, duplicates = [], set()
	data_append, duplicates_add = data.append, duplicates.add
	watched_indicators = watched_indicators_function()
	watched_info = get_media_info(watched_indicators, 'episode')
	watched_info.sort(key=lambda x: (x[0], x[4]), reverse=True)
	prelim_data = [{'media_id': i[0], 'title': i[3], 'last_played': i[4]} for i in watched_info if not (i[0] in duplicates or duplicates_add(i[0]))]
	threads = list(make_thread_list(_process, prelim_data))
	[i.join() for i in threads]
	if lists_sort_order('progress') == 0: data = sort_for_article(data, 'title')
	else: data = sorted(data, key=lambda x: x['last_played'], reverse=True)
	return data

def get_in_progress_episodes():
	data = get_media_info(watched_indicators_function(), 'episode', True, True)
	if lists_sort_order('progress') == 0: data = sort_for_article(data, 7)
	else: data.sort(key=lambda k: k[6], reverse=True)
	episode_list = [{'media_ids': {'tmdb': i[0]}, 'season': int(i[3]), 'episode': int(i[4]), 'resume_point': float(i[1])} for i in data]
	return episode_list

def get_watched_items(media_type, page_no):
	watched_indicators = watched_indicators_function()
	if media_type == 'tvshow':
		def _process(item):
			tmdb_id = item['media_id']
			meta = metadata.tvshow_meta('tmdb_id', tmdb_id, get_datetime())
			playcount = get_watched_status_tvshow(watched_info, tmdb_id, meta.get('total_aired_eps'))[0]
			status = meta.get('status', '')
			if playcount == 1: data_append(item)
		watched_info = get_media_info(watched_indicators, 'episode')
		duplicates, data = set(), []
		duplicates_add, data_append = duplicates.add, data.append
		prelim_data = [{'media_id': i[0], 'title': i[3], 'last_played': i[4]} for i in watched_info if not (i[0] in duplicates or duplicates_add(i[0]))]
		threads = list(make_thread_list(_process, prelim_data))
		[i.join() for i in threads]
	else:
		watched_info = get_media_info(watched_indicators, 'movie')
		data = [{'media_id': i[0], 'title': i[3], 'last_played': i[4]} for i in watched_info]
	if lists_sort_order('watched') == 0: data = sort_for_article(data, 'title')
	else: data = sorted(data, key=lambda x: x['last_played'], reverse=True)
	return data

def get_watched_status_movie(watched_info, tmdb_id):
	try:
		watched = [i for i in watched_info if i[0] == tmdb_id]
		if watched: return 1
		return 0
	except: return 0

def get_watched_status_tvshow(watched_info, tmdb_id, aired_eps):
	playcount, watched, unwatched = 0, 0, aired_eps
	try:
		watched = min(len([i for i in watched_info if i[0] == tmdb_id]), aired_eps)
		unwatched = aired_eps - watched
		if watched >= aired_eps and not aired_eps == 0: playcount = 1
	except: pass
	return playcount, watched, unwatched

def get_watched_status_season(watched_info, tmdb_id, season, aired_eps):
	playcount, watched, unwatched = 0, 0, aired_eps
	try:
		watched = min(len([i for i in watched_info if i[0] == tmdb_id and i[1] == season]), aired_eps)
		unwatched = aired_eps - watched
		if watched >= aired_eps and not aired_eps == 0: playcount = 1
	except: pass
	return playcount, watched, unwatched

def get_watched_status_episode(watched_info, tmdb_id, season='', episode=''):
	try:
		watched = [i for i in watched_info if i[0] == tmdb_id and (i[1], i[2]) == (season, episode)]
		if watched: return 1
		else: return 0
	except: return 0

def mark_movie(params):
	action, media_type = params.get('action'), 'movie'
	refresh, from_playback = params.get('refresh', 'true') == 'true', params.get('from_playback', 'false') == 'true'
	if from_playback: refresh = False
	tmdb_id, title = params.get('tmdb_id'), params.get('title')
	watched_indicators = watched_indicators_function()
	if watched_indicators == 1:
		if from_playback == 'true' and trakt_official_status(media_type) == False: sleep(1000)
		elif not trakt_watched_status_mark(action, 'movies', tmdb_id): return notification('Error')
		clear_trakt_collection_watchlist_data('watchlist', media_type)
	watched_status_mark(watched_indicators, media_type, tmdb_id, action, title=title)
	refresh_container(refresh)

def mark_tvshow(params):
	title, action, tmdb_id = params.get('title', ''), params.get('action'), params.get('tmdb_id')
	try: tvdb_id = int(params.get('tvdb_id', '0'))
	except: tvdb_id = 0
	watched_indicators = watched_indicators_function()
	progressDialogBG.create('[B]Please Wait..[/B]', '')
	if watched_indicators == 1:
		if not trakt_watched_status_mark(action, 'shows', tmdb_id, tvdb_id): return notification('Error')
		clear_trakt_collection_watchlist_data('watchlist', 'tvshow')
	current_date = get_datetime()
	insert_list = []
	insert_append = insert_list.append
	meta = metadata.tvshow_meta('tmdb_id', tmdb_id, get_datetime())
	season_data = meta['season_data']
	season_data = [i for i in season_data if i['season_number'] > 0]
	total = len(season_data)
	last_played = get_last_played_value(watched_indicators)
	for count, item in enumerate(season_data, 1):
		season_number = item['season_number']
		ep_data = metadata.episodes_meta(season_number, meta)
		for ep in ep_data:
			season_number = ep['season']
			ep_number = ep['episode']
			display = '%s - S%.2dE%.2d' % (title, int(season_number), int(ep_number))
			progressDialogBG.update(int(float(count)/float(total)*100), '[B]Please Wait..[/B]', display)
			episode_date, premiered = adjust_premiered_date(ep['premiered'], date_offset())
			if episode_date and current_date < episode_date: continue
			insert_append(make_batch_insert(action, 'episode', tmdb_id, season_number, ep_number, last_played, title))
	batch_watched_status_mark(watched_indicators, insert_list, action)
	progressDialogBG.close()
	refresh_container()

def mark_season(params):
	season = int(params.get('season'))
	if season == 0: return notification('Failed')
	insert_list = []
	insert_append = insert_list.append
	action, title, tmdb_id = params.get('action'), params.get('title'), params.get('tmdb_id')
	try: tvdb_id = int(params.get('tvdb_id', '0'))
	except: tvdb_id = 0
	watched_indicators = watched_indicators_function()
	heading = '[B]Mark Watched %s[/B]' if action == 'mark_as_watched' else '[B]Mark Unwatched %s[/B]'
	if watched_indicators == 1:
		if not trakt_watched_status_mark(action, 'season', tmdb_id, tvdb_id, season): return notification('Error')
		clear_trakt_collection_watchlist_data('watchlist', 'tvshow')
	progressDialogBG.create('[B]Please Wait..[/B]', '')
	current_date = get_datetime()
	meta = metadata.tvshow_meta('tmdb_id', tmdb_id, get_datetime())
	ep_data = metadata.episodes_meta(season, meta)
	last_played = get_last_played_value(watched_indicators)
	for count, item in enumerate(ep_data, 1):
		season_number = item['season']
		ep_number = item['episode']
		display = '%s - S%.2dE%.2d' % (title, season_number, ep_number)
		episode_date, premiered = adjust_premiered_date(item['premiered'], date_offset())
		if episode_date and current_date < episode_date: continue
		progressDialogBG.update(int(float(count) / float(len(ep_data)) * 100), '[B]Please Wait..[/B]', display)
		insert_append(make_batch_insert(action, 'episode', tmdb_id, season_number, ep_number, last_played, title))
	batch_watched_status_mark(watched_indicators, insert_list, action)
	progressDialogBG.close()
	refresh_container()

def mark_episode(params):
	action, media_type = params.get('action'), 'episode'
	refresh, from_playback = params.get('refresh', 'true') == 'true', params.get('from_playback', 'false') == 'true'
	if from_playback: refresh = False
	tmdb_id = params.get('tmdb_id')
	try: tvdb_id = int(params.get('tvdb_id', '0'))
	except: tvdb_id = 0
	season, episode, title = int(params.get('season')), int(params.get('episode')), params.get('title')
	watched_indicators = watched_indicators_function()
	if season == 0: notification('Failed'); return
	if watched_indicators == 1:
		if from_playback == 'true' and trakt_official_status(media_type) == False: sleep(1000)
		elif not trakt_watched_status_mark(action, media_type, tmdb_id, tvdb_id, season, episode): return notification('Error')
		clear_trakt_collection_watchlist_data('watchlist', 'tvshow')
	watched_status_mark(watched_indicators, media_type, tmdb_id, action, season, episode, title)
	refresh_container(refresh)

def watched_status_mark(watched_indicators, media_type='', tmdb_id='', action='', season='', episode='', title=''):
	clear_watched_property(watched_indicators, media_type)
	clear_progress_property(watched_indicators, media_type)
	try:
		last_played = get_last_played_value(watched_indicators)
		dbcon = get_database(watched_indicators)
		if action == 'mark_as_watched':
			dbcon.execute("INSERT OR REPLACE INTO watched VALUES (?, ?, ?, ?, ?, ?)", (media_type, tmdb_id, season, episode, last_played, title))
		elif action == 'mark_as_unwatched':
			dbcon.execute("DELETE FROM watched WHERE (db_type = ? and media_id = ? and season = ? and episode = ?)", (media_type, tmdb_id, season, episode))
		erase_bookmark(media_type, tmdb_id, season, episode)
	except: notification('Error')

def batch_watched_status_mark(watched_indicators, insert_list, action):
	clear_watched_property(watched_indicators, media_type)
	clear_progress_property(watched_indicators, media_type)
	try:
		dbcon = get_database(watched_indicators)
		if action == 'mark_as_watched':
			dbcon.executemany("INSERT OR IGNORE INTO watched VALUES (?, ?, ?, ?, ?, ?)", insert_list)
		elif action == 'mark_as_unwatched':
			dbcon.executemany("DELETE FROM watched WHERE (db_type = ? and media_id = ? and season = ? and episode = ?)", insert_list)
		batch_erase_bookmark(watched_indicators, insert_list, action)
	except: notification('Error')

def get_last_played_value(watched_indicators):
	if watched_indicators == 0: return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	else: return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')

def make_batch_insert(action, media_type, tmdb_id, season, episode, last_played, title):
	if action == 'mark_as_watched': return (media_type, tmdb_id, season, episode, last_played, title)
	else: return (media_type, tmdb_id, season, episode)

def clear_local_bookmarks():
	try:
		dbcon = database.connect(get_video_database_path())
		file_ids = dbcon.execute("SELECT idFile FROM files WHERE strFilename LIKE 'plugin.video.fenlight%'").fetchall()
		for i in ('bookmark', 'streamdetails', 'files'): dbcon.executemany("DELETE FROM %s WHERE idFile=?" % i, file_ids)
	except: pass

def refresh_container(refresh=True):
	if refresh: kodi_refresh()
