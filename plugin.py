# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2013, spline
# All rights reserved.
###

# my libs
import os
import sqlite3
import re
import collections
import datetime
import json
from BeautifulSoup import BeautifulSoup
from base64 import b64decode
from random import choice
import jellyfish  # similarteams.
from operator import itemgetter
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class CFB(callbacks.Plugin):
    """Add the help for "@plugin help CFB" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(CFB, self)
        self.__parent.__init__(irc)
        self._cfbdb = os.path.abspath(os.path.dirname(__file__)) + '/db/cfb.db'

    ##############
    # FORMATTING #
    ##############

    def _red(self, s):
        """Returns a red string."""
        return ircutils.mircColor(s, 'red')

    def _yellow(self, s):
        """Returns a yellow string."""
        return ircutils.mircColor(s, 'yellow')

    def _green(self, s):
        """Returns a green string."""
        return ircutils.mircColor(s, 'green')

    def _blue(self, s):
        """Returns a blue string."""
        return ircutils.mircColor(s, 'blue')

    def _bold(self, s):
        """Returns a bold string."""
        return ircutils.bold(s)

    def _ul(self, s):
        """Returns an underline string."""
        return ircutils.underline(s)

    def _bu(self, s):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(s))

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _splicegen(self, maxchars, stringlist):
        """Return a group of splices from a list based on the maxchars string-length boundary."""

        runningcount = 0
        tmpslice = []
        for i, item in enumerate(stringlist):
            runningcount += len(item)
            if runningcount <= int(maxchars):
                tmpslice.append(i)
            else:
                yield tmpslice
                tmpslice = [i]
                runningcount = len(item)
        yield(tmpslice)

    def _dtFormat(self, outfmt, instring, infmt):
        """Convert from one dateformat to another."""

        try: # infmt/outfmt = "%m/%d/%Y"
            d = datetime.datetime.strptime(str(instring), infmt)
            return d.strftime(outfmt)
        except:  # time.strftime('%m/%d', time.strptime(string, '%B %d, %Y'))
            return instring

    def _validate(self, date, format):
        """Return true or false for valid date based on format."""

        try:
            datetime.datetime.strptime(str(date), format)
            return True
        except ValueError:
            return False

    def _httpget(self, url, h=None, d=None, l=True):
        """General HTTP resource fetcher. Pass headers via h, data via d, and to log via l."""

        if self.registryValue('logURLs') and l:
            self.log.info(url)

        try:
            if h and d:
                page = utils.web.getUrl(url, headers=h, data=d)
            else:
                h = {"User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:17.0) Gecko/20100101 Firefox/17.0"}
                page = utils.web.getUrl(url, headers=h)
            return page
        except utils.web.Error as e:
            self.log.error("ERROR opening {0} message: {1}".format(url, e))
            return None

    def _b64decode(self, s):
        """Returns base64 encoded string."""

        return b64decode(s)

    ######################
    # DATABASE FUNCTIONS #
    ######################

    def _validteams(self, optconf):
        """Returns a list of valid teams for input verification."""

        with sqlite3.connect(self._cfbdb) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT team FROM cfb WHERE conf=?", (optconf,))
            teamlist = [item[0] for item in cursor.fetchall()]  # container for output.
        # return.
        return teamlist

    def _validconfs(self, optlong=None):
        """Return a list of valid confs."""

        with sqlite3.connect(self._cfbdb) as conn:
            cursor = conn.cursor()
            if optlong:
                cursor.execute("SELECT full FROM confs")
            else:
                cursor.execute("SELECT short FROM confs")
            teamlist = [item[0] for item in cursor.fetchall()]  # container for output.
        # return.
        return teamlist

    def _confEid(self, optconf):
        """Lookup conf (shortname) eID."""

        with sqlite3.connect(self._cfbdb) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT eid FROM confs WHERE short=?", (optconf,))
            row = cursor.fetchone()
        # return.
        return row[0]

    def _translateConf(self, optconf):
        "Translate from short to full conference string."

        with sqlite3.connect(self._cfbdb) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full FROM confs WHERE short=?", (optconf,))
            row = cursor.fetchone()
        # return.
        return row[0]

    def _similarTeams(self, optteam, opttable=None):
        """Do fuzzy string matching to find similar team names."""

        similar = [] # empty lists to put our results in.
        # now do our sql work.
        with sqlite3.connect(self._cfbdb) as db:
            cursor = db.cursor() # select all fullnames, eid, rid.
            cursor.execute("SELECT nn, team, %s FROM cfb" % opttable)
            rows = cursor.fetchall()
        # iterate over all rows and do math.
        for row in rows:  # row[0] = nn, row[1] = team, row[2] (what we're looking for.)
            similar.append({'jaro':jellyfish.jaro_distance(optteam, row[0]), 'team':row[1], 'id':row[2]})
            similar.append({'jaro':jellyfish.jaro_distance(optteam, row[1]), 'team':row[1], 'id':row[2]})
        # now, we do two "sorts" to find the "top5" matches. reverse is opposite on each.
        matching = sorted(similar, key=itemgetter('jaro'), reverse=True)[0:5] # bot five.
        # return matching now.
        return matching

    def _lookupTeam(self, optteam, opttable=None):
        "Lookup various strings/variables depending on team."

        if not opttable: # if we have no opttable.
            opttable = 'tid'  # default to opttable.

        optteam = optteam.lower()  # need to lower since fields are lowercase.

        with sqlite3.connect(self._cfbdb) as conn:
            cursor = conn.cursor()  # first check nicenames.
            # first, we try direct matches, then LIKE with %, then fuzzy.
            query = "SELECT %s FROM cfb WHERE nn=?" % opttable
            cursor.execute(query, (optteam,))
            row = cursor.fetchone()
            if row:  # found team via nn.
                retval = row[0]
            else:  # did not fid directly via nn. check team approx.
                query = 'SELECT %s FROM cfb WHERE team=?' % opttable
                cursor.execute(query, (optteam,))
                row = cursor.fetchone()
                if row:  # found via team = directly.
                    retval = row[0]
                else:  # did not find via approx matches. try via 'like'.
                    query = "SELECT %s FROM cfb WHERE nn LIKE ?" % opttable
                    cursor.execute(query, ('%'+optteam+'%',))
                    row = cursor.fetchone()
                    if row:  # we found via nn LIKE.
                        retval = row[0]
                    else:  # did not find via nn like. Check teamname LIKE.
                        query = "SELECT %s FROM cfb WHERE team LIKE ?" % opttable
                        cursor.execute(query, ('%'+optteam+'%',))
                        row = cursor.fetchone()
                        if row:  # matched a team via LIKE.
                            retval = row[0]
                        else:  # we found nothing via approx matching. our last hope is going fuzzy with jaro.
                            st = self._similarTeams(optteam, opttable=opttable)  # get similar teams.
                            if st[0]['jaro'] > 0.75:  # if jaro is > 0.75
                                retval = st[0]['id']  # we match. return id.
                            else:  # we finally bail. return the jaro matches for display.
                                retval = st
        # finally, return.
        return retval

    #############
    # PLAYER DB #
    #############

    def _eplayerfind(self, pname):
        """Find a player's page via google ajax.."""

        # construct url (properly escaped)
        pname = "%s site:espn.go.com/college-football/player/" % pname
        url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=8&q=%s" % pname.replace(' ', '%20')
        # now fetch url.
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # load the json.
        jsonf = json.loads(html)
        # make sure status is 200.
        if jsonf['responseStatus'] != 200:
            return None
        # make sure we have results.
        results = jsonf['responseData']['results']
        if len(results) == 0:
            return None
        # finally, return the url.
        url = results[0]['url']
        return url

    def cfbplayerinfo(self, irc, msg, args, optplayer):
        """<player name>

        Fetch player info/bio information.
        Ex: aj mccarron
        """

        # try and grab a player.
        url = self._eplayerfind(optplayer)
        if not url:
            irc.reply("ERROR: I could not find a player page for: {0}".format(optplayer))
            return
        # we do have url now. fetch it.
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        playerdiv = soup.find('div', attrs={'class':'mod-content'})
        if not playerdiv:
            irc.reply("ERROR: I could not parse {0} for player info.".format(url))
            return
        # ok we did get player info. output.
        pname = playerdiv.find('h1').getText().encode('utf-8')
        playerinfo = playerdiv.find('div', attrs={'class':'player-bio'}).getText(separator=' ')
        irc.reply("{0} :: {1}".format(self._red(pname), playerinfo))

    cfbplayerinfo = wrap(cfbplayerinfo, [('text')])

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def cfbcountdown(self, irc, msg, args):
        """
        Display time until the next CFB Season.
        """

        now = datetime.datetime.today()
        ny = now.year
        base = datetime.datetime(ny, 9, 1)
        base = base-datetime.timedelta(days=1)  # go back one day to the last day of August.
        # base is now always August 31 of the current year. We figure out what day of the week it is.
        wd = base.weekday()
        # do some timedelta math.
        if wd == 0: ma = 5
        elif wd == 1: ma = 4
        elif wd == 2: ma = 5
        elif wd == 3: ma = 6
        elif wd == 4: ma = 1
        elif wd == 5: ma = 2
        elif wd == 6: ma = 3
        # now lets take ma and timedelta. this should be kickoff date unless there is something that pushes it like in 2013.
        kod = base-datetime.timedelta(days=+(ma))  # date itself. we turn it into localtime below.
        kot = datetime.datetime(kod.year, kod.month, kod.day, 18, 01)  # if not run in Eastern, it's off. im not doing timezones.
        # did the kickoff date already pass?
        if kod < now:  # it passed. this will reset when the year passes.
            irc.reply("Sorry, the kickoff date for the {0} CFB Season has already passed.".format(now.year))
        else:  # has not passed. do some math.
            hl = kot-now
            irc.reply("There are {0} days, {1} hours, {2} mins, {3} seconds until the start of the {4} CFB Season".format(hl.days, hl.seconds/60/60, hl.seconds/60%60, hl.seconds%60, now.year))
    
    cfbcountdown = wrap(cfbcountdown)

    def cfbconferences(self, irc, msg, args):
        """
        Show valid CFB conferences.
        """

        conferences = self._validconfs()
        irc.reply("Valid CFB Conferences: {0}".format(" | ".join(sorted([i for i in conferences]))))

    cfbconferences = wrap(cfbconferences)

    def cfbteams(self, irc, msg, args, optconf):
        """<conference>
        Display valid teams in a specific conference.
        Ex: SEC.
        """

        optconf = optconf.upper()
        if optconf not in self._validconfs():
            irc.reply("ERROR: Invalid conference. Valid: {0}".format(" | ".join(sorted([i for i in self._validconfs()]))))
            return

        fullconf = self._translateConf(optconf)  # needs to be lowercase, which this will return
        teams = self._validteams(fullconf)  # grab teams.
        # title because all entries are lc.
        irc.reply("Valid teams are: {0}".format(" | ".join(sorted([self._bold(i.title()) for i in teams]))))

    cfbteams = wrap(cfbteams, [('somethingWithoutSpaces')])

    def cfbarrests(self, irc, msg, args):
        """
        Display the last 5 CFB arrests.
        """

        # build and fetch url.
        url = self._b64decode('aHR0cDovL2FycmVzdG5hdGlvbi5jb20vY2F0ZWdvcnkvY29sbGVnZS1mb290YmFsbC8=')
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        ars = soup.findAll('h2', attrs={'class':'blog-title'})
        if len(ars) == 0:
            irc.reply("No arrests found. Something break?")
            return
        else:
            az = [] # empty list for arrests.
            # iterate over each and inject to list.
            for ar in ars[0:5]: # iterate over each.
                ard = ar.findNext('div', attrs={'class':'blog-date'})
                # text and cleanup.
                ard = ard.getText().encode('utf-8').replace('Posted On', '')
                # print.
                az.append({'d':ard, 'a':ar.getText().encode('utf-8')})
        # now lets create our output.
        delta = datetime.datetime.strptime(str(az[0]['d']), "%B %d, %Y").date() - datetime.date.today()
        daysSince = abs(delta.days)
        # finally, output.
        irc.reply("{0} days since last arrest :: {1}".format(self._red(daysSince), " | ".join([i['a'] + " " + i['d'] for i in az])))

    cfbarrests = wrap(cfbarrests)

    def spurrier(self, irc, msg, args):
        """
        Display a random Steve Spurrier quote.
        """

        # build and fetch url.
        url = self._b64decode('aHR0cHM6Ly9kb2NzLmdvb2dsZS5jb20vZG9jdW1lbnQvcHViP2lkPTFvS2NlR3hQNlJlTDlDQWVWckxoZHRGX0RuR0M5SzdIWTRTbjVKc0tscmxR')
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        quotes = soup.findAll('p', attrs={'class':re.compile('^c.*?')})
        # container to put all quotes in.
        append_list = []
        # process each quote. tricky because of html garbage.
        for quote in quotes:
            quote = quote.getText().replace(u'&#39;',"'").replace(u'&quot;','"')
            if len(quote) > 1:  # we have empties here because of the regex above. skip.
                append_list.append(quote.encode('utf-8'))  # append
        # output time.
        irc.reply("{0}".format(choice(append_list)))

    spurrier = wrap(spurrier)
    
    def cfbtv(self, irc, msg, args, optteam):
        """<team>
        
        Try and see if we can locate what channel is broadcasting
        a team's game. Only works for current week.
        """

        url = 'http://lsufootball.net/tvschedule.htm'
        # build and fetch url.
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
            # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        table = soup.find('table', attrs={'class':'tabdata cellBorders'})
        if not table:
            irc.reply("Something broke on {0}".format(url))
            return
        # container.
        tv = {}
        # rows.
        rows = table.findAll('tr')
        for row in rows[0:60]:  # iterate over all.
            tds = row.findAll('td')
            # we only want len(3)
            if len(tds) == 3:
                d = row.findPrevious('tr', attrs={'bgcolor':'FFFFFF'})
                # find the previous "center"
                if not d:  # bail if none.
                    continue
                tms = tds[0].getText().encode('utf-8').replace('&amp;', '&')
                # split teams on ' at '
                try:
                    tm1, tm2 = tms.split(' at ', 1)
                except:  # just abort if this fucks up.
                    continue
                ct = tds[1].getText().encode('utf-8').replace('.', '')
                nw = tds[2].getText().encode('utf-8').replace('/', '')
                # check if it is within a week.
                os = "{0} {1} {2} {3}".format(d.getText().encode('utf-8'), ct, tms, nw)
                if tm1 not in tv:
                    tv[tm1.lower()] = os
                else:
                    self.log.info("{0} was not put into TV {1}".format(tm1, os))
                if tm2 not in tv:
                    tv[tm2.lower()] = os
        # now lets try and match.
        optteam = optteam.lower()  # lower.
        # match.
        if optteam in tv:
            irc.reply("{0}".format(tv[optteam]))
        else:
            irc.reply("Sorry, I didn't see {0} on {1}".format(optteam, url))

    cfbtv = wrap(cfbtv, [('text')])

    def cfbgamestats(self, irc, msg, args, optteam):
        """<team>

        Fetch live or previous game stats for team.
        Use exact or near exact team name.
        Ex: Alabama
        """

        url = self._b64decode('aHR0cDovL3Njb3Jlcy5lc3BuLmdvLmNvbS9uY2Yvc2NvcmVib2FyZD9jb25mSWQ9ODA=')
        # build and fetch url.
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
            # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        divs = soup.findAll('div', attrs={'id':re.compile('^\d+-gameContainer')})
        # check to make sure we found games.
        if len(divs) == 0:
            irc.reply("ERROR: Something went wrong trying to find games on page. Formatting change?")
            return
        # container to match our games.
        games = {}
        # process games
        for div in divs:
            gameid = div['id'].replace('-gameContainer', '')
            ateam = div.find('span', attrs={'id':'%s-aTeamName' % gameid})
            hteam = div.find('span', attrs={'id':'%s-hTeamName' % gameid})
            # clean-up the names for better matching.
            ateam = ateam.getText().lower().strip().replace('&amp;', '&').replace('.', '')
            hteam = hteam.getText().lower().strip().replace('&amp;', '&').replace('.', '')
            games[ateam] = gameid  # inject away
            games[hteam] = gameid  # inject home.

        # we must match input (teamname) with a gameid.
        if optteam.lower() in games:
            gid = games[optteam.lower()]
        else:
            output = " | ".join(sorted(games.keys()))
            irc.reply("ERROR: I did not find any games with team: {0} in it. I do have: {1}".format(optteam, output))
            return

        # build and fetch url.
        url = self._b64decode('aHR0cDovL3Njb3Jlcy5lc3BuLmdvLmNvbS9uY2YvYm94c2NvcmU/Z2FtZUlkPQ==') + '%s' % (gid)
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return

        # sanity check before we process.
        if 'Box score not currently available.' in html:
            irc.reply("ERROR: Box score is currently unavailable at: {0} . Checking too early?".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        tsh4 = soup.find('h4', text="Team Stat Comparison")
        if not tsh4:  # sanity check.
            irc.reply("ERROR: Something went wrong finding Team Stats in gameid: {0}. Checking too early?".format(gid))
            return
        # we find teamstats here.
        tscontent = tsh4.findNext('table', attrs={'class':'mod-data'})  # table for teamstats.
        tsteams = tscontent.findAll('th', attrs={'nowrap':'nowrap'})  # find the 2x TH with teams.
        teams = {}  # teams container
        for i, tsteam in enumerate(tsteams):  # iterate over these two.
            teams[i] = tsteam.getText().replace('&amp;', '&')  # inject into the dict.
        # now find the tbody with stats.
        tsrows = tscontent.findAll('tr', attrs={'class':re.compile('odd|even')})
        tsstats = collections.defaultdict(list)  # container for the stats.
        for tsrow in tsrows:  # iterate over rows. each row has two tds.
            tds = tsrow.findAll('td')  # find all tds. There should be three per row.
            tsstats[teams[0]].append("{0}: {1}".format(self._bold(tds[0].getText()), tds[1].getText()))  # inject away stats.
            tsstats[teams[1]].append("{0}: {1}".format(self._bold(tds[0].getText()), tds[2].getText()))  # inject home stats.
        # now we prepare to output.
        for (z, y) in tsstats.items():  # k = teamname, v = list of stats.
            irc.reply("{0} :: {1}".format(self._red(z), " | ".join(y)))

    cfbgamestats = wrap(cfbgamestats, [('text')])

    def cfbinjury(self, irc, msg, args, optteam):
        """<team>
        Display injury information for team.
        Ex: Alabama
        """

        ## CURRENTLY THIS COMMAND IS BROKEN.
        irc.reply("Sorry, command is currently broken!")
        return

        # check the team now.
        lookupteam = self._lookupTeam(optteam, opttable='usat')
        if isinstance(lookupteam, list):  # if match no good, list returned. give simmilar teams.
            irc.reply("ERROR: I could not find team '{0}'. Similar: {1}".format(optteam, " | ".join(sorted([i['team'].title() for i in lookupteam]))))
            return
        # build and fetch html.
        url = self._b64decode('aHR0cDovL3Nwb3J0c2RpcmVjdC51c2F0b2RheS5jb20vZm9vdGJhbGwvbmNhYWYtdGVhbXMuYXNweD9wYWdlPS9kYXRhL25jYWFmL3RlYW1zLw==') + 'team%s.html' % lookupteam
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        teamName = soup.find('div', attrs={'class':'sdi-title-page-who'})
        div = soup.find('div', attrs={'class':'sdi-so injuries-showhide'})
        table = div.find('table', attrs={'class':'sdi-data-wide'})
        # process the table.
        if table.find('td', text="No injuries to report."):  # no injuries.
            injreport = "No injuries to report."
        else:  # each tr (row) is an injury.
            injuries = table.findAll('tr', attrs={'valign':'top'})
            if len(injuries) < 1:  # none.
                injreport = "No injuries to report."
            else:  # we found injuries.
                injreport = []  # container to shove them all in.
                for injury in injuries:
                    tds = injury.findAll('td')
                    injReport.append("{0} {1}".format(tds[0].getText(), tds[3].getText()))
        # output time.
        irc.reply("{0} injury report :: {1}".format(self._bold(teamName.getText()), " | ".join(injreport)))

    cfbinjury = wrap(cfbinjury, [('text')])

    def cfbpolls(self, irc, msg, args, optpoll, optyear, optweek):
        """<AP|BCS> <year> <week #>
        Display historical AP/BCS polls (Top 25)for a specific year and week.
        Works from 1936 on for AP; 1998 for BCS.
        Ex. AP 1979 1 or BCS 2007 8
        """

        # checks on input. different depending on the poll.
        optpoll = optpoll.lower() # lower to match the table id.
        if optpoll == "ap": # first ap
            if 1936 >= int(optyear) >= datetime.datetime.now().year:
                irc.reply("ERROR: Year for AP must be after 1936 and less than the current year.")
                return
            if 1 >= int(optweek) >= 16:
                irc.reply("ERROR: Week for AP must be between 1-16.")
                return
        elif optpoll == "bcs": # now bcs. goes away in 2014?
            if 1998 >= int(optyear) >= datetime.datetime.now().year:
                irc.reply("ERROR: Year for BCS must be after 1998 and less than current year.")
                return
            if 1 >= int(optweek) >= 8:
                irc.reply("ERROR: Week for BCS must be between 1-8.")
                return
        else: # if we don't have ap/bcs
            irc.reply("ERROR: poll name must be one of the two: AP or BCS. Ex: BCS 2007 2")
            return
        # build url and fetch.
        url = self._b64decode('aHR0cDovL3d3dy5zcG9ydHMtcmVmZXJlbmNlLmNvbS9jZmIveWVhcnMv') + '%s-polls.html' % optyear
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        table = soup.find('table', attrs={'id':optpoll})
        tbody = table.find('tbody')
        rows = tbody.findAll('tr', attrs={'class':''})
        # containers to put all of the poll data/weekdates/confs in.
        poll = collections.defaultdict(list)  # key is pollname, value is the list.
        weekdate = {}  # weekdates.
        confcount = {}  # counts the confs.
        # each row is a team.
        for row in rows:  # process and populate all.
            tds = row.findAll('td')
            wk = int(tds[0].getText())
            date = tds[1].getText()
            rk = tds[2].getText()
            school = tds[3].getText().replace('&amp;','&')  # aTm fix.
            conf = tds[6].find('a').getText()
            poll[wk].append("{0}. {1}".format(rk, school))
            weekdate[wk] = date  # separate dict for week num/date.
            if wk == optweek:  # is the week the same as input?
                confcount[conf] = confcount.get(conf, 0) + 1  # ++ or +1
        # output time.
        output = poll.get(optweek)
        if output:  # we have a poll for that week.
            irc.reply("{0} {1} Week {2} ({3}) :: {4}".format(self._red(optyear), optpoll.upper(), optweek,\
                weekdate.get(optweek), " | ".join([ircutils.bold(str(k)) + ": " + str(v) for k,v in confcount.items()])))
            irc.reply("{0}".format(" ".join(output)))
        else:  # something usually went wrong if this is not found.
            irc.reply("ERROR: I did not find a poll for {0} in year {1} for week {2}. I do have one for weeks: {3}".format(\
                optpoll, optyear, optweek, " | ".join(sorted(poll.keys()))))

    cfbpolls = wrap(cfbpolls, [('somethingWithoutSpaces'), ('int'), ('int')])

    def cfbbowls(self, irc, msg, args, optyear, optbowl):
        """<year> <bowl name>
        Display bowl game result. Requires year and bowl name.
        Ex: 1982 Sugar or 1984 Rose
        """

        # lower and cleanup input (bowl).
        optbowl = optbowl.lower().replace('bowl','').strip()  # remove 'bowl'.
        # build and process url.
        url = self._b64decode('aHR0cDovL3d3dy5zcG9ydHMtcmVmZXJlbmNlLmNvbS9jZmIveWVhcnMv') + '%s-bowls.html' % optyear
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        table = soup.find('table', attrs={'id':'bowls'})
        rows = table.findAll('tr')[1:]
        # container for output. key=bowl name.
        bowls = collections.defaultdict(list)
        # each row is a bowl.
        for row in rows:
            tds = [item.getText() for item in row.findAll('td')]
            bowl = tds[1].replace(' Bowl','').lower()
            appendString = "{0} {1} :: {2} {3} - {4} {5}".format(self._bold(optyear), self._bold(tds[6]), tds[2], tds[3], tds[4], tds[5], tds[0])
            bowls[bowl] = appendString
        # output time.
        output = bowls.get(optbowl)
        if not output:  # we don't have a bowl.
            irc.reply("ERROR: I didn't find the '{0}' bowl in {1}. Valid bowls: {2}".format(optbowl, optyear, " | ".join(sorted(bowls.keys()))))
        else:
            irc.reply(output)

    cfbbowls = wrap(cfbbowls, [('int'), ('text')])

    def cfbstandings(self, irc, msg, args, optconf):
        """<conf>
        Display conference standings.
        Ex: SEC.
        """

        # verify conf.
        optconf = optconf.upper()  # gotta go upper here.
        if optconf not in self._validconfs():  # make sure we have a valid conf.
            irc.reply("ERROR: Invalid conference. Must be one of: {0}".format(" | ".join(sorted(self._validconfs()))))
            return
        # build and fetch url.
        eid = self._confEid(optconf)  # lookup eid of conf for url.
        url = self._b64decode('aHR0cDovL20uZXNwbi5nby5jb20vbmNmL3N0YW5kaW5ncz8=') + 'groupId=%s&y=1&wjb=' % eid
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        table = soup.find('table', attrs={'class':'table'})
        rows = table.findAll('tr')
        # container for output.
        standings = collections.defaultdict(list)
        # messy because there might be more than one div in the conf.
        for row in rows:
            if not row.find('td', attrs={'class':'sec row nw'}):  # odd workaround here.
                tds = row.findAll('td')
                team = tds[0].getText().replace('&amp;', '&')
                confwl = tds[1].getText()
                ovalwl = tds[2].getText()
                div = row.findPrevious('td', attrs={'class':'sec row nw', 'width':'52%'}).getText()  # divisions.
                standings[div].append("{0} {1} ({2})".format(self._bold(team), confwl, ovalwl))
        # now, output. iterate through standings because there might be n+1.
        for i, j in standings.iteritems(): # for each in the confs.
            output = "{0} :: {1}".format(self._red(i), " | ".join([item for item in j]))  # i = div
            irc.reply(output)

    cfbstandings = wrap(cfbstandings, [('somethingWithoutSpaces')])

    def cfbweeklyleaders(self, irc, msg, args):
        """
        Display CFB weekly leaders.
        """

        # build and fetch url.
        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvd2Vla2x5')
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        title = soup.find('h1', attrs={'class':'h2'}).getText()
        tables = soup.findAll('table', attrs={'class':'tablehead'})
        # container for output.
        weeklyleaders = collections.defaultdict(list)
        # each table is one leader.
        for table in tables:
            rows = table.findAll('tr', attrs={'class':re.compile('^(odd|even)row.*')})[0:3] # top 3 only. List can be long.
            for j, row in enumerate(rows):  # go through each.
                stat = row.findPrevious('tr', attrs={'class':'stathead'})
                colhead = row.findPrevious('tr', attrs={'class':'colhead'}).findAll('td')  # each header is diff.
                statnames = row.findAll('td')
                del statnames[3], colhead[3] # game is always 4th. delete this.
                # each statname is an entry.
                for i, statname in enumerate(statnames):
                    appendString = "{0}: {1}".format(self._bold(colhead[i].getText()), statname.getText()) # prep string to add into the list.
                    if i == len(statnames)-1 and not j == len(rows)-1:  # last in each.
                        weeklyleaders[stat.getText()].append(appendString + " |")
                    else:  # not the last.
                        weeklyleaders[stat.getText()].append(appendString)
        # output time.
        irc.reply("{0}".format(self._blue(title)))
        for i, j in weeklyleaders.iteritems():  # iterate through each stat.
            irc.reply("{0} :: {1}".format(self._ul(i), " ".join([item for item in j])))

    cfbweeklyleaders = wrap(cfbweeklyleaders)

    def cfbrankings(self, irc, msg, args, optpoll):
        """<ap|usatoday|playoff|<team>
        If ap, usatoday or playoff are given, it will display this week's poll.
        If <team> is given, it will search each poll for that team and display.
        Ex: ap OR Alabama
        """

        # handle input.
        optpoll, optinput = optpoll.lower(), False
        # check poll. url conditional on the string.
        if optpoll not in ['playoff', 'ap', 'usatoday']:  # check for ap|bcs|usatoday.
            optinput = optpoll  # change optpoll into optinput so we can search later.
        # fetch url.
        url = self._b64decode('aHR0cDovL3JpdmFscy55YWhvby5jb20vbmNhYS9mb290YmFsbC9wb2xscw==')
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        tables = soup.findAll('div', attrs={'class':'ysprankings_poll ysprankings_poll_3column'})
        heading = soup.find('div', attrs={'id':'ysprankings-hd'}).find('h2').getText()
        # output container.
        polls = collections.defaultdict(list)
        # now, process html data in the tables, each poll has its own. polls[string] = [teams].
        for table in tables:
            ul = table.find('ul')  # all teams are in a ul
            if ul:  # during the offseason, these won't be present in all polls.
                poll = table.find('div', attrs={'class':'hd'})  # poll's name hidden in here. replace text below.
                poll = poll.getText()  # replace text below to mate up keys.
                poll = poll.replace('AP Top 25', 'ap').replace('USA Today', 'usatoday').replace('CFB Selection Committee', 'playoff')
                lis = ul.findAll('li')  # each li in table = teams.
                for li in lis:  # enumerate through each team.
                    if li.find('span'):  # do some cleaning up. rank is contained in span.
                        li.span.extract()  # remove it if found.
                    team = li.getText().replace('&amp;', '&')  # aTm fix.
                    polls[poll].append(team)  # finally, append to our defaultdict.
        # output time.
        if optinput:  # if we have a teamname not poll.
            # matchingteams = [q for q, item in enumerate(x) if re.search(optinput, item, re.I)]
            newpoll = {}  # dict to put matching items in.
            for key, values in polls.iteritems():  # iterate through each poll, values = list of teams.
                for v in values:  # go through list of teams in value.
                    if optinput in v.lower():  # if we match anything. lowered. add rank + team below.
                        newpoll.setdefault(key, []).append("{0}. {1}".format(values.index(v)+1, v))
            # output time.
            if len(newpoll) != 0:  # if we have matches. listcmp
                output = [self._red(k.upper()) + " :: " + (" ".join(v)) for (k, v) in newpoll.items()]
                irc.reply(" || ".join(output))  # out.
            else:
                irc.reply("ERROR: I did not find anything matching '{0}' in the AP, BCS or USA Today polls.".format(optinput))
        else:  # just display the poll.
            if len(polls[optpoll]) == 0:
                irc.reply("{0} :: No poll data yet.".format(self._red(optpoll.upper())))
            else:
                output = " ".join([(str(i+1) + ". " + j) for i, j in enumerate(polls[optpoll])])  # listcmp + rank.
                irc.reply("{0} :: {1} :: {2}".format(self._red(optpoll.upper()), self._bold(heading), output))

    cfbrankings = wrap(cfbrankings, [('text')])

    def cfbteamleaders(self, irc, msg, args, optstat, optteam):
        """<passing|rushing|receiving|touchdowns> <team>
        Display the top four leaders in a stat category for team.
        Ex: rushing Alabama
        """

        # check stat input first.
        # http://espn.go.com/college-football/team/stats/_/id/333/alabama-crimson-tide
        validstats = ['passing', 'rushing', 'receving', 'kicking']
        optstat = optstat.lower()
        if optstat not in validstats:
            irc.reply("ERROR: stat type must be one of: {0}".format(sorted(validstats)))
            return
        # check the team now.
        lookupteam = self._lookupTeam(optteam, opttable='eid')
        if isinstance(lookupteam, list):  # if match no good, list returned. give simmilar teams.
            irc.reply("ERROR: I could not find team '{0}'. Similar: {1}".format(optteam, " | ".join(sorted([i['team'].title() for i in lookupteam]))))
            return
        # url is conditional because of an odd bug.
        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvdGVhbS9zdGF0cy9fL2lkLw==') + '%s' % lookupteam
        # fetch url and return html.
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        title = soup.find('h1', attrs={'class':'h2'}).getText()  # title for output.
        tables = soup.findAll('table', attrs={'class':'tablehead'})  # each stat is in a table.
        # container for output.
        teamleaders = collections.defaultdict(list)
        # iterate through each table.
        for table in tables:
            stat = table.find('tr', attrs={'class':'stathead'}).getText()
            stat = stat.lower().replace(' statistics', '')  # fix our key text. cheap!
            headers = table.find('tr', attrs={'class':'colhead'}).findAll('td')  # lookup stat this way.
            rows = table.findAll('tr', attrs={'class':re.compile('(odd|even)row')})  # each row is a player.
            for row in rows:  # iterate through players.
                tds = row.findAll('td')  # we use this for player and neat trick below.
                player = tds[0].getText()  # sortcell has the stat the order is determined by.
                tag = [(x, y) for (x, y) in enumerate(tds) if y.get('class') == "sortcell"][0]  # returns a list with a tuple.
                # append into k:v
                teamleaders[stat].append("{0} - {1} {2}".format(player, headers[tag[0]].getText(), tag[1].getText()))
        # output time.
        output = teamleaders.get(optstat)
        if not output:  # we didn't find a stat. something probably wrong.
            irc.reply("ERROR: I did not find any stats for {0} on {1}".format(optstat, optteam))
            return
        else:  # we found our stat.
            irc.reply("{0} :: {1} :: {2}".format(self._red(title), self._bold(optstat.upper()), " | ".join(output)))

    cfbteamleaders = wrap(cfbteamleaders, [('somethingWithoutSpaces'), ('text')])

    def cfbroster(self, irc, msg, args, optlist, optteam):
        """[--number #|--position LS|TE|RB|WR|QB|FB|P|DB|K|LB|OL|DL|T|S|DE|G|C|NT] <team>
        Display the roster for a CFB team.
        Use --position POS to only display position.
        Use --number # to find a roster #.
        Ex: Alabama or --number 63 Alabama --position QB Alabama
        """

        # broken :[
        irc.reply("Sorry, cfbroster is broken.")
        return

        # handle optlist --getopts here for position and number.
        position, roster = None, None
        for (option, arg) in optlist:
            if option == 'position':  # find a position.
                validpositions = ['LS', 'TE', 'RB', 'WR', 'QB', 'FB', 'P', 'DB', 'K', 'LB', 'OL', 'DL', 'T', 'S', 'DE', 'G', 'C', 'NT']
                if arg.upper() not in validpositions:  # position is invalid.
                    irc.reply("ERROR: --position must be one of: {0}".format(" | ".join(sorted(validpositions))))
                    return
                else:  # position is valid.
                    position = arg.upper()
            if option == 'number':  # find a specific #.
                roster = arg.replace('#', '')  # strip #.
                if not roster.isdigit():  # sanity check on the number.
                    irc.reply("ERROR: --number # must be a number like 5 or 63.")
                    return
        # check the team now.
        lookupteam = self._lookupTeam(optteam)
        if isinstance(lookupteam, list):  # if match no good, list returned. give simmilar teams.
            irc.reply("ERROR: I could not find team '{0}'. Similar: {1}".format(optteam, " | ".join(sorted([i['team'].title() for i in lookupteam]))))
            return
        # build and fetch url.
        url = self._b64decode('aHR0cDovL3d3dy5jYnNzcG9ydHMuY29tL2NvbGxlZ2Vmb290YmFsbC90ZWFtcy9yb3N0ZXI=') + '/%s/' % lookupteam
        # fetch url and return html.
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        self.log.info(str(html))
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        tn = soup.find('div', attrs={'class':'info'}).find('h1').getText(separator=' ')  # teamname.
        tn = utils.str.normalizeWhitespace(tn)  # clean up teamname.
        div = soup.find('div', attrs={'class':'spacer10 clearBoth'})
        table = div.findNext('table', attrs={'class':'data', 'width':'100%'})
        rows = table.findAll('tr', attrs={'class':re.compile('^row1$|^row2$')})
        # containers for output.
        players = collections.defaultdict(list)
        rosters = collections.defaultdict(list)
        # each row is a player. populate defaultdict above.
        for row in rows:
            tds = row.findAll('td')
            pNumber = tds[0].getText()
            pName = tds[1].getText()
            pPos = tds[2].getText()
            players[pPos].append("#{0} {1}".format(pNumber, pName))  # append for roster (position or all)
            rosters[pNumber].append("{0}".format(pName))  # append for roster #'s
        # output time.
        if position:  # looking for a specific position.
            output = players.get(position)  # key is the position.
            if output:  # if we have people there.
                irc.reply("{0} Roster at {1} :: {2}".format(self._red(optteam.title()), self._bold(position), " | ".join(output)))
            else:  # no players at that position.
                irc.reply("I did not find anyone at {0} on {1}".format(self._bold(position), self._red(optteam.title())))
        elif roster:  # looking for a specific roster.
            output = rosters.get(roster)
            if output:  # we found someone on the team.
                irc.reply("#{0} on {1} :: {2}".format(self._bold(roster), self._red(optteam), " | ".join(output)))
            else:  # we did not find someone on the team.
                irc.reply("I did not find anyone on {0} with roster number: {1}".format(optteam, roster))
        else:  # just display  the roster.
            output = [k.upper()+ " :: " + (" ".join(v)) for (k, v) in players.items()]
            irc.reply("{0} Roster :: {1}".format(self._red(tn), " | ".join(output)))

    cfbroster = wrap(cfbroster, [(getopts({'position':('somethingWithoutSpaces'), 'number':('somethingWithoutSpaces')})), ('text')])

    def cfbcoachsalary(self, irc, msg, args, optcoach):
        """<school/coach>

        Display a salary for a college football coach from the USAT table.
        Issue with school or coach name to display a specific one.
        Ex: Saban OR Alabama
        """

        # fetch url and return html.
        url = self._b64decode('aHR0cDovL3d3dy51c2F0b2RheS5jb20vc3BvcnRzL2NvbGxlZ2Uvc2FsYXJpZXMvbmNhYWYvY29hY2gv')
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # so this is kinda nasty but it works..
        def everything_between(text, begin, end):
            idx1=text.find(begin)
            idx2=text.find(end,idx1)
            return text[idx1+len(begin):idx2].strip()
        # have to scrape out things between because of horrible html.
        rawtable = everything_between(html, '<table class="sort custom-sort ribbonfx" border="0" cellspacing="0" cellpadding="0">', '</table>')
        # now we go back to doing things normally.
        soup = BeautifulSoup(rawtable, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        # container for output.
        salaries = []
        # now process the table.
        rows = soup.findAll('tr')[1:]  # skip header row.
        for ff, row in enumerate(rows):
            tds = [i for i in row.findAll('td')]
            rank = tds[0].getText()
            school = tds[1].getText().replace('&amp;', '&')
            #conf = tds[2].getText()
            coach = tds[3].getText()
            salary = tds[4].getText()
            cs = "{0} - {1} - {2}".format(school, coach, salary)
            # insert.
            salaries.append(cs)
        # now, determine how to output.
        if not optcoach:  # just display the top10.
            o = [v for v in salaries[0:9]]
            irc.reply("{0} :: {1}".format(self._red("Top10 CFB Coach Salaries"), " | ".join(o)))
        else:  # optcoach so lets search.
            output = []
            for v in salaries:
                if optcoach in v.lower():  # matched.
                    output.append(v)
            # now determine if we found any.
            if len(output) == 0:
                irc.reply("ERROR: I could not find any matching coaches/schools for: {0}".format(optcoach))
                return
            else:  # we did match. output.
                irc.reply("{0}".format(" | ".join(output)))

    cfbcoachsalary = wrap(cfbcoachsalary, [optional('text')])

    def cfbheismanvoting(self, irc, msg, args, optyear):
        """<year>

        Display historical voting for the Heisman Trophy.
        Works for <year> 1935 - current season.
        """

        # fetch url and return html.
        url = self._b64decode('aHR0cDovL3d3dy5zcG9ydHMtcmVmZXJlbmNlLmNvbS9jZmIvYXdhcmRzL2hlaXNtYW4t') + str(optyear) + '.html'
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        table = soup.find('table', attrs={'id':'heisman'})
        if not table:
            irc.reply("ERROR: I could not find Heisman voting for year: {0}. Make sure year is between 1935-current year".format(optyear))
            return
        # container for output
        voting = []
        # find all of our rows
        rows = table.findAll('tr')[1:]
        # process each row.
        for row in rows:
            tds = row.findAll('td')
            name = tds[1].getText()
            school = tds[2].getText()
            year = tds[3].getText()
            pos = tds[4].getText()
            tot = tds[8].getText()  # adds to dict below.
            voting.append("{0} Col: {1} Class: {2} POS: {3} Tot: {4}".format(self._ul(name), self._bold(school), self._bold(year), self._bold(pos), self._bold(tot)))
        # now lets prepare to output.
        irc.reply("{0} Heisman Trophy Voting :: {1}".format(self._red(optyear), " | ".join([i for i in voting])))

    cfbheismanvoting = wrap(cfbheismanvoting, [('int')])

    def cfbheisman(self, irc, msg, args):
        """
        Display poll results on Heisman voting.
        """

        # fetch url and return html.
        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvaGVpc21hbi8=')
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        div = soup.findAll('div', attrs={'class':'hw-module'})[1]
        h2 = div.find('h2').getText()
        date = div.find('div', attrs={'class':'hw-module-date'}).getText()
        table = div.find('table', attrs={'class':'tablehead'})
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*?|^evenrow.*?')})
        # container for output.
        append_list = []
        # each row is a player.
        for row in rows:
            tds = row.findAll('td')
            player = tds[0].getText()
            school = tds[2].getText().replace('&amp;', '&')  # aTm fix.
            points = tds[-1].getText()
            append_list.append("{0} - {1} ({2})".format(self._bold(player), school, points))
        # output time.
        output = "{0} on {1} :: {2}".format(self._red(h2), self._bold(date), " | ".join([item for item in append_list]))
        irc.reply(output)

    cfbheisman = wrap(cfbheisman)

    def cfbteamstats(self, irc, msg, args, optstat):
        """<stat>
        Display team leaders for a specific CFB stat.
        Issue with 'help' to display all valid categories.
        Ex: totaloffense
        """

        # validate opstat.
        optstat = optstat.lower()
        validcategories = { 'totaloffense':'total', 'sacks':'defense/sort/sacks', 'fg':'kicking/sort/fieldGoalsMade',
                            'passing':'passing', 'int':'defense/sort/interceptions', 'xp':'kicking/sort/extraPointsMade',
                            'rushing':'rushing', 'punting':'punting', 'receiving':'receiving/sort/totalTouchdowns',
                            'kickoffreturns':'returning/sort/kickReturnYards', 'firstdowns':'downs/sort/firstDowns',
                            'puntreturns':'returning/sort/puntReturnYards', '3rdconv':'downs/sort/thirdDownConvs',
                            '4thconv':'downs/sort/fourthDownConvs' }

        if optstat not in validcategories or optstat == 'help':
            irc.reply("Stat category must be one of: {0}".format(" | ".join(sorted(validcategories.keys()))))
            return
        # build and fetch url.
        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvc3RhdGlzdGljcy90ZWFtL18vc3RhdC8=') + validcategories[optstat]
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        heading = soup.find('div', attrs={'class':'mod-header stathead'}).getText()
        table = soup.find('table', attrs={'class':'tablehead'})
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*?|^evenrow.*?')})[0:10]
        # container list for output.
        append_list = []
        # each row is a stat/player
        for row in rows:
            tds = row.findAll('td')
            team = tds[1].getText().replace('&amp;', '&')  # aTm fix.
            stat = row.find('td', attrs={'class':'sortcell'}).getText()
            append_list.append("{0} {1}".format(self._bold(team), stat))
        # output time.
        output = "{0} :: {1}".format(self._red(heading), " | ".join([item for item in append_list]))
        irc.reply(output)

    cfbteamstats = wrap(cfbteamstats, [('somethingWithoutSpaces')])

    def cfbstats(self, irc, msg, args, optstat):
        """<stat>
        Display individual leaders for a specific CFB stat.
        Issue with 'help' to display all valid categories.
        Ex: rushing
        """

        # validate category.
        optstat = optstat.lower()
        validcategories = { 'rushing':'rushing', 'receving':'receving', 'touchdowns':'scoring/sort/totalTouchdowns',
                            'points':'scoring/sort/totalPoints', 'qbr':'passing/sort/collegeQuarterbackRating',
                            'comppct':'passing/sort/completionPct', 'sacks':'defense/sort/sacks',
                            'int':'defense/sort/interceptions', 'fgs':'kicking/sort/fieldGoalsMade',
                            'punting':'punting', 'kickreturnyds':'returning/sort/kickReturnYards',
                            'puntreturnyards':'returning/sort/puntReturnYards', 'passing':'passing' }

        if optstat not in validcategories or optstat == 'help':
            irc.reply("Stat category must be one of: {0}".format(" | ".join(sorted(validcategories.keys()))))
            return
        # build and fetch url.
        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvc3RhdGlzdGljcy9wbGF5ZXIvXy9zdGF0Lw==') + '%s' % validcategories[optstat]
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        table = soup.find('table', attrs={'class':'tablehead'})
        # header = table.find('tr', attrs={'class':'colhead'})
        h2 = soup.find('h1', attrs={'class':'h2'}).getText()
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*?|^evenrow.*?')})[0:10]
        # container for output.
        append_list = []
        # each row is a stat/player.
        for row in rows:
            tds = row.findAll('td')
            player = tds[1].getText()
            team = tds[2].getText().replace('&amp;', '&')  # aTm fix.
            stat = row.find('td', attrs={'class':'sortcell'}).getText()
            append_list.append("{0} ({1}) {2}".format(self._bold(player), team, stat))
        # output time.
        output = "{0} :: {1}".format(self._red(h2), " | ".join([item for item in append_list]))
        irc.reply(output)

    cfbstats = wrap(cfbstats, [('somethingWithoutSpaces')])

    def cfbschedule(self, irc, msg, args, optteam):
        """<team>
        Display the schedule/results for team.
        Ex: Alabama
        """

        # check the team now.
        lookupteam = self._lookupTeam(optteam, opttable='eid')
        if isinstance(lookupteam, list):  # if match no good, list returned. give simmilar teams.
            irc.reply("ERROR: I could not find team '{0}'. Similar: {1}".format(optteam, " | ".join(sorted([i['team'].title() for i in lookupteam]))))
            return
        # build and fetch url.
        url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvdGVhbS9fL2lk') + '/%s/' % lookupteam
        html = self._httpget(url)
        if not html:
            irc.reply("ERROR: Failed to fetch {0}.".format(url))
            self.log.error("ERROR opening {0}".format(url))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        div = soup.find('div', attrs={'id':'showschedule'})
        table = div.find('table', attrs={'class':'tablehead'})
        team = table.find('tr', attrs={'class':'stathead'}).getText()  # team
        rows = table.findAll('tr', attrs={'class':re.compile('^oddrow.*|^evenrow.*')})
        # container list for output.
        append_list = []
        # each row is a game.
        for row in rows:
            tds = row.findAll('td')
            if len(tds) < 2:  # have to do this for bowls.
                continue
            date = tds[0].getText()
            opp = tds[1].getText().replace('&amp;', '&')  # aTm fix.
            if opp.startswith('vs'):  # replace the vsTeam due to getText()
                opp = opp.replace('vs', '', 1)  # max 1.
            result = tds[2].getText()
            append_list.append("{0} - {1} ({2})".format(date, self._bold(opp), result))
        # output time.
        output = "{0} :: {1}".format(self._red(team), " | ".join([item for item in append_list]))
        irc.reply(output)

    cfbschedule = wrap(cfbschedule, [('text')])

Class = CFB