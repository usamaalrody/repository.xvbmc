#!/usr/bin/python
#-*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os.path,sys,re,urllib,urllib2,cookielib,os
from StringIO import StringIO
import gzip,tempfile,time
import xbmcvfs
progress=xbmcgui.DialogProgress()
dialog=xbmcgui.Dialog()
herstart='[COLOR white]PRESS OK TO FORCECLOSE AND REBOOT![/COLOR]'
forceersluiten='[COLOR dimgray]indien forceclose niet werkt, herstart uw systeem handmatig, if forceclose does not work shutdown Kodi manually.[/COLOR]'
__scriptid__="script.tar.gz.updater"
addon=xbmcaddon.Addon(id=__scriptid__)
USER_AGENT='Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
headers={'User-Agent':USER_AGENT,'Accept':'*/*','Connection':'keep-alive'}
profileDir=addon.getAddonInfo('profile')
profileDir=xbmc.translatePath(profileDir).decode("utf-8")
if not os.path.exists(profileDir):
 os.makedirs(profileDir)
COOKIEFILE=os.path.join(profileDir,'cookies.lwp')
cj=None
urlopen=urllib2.urlopen
Request=urllib2.Request
cj=cookielib.LWPCookieJar(COOKIEFILE)
if cj!=None:
 if os.path.isfile(COOKIEFILE):
  cj.load()
 opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),urllib2.HTTPHandler())
else:
 opener=urllib2.build_opener()
urllib2.install_opener(opener)
def showFiles(url,location=1):
 token=url.split('/')[4]
 domain=url.split('/')[2]
 listurl='https://%s/public-share/%s/list'%(domain,token)
 dlurl='https://%s/public-share/%s/download'%(domain,token)
 if location==1:
  download_path=xbmc.translatePath(os.path.join('/storage/.update/',''))
 else:
 #download_path=xbmc.translatePath(os.path.join('/storage/.restore/',''))
  download_path=xbmc.translatePath(os.path.join('/storage/.update/',''))
 bestanden=[]
 filelist=getHtml(listurl)
 filelist=re.compile('path":"([^"]+)"',re.DOTALL|re.IGNORECASE).findall(filelist)
 for bestand in filelist:
  bestanden.append(urllib.unquote_plus(bestand[1:].replace('\u00','%')))
 vh=dialog.select('Select een bestand om te downloaden',bestanden)
 if vh==-1:
  return
 dlpath=filelist[vh]
 dlname=bestanden[vh]
 dlpath=urllib.unquote_plus(dlpath.replace('\u00','%'))
 stackpage=getHtml(url)
 csrftoken=re.compile('csrf-token" content="([^"]+)"',re.DOTALL|re.IGNORECASE).findall(stackpage)[0]
 archive="zip"
 all="false"
 stackdata={'CSRF-Token':csrftoken,'archive':archive,'all':all,'query':'','paths[]':dlpath}
 stackdata=urllib.urlencode(stackdata)
 fullurl=dlurl+"|"+stackdata
 fildl=downloadFile(fullurl,dlname,download_path)
 try:
  if os.path.isfile(fildl):
   dialog.ok('[COLOR lime]DOWNLOAD FINISHED![/COLOR]',herstart,forceersluiten)
   try:os.system('reboot')
   except:pass
   try:xbmc.executebuiltin("Reboot")
   except:pass
  else:
   dialog.ok('Downloaden Mislukt','Downloaden mislukt','Probeer opnieuw','')
 except:dialog.ok('Downloaden Mislukt','Downloaden mislukt','Probeer opnieuw','')
class StopDownloading(Exception):
 def __init__(self,value):self.value=value 
 def __str__(self):return repr(self.value)
def downloadFile(url,name,download_path):
 def _pbhook(downloaded,filesize,url=None,dp=None):
  try:
   percent=min((downloaded*100)/filesize,100)
   currently_downloaded=float(downloaded)/(1024*1024)
   kbps_speed=int(downloaded/(time.clock()-start))
   if kbps_speed>0:
    eta=(filesize-downloaded)/kbps_speed
   else:
    eta=0
   kbps_speed=kbps_speed/1024
   total=float(filesize)/(1024*1024)
   mbs='%.02f MB of %.02f MB'%(currently_downloaded,total)
   e='Speed: %.02f Kb/s '%kbps_speed
   e+='ETA: %02d:%02d'%divmod(eta,60)
   dp.update(percent,'',mbs,e)
  except:
   percent=100
   dp.update(percent)
  if dp.iscanceled():
   dp.close()
   raise StopDownloading('Stopped Downloading')
 def getResponse(url,headers,size,data=None):
  try:
   if size>0:
    size=int(size)
    headers['Range']='bytes=%d-'%size
   if data:req=Request(url,data,headers=headers)
   else:req=Request(url,headers=headers)
   resp=urlopen(req,timeout=30)
   return resp
  except:
   return None
 def doDownload(url,dest,dp):
  data=url.split('|')[1]
  url=url.split('|')[0]
  file=dest.rsplit(os.sep,1)[-1]
  resp=getResponse(url,headers,0,data)
  if not resp:
   xbmcgui.Dialog().ok("Downloaden Mislukt",'Download failed','No response from server')
   return False
  try:content=int(resp.headers['Content-Length'])
  except:content=0
  try:resumable='bytes' in resp.headers['Accept-Ranges'].lower()
  except:resumable=False
  if resumable:
   xbmc.log("Download is resumable")
  if content<1:
   xbmcgui.Dialog().ok("Downloaden Mislukt",'Unknown filesize','Unable to download')
   return False
  size=8192
  mb=content/(1024*1024)
  if content<size:
   size=content
  total=0
  errors=0
  count=0
  resume=0
  sleep=0
  print 'Download File Size : %dMB %s '%(mb,dest)
  f=xbmcvfs.File(dest,'w')
  chunk=None
  chunks=[]
  while True:
   downloaded=total
   for c in chunks:
    downloaded+=len(c)
   percent=min(100*downloaded/content,100)
   _pbhook(downloaded,content,url,dp)
   chunk=None
   error=False
   try:
    chunk=resp.read(size)
    if not chunk:
     if percent<99:
      error=True
     else:
      while len(chunks)>0:
       c=chunks.pop(0)
       f.write(c)
       del c
      f.close()
      print '%s download complete'%(dest)
      return True
   except Exception,e:
    print str(e)
    error=True
    sleep=10
    errno=0
    if hasattr(e,'errno'):
     errno=e.errno
    if errno==10035:
     pass
    if errno==10054:
     errors=10
     sleep=30
    if errno==11001:
     errors=10
     sleep=30
   if chunk:
    errors=0
    chunks.append(chunk)
    if len(chunks)>5:
     c=chunks.pop(0)
     f.write(c)
     total+=len(c)
     del c
   if error:
    errors+=1
    count+=1
    print '%d Error(s) whilst downloading %s'%(count,dest)
    xbmc.sleep(sleep*1000)
   if(resumable and errors>0)or errors>=10:
    if(not resumable and resume>=50)or resume>=500:
     print '%s download canceled - too many error whilst downloading'%(dest)
     return False
    resume+=1
    errors=0
    if resumable:
     chunks=[]
     print 'Download resumed (%d) %s'%(resume,dest)
     resp=getResponse(url,headers,total,data)
    else:
     pass
 def clean_filename(s):
  if not s:
   return ''
  badchars='\\/:*?\"<>|\''
  for c in badchars:
   s=s.replace(c,'')
  return s;
 if download_path!='':
  dp=xbmcgui.DialogProgress()
  name=name.split("[")[0]
  dp.create("Downloading file",name[:50])
  tmp_file=tempfile.mktemp(dir=download_path,suffix=".tmp")
  tmp_file=xbmc.makeLegalFilename(tmp_file)
  start=time.clock()
  try:
   downloaded=doDownload(url,tmp_file,dp)
   xbmc.log("Downloaded "+str(downloaded))
   if downloaded:
    vidfile=xbmc.makeLegalFilename(download_path+clean_filename(name))
    try:
     os.rename(tmp_file,vidfile)
     return vidfile
    except:
     return tmp_file
   else:raise StopDownloading('Stopped Downloading')
  except:
   while os.path.exists(tmp_file):
    try:
     os.remove(tmp_file)
     break
    except:
     pass
   return
def getHtml(url,referer=None,hdr=None,NoCookie=None,data=None):
 try:
  if data:
   data=urllib.urlencode(data)
   print data
  if not hdr:
   req=Request(url,data,headers)
  else:
   req=Request(url,data,hdr)
  if referer:
   req.add_header('Referer',referer)
  if data:
   req.add_header('Content-Length',len(data))
  response=urlopen(req,timeout=60)
  if response.info().get('Content-Encoding')=='gzip':
   buf=StringIO(response.read())
   f=gzip.GzipFile(fileobj=buf)
   data=f.read()
   f.close()
  else:
   data=response.read()
  if not NoCookie:
   try:
    cj.save(COOKIEFILE)
   except:pass
  response.close()
 except Exception as e:
  print "Error: "+str(e)
 return data
def getCookiesString():
 cookieString=""
 import cookielib
 try:
  cookieJar=cookielib.LWPCookieJar()
  cookieJar.load(COOKIEFILE,ignore_discard=True)
  for index,cookie in enumerate(cookieJar):
   cookieString+=cookie.name+"="+cookie.value+";"
 except:
  import sys,traceback
  traceback.print_exc(file=sys.stdout)
 return cookieString