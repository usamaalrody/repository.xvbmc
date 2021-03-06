import urllib2,urllib,cgi, re, os
import urlparse
import HTMLParser
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import base64
from operator import itemgetter
import traceback,cookielib
import time,datetime
from datetime import date, datetime, timedelta

try:
    import json
except:
    import simplejson as json


addon = xbmcaddon.Addon('plugin.video.wildhitz')
addonname = addon.getAddonInfo('name')
#icon = addon.getAddonInfo('icon')
addon_id = 'plugin.video.wildhitz'
selfAddon = xbmcaddon.Addon(id=addon_id)
profile_path =  xbmc.translatePath(selfAddon.getAddonInfo('profile'))
home = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
icon = os.path.join(home, 'icon.png')
FANART = os.path.join(home, 'fanart.jpg')

addonDir = addon.getAddonInfo('path').decode("utf-8")
libDir = os.path.join(addonDir, 'resources', 'lib')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
home = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
favorites = os.path.join(profile, 'favorites')
history = os.path.join(profile, 'history')
addonInfo = xbmcaddon.Addon().getAddonInfo
execute = xbmc.executebuiltin


addon_handle = int(sys.argv[1])
pluginhandle = int(sys.argv[1])

video_quality = addon.getSetting('video_quality')


class NoRedirection(urllib2.HTTPErrorProcessor):
   def http_response(self, request, response):
       return response
   https_response = http_response


def make_request(url):
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0')
		response = urllib2.urlopen(req)
		link = response.read()
		response.close()
		return link
	except urllib2.URLError, e:
		print 'We failed to open "%s".' % url
		if hasattr(e, 'code'):
			print 'We failed with error code - %s.' % e.code
		if hasattr(e, 'reason'):
			print 'We failed to reach a server.'
			print 'Reason: ', e.reason
		link = 'index.html'
		return link


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=5"
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

def addDir(name,url,mode,iconimage,fanart,description,genre,date,credits,isItFolder=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)
        ok=True
        if date == '':
            date = None
        else:
            description += '\n\nDate: %s' %date
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "dateadded": date, "credits": credits })
        liz.setProperty("Fanart_Image", fanart)


        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isItFolder)
        return ok



def GetHTML(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link

def sorted_nicely( l ):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key[1]) ]
    return sorted(l, key = alphanum_key)


def week_day():
    a = datetime.today().weekday()
    if a == 0:
        return("monday")
    elif a == 1:
        return("tuesday")
    elif a == 2:
        return("wednesday")
    elif a == 3:
        return("thursday")
    elif a ==4:
        return("friday")
    elif a == 5:
        return("saturday")
    elif a == 6:
        return("sunday")

def Addtypes():   
    addDir('Play WildHitz' ,'wild',2,icon ,  FANART,'','','','')
    addDir('Today Shuffle Clips' ,week_day(),3,icon ,  FANART,'','','','')
    addDir('Week Shuffle Clips' ,'wild',4,icon ,  FANART,'','','','')
    addDir('Settings' ,'wild',5,icon ,  FANART,'','','','')

def Adddays():   
    addDir('Play Monday Shuffle Clips' ,'monday',3,icon ,  FANART,'','','','')
    addDir('Play Tuesday Shuffle Clips' ,'tuesday',3,icon ,  FANART,'','','','')
    addDir('Play Wednesday Shuffle Clips' ,'wednesday',3,icon ,  FANART,'','','','')
    addDir('Play Thursday Shuffle Clips' ,'thursday',3,icon ,  FANART,'','','','')
    addDir('Play Friday Shuffle Clips' ,'friday',3,icon ,  FANART,'','','','')
    addDir('Play Saturday Shuffle Clips' ,'saturday',3,icon ,  FANART,'','','','')
    addDir('Play Sunday Shuffle Clips' ,'sunday',3,icon ,  FANART,'','','','')

def Wildhitz_playlist():
    scantime = False
    pl=xbmc.PlayList(1)
    pl.clear()
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%H')
    st = int(st)
    now = datetime.now().time()
    readjsondata = 'http://wildhitz.nl/download.php?file=jsondata-wildhitz-'+week_day()+'.json'
    data = GetHTML(readjsondata)
    data = json.loads(data)
    for i in data['rss']['channel']['program']:
        start = i['start']
        start = start[11:13]
        start = int(start)
        if start >= st:
            for x in i['items']['item']:
                airtime = x['airtime']
                try:
                    try:
                        dt = datetime.strptime(airtime,"%H:%M:%S").time()
                    except:
                        dt = datetime(*(time.strptime(airtime,"%H:%M:%S")[0:6])).time()
                except:
                    dt=now
                if scantime == False and dt < now :
                    pass
                else:
                    scantime = True
                    title = x['title']['__cdata']
                    artist = x['artist']['__cdata']
                    source = x['source'][int(video_quality)]['_file']
                    if title:
                        name = '|'+title+' - '+artist
                    else:
                        name =''
                    url = source
                    listitem = xbmcgui.ListItem('WildHitz'+name,thumbnailImage=icon)
                    xbmc.PlayList(1).add(url, listitem)
    xbmc.Player().play(pl)

def Wildhitz_shuffle(url):   
    scantime = False
    pl=xbmc.PlayList(1)
    pl.clear()
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%H')
    st = int(st)
    now = datetime.now().time()
    readjsondata = 'http://wildhitz.nl/download.php?file=jsondata-wildhitz-'+url+'.json'
    data = GetHTML(readjsondata)
    data = json.loads(data)
    for i in data['rss']['channel']['program']:
        start = i['start']
        start = start[11:13]
        start = int(start)
        if start >= st:
            for x in i['items']['item']:
                airtime = x['airtime']
                try:
                    try:
                        dt = datetime.strptime(airtime,"%H:%M:%S").time()
                    except:
                        dt = datetime(*(time.strptime(airtime,"%H:%M:%S")[0:6])).time()
                except:
                    dt=now
                if scantime == False and dt < now :
                    pass
                else:
                    scantime = True
                    title = x['title']['__cdata']
                    artist = x['artist']['__cdata']
                    source = x['source'][int(video_quality)]['_file']
                    if title:
                        name = '|'+title+' - '+artist
                    else:
                        name =''
                    if name:
                        url = source
                        listitem = xbmcgui.ListItem('WildHitz'+name,thumbnailImage=icon)
                        xbmc.PlayList(1).add(url, listitem)
    pl.shuffle()
    xbmc.Player().play(pl)

def openSettings(query=None, id=addonInfo('id')):
    try:
        execute('addon.OpenSettings(%s)' % id)
        if query == None: raise Exception()
        c, f = query.split('.')
        execute('SetFocus(%i)' % (int(c) + 100))
        execute('SetFocus(%i)' % (int(f) + 200))
    except:
        return 

def getResponse(url):
    try:
        response = urllib2.urlopen(url, timeout=200)
        if response and response.getcode() == 200:
            return response
        else :
            return False
    except:
        return False


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
mode=None
linkType=None

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


args = cgi.parse_qs(sys.argv[2][1:])
linkType=''
try:
	linkType=args.get('linkType', '')[0]
except:
	pass


print 	mode,url,linkType

try:
   if mode==None or url==None or len(url)<1:
      print "InAddTypes"
      Addtypes()
   elif mode==2 : Wildhitz_playlist()
   elif mode==3 : Wildhitz_shuffle(url)
   elif mode==4 : Adddays()
   elif mode==5 : openSettings()
  



except:
   print 'somethingwrong'
   traceback.print_exc(file=sys.stdout)



if not ( (mode==2 or mode==3 or mode==5 or mode==10 or mode==15 or mode==21 or mode==22 or mode==27 or mode==33 or mode==35 or mode==37 or mode==40 or mode==42 or mode==0)  )  :
	if mode==144:
		xbmcplugin.endOfDirectory(int(sys.argv[1]),updateListing=True)
	else:
		xbmcplugin.endOfDirectory(int(sys.argv[1]))
