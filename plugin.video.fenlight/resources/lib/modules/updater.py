# -*- coding: utf-8 -*-
import shutil
import time
import sqlite3 as database
from zipfile import ZipFile
from modules.utils import string_alphanum_to_num
from modules.settings import update_check_test
from modules import kodi_utils 
# logger = kodi_utils.logger

requests, addon_info, unzip, confirm_dialog, ok_dialog = kodi_utils.requests, kodi_utils.addon_info, kodi_utils.unzip, kodi_utils.confirm_dialog, kodi_utils.ok_dialog
translate_path, osPath, delete_file, execute_builtin = kodi_utils.translate_path, kodi_utils.osPath, kodi_utils.delete_file, kodi_utils.execute_builtin
update_local_addons, disable_enable_addon, close_all_dialog = kodi_utils.update_local_addons, kodi_utils.disable_enable_addon, kodi_utils.close_all_dialog
update_kodi_addons_db, notification = kodi_utils.update_kodi_addons_db, kodi_utils.notification

packages_dir = translate_path('special://home/addons/packages/')
home_addons_dir = translate_path('special://home/addons/')
destination_check = translate_path('special://home/addons/plugin.video.fenlight/')
addon_dir = 'plugin.video.fenlight'
repo_location = {True: 'tikipeter.test', False: 'tikipeter.github.io'}
zipfile_name = 'plugin.video.fenlight-%s.zip'
versions_url = 'https://github.com/Tikipeter/%s/raw/main/packages/fen_light_version'
location_url = 'https://github.com/Tikipeter/%s/raw/main/packages/%s'
heading_str = 'Fen Light Updater'
notification_error_str = 'Fen Light Update Error'
notification_occuring_str = 'Fen Light Update Occuring'
notification_available_str = 'Fen Light Update Available'
result_line = 'Installed Version: [B]%s[/B][CR]Online Version: [B]%s[/B][CR][CR] %s'
no_update_line = '[B]No Update Available[/B]'
update_available_line = '[B]An Update is Available[/B][CR]Perform Update?'
success_line = 'Success.[CR]Fen Light updated to version [B]%s[/B]'
error_line = 'Error Updating.[CR]Please install new update manually'


def get_versions(is_test=False):
	try:
		result = requests.get(versions_url % repo_location[is_test])
		if result.status_code != 200: return None, None
		online_version = result.text.replace('\n', '')
		current_version = addon_info('version')
		return current_version, online_version
	except: return None, None

def update_check(action=4):
	update_test_versions = update_check_test()
	no_update, is_test = True, False
	if action == 3: return
	current_version, online_version = get_versions()
	if not current_version: return notification(notification_error_str)
	if string_alphanum_to_num(current_version) == string_alphanum_to_num(online_version):
		if update_test_versions:
			current_version, online_version = get_versions(is_test=True)
			if current_version != online_version: no_update, is_test = False, True
		if no_update:
			if action == 4: return ok_dialog(heading=heading_str, text=result_line % (current_version, online_version, no_update_line))
			return
	if action in (0, 4):
		if not confirm_dialog(heading=heading_str, text=result_line % (current_version, online_version, update_available_line)): return
	if action == 1: notification(notification_occuring_str)
	if action == 2: return notification(notification_available_str)
	return update_addon(online_version, action, is_test)

def update_addon(new_version, action, is_test):
	close_all_dialog()
	execute_builtin('ActivateWindow(Home)', True)
	zip_name = zipfile_name % new_version
	url = location_url % (repo_location[is_test], zip_name)
	result = requests.get(url, stream=True)
	if result.status_code != 200: return ok_dialog(heading=heading_str, text=error_line)
	zip_location = osPath.join(packages_dir, zip_name)
	with open(zip_location, 'wb') as f: shutil.copyfileobj(result.raw, f)
	shutil.rmtree(osPath.join(home_addons_dir, addon_dir))
	success = unzip(zip_location, home_addons_dir, destination_check)
	delete_file(zip_location)
	if not success: return ok_dialog(heading=heading_str, text=error_line)
	if action in (0, 4): ok_dialog(heading=heading_str, text=success_line % new_version)
	update_local_addons()
	disable_enable_addon()
	update_kodi_addons_db()
