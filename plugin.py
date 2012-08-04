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

    def _lookupTeam(self, optteam):
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
            
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        query = "select tid from cfb where nn LIKE ?"
        cursor.execute(query, (optteam,))
        row = cursor.fetchone()
        
        if row is None: # look at nicknames first, then teams
            query = "select tid from cfb where team LIKE ?"
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
        
        if optconf not in self._validconfs():
            irc.reply("Invalid conf. Must be one of: %s" % self._validconfs())
            return
        
        fullconf = self._translateConf(optconf) # needs to be lowercase, which this will return
        teams = self._validteams(fullconf)
                
        irc.reply("Valid teams are: %s" % (string.join([ircutils.bold(item.title()) for item in teams], " | "))) # title because all entries are lc. 
        
    cfbteams = wrap(cfbteams, [('somethingWithoutSpaces')])
    
    
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
    
    
    def cfbstandings(self, irc, msg, args, optconf):
        """[conf]
        Display conference standings.
        """
        
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
        output = "{0} :: {1}".format(ircutils.bold(title.text), descstring)
        
        irc.reply(output)
        
    cfbschedule = wrap(cfbschedule, [('text')])

Class = CFB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
