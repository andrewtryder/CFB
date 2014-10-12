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
        # cfbheismanvoting, cfbinjury, cfbplayerinfo, cfbpolls,
        # cfbrankings, cfbroster, cfbschedule, cfbstandings, cfbstats,
        # cfbteaminfo, cfbteamleaders, cfbteams, cfbteamstats, cfbtv, cfbweeklyleaders,
        # spurrier
        self.assertNotError('cfbarrests')
        self.assertRegexp('cfbbowls 2011 orange', 'West Virginia 70 \- Clemson 33')
        self.assertNotError('cfbcoachsalary')
        self.assertResponse('cfbconferences', 'Valid CFB Conferences: AAC | ACC | BIG10 | BIG12 | IA | MAC | MWC | PAC12 | SEC | SUN | USA')
        self.assertNotError('cfbcountdown')
        self.assertNotError('cfbgamestats Oregon State')
        self.assertNotError('cfbpolls ap 2007 2')
        self.assertNotError('cfbpolls bcs 2007 2')
        self.assertNotError('cfbpolls ap')
        self.assertNotError('cfbpolls usatoday')
        # self.assertNotError('cfbroster Alabama')  # broken.
        # self.assertNotError('cfbschedule LSU') # broken test.
        self.assertNotError('cfbstandings sec')
        self.assertNotError('cfbstats rushing')
        self.assertNotError('cfbstats points')
        self.assertNotError('cfbteamleaders passing Alabama')
        self.assertNotError('cfbteams SEC')
        self.assertNotError('cfbteamstats int')
        self.assertNotError('cfbteamstats sacks')
        self.assertNotError('cfbweeklyleaders')
        self.assertNotError('spurrier')
                            
        
        
        

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
