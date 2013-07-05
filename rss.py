#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
#
# Python RSS (2.0) feed generator
#
# il file xml di esempio sul quale si basa l'output generato
# da questa applicazione e' reperibile all'indirizzo
# http://media-cyber.law.harvard.edu/blogs/gems/tech/rss2sample.xml

__version__ = "Revision: 0.1"
__author__ = "Leonardo"


import httplib, re, string
from time import *
from httplib import *
import cli, di
import sys

cachePath="/var/www/rss/cache_"
#cachePath="/home/leonardo/rss/cache_"

def main(choose="cli"):

   # definizione parametri
   mod=sys.modules[choose]

   env=mod.Defs()

   # connessione all'Host
   conn=httplib.HTTPConnection(env.hostToAttack,env.portToHost)

   # apertura/creazione del file di cache
   lastbuild=mktime(strptime("Mon, 01 Jan 1970 00:00:00 GMT",
                             '%a, %d %b %Y %H:%M:%S GMT'))

   try:
      cache=file(cachePath+choose+".xml","r+")
      for line in  cache.readlines(10):
         if re.search("lastBuildDate", line):
            lastbuild=mktime(strptime(re.sub("\s*<[/]*lastBuildDate>\s*","",line),
                                             '%a, %d %b %Y %H:%M:%S GMT'))
            break
   except IOError:
      cache=file(cachePath+choose+".xml","w")

   lastupdate=mktime(gmtime())

   if lastupdate - lastbuild < 1800 :
      cache.seek(0)
      for line in cache:
         print line
      cache.close()
      return

   # ricezione del file
   try:
      conn.connect()
      conn.request("GET",env.pageToSuck)
      response=conn.getresponse()
   except HTTPException:
      conn.close()

   if response.status!=200:
      cache.seek(0)
      for line in cache:
         print line
      cache.close()
      return

   # creazione intestazione RSS (codice XML):
   out=env.xmlHead

   # parsing notizie
   page=response.read()

   # eliminazione parti inutili (codice prima e dopo le tabelle news)
   tokens = list(re.split(env.startRegexp,page))
   tokens = list(re.split(env.endRegexp,tokens[len(tokens)-1]))

   # lowercase di tutti i caratteri (per evitare problemi con XHTML)
   replaceTable=string.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'abcdefghijklmnopqrstuvwxyz')

   # feed the poor parser!
   parser=mod.Parser()
   cookedPage=parser.cook(string.translate(tokens[0],replaceTable))

   cookedPage=re.sub("“|”|’","\"",cookedPage)


   replaceTable=string.maketrans(
                'áâàäãéêèëíîìïóôòöõúûùüçøñÁÂÀÄÉÊÈËÍÎÌÏÓÔÒÖÚÛÙÜÇØÑ¡¿&',
                'aaaaaeeeeiiiiooooouuuuconAAAAEEEEIIIIOOOOUUUUCON!?e')


   out=out+string.translate(cookedPage,replaceTable)

   #chiusura tag XML
   out=out+env.xmlFoot

   print out
   cache.seek(0)
   cache.truncate(0)
   cache.write(out)
   cache.close()

   #technorati ping
   conn = httplib.HTTPConnection("rpc.technorati.com:80")
   conn.connect()
   techMsg = """
   <?xml version="1.0"?>
   <methodCall>
     <methodName>weblogUpdates.ping</methodName>
     <params>
       <param>
         <value>Gruppo Beatrice"""+env.title+"""</value>
       </param>
       <param>
         <value>http://beatrice.cli.di.unipi.it/pub/rss/rss_"""+choose+""".py.xml</value>
       </param>
     </params>
   </methodCall>"""
   techHeads = {"User-Agent": "Plone 2.05",
                "Host": "rpc.technorati.com",
                "Content-Type": "text/xml",
                "Content-length": len(techMsg)}
   conn.request("POST", "/rpc/ping", techMsg, techHeads)
   techdebug = file("/var/www/rss/technorati.log", "r+")
   response = conn.getresponse()
   techdebug.write("response: " + str(response.status))
   techdebug.close()
   conn.close()


if __name__=="__main__":
   if len(sys.argv)>1:
      main(sys.argv[1])


