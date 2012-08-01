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
    
    def _translateTeam(self, db, column, optteam):
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
            
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        query = "select %s from cfb where %s='%s'" % (db, column, optteam)
        cursor.execute(query)
        row = cursor.fetchone()

        cursor.close()            

        return (str(row[0]))
        
    def _validteams(self, conf=None):
        """Returns a list of valid teams for input verification."""
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
            
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("select team from cfb where conf=?", (conf,))        
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
    
    def _translateConf(self, optconf):
        # conf is validated previously, so no error checking.
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
            
    def cfbconferences(self, irc, msg, args):
        """ .  """
        
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
        
        fullconf = self._translateConf(optconf)
        
        teams = self._validteams(conf=fullconf)
                
        irc.reply("Valid teams are: %s" % (string.join([ircutils.bold(item) for item in teams], " | ")))
        
    cfbteams = wrap(cfbteams, [('somethingWithoutSpaces')])

Class = CFB


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
