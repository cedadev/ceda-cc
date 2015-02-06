
import sys, os, glob, string
if os.path.isfile( 'step2.sh' ):
  os.unlink( 'step2.sh' )

ii = string.join( open( 'versionConfig.tmpl' ).readlines() )
tags = glob.glob( '../tags/*' )
f1 = lambda x: map( int, string.split(x, '.' ) )
tn = map( lambda x: tuple( f1(string.split(x,'/')[-1]) ),  tags )
tn.sort()
thistag, thiscomment = sys.argv[1:]
thistn = tuple( f1( thistag ) )
assert thistn > tn[-1], 'Requested tag not greater than last tag: %s' % str(tn[-1])

oo = open( '../trunk/ceda_cc/versionConfig.py', 'w' )
for l in string.split( ii % (thistag, thiscomment), '\n' ):
  oo.write( '%s\n' % string.strip(l) )
oo.close()

bashtmpl = """
tag=%(thistag)s
comment='"%(thiscomment)s"'

echo $tag, $comment
cd ../trunk
svn ci -m "Updated setup for tag %(thistag)s"
svn copy http://proj.badc.rl.ac.uk/svn/exarch/CCCC/trunk http://proj.badc.rl.ac.uk/svn/exarch/CCCC/tags/%(thistag)s -m "%(thiscomment)s"
"""

oo = open( 'step2.sh', 'w' )
oo.write( bashtmpl % locals() )
oo.close()
