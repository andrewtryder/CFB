/* CFB TEAMS */
CREATE TABLE cfb (
    team TEXT, -- college or teamname.
    tid TEXT PRIMARY KEY, -- http://cbsprt.co/16W3DNl
    conf TEXT, -- confname.
    nn TEXT, -- alias name (usually team name)
    eid INTEGER, -- http://es.pn/130eoIA
    usat INTEGER, -- http://usat.ly/130ernG
    cfbstats INTEGER, -- http://bit.ly/130eFLr
    yahoo TEXT); -- http://bit.ly/130eLmk

/* AAC */
INSERT INTO cfb VALUES ('cincinnati','CINCY','american athletic','bearcats','2132','46','140','ccj');
INSERT INTO cfb VALUES ('connecticut','UCONN','american athletic','huskies','41','144','164','ccq');
INSERT INTO cfb VALUES ('east carolina','ECU','american athletic','pirates','151','78','196','eea');
INSERT INTO cfb VALUES ('houston','HOU','american athletic','cougars','248','96','288','hhe');
INSERT INTO cfb VALUES ('memphis','MEMP','american athletic','tigers','235','37','404','mmg');
INSERT INTO cfb VALUES ('southern methodist','SMU','american athletic','mustangs','2567','73','663','ssh');
INSERT INTO cfb VALUES ('south florida','SFLA','american athletic','bulls','58','204','651','sbn');
INSERT INTO cfb VALUES ('temple','TEMPLE','american athletic','owls','218','56','690','ttb');
INSERT INTO cfb VALUES ('tulane','TULANE','american athletic','green wave','2655','48','718','tts');
INSERT INTO cfb VALUES ('tulsa','TULSA','american athletic','golden hurricane','202','97','719','ttt');
INSERT INTO cfb VALUES ('ucf','UCF','american athletic','knights','2116','142','128','ccf');
/* ACC - ATLANTIC */
INSERT INTO cfb VALUES ('boston college','BC','atlantic coast','eagles','103','34','67','bbf');
INSERT INTO cfb VALUES ('clemson','CLEM','atlantic coast','tigers','228','128','147','ccl');
INSERT INTO cfb VALUES ('florida state','FSU','atlantic coast','seminoles','52','47','234','ffc');
INSERT INTO cfb VALUES ('louisville','LVILLE','atlantic coast','cardinals','97','61','367','llh');
INSERT INTO cfb VALUES ('north carolina state','NCST','atlantic coast','wolfpack','152','79','490','nnn');
INSERT INTO cfb VALUES ('syracuse','CUSE','atlantic coast','orange','183','104','688','ssw');
INSERT INTO cfb VALUES ('wake forest','WAKE','atlantic coast','demon deacons','154','138','749','wwa');
/* ACC - COASTAL */
INSERT INTO cfb VALUES ('duke','DUKE','atlantic coast','blue devils','150','95','193','ddf');
INSERT INTO cfb VALUES ('georgia tech','GATECH','atlantic coast','yellow jackets','59','125','255','ggc');
INSERT INTO cfb VALUES ('miami','MIAMI','atlantic coast','hurricanes','2390','70','415','mmi');
INSERT INTO cfb VALUES ('north carolina','UNC','atlantic coast','tar heels','153','65','457','nnl');
INSERT INTO cfb VALUES ('pittsburgh','PITT','atlantic coast','panthers','221','36','545','ppd');
INSERT INTO cfb VALUES ('virginia','UVA','atlantic coast','cavaliers','258','134','746','vvb');
INSERT INTO cfb VALUES ('virginia tech','VATECH','atlantic coast','hokies','259','45','742','vvd');
/* B1G10 - WEST */
INSERT INTO cfb VALUES ('illinois','ILL','big ten','fighting illini','356','72','301','iic');
INSERT INTO cfb VALUES ('iowa','IOWA','big ten','hawkeyes','2294','133','312','iig');
INSERT INTO cfb VALUES ('minnesota','MINN','big ten','golden gophers','135','140','428','mmn');
INSERT INTO cfb VALUES ('nebraska','NEB','big ten','cornhuskers','158','55','463','nnd');
INSERT INTO cfb VALUES ('northwestern','NWEST','big ten','wildcats','77','94','509','nnv');
INSERT INTO cfb VALUES ('purdue','PURDUE','big ten','boilermakers','2509','35','559','ppj');
INSERT INTO cfb VALUES ('wisconsin','WISC','big ten','badgers','275','111','796','wwo');
/* B1G10 - EAST */
INSERT INTO cfb VALUES ('indiana','IND','big ten','hoosiers','84','107','306','iie');
INSERT INTO cfb VALUES ('maryland','MD','big ten','terrapins','120','60','392','mmd');
INSERT INTO cfb VALUES ('michigan','MICH','big ten','wolverines','130','103','418','mmk');
INSERT INTO cfb VALUES ('michigan state','MICHST','big ten','spartans','127','113','416','mml');
INSERT INTO cfb VALUES ('ohio state','OHIOST','big ten','buckeyes','194','105','518','oob');
INSERT INTO cfb VALUES ('penn state','PSU','big ten','nittany lions','213','59','539','ppb');
INSERT INTO cfb VALUES ('rutgers','RUT','big ten','scarlet knights','164','129','587','rrd');
/* BIG12 */
INSERT INTO cfb VALUES ('baylor','BAYLOR','big 12','bears','239','88','51','bbb');
INSERT INTO cfb VALUES ('iowa state','IOWAST','big 12','cyclones','66','101','311','iih');
INSERT INTO cfb VALUES ('kansas','KANSAS','big 12','jayhawks','2305','49','328','kka');
INSERT INTO cfb VALUES ('kansas state','KSTATE','big 12','wildcats','2306','130','327','kkb');
INSERT INTO cfb VALUES ('oklahoma','OKLA','big 12','sooners','201','139','522','ooc');
INSERT INTO cfb VALUES ('oklahoma state','OKLAST','big 12','cowboys','197','53','521','ood');
INSERT INTO cfb VALUES ('tcu','TCU','big 12','horned frogs','2628','110','698','tta');
INSERT INTO cfb VALUES ('texas','TEXAS','big 12','longhorns','251','131','703','tth');
INSERT INTO cfb VALUES ('texas tech','TXTECH','big 12','red raiders','2641','64','700','tto');
INSERT INTO cfb VALUES ('west virginia','WVU','big 12','mountaineers','277','62','768','wwh');
/* CONFUSA - EAST */
INSERT INTO cfb VALUES ('florida atlantic','FAU','conference usa','owls','2226','221','229','ffr');
INSERT INTO cfb VALUES ('florida international','FIU','conference usa','golden panthers','2229','230','231','fli');
INSERT INTO cfb VALUES ('marshall','MRSHL','conference usa','thundering herd','276','118','388','mmc');
INSERT INTO cfb VALUES ('middle tennessee','MTSU','conference usa','blue raiders','2393','143','419','mmm');
INSERT INTO cfb VALUES ('old dominion','','conference usa','monarchs','295','','','oah');
INSERT INTO cfb VALUES ('uab','UAB','conference usa','blazers','5','146','9','aaz');
INSERT INTO cfb VALUES ('western kentucky','WKY','conference usa','hilltoppers','98','189','772','wwk');
/* CONFUSA - WEST */
INSERT INTO cfb VALUES ('louisiana tech','LATECH','conference usa','bulldogs','2348','57','366','llg');
INSERT INTO cfb VALUES ('north texas','NTEXAS','conference usa','mean green','249','99','497','nnp');
INSERT INTO cfb VALUES ('rice','RICE','conference usa','owls','242','98','574','rrb');
INSERT INTO cfb VALUES ('southern mississippi','USM','conference usa','golden eagles','2572','58','664','sso');
INSERT INTO cfb VALUES ('texas-san antonio','TXSA','conference usa','roadrunners','2636','461','706','tsa');
INSERT INTO cfb VALUES ('texas-el paso','UTEP','conference usa','miners','2638','41','704','ttl');
/* INDEPENDENTS */
INSERT INTO cfb VALUES ('army','ARMY','fbs independents','black knights','349','127','725','aaq');
INSERT INTO cfb VALUES ('brigham young','BYU','fbs independents','cougars','252','33','77','bbi');
INSERT INTO cfb VALUES ('navy','NAVY','fbs independents','midshipmen','2426','66','726','nna');
INSERT INTO cfb VALUES ('notre dame','ND','fbs independents','irish','87','102','513','nnx');
/* MID-AMERICAN - EAST */
INSERT INTO cfb VALUES ('akron','AKRON','mid american','zips','2006','124','5','aac');
INSERT INTO cfb VALUES ('bowling green','BGREEN','mid american','green falcons','189','85','71','bbh');
INSERT INTO cfb VALUES ('buffalo','BUFF','mid american','bulls','2084','145','86','bbp');
INSERT INTO cfb VALUES ('kent state','KENTST','mid american','golden flashes','2309','123','331','kkc');
INSERT INTO cfb VALUES ('massachusetts','MA','mid american','minutemen','113','207','400','mme');
INSERT INTO cfb VALUES ('miami (ohio)','MIAOH','mid american','redhawks','193','121','414','mmj');
INSERT INTO cfb VALUES ('ohio','OHIO','mid american','bobcats','195','117','519','ooa');
/* MID-AMERICAN - WEST */
INSERT INTO cfb VALUES ('ball state','BALLST','mid american','cardinals','2050','86','47','bba');
INSERT INTO cfb VALUES ('central michigan','CMICH','mid american','chippewas','2117','141','129','ccg');
INSERT INTO cfb VALUES ('eastern michigan','EMICH','mid american','eagles','2199','136','204','eef');
INSERT INTO cfb VALUES ('northern illinois','NILL','mid american','huskies','2459','68','503','nns');
INSERT INTO cfb VALUES ('toledo','TOLEDO','mid american','rockets','2649','82','709','ttp');
INSERT INTO cfb VALUES ('western michigan','WMICH','mid american','broncos','2711','67','774','wwl');
/* MOUNTAIN WEST - MOUNTAIN */
INSERT INTO cfb VALUES ('air force','AF','mountain west','falcons','2005','42','721','aab');
INSERT INTO cfb VALUES ('boise state','BOISE','mountain west','broncos','68','92','66','bbe');
INSERT INTO cfb VALUES ('colorado state','COLOST','mountain west','rams','36','89','156','cco');
INSERT INTO cfb VALUES ('new mexico','NMEX','mountain west','lobos','167','63','473','nnh');
INSERT INTO cfb VALUES ('utah state','UTAHST','mountain west','aggies','328','100','731','uud');
INSERT INTO cfb VALUES ('wyoming','WYO','mountain west','cowboys','2751','87','811','wwq');
/* MOUNTAIN WEST - WEST */
INSERT INTO cfb VALUES ('fresno state','FRESNO','mountain west','bulldogs','278','109','96','ffe');
INSERT INTO cfb VALUES ('hawaii','HAWAII','mountain west','warriors','62','50','277','hhc');
INSERT INTO cfb VALUES ('nevada','NEVADA','mountain west','wolf pack','2440','135','466','nnf');
INSERT INTO cfb VALUES ('san diego state','SDGST','mountain west','aztecs','21','132','626','ssb');
INSERT INTO cfb VALUES ('san jose state','SJST','mountain west','spartans','23','43','630','ssc');
INSERT INTO cfb VALUES ('unlv','UNLV','mountain west','rebels','2439','108','465','nne');
/* PAC-12 - NORTH */
INSERT INTO cfb VALUES ('california','CAL','pacific 12','golden bears','25','44','107','ccd');
INSERT INTO cfb VALUES ('oregon','OREG','pacific 12','ducks','2483','39','529','ooe');
INSERT INTO cfb VALUES ('oregon state','OREGST','pacific 12','beavers','204','81','528','oof');
INSERT INTO cfb VALUES ('stanford','STNFRD','pacific 12','cardinal','24','106','674','sss');
INSERT INTO cfb VALUES ('washington','WASH','pacific 12','huskies','264','54','756','wwb');
INSERT INTO cfb VALUES ('washington state','WASHST','pacific 12','cougars','265','40','754','wwc');
/* PAC-12 - SOUTH */
INSERT INTO cfb VALUES ('arizona','ARIZ','pacific 12','wildcats','12','83','29','aal');
INSERT INTO cfb VALUES ('arizona state','ARIZST','pacific 12','sun devils','9','112','28','aam');
INSERT INTO cfb VALUES ('colorado','COLO','pacific 12','buffalos','38','90','157','ccn');
INSERT INTO cfb VALUES ('ucla','UCLA','pacific 12','bruins','26','91','110','uua');
INSERT INTO cfb VALUES ('southern california','USC','pacific 12','trojans','30','71','657','uub');
INSERT INTO cfb VALUES ('utah','UTAH','pacific 12','utes','254','93','732','uuc');
/* SUNBELT - NEED THE LAST 2 NUMBERS FOR APP/GS */
INSERT INTO cfb VALUES ('appalacian state','APLST','sun belt','mountaineers','2026','75','27','aak'); 
INSERT INTO cfb VALUES ('arkansas state','ARKST','sun belt','red wolves','2032','75','30','aap');
INSERT INTO cfb VALUES ('georgia state','GAST','sun belt','panthers','2247','','254','gag');
INSERT INTO cfb VALUES ('georgia southern','GAS','sun belt','eagles','290','75','253','ggh'); 
INSERT INTO cfb VALUES ('idaho','IDAHO','sun belt','vandals','70','80','295','iia');
INSERT INTO cfb VALUES ('la.-lafayette','LALAF','sun belt','ragin cajuns','309','38','671','ssq');
INSERT INTO cfb VALUES ('louisiana-monroe','LAMON','sun belt','warhawks','2433','137','498','nnb');
INSERT INTO cfb VALUES ('new mexico state','NMEXST','sun belt','aggies','166','74','472','nni');
INSERT INTO cfb VALUES ('south alabama','SALA','sun belt','jaguars','6','459','646','sal');
INSERT INTO cfb VALUES ('texas state','TXSTSM','sun belt','bobcats','326','233','670','ssv');
INSERT INTO cfb VALUES ('troy','TROY','sun belt','trojans','2653','196','716','ttv');
/* SEC - EAST */
INSERT INTO cfb VALUES ('florida','FLA','southeastern','gators','57','69','235','ffa');
INSERT INTO cfb VALUES ('georgia','UGA','southeastern','bulldogs','61','52','257','ggb');
INSERT INTO cfb VALUES ('kentucky','UK','southeastern','wildcats','96','122','334','kkd');
INSERT INTO cfb VALUES ('missouri','MIZZOU','southeastern','tigers','142','119','434','mms');
INSERT INTO cfb VALUES ('south carolina','SC','southeastern','gamecocks','2579','161','648','ssi');
INSERT INTO cfb VALUES ('tennessee','TENN','southeastern','volunteers','2633','114','694','ttd');
INSERT INTO cfb VALUES ('vanderbilt','VANDY','southeastern','commodores','238','115','736','vva');
/* SEC - WEST */
INSERT INTO cfb VALUES ('alabama','BAMA','southeastern','crimson tide','333','51','8','aad');
INSERT INTO cfb VALUES ('arkansas','ARK','southeastern','razorbacks','8','126','31','aan');
INSERT INTO cfb VALUES ('auburn','AUBURN','southeastern','tigers','2','84','37','aar');
INSERT INTO cfb VALUES ('lsu','LSU','southeastern','tigers','99','116','365','lli');
INSERT INTO cfb VALUES ('mississippi','MISS','southeastern','rebels','145','77','433','mmo');
INSERT INTO cfb VALUES ('mississippi state','MISSST','southeastern','bulldogs','344','76','430','mmq');
INSERT INTO cfb VALUES ('texas a&m','TXAM','southeastern','aggies','245','120','697','ttj');

/* http://www.fbschedules.com/ncaa/2013-college-football-schedules.php */

/* CONFERENCES TABLE */
CREATE TABLE confs (
    full TEXT,  -- full name.
    short TEXT,  -- abbr.
    eid INTEGER PRIMARY KEY -- unique EID.
    );
/* ONE PER CONFERENCE */
INSERT INTO confs VALUES ('american athletic', 'AAC', '10');
INSERT INTO confs VALUES ('atlantic coast','ACC','1');
INSERT INTO confs VALUES ('big ten','BIG10','5');
INSERT INTO confs VALUES ('big 12','BIG12','4');
INSERT INTO confs VALUES ('pacific 12','PAC12','9');
INSERT INTO confs VALUES ('conference usa','USA','12');
INSERT INTO confs VALUES ('mid american','MAC','15');
INSERT INTO confs VALUES ('fbs independents','IA','18');
INSERT INTO confs VALUES ('mountain west','MWC','17');
INSERT INTO confs VALUES ('southeastern','SEC','8');
INSERT INTO confs VALUES ('sun belt','SUN','37');
