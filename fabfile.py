import json
from fabric.api import *
from fabric.contrib.project import rsync_project
import datetime, os

json_data_file =open('cfg.json','r+')
data = json.load(json_data_file)

configuration_name = ''
def init(configName):
	global configuration_name
	configuration_name = configName
	print "Initializing....."
	fab = data[configName]
	env.hosts=fab["host"]
	env.passwords=fab["password"]
	print "Init Done!!"

def sync():
	configName = configuration_name
	print "starting the sync now....."
	fab = data[configName]
	version=float(fab['version_info'])
	version+=1
	version=str(version)
	with open('a.json', 'r+') as settingsData:
		settings = json.load(settingsData)
		settings[configName]['version_info'] = version
		settingsData.seek(0)
		settingsData.write(json.dumps(settings,indent=4,sort_keys=True))
		settingsData.truncate()
	local_dir=fab['local_dir']
	remdir=fab['remote_dir']
	remote_dir = remdir[env.host]
	ex = fab['exclude_file']
	rsync_project(remote_dir, local_dir,exclude=ex,extra_opts="--log-file=./project/logfile/sync_logs.log --delete --human-readable --stats --progress --ignore-times --protect-args --links")
	print "sync done!!"

def backup():
	configName = configuration_name
	print "backup started.."
	fab = data[configName]
	version=fab['version_info']
	b=float(version)
	today=datetime.date.today()
	todaystr=today.isoformat()
	backup_dir=fab['backup_dir']
	backup_main=backup_dir[env.host]
	remote_dir=''+backup_main+todaystr+'/%d'%b
	local_dir=fab['local_dir']
	mkd="mkdir -p "+remote_dir+""
	ex = fab['exclude_file']
	run(mkd)
	ex.append('*.log')
	rsync_project(remote_dir, local_dir,exclude=ex,extra_opts="--ignore-times --protect-args --links")

def backup_revert():
	configName = configuration_name
	fab = data[configName]
	print "Reverting the backup..."
	version=fab['version_info']
	a=float(version)-1
	today = datetime.date.today()
	todaystr = today.isoformat()
	backup_dir=fab['backup_dir']
	backup_main=backup_dir[env.host]
	srcf =''+backup_main+todaystr+'/%d'%a
	path_a=fab['remote_dir']
	path=path_a[env.host]
	command= "rsync -r "+srcf+"/ "+path+""
	run(command)
	print "Bakup revert done!"

def build():
	configName = configuration_name
	print "building project...."
	fab=data[configName]
	build_command = fab['build_command']
	length= len(build_command)
	remote_d = fab['remote_dir']
	remote_dir=remote_d[env.host]
	ht=fab['host_type']
	host_type=ht[env.host]
	if host_type=="Windows":
		with cd(remote_dir):
			for x in xrange(0,length):
				run("date && "+build_command[x]+"",stdout=open('./project/logfile/build_logs.log','a'))
	else:
		with cd(remote_dir):
			for x in xrange(0,length):
				sudo("date && "+build_command[x]+"",stdout=open('./project/logfile/build_logs.log','a'))

def deploy():
	configName = configuration_name
	sync()
	build()
	backup()