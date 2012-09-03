# -*- coding: utf-8 -*-
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

import os
import sqlite3
import urllib2
from BeautifulSoup import BeautifulSoup
import string
import re
import collections
from itertools import groupby, izip, count
import datetime
import time
from random import choice
import json

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('CFB')

@internationalizeDocstring
class CFB(callbacks.Plugin):
    """Add the help for "@plugin help CFB" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def _batch(self, iterable, size):
        c = count()
        for k, g in groupby(iterable, lambda x:c.next()//size):
            yield g

    def _shortenUrl(self, url):
        posturi = "https://www.googleapis.com/urlshortener/v1/url"
        headers = {'Content-Type' : 'application/json'}
        data = {'longUrl' : url}

        data = json.dumps(data)
        request = urllib2.Request(posturi,data,headers)
        response = urllib2.urlopen(request)
        response_data = response.read()
        shorturi = json.loads(response_data)['id']
        return shorturi

    def _daysSince(self, string):
        a = datetime.date.today()
        b = datetime.datetime.strptime(string, "%B %d, %Y")
        b = b.date()
        delta = b - a
        delta = abs(delta.days)
        return delta
    
    def _shortDateFormat(self, string):
        """Return a short date string from a full date string."""
        return time.strftime('%m/%d', time.strptime(string, '%B %d, %Y'))

    def _b64decode(self, string):
        """Returns base64 encoded string."""
        import base64
        return base64.b64decode(string)
        
    def _validteams(self, optconf):
        """Returns a list of valid teams for input verification."""
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
            
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("select team from cfb where conf=?", (optconf,))        
        teamlist = []
        
        for row in cursor.fetchall():
            teamlist.append(str(row[0]))

        cursor.close()
        
        return teamlist

    def _validconfs(self, optlong=None):
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
        
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
    
        if optlong:
            cursor.execute("select full from confs")        
        else:
            cursor.execute("select short from confs")        
    
        teamlist = []
        
        for row in cursor.fetchall():
            teamlist.append(str(row[0]))

        cursor.close()
        
        return teamlist

    def _confEid(self, optconf):
        """Lookup conf (shortname) eID."""
        
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
        
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("select eid from confs where short=?", (optconf,))
        row = cursor.fetchone()
        cursor.close() 
        
        return (str(row[0])) 
    
    def _translateConf(self, optconf):
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
        
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("select full from confs where short=?", (optconf,))
        row = cursor.fetchone()
        cursor.close()            

        return (str(row[0])) 

    def _lookupTeam(self, optteam, opttable=None):
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
        
        if not opttable: # tid is the default
            opttable = 'tid'
        
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        query = "select %s from cfb where nn LIKE ?" % opttable
        self.log.info(query)
        cursor.execute(query, (optteam,))
        row = cursor.fetchone()
        
        if row is None: # look at nicknames first, then teams
            query = "select %s from cfb where team LIKE ?" % opttable
            self.log.info(query)
            cursor.execute(query, (optteam,))
            row = cursor.fetchone()
            
            if row is None:
                conn.close()
                return "0"
            else:
                conn.close()
                return (str(row[0]))      
        else:
            conn.close()
            return (str(row[0]))

    ######################
    # public functions   #        
    ######################
    
    def cfbconferences(self, irc, msg, args):
        """Show valid conferences."""

        conferences = self._validconfs()
        irc.reply("Valid conferences are: %s" % (string.join([ircutils.bold(item) for item in conferences], " | ")))
        
    cfbconferences = wrap(cfbconferences)


    def cfbteams(self, irc, msg, args, optconf):
        """[conference]
        Display valid teams in a specific conference. 
        """
        
        optconf = optconf.upper()
        
        if optconf not in self._validconfs():
            irc.reply("Invalid conf. Must be one of: %s" % self._validconfs())
            return
        
        fullconf = self._translateConf(optconf) # needs to be lowercase, which this will return
        teams = self._validteams(fullconf)
                
        irc.reply("Valid teams are: %s" % (string.join([ircutils.bold(item.title()) for item in teams], " | "))) # title because all entries are lc. 
        
    cfbteams = wrap(cfbteams, [('somethingWithoutSpaces')])


    def cfbnews(self, irc, msg, args, optnumber):
        """<#>
        Display latest CFB news. If # is given (min 1, max 10), will display more. 
        """
        
        url = self._b64decode('aHR0cDovL20uZXNwbi5nby5jb20vbmNmL25ld3M/JndqYj0=')

        if optnumber:
            if optnumber.isdigit() and 1 <= int(optnumber) <= 10:
                optnumber = optnumber
            else:
                optnumber = '4'
        else:
            optnumber = '4'

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('class="ind alt"','class="ind"')

        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'class':'ind', 'style':'white-space: nowrap;'})
        
        append_list = []
        
        for div in divs[0:int(optnumber)]:
            link = div.find('a')['href']
            linkText = div.find('a')
            append_list.append(ircutils.bold(linkText.getText()) + " " + self._shortenUrl(link))
        
        for each in append_list:
            irc.reply(each)
    
    cfbnews = wrap(cfbnews, [optional('somethingWithoutSpaces')])
    
    
    def cfbarrests(self, irc, msg, args):
        """
        Display the last 5 CFB arrests.
        """    
    
        url = self._b64decode('aHR0cDovL2FycmVzdG5hdGlvbi5jb20vY2F0ZWdvcnkvY29sbGVnZS1mb290YmFsbC8=')

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('&nbsp;',' ').replace('&#8217;','’')

        soup = BeautifulSoup(html)
        lastDate = soup.findAll('span', attrs={'class':'time'})[0] 
        divs = soup.findAll('div', attrs={'class':'entry'})

        append_list = []

        for div in divs:
            title = div.find('h2')
            datet = div.find('span', attrs={'class':'time'})
            datet = self._shortDateFormat(str(datet.getText()))
            arrestedFor = div.find('strong', text=re.compile('Team:'))    
            if arrestedFor:
                matches = re.search(r'<strong>Team:.*?</strong>(.*?)<br />', arrestedFor.findParent('p').renderContents(), re.I|re.S|re.M)
                if matches:
                    college = matches.group(1).replace('(College Football)','').strip()
                else:
                    college = "None"
            else:
                college = "None"
            
            append_list.append(ircutils.bold(datet) + " :: " + title.getText() + " - " + college) # finally add it all
        
        daysSince = self._daysSince(str(lastDate.getText()))
        irc.reply("{0} days since last CFB arrest".format(ircutils.mircColor(daysSince, 'red')))
        
        for each in append_list[0:6]:
            irc.reply(each)

    cfbarrests = wrap(cfbarrests)
    
    
    def cfbanalysis(self, irc, msg, args, optnumber):
        """<#>
        Display latest CFB analysis. If # is given (min 1, max 10), will display more. 
        """
        
        url = self._b64decode('aHR0cDovL20uZXNwbi5nby5jb20vbmNmL2FuYWx5c2lzPyZ3amI9')

        if optnumber:
            if optnumber.isdigit() and 1 <= int(optnumber) <= 10:
                optnumber = optnumber
            else:
                optnumber = '4'
        else:
            optnumber = '4'

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('class="ind alt"','class="ind"')

        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'class':'ind', 'style':'white-space: nowrap;'})
        
        append_list = []
        
        for div in divs[0:int(optnumber)]:
            link = div.find('a')['href']
            linkText = div.find('a')
            append_list.append(ircutils.bold(linkText.getText()) + " " + self._shortenUrl(link))
        
        for each in append_list:
            irc.reply(each)
    
    cfbanalysis = wrap(cfbanalysis, [optional('somethingWithoutSpaces')])
    
    
    def spurrier(self, irc, msg, args):
        """Display a random Steve Spurrier quote."""
    
        url = 'https://docs.google.com/document/pub?id=1oKceGxP6ReL9CAeVrLhdtF_DnGC9K7HY4Sn5JsKlrlQ'

        try:
            headers={'User-Agent':' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0'}
            req = urllib2.Request(url, None, headers)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        soup = BeautifulSoup(html)
        quotes = soup.findAll('p', attrs={'class':re.compile('^c.*?')})

        append_list = []

        for quote in quotes:
            quote = quote.getText().replace(u'&#39;',"'").replace(u'&quot;','"') #.encode('ascii', 'replace')
            #quote = quote.replace('&#39;',"'").replace('&quot;','\"') #.replace(u'\u2019', '\'')
            #quote = quote.text.encode('ascii', 'ignore')
            if len(quote) > 1: # we have empties here because of the regex above. Only way to discard empty quotes here.
                append_list.append(quote)


        output = choice(append_list)
        irc.reply(output)
    
    spurrier = wrap(spurrier)
    
    
    def cfbinjury(self, irc, msg, args, optteam):
        """[team]
        Display injury information for team.
        """
        
        lookupteam = self._lookupTeam(optteam, opttable='usat')
        
        if lookupteam == "0":
            irc.reply("I could not find a schedule for: %s" % optteam)
            return
        
        url = self._b64decode('aHR0cDovL3Nwb3J0c2RpcmVjdC51c2F0b2RheS5jb20vZm9vdGJhbGwvbmNhYWYtdGVhbXMuYXNweD9wYWdlPS9kYXRhL25jYWFmL3RlYW1zLw==') + 'team%s.html' % lookupteam
        
        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('&#039; ','-').replace('&amp;','&')

        soup = BeautifulSoup(html)

        teamName = soup.find('div', attrs={'class':'sdi-title-page-who'})
        div = soup.find('div', attrs={'class':'sdi-so injuries-showhide'})
        table = div.find('table', attrs={'class':'sdi-data-wide'})

        if table.find('td', text="No injuries to report."):
            injReport = "No injuries to report."
        else:
            injuries = table.findAll('tr', attrs={'valign':'top'})
            if len(injuries) < 1:
                injReport = "No injuries to report."
            else:    
                injReport = []
                for injury in injuries:
                    tds = injury.findAll('td')
                    player = tds[0]
                    status = tds[3]
                    appendText = str(player.getText() + " " + status.getText())
                    injReport.append(appendText)
        
        output = "{0} injury report :: {1}".format(ircutils.bold(teamName.getText()), injReport)
        irc.reply(output)
        
    cfbinjury = wrap(cfbinjury, [('text')])
    
    
    def cfbteaminfo(self, irc, msg, args, optteam):
        """[team]
        Display basic info/stats on a team
        """
        
        lookupteam = self._lookupTeam(optteam)
        
        if lookupteam == "0":
            irc.reply("I could not find a schedule for: %s" % optteam)
            return
        
        url = 'http://www.cbssports.com/collegefootball/teams/page/%s/' % lookupteam

        try:        
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open %s" % url)
            return
            
        html = html.replace('&amp;','&').replace(';','')

        soup = BeautifulSoup(html)
        div = soup.find('div', attrs={'class':'pageTitle team'})

        name = div.find('div', attrs={'class':'name'}).find('h1')
        record = div.find('div', attrs={'class':re.compile('^record')})
        table = div.find('div', attrs={'class':'stats'}).find('table', attrs={'class':'data'})
        rows = table.findAll('tr')

        rushingOff = rows[1].findAll('td')[1]
        rushingDef = rows[1].findAll('td')[2]
        passingOff = rows[2].findAll('td')[1]
        passingDef = rows[2].findAll('td')[2]
        overallOff = rows[3].findAll('td')[1]
        overallDef = rows[3].findAll('td')[2]

        output = "{0} :: {1} - Rushing: o: {2} d: {3}  Passing: o: {4} d: {5}  Overall: o: {6} d: {7}".format(\
            ircutils.underline(name.text), record.text, rushingOff.text, rushingDef.text,\
            passingOff.text, passingDef.text, overallOff.text, overallDef.text)
            
        irc.reply(output)
        
    cfbteaminfo = wrap(cfbteaminfo, [('text')])
    
    
    def cfbbowls(self, irc, msg, args, optyear, optbowl):
        """[year] [bowl name]
        Display bowl game result. Requires year and bowl name. Ex: 1982 Sugar or 1984 Rose
        """
        
        currentYear = datetime.datetime.now().strftime("%Y")
        
        if optyear < 1900 or optyear > currentYear:
            irc.reply("Year must be between 1900 and %s" % currentYear)
            return
                        
        optbowl = optbowl.lower().replace('bowl','').strip()
        
        url = 'http://www.sports-reference.com/cfb/years/%s-bowls.html' % optyear

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        soup = BeautifulSoup(html)
        table = soup.find('table', attrs={'id':'bowls'})
        rows = table.findAll('tr')[1:]
       
        new_data = collections.defaultdict(list)

        for row in rows:
            date = row.find('td')
            bowl = date.findNext('td')
            t1 = bowl.findNext('td')
            t1score = t1.findNext('td')
            t2 = t1score.findNext('td')
            t2score = t2.findNext('td')
            loc = t2score.findNext('td')
            new_data[str(bowl.getText().replace(' Bowl','').lower())].append(str(loc.getText() + " :: " + t1.getText() + " " +\
                t1score.getText() + " - " + t2.getText() + " " + t2score.getText()))

        output = new_data.get(optbowl, None)

        if output is None:
            irc.reply("Error: Bowl must be one of: %s" % new_data.keys())
        else:
            irc.reply(" ".join(output))
    
    cfbbowls = wrap(cfbbowls, [('somethingWithoutSpaces'), ('text')])
    
    
    def cfbstandings(self, irc, msg, args, optconf):
        """[conf]
        Display conference standings.
        """
        
        optconf = optconf.upper()
        
        if optconf not in self._validconfs():
            irc.reply("Invalid conf. Must be one of: %s" % self._validconfs())
            return
        
        eid = self._confEid(optconf)
        
        url = 'http://m.espn.go.com/ncf/standings?groupId=%s&y=1&wjb=' % eid
        
        self.log.info(url)

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return

        html = html.replace('class="ind alt', 'class="ind').replace(';', '')

        soup = BeautifulSoup(html)
        table = soup.find('table', attrs={'class':'table'})
        rows = table.findAll('tr')

        new_data = collections.defaultdict(list)

        for row in rows:
            if not row.find('td', attrs={'class':'sec row nw'}):
                team = row.find('td', attrs={'width':'52%'})
                confwl = team.findNext('td')
                ovalwl = confwl.findNext('td')
                div = row.findPrevious('td', attrs={'class':'sec row nw', 'width':'52%'})
                new_data[str(div.getText())].append(str(team.getText() + " " + confwl.getText() + " (" + ovalwl.getText() + ")")) #setdefault method.

        for i,j in new_data.iteritems(): # for each in the confs. 
            output = "{0} :: {1}".format(i, string.join([item for item in j], " | "))
            irc.reply(output)

    cfbstandings = wrap(cfbstandings, [('somethingWithoutSpaces')])
    
    def cfbweeklyleaders(self, irc, msg, args):
        """
        Display CFB weekly leaders.
        """
        
        url = 'http://espn.go.com/college-football/weekly'

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
    
        html = html.replace('tr class="evenrow', 'tr class="oddrow')

        soup = BeautifulSoup(html)
        title = soup.find('h1', attrs={'class':'h2'}) 
        tables = soup.findAll('table', attrs={'class':'tablehead'}) 

        new_data = collections.defaultdict(list)

        for table in tables:
            rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*')})[0:3] # top 3 only. List can be long. 
            for j,row in enumerate(rows): 
                stat = row.findPrevious('tr', attrs={'class':'stathead'})
                colhead = row.findPrevious('tr', attrs={'class':'colhead'}).findAll('td')
                statnames = row.findAll('td')

                del statnames[3], colhead[3] # game is always 4th. delete this. 
        
                for i,statname in enumerate(statnames):            
                    appendString = str(ircutils.bold(colhead[i].text)) + ": " + str(statname.text) # prep string to add into the list.
            
                    if i == len(statnames)-1 and not j == len(rows)-1: # last in each.
                        new_data[str(stat.getText())].append(appendString + " |")  
                    else:
                        new_data[str(stat.getText())].append(appendString)
                
        if title:
            irc.reply(ircutils.mircColor(title.getText(), 'blue'))
        
        for i,j in new_data.iteritems():
            output = "{0} :: {1}".format(ircutils.underline(i), string.join([item for item in j], " "))
            irc.reply(output)
        
    cfbweeklyleaders = wrap(cfbweeklyleaders)


    def cfbpowerrankings(self, irc, msg, args):
        """
        Display this week's CFB Power Rankings.
        """
        
        url = 'http://espn.go.com/college-football/powerrankings'

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
            html = html.replace("evenrow", "oddrow")
        except:
            irc.reply("Failed to fetch: %s" % url)
            return

        soup = BeautifulSoup(html)
        updated = soup.find('div', attrs={'class':'date floatleft'}).text.replace('Updated:','- ')
        table = soup.find('table', attrs={'class': 'tablehead'})
        prdate = soup.find('h1', attrs={'class':'h2'})
        t1 = table.findAll('tr', attrs={'class': re.compile('[even|odd]row')})[0:25]

        object_list = []
        
        for row in t1:
            rowrank = row.find('td')
            rowteam = row.find('div', attrs={'style': re.compile('^padding.*')}).findAll('a')[1]
            rowrecord = row.find('span', attrs={'class': 'pr-record'})
            rowlastweek = row.find('span', attrs={'class': 'pr-last'}) 

            d = collections.OrderedDict()
            d['rank'] = str(rowrank.text)
            d['team'] = str(rowteam.renderContents())
            d['record'] = str(rowrecord.getText()).strip()
            d['lastweek'] = str(rowlastweek.getText()).strip()
            object_list.append(d)

        if prdate:
            irc.reply(ircutils.mircColor(prdate.text, 'blue') + " " + updated)

        for N in self._batch(object_list, 8):
            irc.reply(' '.join(str(str(n['rank']) + "." + " " + ircutils.bold(n['team'])) + " (" + n['lastweek'] + ")" for n in N))
        
    cfbpowerrankings = wrap(cfbpowerrankings)
    
        
    def cfbrankings(self, irc, msg, args, optpoll):
        """[ap|usatoday|bcs]
        Display this week's poll.
        """
        
        validpoll = ['ap', 'usatoday', 'bcs']
        
        optpoll = optpoll.lower()
        
        if optpoll not in validpoll:
            irc.reply("Poll must be one of: %s" % validpoll)
            return
        
        if optpoll == "ap":
            url = 'http://m.espn.go.com/ncf/rankings?pollId=1&wjb=' # AP
        if optpoll == "usatoday":
            url = 'http://m.espn.go.com/ncf/rankings?pollId=2&wjb=' # USAT
        if optpoll == "bcs":
            url = 'http://m.espn.go.com/ncf/rankings?pollId=3&wjb=' # BCS
    
        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
        
        if "No rankings available." in html:
            irc.reply("No rankings available.")
            return

        html = html.replace('class="ind alt','class="ind')

        soup = BeautifulSoup(html)
        rows = soup.find('table', attrs={'class':'table'}).findAll('tr')[1:] # skip header row

        append_list = []

        for row in rows:
            rank = row.find('td')
            team = rank.findNext('td')
            append_list.append(str(rank.getText()) + ". " + str(ircutils.bold(team.getText())))
    
        descstring = string.join([item for item in append_list], " | ") 
        irc.reply(descstring)
    
    cfbrankings = wrap(cfbrankings, [('somethingWithoutSpaces')])    

    
    def cfbteamleaders(self, irc, msg, args, opttype, optteam):
        """<passing|rushing|receiving|touchdowns> [team] 
        Display the top four leaders in team stats.
        """
        
        validtypes = ['passing', 'rushing', 'receving', 'touchdowns']
        
        opttype = opttype.lower()
        
        if opttype not in validtypes:
            irc.reply("type must be one of: %s" % [validtypes])
            return
        
        lookupteam = self._lookupTeam(optteam)
        
        if lookupteam == "0":
            irc.reply("I could not find a schedule for: %s" % optteam)
            return
        
        opttype = opttype.upper()
        
        if opttype == "RUSHING":
            url = 'http://www.cbssports.com/collegefootball/teams/stats/%s/%s?&_1:col_1=4' % (lookupteam, opttype)
        else:
            url = 'http://www.cbssports.com/collegefootball/teams/stats/%s/%s' % (lookupteam, opttype)

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to remove: %s" % url)
            return
            
        html = html.replace('&amp;','&').replace(';','')
    
        soup = BeautifulSoup(html)
        table = soup.find('div', attrs={'id':'layoutTeamsPage'}).find('table', attrs={'class':'data'})
        title = table.find('tr', attrs={'class':'title'}).find('td') 
        headers = table.find('tr', attrs={'class':'label'}).findAll('td')
        rows = table.findAll('tr', attrs={'class':re.compile('row[1|2]')})[0:5]

        object_list = []

        for row in rows:
            tds = row.findAll('td')
            d = collections.OrderedDict() # start the dict per row, append each into that row. one player is one row.
            for i,td in enumerate(tds):
                d[str(headers[i].getText())] = str(td.getText())
            object_list.append(d)
        
        for each in object_list:
            irc.reply(each)
    
    cfbteamleaders = wrap(cfbteamleaders, [('somethingWithoutSpaces'), ('text')])


    def cfbroster(self, irc, msg, args, optlist, optteam):
        """<--position LS|TE|RB|WR|QB|FB|P|DB|K|LB|OL|DL|T|S|DE|G|C|NT> [team]
        Display the roster for a CFB team. With optional --position POS, it will only display people listed at that position.
        """
        
        position = None
        for (option, arg) in optlist:
            if option == 'position':
                position = arg.upper()
                
        validpositions = ['LS', 'TE', 'RB', 'WR', 'QB', 'FB', 'P', 'DB', 'K', 'LB', 'OL', 'DL', 'T', 'S', 'DE', 'G', 'C', 'NT']

        if position is not None:
            if position not in validpositions:
                irc.reply('Position must be one of: %s' % validpositions)
                return

        lookupteam = self._lookupTeam(optteam)
        
        if lookupteam == "0":
            irc.reply("I could not find the team: %s" % optteam)
            return

        url = 'http://www.cbssports.com/collegefootball/teams/roster/%s/' % lookupteam

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('&nbsp;','')

        soup = BeautifulSoup(html)
        div = soup.find('div', attrs={'class':'spacer10 clearBoth'})
        table = div.findNext('table', attrs={'class':'data', 'width':'100%'})
        rows = table.findAll('tr', attrs={'class':re.compile('^row1$|^row2$')})

        players = collections.defaultdict(list)

        for row in rows:
            tds = row.findAll('td')
            pNumber = tds[0]
            pName = tds[1]
            pPos = tds[2]
            pString = str("#" + pNumber.getText() + " " + pName.getText())
            players[str(pPos.getText())].append(pString)
    
        output_list = []
        
        if position is not None:
            output = players.get(position, None)
            if output:
                irc.reply("{0} Roster at {1} :: {2}".format(ircutils.mircColor(optteam.title(), 'red'), ircutils.bold(position), " ".join(output)))
            else:
                irc.reply("I did not find anyone at {0} on {1}".format(ircutils.bold(position), ircutils.bold(optteam.title())))
        else:
            for i,x in players.iteritems():
                output_list.append("{0} :: {1}".format(i, " ".join(x)))
        
            irc.reply("{0} Roster :: {1}".format(ircutils.mircColor(optteam.title(), 'red'), " | ".join(output_list)))
    
    cfbroster = wrap(cfbroster, [(getopts({'position':'somethingWithoutSpaces'})), ('text')])        
    
    
    def cfbheisman(self, irc, msg, args):
        """
        Display poll results on Heisman voting.
        """

        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvaGVpc21hbi8=')

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
                       
        html = html.replace('&nbsp;','')

        soup = BeautifulSoup(html)
        div = soup.find('div', attrs={'class':'hw-module'})
        h2 = div.find('h2').getText()
        date = div.find('div', attrs={'class':'hw-module-date'}).getText()
        table = div.find('table', attrs={'class':'tablehead'})
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*?|^evenrow.*?')})

        append_list = []

        for row in rows:
            tds = row.findAll('td')
            player = tds[0]
            position = tds[1]
            school = tds[2]
            points = tds[-1]
            appendString = str(ircutils.bold(player.getText()) + " " + school.getText() + " (" +points.getText() + ")")
            append_list.append(appendString)
    
        
        descstring = string.join([item for item in append_list], " | ")
        output = "{0} on {1} :: {2}".format(ircutils.mircColor(h2, 'red'), ircutils.bold(date), descstring)

        irc.reply(output)
    
    cfbheisman = wrap(cfbheisman)


    def cfbteamstats(self, irc, msg, args, optstat):
        """[stat]
        Display team leaders for a specific CFB stat.
        """
        
        validcategories = { 'totalOffense':'total', 'sacks':'defense/sort/sacks', 'fg':'kicking/sort/fieldGoalsMade',
                            'passing':'passing', 'int':'defense/sort/interceptions', 'xp':'kicking/sort/extraPointsMade', 'rushing':'rushing',
                            'punting':'punting', 'receiving':'receiving/sort/totalTouchdowns', 'koReturns':'returning/sort/kickReturnYards',
                            'firstDowns':'downs/sort/firstDowns', 'puntReturns':'returning/sort/puntReturnYards',
                            '3rdConv':'downs/sort/thirdDownConvs', '4thConv':'downs/sort/fourthDownConvs'
                            }
        
        if optstat not in validcategories:
            irc.reply("Invalid stat/category. Must be one of: %s" % validcategories.keys())
            return

        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvc3RhdGlzdGljcy90ZWFtL18vc3RhdC8=') + '%s' % validcategories[optstat]

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('&nbsp;','')

        soup = BeautifulSoup(html)
        heading = soup.find('div', attrs={'class':'mod-header stathead'})
        table = soup.find('table', attrs={'class':'tablehead'})
        header = table.find('tr', attrs={'class':'colhead'})
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*?|^evenrow.*?')})[0:10]

        append_list = []

        for row in rows:
            tds = row.findAll('td')
            rank = tds[0]
            team = tds[1]
            stat = row.find('td', attrs={'class':'sortcell'})
            appendString = str(ircutils.bold(team.getText()) + " " + stat.getText())
            append_list.append(appendString)
        
        descstring = string.join([item for item in append_list], " | ")
        output = "{0} :: {1}".format(ircutils.mircColor(heading.getText(), 'red'), descstring)
        
        irc.reply(output)
    
    cfbteamstats = wrap(cfbteamstats, [('somethingWithoutSpaces')])
    
    
    def cfbstats(self, irc, msg, args, optstat):
        """[stat]
        Display individual leaders for a specific CFB stat.
        """
        
        validcategories = { 
                    'rushing':'rushing', 'receving':'receving', 'touchdowns':'scoring/sort/totalTouchdowns',
                    'points':'scoring/sort/totalPoints', 'qbr':'passing/sort/collegeQuarterbackRating',
                    'comppct':'passing/sort/completionPct', 'sacks':'defense/sort/sacks', 
                    'int':'defense/sort/interceptions', 'fgs':'kicking/sort/fieldGoalsMade', 
                    'punting':'punting', 'kickreturnyds':'returning/sort/kickReturnYards',
                    'puntreturnyards':'returning/sort/puntReturnYards', 'passing':'passing'
                    }
        
        if optstat not in validcategories:
            irc.reply("Invalid stat/category. Must be one of: %s" % validcategories.keys())
            return

        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvc3RhdGlzdGljcy9wbGF5ZXIvXy9zdGF0Lw==') + '%s' % validcategories[optstat]

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('&nbsp;','')

        soup = BeautifulSoup(html)
        table = soup.find('table', attrs={'class':'tablehead'})
        header = table.find('tr', attrs={'class':'colhead'})
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*?|^evenrow.*?')})[0:10]

        append_list = []

        for row in rows:
            tds = row.findAll('td')
            rank = tds[0]
            player = tds[1]
            team = tds[2]
            stat = row.find('td', attrs={'class':'sortcell'})
            appendString = str(ircutils.bold(player.getText()) + " (" + team.getText() + ") " + stat.getText())
            append_list.append(appendString)
        
        descstring = string.join([item for item in append_list], " | ")
        output = "Leaders for {0} :: {1}".format(ircutils.mircColor(optstat, 'red'), descstring)
        
        irc.reply(output)
    
    cfbstats = wrap(cfbstats, [('somethingWithoutSpaces')])


    def cfbschedule(self, irc, msg, args, optteam):
        """[team]
        Display the schedule/results for team.
        """
        
        lookupteam = self._lookupTeam(optteam)
        
        if lookupteam == "0":
            irc.reply("I could not find a schedule for: %s" % optteam)
            return
        
        url = 'http://www.cbssports.com/collegefootball/teams/schedule/%s/' % lookupteam

        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
        except:
            irc.reply("Failed to open: %s" % url)
            return
            
        html = html.replace('&amp;','&').replace(';','')
    
        soup = BeautifulSoup(html)
        
        if soup.find('table', attrs={'class':'data stacked'}).find('tr', attrs={'class':'title'}).find('td'):
            title = soup.find('table', attrs={'class':'data stacked'}).find('tr', attrs={'class':'title'}).find('td')
        else:
            irc.reply("Something broke with schedules. Did formatting change?")
            return

        div = soup.find('div', attrs={'id':'layoutTeamsPage'}) # must use this div first since there is an identical table.
        table = div.find('table', attrs={'class':'data', 'width':'100%'})
        rows = table.findAll('tr', attrs={'class':re.compile('^row[1|2]')})

        append_list = []
        
        for row in rows:
            date = row.find('td')
            team = date.findNext('td').find('a')
            time = team.findNext('td')
            
            if team.text.startswith('@'): # underline home
                team = team.text
            else:
                team = ircutils.underline(team.text)
        
            if time.find('span'): # span has score time. empty otherwise.
                time = time.find('span').string
                append_list.append(date.text + " - " + ircutils.bold(team) + " (" + time + ")")
            else:
                time = time.string
                append_list.append(date.text + " - " + ircutils.bold(team))

        descstring = string.join([item for item in append_list], " | ")
        output = "{0} for {1} :: {2}".format(title.text, ircutils.bold(optteam.title()), descstring)
        
        irc.reply(output)
        
    cfbschedule = wrap(cfbschedule, [('text')])

Class = CFB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
