
import json


class checker(object):
   def __init__(self,parent):
     self.parent = parent

   def run(self):
     print ( 'Hello from plugin', self.parent.fnParts )
     ee = {'filename':self.parent.fnParts, 'time':self.parent.da['time'] }
     ofile = '_'.join( self.parent.fnParts ) + '.txt' 
     json.dump( ee, open( ofile, 'w' ) )
