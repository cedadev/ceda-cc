import json, re, os

HERE = os.path.dirname(__file__)
CC_CONFIG_DEFAULT_DIR = HERE
CC_CONFIG_DIR = os.environ.get('CC_CONFIG_DIR', CC_CONFIG_DEFAULT_DIR)

class Ingest_ccmi2022(object):
    def __init__(self,idir='ccmi2022/Tables', verbose=False ):
        self.cvs = json.load( open( '%s/%s/CCMI2022_CV.json' % (CC_CONFIG_DIR,idir) ) )['CV']
        self.required = self.cvs["required_global_attributes"]
        self.acvs = {x:'unknown' for x in self.required if x in self.cvs}
        if verbose:
          print (self.required)
          print (self.acvs.keys())
        for k in self.acvs:
            done = False
            item = self.cvs[k]
            if type(item) == type([]) and len( item ) == 1:
                this = item[0]
                if this[0] == '^' and this[-1] == '$':
                    self.acvs[k] = ('regex', this.replace( '\\', '').replace('[[:digit:]]','[0-9]' ) )
                    done = True
            if not done:
                if k in ['tracking_id','variant_label']:
                   pass
                elif type(item) == type([]) and all( [type(x) == type('') for x in item] ):
                    self.acvs[k] = ('list', item )
                elif type(item) == type({}):
                    self.acvs[k] = ('list', sorted( list( item.keys() ) ) )

        y = re.compile( self.acvs["data_specs_version"][1] )
        if verbose:
          print( self.acvs["data_specs_version"][1]  )
          print( y.match( '01.00.32' ) )
          print( [k for k,item in self.acvs.items() if item == 'unknown'] )


if __name__ == "__main__":
  ic = Ingest_ccmi2022()
