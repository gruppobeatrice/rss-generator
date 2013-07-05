""" Parser per news del DI 

"""

from formatter import AbstractFormatter, DumbWriter, NullWriter
#from HTMLParser import HTMLParser
from htmllib import HTMLParser
import time, re


class Defs:

   def __init__(self):
      self.hostToAttack="compass2.di.unipi.it"
      self.pageToSuck="/didattica/inf/"
      self.portToHost=80
      self.title="News Dipartimento di Informatica"
      self.proxyJump=None
      self.startRegexp="""<h1>Avvisi</h1>"""
      self.endRegexp="""</div>
<div id="footer">"""


      self.xmlHead= """
<?xml-stylesheet type="text/css" href="rss_style.css" ?>
   <rss version="2.0">
     <channel>
       <title>DI News</title>
       <link>http://www.di.unipi.it/</link>
       <description>News Dipartimento di Informatica, Univ. di Pisa.</description>""" + \
      "\n    <lastBuildDate>%s</lastBuildDate>" % time.strftime('%a, %d %b %Y %H:%M:%S GMT') + \
      """
    <docs>http://blogs.law.harvard.edu/tech/rss</docs>
    <generator>Gruppo Beatrice</generator>
    <managingEditor>fiorini@cli.di.unipi.it</managingEditor>
    <webMaster>g_beatrice@cli.di.unipi.it</webMaster>
"""
      self.xmlFoot="""
  </channel>
</rss>
"""




class Parser(HTMLParser):
   """ Classe parser HTML derivata da htmllib

       questo parser e' scritto specificatamente per
       la struttura corrente della pagina index.asp
       del sito del DI <http://compass2.di.unipi.it/didattica/inf/>.

       struttura dei box notizia del DI:

       <a name="avvisoXXX">Ancora per la news</a>
       <div class="data-avviso">Data pubblicazione</div>
       <div class="titolo-avviso">Titolo</div>
       <div class="testo-avviso">Testo</div>

   """


   def __init__(self, formatter=AbstractFormatter(DumbWriter())):

      #HTMLParser.__init__(self)
      HTMLParser.__init__(self,formatter)
      self.intoTheAnchor=False   #ingresso/uscita dai tag anchor
      self.intoTheDate=False     #ingresso/uscita dal box data
      self.intoTheTitle=False    #ingresso/uscita dal box titolo
      self.intoTheNews=False     #ingresso/uscita dal box notizia
      self.writable=False        #testo scrivibile
      self.maxNews=10            #totale notizie visualizzate
      self.cookedText=""         #testo xml risultante
      self.gotTitle=False        #flag indicante la reale presenza del titolo
      self.pseudoTitle=""        #titolo fake (se mancante)


   # ridefinizione dei metodi di parsing dei tag


   def start_a(self, attrs):
      for attr in attrs:
         if attr[0]=="name":
            if attr[1][:6]=="avviso" and not self.intoTheAnchor:
               if not self.maxNews:
                  self.setnomoretags()
                  return
               self.intoTheAnchor=True
               self.writable=True
               self.cookedText=self.cookedText+"    <item>"+ \
               "      <link>http://compass2.di.unipi.it/didattica/inf/index.asp#"+attr[1]+"</link>"+ \
               "      <guid>http://compass2.di.unipi.it/didattica/inf/index.asp#"+attr[1]+"</guid>"
            break

   def end_a(self):
      if self.intoTheAnchor:
         self.intoTheAnchor=False
         self.writable=False


   def start_div(self, attrs):
      for attr in attrs:
         if attr[0]=="class":
            if attr[1]=="data-avviso" and not self.intoTheDate:
               self.intoTheDate=True
               self.writable=True
               self.cookedText=self.cookedText+"<pubDate>"
            if attr[1]=="titolo-avviso" and not self.intoTheTitle:
               self.intoTheTitle=True
               self.writable=True
               self.cookedText=self.cookedText+"<title>"
            if attr[1]=="testo-avviso" and not self.intoTheNews:
               self.intoTheNews=True
               self.writable=True
               self.cookedText=self.cookedText+"<description>"
            break

   def end_div(self):
      if self.intoTheDate:
         self.intoTheDate=False
         self.writable=False
         self.cookedText=self.cookedText+"</pubDate>"
      if self.intoTheTitle:
         self.intoTheTitle=False
         self.writable=False
         self.gotTitle=True
         self.cookedText=self.cookedText+"</title>"
      if self.intoTheNews:
         self.intoTheNews=False
         self.intoTheAnchor=False
         self.writable=False
         self.maxNews=self.maxNews-1
         self.cookedText=self.cookedText+"</description>"
         if not self.gotTitle:
            self.cookedText=self.cookedText+"<title>"+self.pseudoTitle+"</title>"
         self.pseudoTitle=""
         self.cookedText=self.cookedText+"</item>"

   def do_br(self, attrs):
      self.cookedText=self.cookedText+" "


   def handle_data(self, data):
      data=re.sub("[<>]*","",data)
      if self.writable:
         if self.intoTheDate:
            data=time.strftime('%a, %d %b %Y %H:%M:00 GMT',time.strptime(data,'%d/%m/%Y'))
         if self.intoTheNews and not self.gotTitle:
            if len(data)>128:
               self.pseudoTitle=data[:64]+"..."
            else:
               self.pseudoTitle=data
         self.cookedText=self.cookedText+data



   def cook(self, text):
      # rimozione tag <a> a causa di problemi di validazione della pagina stessa (non standard!)
      text=re.sub("<a href=\"\S*\">","",text )
      text=re.sub("[a-zA-Z0-9 ]*</a[ ]*>","",text )
      self.feed(text)
      self.close()
      return self.cookedText

