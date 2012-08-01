#!/usr/bin/env python
from BeautifulSoup import BeautifulSoup
import urllib2
import re
import string
import sys

url = 'http://www.cbssports.com/collegefootball/teams'

req = urllib2.Request(url)
html = (urllib2.urlopen(req)).read()
    
soup = BeautifulSoup(html)

html = html.replace('&amp;','&')
table = soup.find('table', attrs={'width':'100%'})

teams = table.findAll('tr', attrs={'class':re.compile('row[1|2]')})

def stripTeam(string):
    string = re.sub(r'/collegefootball/teams/page/(.*?)/.*','\g<1>', string)
    return string

for team in teams:
    if team.find('a'):
        teamname = team.find('a').string
        teamlink = stripTeam(team.find('a')['href'])
        conf = teamname.findPrevious('tr', attrs={'class':'title'}).find('td', attrs={'colspan':'1'})
        if teamname.findPrevious('tr', attrs={'class':'label'}).find('td'):
            division = teamname.findPrevious('tr', attrs={'class':'label'}).find('td').string
        else:
            division = None
        print "insert into cfb (team, tid, conf) VALUES ('%s','%s','%s');" % (teamname, teamlink, conf.string)

# CREATE TABLE cfb (team TEXT, tid TEXT PRIMARY KEY, conf TEXT);
# CREATE TABLE confs (full TEXT, short TEXT);
#insert into confs (full, short) VALUES ('Big Ten','BIG10');
#insert into confs (full, short) VALUES ('Atlantic Coast','ACC');
#insert into confs (full, short) VALUES ('Big East','BIGE');
#insert into confs (full, short) VALUES ('Pacific 12','PAC12'); # Pacific 12
#insert into confs (full, short) VALUES ('Big 12','BIG12');
#insert into confs (full, short) VALUES ('Conference USA','USA');
#insert into confs (full, short) VALUES ('Mid American','MAC');
#insert into confs (full, short) VALUES ('FBS Independents','IA');
#insert into confs (full, short) VALUES ('Mountain West','MWC');
#insert into confs (full, short) VALUES ('Southeastern','SEC');
#insert into confs (full, short) VALUES ('Sun Belt','SUN');
#insert into confs (full, short) VALUES ('Western Athletic','WAC');


