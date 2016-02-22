# mode:
#	c	compress
#	e	encrypt
#	p	pack
#	a	advanced encrypt

RULE_LIST = [
#	[src_path, dst_path, mode:cev, skips:path1,path2]

	["../../resource/clientsettings", "clientsettings.pk", "cep"],
	["../../resource/settings", "settings.pk", "cep"],
	["../../resource/represent", "represent.pk", "cep"],
	
	["../../resource/res/audio", "res/audio", ""],
	["../../resource/res/bullet", "res/bullet", ""],
	["../../resource/res/character/*/*", "res/character/$1/$2.pk", "cep", "*.md5mesh,*.md5anim"],
	["../../resource/res/doodads/*", "res/doodads/$1.pk", "cep"],
	["../../resource/res/effect", "res/effect", ""],
	["../../resource/res/fonts", "res/fonts.pk", "cep"],
	["../../resource/res/maps/*", "res/maps/$1.pk", "cep", "../../resource/res/maps/main*"],
	["../../resource/res/maps/main*", "res/maps/main$1", "e"],
	["../../resource/res/particleeffect/textures", "res/particleeffect/textures", "e"],
	["../../resource/res/particleeffect/mesh", "res/particleeffect/mesh.pk", "cep"],
	["../../resource/res/particleeffect/particles", "res/particleeffect/particles.pk", "cep"],
	["../../resource/res/rides/*", "res/rides/$1.pk", "cep"],
	["../../resource/res/uiv", "res/uiv", "e", "../../resource/res/uiv/swf/KUIShareLib.swf"],
	["../../resource/res/uiv/swf/KUIShareLib.swf", "res/uiv/swf", ""],
	["../../resource/res/unpack", "res/unpack", ""],
	["../../resource/res/weapons/*", "res/weapons/$1.pk", "cep"],
	["../../resource/res/wing/*", "res/wing/$1.pk", "cep"],
	
	["../../client/config", "config", ""],
	["../../client/history", "history", ""],
	["../../client/js", "js", ""],
	["../../client/ks", "ks", "a"],
	["../../client/swfobject.js", "", ""],
	["../../client/playerProductInstall.swf", "", ""],
	["../../client/T3.html", "", ""],
	["../../client/T3.swf", "", ""]
]

GLOBAL_SKIP_LIST = [
	"../../resource/res/character/*/*/*.jpg",
	"*.bin",
	"*.skill",
	"../../resource/res/particleeffect/check.*",
	"../../resource/res/maps/*/*.png",
]

#################################################################

import os
import re
import time
import glob
import struct
import zlib
import fnmatch
import shutil
import zipfile

import binascii


TIME = time.strftime("%Y%m%d_%H%M%S", time.localtime())
DST_PATH_NAME = "publish_" + TIME
DST_PATH = DST_PATH_NAME + "/client/"
ROOT_PATH = os.getcwd()
VER_FILE_PATH = DST_PATH + "versions.txt"

global_file_size = 0
global_logs = ""

def log(*msgs):
	print(*msgs)
	global global_logs
	for msg in msgs:
		global_logs += str(msg)
	if len(msgs) > 0:
		global_logs += "\n"
		
os.mkdir(DST_PATH_NAME)	
os.chdir(DST_PATH_NAME)

os.mkdir("server")

server_path = "../../../server/"
resource_path = "../../../resource/"
copy_server_files = [
	(server_path, "T3ApplicationD"), 
	(server_path, "T3DBCenterD"), 
	(server_path, "T3GatewayD"), 
	(resource_path, "settings"),
	(resource_path, "scripts")
]

for urlInfo in copy_server_files:
	path = urlInfo[0]
	name = urlInfo[1]
	url = path + name
	if os.path.isdir(url):
		shutil.copytree(url, "server/" + name)
	else:
		shutil.copy(url, "server")

f = zipfile.ZipFile("server_" + TIME + ".zip", "w")
for dirpath, dirnames, filenames in os.walk("server/"):
	for filename in filenames:
		dst_path = os.path.join(dirpath, filename)
		log("zip " + dst_path + " ... ")
		f.write(dst_path)
f.close()

log("copy done.")
log("-----------------------------------")
log("publish to \"" + DST_PATH_NAME + "\" complete.")

os.chdir(ROOT_PATH)
if not os.path.exists("logs"):
	os.makedirs("logs")
log_file = open("logs/" + DST_PATH_NAME + ".txt", "wt")
log_file.write(global_logs)
log_file.close()

