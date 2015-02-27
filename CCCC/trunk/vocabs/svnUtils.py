


import svn
import svn.remote

r = svn.remote.RemoteClient('http://proj.badc.rl.ac.uk/svn/exarch/CCCC/trunk/ceda_cc/config/cmip5_vocabs' )
i = r.info()
print i.keys()
print i['commit_date'].ctime()
print list( i['commit_date'].timetuple() )
