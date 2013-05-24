# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2013, spline
# All rights reserved.
###

# my libs
import os
import sqlite3
from BeautifulSoup import BeautifulSoup
import base64
import re
import collections
import datetime
from random import choice
# supybot libs
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

	def __init__(self, irc):
		self.__parent = super(CFB, self)
		self.__parent.__init__(irc)
		self._cfbdb = os.path.abspath(os.path.dirname(__file__)) + '/db/cfb.db'

	##############
	# FORMATTING #
	##############

	def _red(self, string):
		"""Returns a red string."""
		return ircutils.mircColor(string, 'red')

	def _yellow(self, string):
		"""Returns a yellow string."""
		return ircutils.mircColor(string, 'yellow')

	def _green(self, string):
		"""Returns a green string."""
		return ircutils.mircColor(string, 'green')

	def _blue(self, string):
		"""Returns a blue string."""
		return ircutils.mircColor(string, 'blue')

	def _bold(self, string):
		"""Returns a bold string."""
		return ircutils.bold(string)

	def _ul(self, string):
		"""Returns an underline string."""
		return ircutils.underline(string)

	def _bu(self, string):
		"""Returns a bold/underline string."""
		return ircutils.bold(ircutils.underline(string))

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
				page = utils.web.getUrl(url)
			return page
		except utils.web.Error as e:
			self.log.error("ERROR opening {0} message: {1}".format(url, e))
			return None

	def _b64decode(self, string):
		"""Returns base64 encoded string."""

		return base64.b64decode(string)

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

	def _lookupTeam(self, optteam, opttable=None):
		"Lookup various strings/variables depending on team."

		if not opttable: # if we have no opttable.
			opttable = 'tid'  # default to opttable.

		optteam = optteam.lower()  # need to lower since fields are lowercase.

		with sqlite3.connect(self._cfbdb) as conn:
			cursor = conn.cursor()  # first check nicenames.
			query = "SELECT %s FROM cfb WHERE nn LIKE ?" % opttable
			cursor.execute(query, ('%'+optteam+'%',)) # can't parimeter sub tablenames.
			row = cursor.fetchone()
			if not row:  # no nickname. check teamname.
				query = "SELECT %s FROM cfb WHERE team LIKE ?" % opttable
				cursor.execute(query, ('%'+optteam+'%',))
				row = cursor.fetchone()
				if not row:  # we found nothing under either.
					retrval = None  # bailout.
				else:  # return teamname.
					retrval = row[0]
			else:  # return nickname.
				retrval = row[0]
		# return.
		return retrval

	####################
	# PUBLIC FUNCTIONS #
	####################

	def cfbplayoffcountdown(self, irc, msg, args):
		"""
		Display the time until the next NFL season starts.
		"""

		dDelta = datetime.datetime(2015, 1, 1, 1, 0) - datetime.datetime.now()
		irc.reply("There are {0} days {1} hours {2} minutes {3} seconds until the 2015 College Football Playoff.".format(\
											dDelta.days, dDelta.seconds/60/60, dDelta.seconds/60%60, dDelta.seconds%60))

	cfbplayoffcountdown = wrap(cfbplayoffcountdown)

	def cfbcountdown(self, irc, msg, args):
		"""
		Display the time until the next NFL season starts.
		"""

		dDelta = datetime.datetime(2013, 8, 29, 19, 0) - datetime.datetime.now()
		irc.reply("There are {0} days {1} hours {2} minutes {3} seconds until the start of the 2013 College Football Season.".format(\
											dDelta.days, dDelta.seconds/60/60, dDelta.seconds/60%60, dDelta.seconds%60))

	cfbcountdown = wrap(cfbcountdown)

	def cfbconferences(self, irc, msg, args):
		"""
		Show valid CFB conferences.
		"""

		conferences = self._validconfs()
		irc.reply("Valid CFB Conferences: {0}".format(" | ".join(sorted([item for item in conferences]))))

	cfbconferences = wrap(cfbconferences)

	def cfbteams(self, irc, msg, args, optconf):
		"""<conference>
		Display valid teams in a specific conference.
		Ex: SEC.
		"""

		optconf = optconf.upper()
		if optconf not in self._validconfs():
			irc.reply("ERROR: Invalid conference. Must be one of: {0}".format(self._validconfs()))
			return

		fullconf = self._translateConf(optconf) # needs to be lowercase, which this will return
		teams = self._validteams(fullconf)

		irc.reply("Valid teams are: %s" % (string.join([ircutils.bold(item.title()) for item in teams], " | "))) # title because all entries are lc.

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
		lastDate = soup.findAll('span', attrs={'class': 'time'})[0]
		divs = soup.findAll('div', attrs={'class': 'entry'})
		# container for output.
		arrestlist = []
		# each div is one arrest.
		for div in divs:
			title = div.find('h2').getText().encode('utf-8')
			datet = div.find('span', attrs={'class': 'time'}).getText().encode('utf-8')
			datet = self._dtFormat("%m/%d", datet, "%B %d, %Y") # translate date.
			arrestedfor = div.find('strong', text=re.compile('Team:'))
			if arrestedfor:
				matches = re.search(r'<strong>Team:.*?</strong>(.*?)<br />', arrestedfor.findParent('p').renderContents(), re.I| re.S| re.M)
				if matches:
					college = matches.group(1).replace('(College Football)', '').encode('utf-8').strip()
				else:
					college = "None"
			else:
				college = "None"
			arrestlist.append("{0} :: {1} - {2}".format(datet, title, college))
		# date math.
		a = datetime.date.today()
		b = datetime.datetime.strptime(str(lastDate.getText()), "%B %d, %Y")
		b = b.date()
		delta = b - a
		daysSince = abs(delta.days)
		# output
		irc.reply("{0} days since last College Football arrest".format(self._red(daysSince)))
		for each in arrestlist[0:6]:
			irc.reply(each)

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

	def cfbinjury(self, irc, msg, args, optteam):
		"""<team>
		Display injury information for team.
		Ex: Alabama
		"""

		## CURRENTLY THIS COMMAND IS BROKEN.
		irc.reply("Sorry, command is currently broken!")
		return

		# first, lookup and make sure we have a valid team.
		lookupteam = self._lookupTeam(optteam, opttable='usat')
		if not lookupteam:  # no valid team found.
			irc.reply("ERROR: I could not find {0} in my database of teams.".format(optteam))
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

	def cfbteaminfo(self, irc, msg, args, optteam):
		"""<team>
		Display basic info/stats on a team.
		Ex: Alabama
		"""

		# lookup team.
		lookupteam = self._lookupTeam(optteam)
		if not lookupteam:
			irc.reply("ERROR: I could not find {0} in my database of teams.".format(optteam))
			return
		# build and fetch url.
		url = self._b64decode('aHR0cDovL3d3dy5jYnNzcG9ydHMuY29tL2NvbGxlZ2Vmb290YmFsbC90ZWFtcy9wYWdl') + '/%s/' % lookupteam
		html = self._httpget(url)
		if not html:
			irc.reply("ERROR: Failed to fetch {0}.".format(url))
			self.log.error("ERROR opening {0}".format(url))
			return
		# process html.
		soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
		div = soup.find('div', attrs={'class':'pageTitle team'})
		name = div.find('div', attrs={'class':'info'}).find('h1').getText(separator=' ')
		record = div.find('div', attrs={'class':re.compile('^record')}).getText(separator=u' ')
		table = div.find('div', attrs={'class':'stats'}).find('table', attrs={'class':'data'})
		rows = table.findAll('tr')
		# put each stat into a string.
		rushingOff = rows[1].findAll('td')[1].getText()
		rushingDef = rows[1].findAll('td')[2].getText()
		passingOff = rows[2].findAll('td')[1].getText()
		passingDef = rows[2].findAll('td')[2].getText()
		overallOff = rows[3].findAll('td')[1].getText()
		overallDef = rows[3].findAll('td')[2].getText()
		# build output.
		output = "{0} :: {1} - {2} o: {3} d: {4} | {5} o: {6} d: {7} | {8} o: {9} d: {10}".format(\
			self._red(utils.str.normalizeWhitespace(name)), record, self._bold('Rushing:'), rushingOff,\
			rushingDef, self._bold('Passing:'), passingOff, passingDef, self._bold('Overall:'), overallOff,\
			overallDef)
		# output.
		irc.reply(output)

	cfbteaminfo = wrap(cfbteaminfo, [('text')])

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

	def cfbpowerrankings(self, irc, msg, args):
		"""
		Display this week's CFB Power Rankings.
		"""

		# build and fetch url.
		url = self._b64decode('aHR0cDovL2VzcG4uZ28uY29tL2NvbGxlZ2UtZm9vdGJhbGwvcG93ZXJyYW5raW5ncw==')
		html = self._httpget(url)
		if not html:
			irc.reply("ERROR: Failed to fetch {0}.".format(url))
			self.log.error("ERROR opening {0}".format(url))
			return
		# process html.
		soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
		if not soup.find('table', attrs={'class':'tablehead'}):
			irc.reply("Something broke heavily formatting on powerrankings page.")
			return
		# go about regular html business.
		datehead = soup.find('div', attrs={'class':'date floatleft'}).getText(separator=' ')
		table = soup.find('table', attrs={'class':'tablehead'})
		headline = table.find('tr', attrs={'class':'stathead'}).getText()
		rows = table.findAll('tr', attrs={'class':re.compile('^oddrow|^evenrow')})
		# list for each team.
		powerrankings = []
		# each row is a team.
		for row in rows: # one row per team.
			tds = row.findAll('td') # findall tds.
			if len(tds) == 5:  # bad row like "Others getting votes.". ugly but works.
				rank = tds[0].getText() # rank number.
				team = tds[1].find('div', attrs={'style':'padding: 10px;'}).findAll('a')[1].getText() # 2nd link text.
				team = team.replace('&amp;', '&')  # for aTm.
				lastweek = tds[2].find('span', attrs={'class':'pr-last'}).getText()
				lastweek = lastweek.replace('Last Week:', '').strip() # rank #
				# check if we're up or down and insert a symbol.
				if lastweek == "NR":
					symbol = self._green('▲')
				elif int(rank) < int(lastweek):  # specific to CFB.
					symbol = self._green('▲')
				elif int(rank) > int(lastweek):
					symbol = self._red('▼')
				else: # - if the same.
					symbol = "-"
				# now add the rows to our data structures.
				powerrankings.append("{0}. {1} (prev: {2} {3})".format(rank, team, symbol, lastweek))

		# now output. conditional if we have the team or not.
		irc.reply("{0} :: {1}".format(self._blue(headline), datehead))
		for splice in self._splicegen('380', powerrankings):
			irc.reply(" | ".join([powerrankings[item] for item in splice]))

	cfbpowerrankings = wrap(cfbpowerrankings)

	def cfbrankings(self, irc, msg, args, optpoll):
		"""<ap|usatoday|bcs|<team>
		If ap, usatoday or bcs are given, it will display this week's poll.
		If <team> is given, it will search each poll for that team and display.
		Ex: bcs OR Alabama
		"""

		# handle input.
		optpoll, optinput = optpoll.lower(), False
		# check poll. url conditional on the string.
		if optpoll not in ['bcs', 'ap', 'usatoday']:  # check for ap|bcs|usatoday.
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
			poll = table.find('div', attrs={'class':'hd'})  # poll's name hidden in here. replace text below.
			poll = poll.getText()  # replace text below to mate up keys.
			poll = poll.replace('AP Top 25', 'ap').replace('USA Today', 'usatoday').replace('Bowl Champ. Series', 'bcs')
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
		if not lookupteam:
			irc.reply("ERROR: I could not find {0} in my database of teams.".format(optteam))
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
		if not lookupteam:
			irc.reply("ERROR: I could not find {0} in my database of teams.".format(optteam))
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
		soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
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
			irc.reply("{0} Roster :: {1}".format(self._red(optteam.title()), " | ".join(output)))

	cfbroster = wrap(cfbroster, [(getopts({'position':('somethingWithoutSpaces'), 'number':('somethingWithoutSpaces')})), ('text')])

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
		div = soup.find('div', attrs={'class':'hw-module'})
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

		# lookup team in eid table.
		lookupteam = self._lookupTeam(optteam, opttable='eid')
		if not lookupteam:
			irc.reply("ERROR: I could not find {0} in my database of teams.".format(optteam))
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
			date = tds[0].getText()
			opp = tds[1].getText().replace('&amp;', '&')  # aTm fix.
			if opp.startswith('vs'):  # replace the vsTeam due to getText()
				opp = opp.replace('vs', 'v ', 1)  # max 1.
			result = tds[2].getText()
			append_list.append("{0} - {1} ({2})".format(date, opp, result))
		# output time.
		output = "{0} :: {1}".format(self._red(team), " | ".join([item for item in append_list]))
		irc.reply(output)

	cfbschedule = wrap(cfbschedule, [('text')])

Class = CFB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
