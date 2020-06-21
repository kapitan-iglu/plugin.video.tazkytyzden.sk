# -*- coding: utf-8 -*-
import urllib2,urllib,re,os
import xbmcplugin,xbmcgui,xbmcaddon
import simplejson as json

__baseurl__ = 'https://www.tazkytyzden.sk'
__addon__ = xbmcaddon.Addon('plugin.video.tazkytyzden.sk')
__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")
__scriptname__ = __addon__.getAddonInfo('name')
icon =  os.path.join( __cwd__, 'icon.png' )
nexticon = os.path.join( __cwd__, 'nextpage.png' )

section_delimiters = ['<div id="aktualny-diel"', '<div id="vsetky-diely"', '<div id="best-of"', '<div id="o-relacii"']
video_desc_url = 'https://video.azet.sk/embed/playlistVideoJson/'

def log(msg, level=xbmc.LOGDEBUG):
	if type(msg).__name__=='unicode':
		msg = msg.encode('utf-8')
	xbmc.log("[%s] %s"%(__scriptname__,msg.__str__()), level)

def logDbg(msg):
	log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
	log(msg,level=xbmc.LOGERROR)

def notifyErr(msg, timeout = 7000):
	xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__scriptname__, msg.encode('utf-8'), timeout, __addon__.getAddonInfo('icon')))
	logErr(msg)

def addLink(name,url,mode,iconimage,date):
	logDbg("addLink(): '"+name+"' url='"+url+ "' img='"+iconimage+"'date='"+date+"'")
	u=sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8'))
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name, "dateadded": date} )
	liz.setProperty("IsPlayable", "true")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok

def addDir(name,url,mode,iconimage,desc):
	logDbg("addDir(): '"+name+"' url='"+url+"' img='"+iconimage+"' desc='"+desc+"'")
	u=sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8'))+"&desc="+urllib.quote_plus(desc.encode('utf-8'))
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc} )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def getDataFromUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

def getHtmlFromUrl(url):
	return getDataFromUrl(url).decode("utf-8")

def getJsonDataFromUrl(url):
    return json.loads(getDataFromUrl(url))

def listCategories():
	logDbg("listCategories()")
	listEpisodes(0,u'[B]Aktuálny diel:[/B] ')
	addDir(u'[B]Všetky diely[/B]',__baseurl__,1,icon,'')
	addDir(u'[B]Špeciály[/B]',__baseurl__,2,icon,'')

def listEpisodes(category = 0, prefix = ''):
	logDbg("listEpisodes("+str(category)+")")
	if category > len(section_delimiters)-1:
		return
	
	httpdata = getHtmlFromUrl(__baseurl__)
	beg_idx=httpdata.find(section_delimiters[category])
	end_idx=httpdata.find(section_delimiters[category+1])
	data=httpdata[beg_idx:end_idx]
	
	pattern = re.compile('href="(.+?)">(?:.+?)data-src="(.+?)"(?:.+?)<h3>(.+?)<\/h3>(?:.+?)cz_data_date">(.+?)<\/span>', re.DOTALL)
	it = re.finditer(pattern,data)
	for item in it:
		link,img,title,date = item.groups()
		if ':' in title:
			title=title.split(':')[1].strip()
		addLink(prefix+title,link,3,img,date)


def playEpisode(url):
	logDbg("playEpisode()")
	logDbg("\turl="+url)
	url=getVideoUrl(url)
	if url:
		liz = xbmcgui.ListItem(path=url, iconImage="DefaultVideo.png")
#		liz.setInfo( type="Video", infoLabels={ "Title": 'titulok'} )
		liz.setProperty('IsPlayable', "true")
		liz.setProperty('inputstreamaddon','inputstream.adaptive')
		liz.setProperty('inputstream.adaptive.manifest_type','hls')
		xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)
	return


def getVideoUrl(url):
	logDbg("getVideoUrl()")
	httpdata = getHtmlFromUrl(url)
	
	match = re.compile(r'src="http[^"]+?embed/([0-9]+)"', re.DOTALL).search(httpdata)
	if not match:
		logDbg("\tembed URL not found")
		return None
	data = getJsonDataFromUrl(video_desc_url+match.group(1))
	for item in data[0]['sources']:
		url=item['file']
		logDbg(url)
		if url.endswith("m3u8"):
			return url
	return None


def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

params=get_params()
url=None
name=None
desc=None
mode=None

try:
	url=urllib.unquote_plus(params["url"])
except:
	pass
try:
	name=urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode=int(params["mode"])
except:
	pass
try:
	desc=urllib.unquote_plus(params["desc"])
except:
	pass

logDbg("Mode: "+str(mode))
logDbg("URL: "+str(url))
logDbg("Name: "+str(name))
logDbg("Desc: "+str(desc))

if mode==None or url==None or len(url)<1:
	listCategories()

elif mode==1:
	listEpisodes(1)

elif mode==2:
	listEpisodes(2)

elif mode==3:
	playEpisode(url)
	sys.exit(0)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
