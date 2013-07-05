""" Parser per news del CLI

"""

from formatter import AbstractFormatter, DumbWriter, NullWriter
from htmllib import HTMLParser
import time


class Defs:

   def __init__(self):
      self.hostToAttack="www.cli.di.unipi.it"
      self.pageToSuck="/news.php"
      self.portToHost=80
      self.proxyJump=None
      self.title="News Centro Di Calcolo"
#      self.startRegexp="""</td></tr>
#</table>
#</center>
#<p>
#"""
      self.startRegexp="""\)</td>
</tr>
<tr><td colspan=2>
"""
#      self.endRegexp="""<p>
#
#<h>"""
      self.endRegexp="""</table><p>

</td></tr>"""


      self.xmlHead= """
<?xml-stylesheet type="text/css" href="rss_style.css" ?>
   <rss version="2.0">
     <channel>
       <title>CDC News</title>
       <link>http://www.cli.di.unipi.it/</link>
       <description>News Centro di Calcolo Univ. di Pisa.</description>""" + \
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
       la struttura corrente della pagina news.php
       del sito del CLI <http://www.cli.di.unipi.it/news.php>.
       e' lecito pensare ad una prossima trasformazione
       in moduli.

       struttura dei box notizia del CLI:

       <table>
         <table>
           <tr>
             <td>
               <span>Titolo</span>
               <span>Data</span>
               <div>Autore</div>
             </td>
           </tr>
           <tr>
             <td>
               <div>Testo notizia</div>
             </td>
           </tr>
         </table>
       </table
   """


   def __init__(self, formatter=AbstractFormatter(DumbWriter())):

      HTMLParser.__init__(self,formatter)
      self.intoTheBox=False      #ingresso/uscita dall'ambiente del box
      self.intoTheTitle=None     #ingresso/uscita dalla riga titolo
      self.intoTheNews=None      #ingresso/uscita dal testo della notizia
      self.effectiveTitle=False  #tag <span> del titolo
      self.effectiveDate=False   #tag <span> della data
      self.effectiveAuth=False   #tag <div> dell'autore
      self.writable=False        #testo scrivibile
      self.cookedText=""         #testo xml risultante


   # ridefinizione dei metodi di parsing dei tag

   def start_table(self, attrs):
      if not self.intoTheBox:
         self.intoTheBox=True
         self.writable=True
         self.cookedText=self.cookedText+"    <item>"+ \
                                         "      <link>http://www.cli.di.unipi.it/news.php</link>"+\
                                         "      <guid>http://www.cli.di.unipi.it/news.php</guid>"

   def end_table(self):
      if self.intoTheBox and not self.intoTheNews and not self.intoTheTitle:
         self.intoTheBox=False
         self.intoTheTitle=None
         self.intoTheNews=None
         self.writable=False
         self.cookedText=self.cookedText+"    </item>"



   def start_td(self, attrs):
      if self.intoTheBox:
         if self.intoTheTitle==None:
            self.intoTheTitle=True
         if not self.intoTheTitle:
            self.intoTheNews=True
            self.writable=True
            self.cookedText=self.cookedText+"      <description>"

   def end_td(self):
      if self.intoTheBox:
         if self.intoTheTitle:
            self.intoTheTitle=False
            self.effectiveDate=False
            self.effectiveTitle=False
         if self.intoTheNews:
            self.intoTheNews=False
            self.writable=False
            self.cookedText=self.cookedText+"      </description>"



   def start_span(self, attrs):
      if self.intoTheTitle:
         if self.effectiveTitle and not self.effectiveDate:
            self.effectiveDate=True
            self.writable=True
            self.cookedText=self.cookedText+"      <pubDate>"
         if not self.effectiveTitle and not self.effectiveDate:
            self.effectiveTitle=True
            self.writable=True
            self.cookedText=self.cookedText+"      <title>"

   def end_span(self):
      if self.intoTheTitle:
         if self.effectiveTitle and not self.effectiveDate:
            self.writable=False
            self.cookedText=self.cookedText+"      </title>"
         if self.effectiveTitle and self.effectiveDate:
            self.writable=False
            self.cookedText=self.cookedText+"      </pubDate>"


   def start_a(self, attrs):
      return

   def end_a(self):
      return



   def handle_data(self, data):
      if self.writable and self.intoTheBox:
         if self.effectiveTitle and self.effectiveDate:
            data=time.strftime('%a, %d %b %Y %H:%M:00 GMT',time.strptime(data,'%d-%b-%Y %H:%M '))
         self.cookedText=self.cookedText+data



   def cook(self, text):
      self.feed(text)
      self.close()
      return self.cookedText

