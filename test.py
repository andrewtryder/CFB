###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class CFBTestCase(PluginTestCase):
    plugins = ('CFB',)
    
    def testCFB(self):
        # cfbarrests, cfbbowls, cfbcoachsalary, cfbconferences, cfbcountdown, cfbgamestats, cfbheisman,
        # cfbheismanvoting, cfbinjury, cfbplayerinfo, cfbplayoffcountdown, cfbpolls,
        # cfbpowerrankings, cfbrankings, cfbroster, cfbschedule, cfbstandings, cfbstats,
        # cfbteaminfo, cfbteamleaders, cfbteams, cfbteamstats, cfbtv, cfbweeklyleaders,
        # spurrier
        self.assertNotError('cfbarrests')
        self.assertRegexp('cfbbowls 2011 orange', 'West Virginia 70 \- Clemson 33')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
