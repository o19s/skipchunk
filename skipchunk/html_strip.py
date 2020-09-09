import re

# --------------------------------------
from io import StringIO
from html import unescape
from html.parser import HTMLParser
#Strips HTML tags and entities
class stdlib_strip(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_html(html):
    html = unescape(html)
    strip = stdlib_strip()
    strip.feed(html)
    text = strip.get_data()
    text = text.strip()
    text = re.sub(r'\s+',' ',text)
    return text

# --------------------------------------
from bs4 import BeautifulSoup
def strip_html_bs4(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ')
    text = text.strip()
    text = re.sub(r'\s+',' ',text)
    return text

# --------------------------------------
def strip_html_lxml(html):
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text(separator=' ')
    text = text.strip()
    text = re.sub(r'\s+',' ',text)
    return text

def strip(html,parser="lxml"):
    if parser == "lxml":
        text = strip_html_lxml(html)
    elif parser == "bs4":
        text = strip_html_bs4(html)
    elif parser == "html":
        text = strip_html(html)
    return text


##==========================================================
## EASY SANITY TESTING:
## python html_strip.py

if __name__ == "__main__":

    def test(html,gold,parser="html"):
        text = strip(html,parser=parser)
        gold = gold.strip()
        gold = re.sub(r'\s+',' ',gold)
        passed = (text == gold) or len(text)==0
        if not passed:
            print('-------------------------------')
            print('FAILED::',parser)
            print(html)
            print('- - - - - - - BECAME')
            print(text)
            print('- - - - - - - SHOULD BE')
            print(gold)
        #else:
        #    print('-------------------------------')
        #    print('PASSED')
        #    print(html)
        #    print('- - - - - - - EQUALS')
        #    print(gold)

        return passed


    def main(parser="html"):
        tests = [
            "<div class=\"foo\">this is some text</div> here is a <a href=\"#bar\">link</a> and another <a href=\"http://lucene.apache.org/\">link</a>. This is an entity: &amp; plus a &lt;.  Here is an &. <!-- is a comment -->",
            "this is some text here is a link and another link. This is an entity: & plus a <.  Here is an &. ",

            "a <a hr<ef=aa<a>> </close</a>",
            "a <a hr<ef=aa> </close",

            "<a href=http://dmoz.org/cgi-bin/add.cgi?where=/arts/\" class=lu style=\"font-size: 9px\" target=dmoz>Submit a Site</a>",
            "Submit a Site",

            "<a href=javascript:ioSwitch('p8','http://www.csmonitor.com/') title=expand id=e8 class=expanded rel=http://www.csmonitor.com/>Christian Science",
            "Christian Science",

            "<link rel=\"alternate\" type=\"application/rss+xml\" title=\"San Francisco \" 2008 RSS Feed\" href=\"http://2008.sf.wordcamp.org/feed/\" />",
            "\n",

            # "<" before ">" inhibits tag recognition
            "<a href=\" http://www.surgery4was.happyhost.org/video-of-arthroscopic-knee-surgery symptoms.html, heat congestive heart failure <a href=\" http://www.symptoms1bad.happyhost.org/canine",
            "<a href=\" http://www.surgery4was.happyhost.org/video-of-arthroscopic-knee-surgery symptoms.html, heat congestive heart failure <a href=\" http://www.symptoms1bad.happyhost.org/canine",

            "<a href=\"http://ucblibraries.colorado.edu/how/index.htm\"class=\"pageNavAreaText\">",
            "",

            "<link title=\"^\\\" 21Sta's Blog\" rel=\"search\"  type=\"application/opensearchdescription+xml\"  href=\"http://21sta.com/blog/inc/opensearch.php\" />",
            "\n",

            "<a href=\"#postcomment\" title=\"\"Leave a comment\";\">?",
            "?",

            "<a href='/modern-furniture'   ' id='21txt' class='offtab'   onMouseout=\"this.className='offtab';  return true;\" onMouseover=\"this.className='ontab';  return true;\">",
            "",

            "<a href='http://alievi.wordpress.com/category/01-todos-posts/' style='font-size: 275%; padding: 1px; margin: 1px;' title='01 - Todos Post's (83)'>",
            "",

            "The <a href=<a href=\"http://www.advancedmd.com>medical\">http://www.advancedmd.com>medical</a> practice software</a>",
            "The <a href=medical\">http://www.advancedmd.com>medical practice software",

            "<a href=\"node/21426\" class=\"clipTitle2\" title=\"Levi.com/BMX 2008 Clip of the Week 29 \"Morgan Wade Leftover Clips\"\">Levi.com/BMX 2008 Clip of the Week 29...",
            "Levi.com/BMX 2008 Clip of the Week 29...",

            "<a href=\"printer_friendly.php?branch=&year=&submit=go&screen=\";\">Printer Friendly",
            "Printer Friendly",

            "<a href=#\" ondragstart=\"return false\" onclick=\"window.external.AddFavorite('http://www.amazingtextures.com', 'Amazing Textures');return false\" onmouseover=\"window.status='Add to Favorites';return true\">Add to Favorites",
            "Add to Favorites",

            "<a href=\"../at_home/at_home_search.html\"../_home/at_home_search.html\">At",
            "At",

            "E-mail: <a href=\"\"mailto:XXXXXX@example.com\" \">XXXXXX@example.com </a>",
            "E-mail: XXXXXX@example.com ",

            "<li class=\"farsi\"><a title=\"A'13?\" alt=\"A'13?\" href=\"http://www.america.gov/persian\" alt=\"\" name=\"A'13?\"A'13? title=\"A'13?\">A'13?</a></li>",
            "\nA'13?\n",

            "<li><a href=\"#28\" title=\"Hubert \"Geese\" Ausby\">Hubert \"Geese\" Ausby</a></li>",
            "\nHubert \"Geese\" Ausby\n",

            "<href=\"http://anbportal.com/mms/login.asp\">",
            "\n",

            "<a href=\"",
            "<a href=\"",

            "<a href=\">",
            "",

            "<a rel=\"nofollow\" href=\"http://anissanina31.skyrock.com/1895039493-Hi-tout-le-monde.html\" title=\" Hi, tout le monde !>#</a>",
            "#",

            "<a href=\"http://annunciharleydavidsonusate.myblog.it/\" title=\"Annunci Moto e Accessori Harley Davidson\" target=\"_blank\"><img src=\"http://annunciharleydavidsonusate.myblog.it/images/Antipixel.gif\" /></a>",
            "",

            "<a href=\"video/addvideo&v=120838887181\" onClick=\"return confirm('Are you sure you want  add this video to your profile? If it exists some video in your profile will be overlapped by this video!!')\" \" onmouseover=\"this.className='border2'\" onmouseout=\"this.className=''\">",
            "",

            "<a href=#Services & Support>",
            "",

            # "<" and ">" chars are accepted in on[Event] attribute values
            "<input type=\"image\" src=\"http://apologyindex.com/ThemeFiles/83401-72905/images/btn_search.gif\"value=\"Search\" name=\"Search\" alt=\"Search\" class=\"searchimage\" onclick=\"incom ='&sc=' + document.getElementById('sel').value ; var dt ='&dt=' + document.getElementById('dt').value; var searchKeyword = document.getElementById('q').value ; searchKeyword = searchKeyword.replace(/\\s/g,''); if (searchKeyword.length < 3){alert('Nothing to search. Search keyword should contain atleast 3 chars.'); return false; } var al='&al=' +  document.getElementById('advancedlink').style.display ;  document.location.href='http://apologyindex.com/search.aspx?q=' + document.getElementById('q').value + incom + dt + al;\" />",
            "",

            "<input type=\"image\" src=\"images/afbe.gif\" width=\"22\" height=\"22\"  hspace=\"4\" title=\"Add to Favorite\" alt=\"Add to Favorite\"onClick=\" if(window.sidebar){ window.sidebar.addPanel(document.title,location.href,''); }else if(window.external){ window.external.AddFavorite(location.href,document.title); }else if(window.opera&&window.print) { return true; }\">",
            "",

            "<area shape=\"rect\" coords=\"12,153,115,305\" href=\"http://statenislandtalk.com/v-web/gallery/Osmundsen-family\"Art's Norwegian Roots in Rogaland\">",
            "\n",

            "<a rel=\"nofollow\" href=\"http://arth26.skyrock.com/660188240-bonzai.html\" title=\"bonza>#",
            "#",

            "<a href=  >",
            "",

            "<ahref=http:..",
            "<ahref=http:..",

            "<ahref=http:..>",
            "\n",

            "<ahref=\"http://aseigo.bddf.ca/cms/1025\">A",
            "\nA",

            "<a href=\"javascript:calendar_window=window.open('/calendar.aspx?formname=frmCalendar.txtDate','calendar_window','width=154,height=188');calendar_window.focus()\">",
            "",

            "<a href=\"/applications/defenseaerospace/19+rackmounts\" title=\"19\" Rackmounts\">",
            "",

            "<a href=http://www.azimprimerie.fr/flash/backup/lewes-zip-code/savage-model-110-manual.html title=savage model 110 manual rel=dofollow>",
            "",

            "<a class=\"at\" name=\"Lamborghini  href=\"http://lamborghini.coolbegin.com\">Lamborghini /a>",
            "Lamborghini /a>",

            "<A href='newslink.php?news_link=http%3A%2F%2Fwww.worldnetdaily.com%2Findex.php%3Ffa%3DPAGE.view%26pageId%3D85729&news_title=Florida QB makes 'John 3:16' hottest Google search Tebow inscribed Bible reference on eye black for championship game' TARGET=_blank>",
            "",

            "<a href=/myspace !style='color:#993333'>",
            "",

            "<meta name=3DProgId content=3DExcel.Sheet>",
            "\n",

            "<link id=3D\"shLink\" href=3D\"PSABrKelly-BADMINTONCupResults08FINAL2008_09_19=_files/sheet004.htm\">",
            "\n",

            "<td bgcolor=3D\"#FFFFFF\" nowrap>",
            "\n",

            "<a href=\"http://basnect.info/usersearch/\"predicciones-mundiales-2009\".html\">\"predicciones mundiales 2009\"</a>",
            "\"predicciones mundiales 2009\"",

            "<a class=\"comment-link\" href=\"https://www.blogger.com/comment.g?blogID=19402125&postID=114070605958684588\"location.href=https://www.blogger.com/comment.g?blogID=19402125&postID=114070605958684588;>",
            "",

            "<a href = \"/videos/Bishop\"/\" title = \"click to see more Bishop\" videos\">Bishop\"</a>",
            "Bishop\"",

            "<a href=\"http://bhaa.ie/calendar/event.php?eid=20081203150127531\"\">BHAA Eircom 2 &amp; 5 miles CC combined start</a>",
            "BHAA Eircom 2 & 5 miles CC combined start",

            "<a href=\"http://people.tribe.net/wolfmana\" onClick='setClick(\"Application[tribe].Person[bb7df210-9dc0-478c-917f-436b896bcb79]\")'\" title=\"Mana\">",
            "",

            "<a  href=\"http://blog.edu-cyberpg.com/ct.ashx?id=6143c528-080c-4bb2-b765-5ec56c8256d3&url=http%3a%2f%2fwww.gsa.ac.uk%2fmackintoshsketchbook%2f\"\" eudora=\"autourl\">",
            "",

            # "<" before ">" inhibits tag recognition
            "<input type=\"text\" value=\"<search here>\">",
            "<input type=\"text\" value=\"\n\">",

            "<input type=\"text\" value=\"<search here\">",
            "<input type=\"text\" value=\"\n",

            "<input type=\"text\" value=\"search here>\">",
            "\">",

            # "<" and ">" chars are accepted in on[Event] attribute values
            "<input type=\"text\" value=\"&lt;search here&gt;\" onFocus=\"this.value='<search here>'\">",
            "",

            "<![if ! IE]>\n<link href=\"http://i.deviantart.com/icons/favicon.png\" rel=\"shortcut icon\"/>\n<![endif]>",
            "\n\n\n",

            "<![if supportMisalignedColumns]>\n<tr height=0 style='display:none'>\n<td width=64 style='width:48pt'></td>\n</tr>\n<![endif]>",
            "\n\n\n\n\n\n\n\n",

            "one<![CDATA[<one><two>three<four></four></two></one>]]>two",
            "one<one><two>three<four></four></two></one>two",

            "one<![CDATA[two<![CDATA[three]]]]><![CDATA[>four]]>five",
            "onetwo<![CDATA[three]]>fourfive",

            "<! [CDATA[&]]>", "",

            "<! [CDATA[&] ] >", "",

            "<! [CDATA[&]]", "<! [CDATA[&]]", # unclosed angle bang - all input is output
            u"<!\u2009[CDATA[&]]>", "",

            u"<!\u2009[CDATA[&]\u2009]\u2009>", "",

            u"<!\u2009[CDATA[&]\u2009]\u2009", u"<!\u2009[CDATA[&]\u2009]\u2009", #unclosed angle bang - all input is output

            "<![CDATA[", "",

            "<![CDATA[<br>", "<br>",

            "<![CDATA[<br>]]", "<br>]]",

            "<![CDATA[<br>]]>", "<br>",

            u"<![CDATA[<br>] ] >", "<br>] ] >",

            u"<![CDATA[<br>]\u2009]\u2009>", u"<br>]\u2009]\u2009>",

            u"<!\u2009[CDATA[", u"<!\u2009[CDATA[",

            "one<sPAn class=\"invisible\">two<sup>2<sup>e</sup></sup>.</SpaN>three",
            "onetwo2e.three",

            "one<BR />two<br>three",
            "one\ntwo\nthree",

            "one<BR some stuff here too>two</BR>",
            "one\ntwo\n",

            "one<style type=\"text/css\"> body,font,a { font-family:arial; } </style>two",
            "one<style type=\"text/css\"></style>two",

            #testServerSideIncludes 
            "one<img src=\"image.png\"\n alt =  \"Alt: <!--#echo var='${IMAGE_CAPTION:<!--comment-->\\'Comment\\'}'  -->\"\n\n title=\"Title: <!--#echo var=\"IMAGE_CAPTION\"-->\">two",
            "onetwo",

            "one<script><!-- <!--#config comment=\"<!-- \\\"comment\\\"-->\"--> --></script>two",
            "one\ntwo",

            #testScriptQuotes 
            "one<script attr= bare><!-- action('<!-- comment -->', \"\\\"-->\\\"\"); --></script>two",
            "one\ntwo",

            "hello<script><!-- f('<!--internal--></script>'); --></script>",
            "hello\n",

            #testEscapeScript 
            "one<script no-value-attr>callSomeMethod();</script>two",
            "one<script no-value-attr></script>two",

            #testStyle 
            "one<style type=\"text/css\">\n<!--\n@import url('http://www.lasletrasdecanciones.com/css.css');\n-->\n</style>two",
            "one\ntwo"


        ]

        print('==========================================')
        for i in range(20):
            print('')


        ok = 0
        total = 0
        for t in range(len(tests)//2):
            result = test(tests[t*2],tests[t*2+1],parser=parser)
            if result:
                ok += 1
            total += 1
        print('==========================================')
        print('passed %i out of %i (%f)' % (ok,total,ok/total))

    main("lxml")

