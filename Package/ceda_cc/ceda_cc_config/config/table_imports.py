import json, re, os, glob

HERE = os.path.dirname(__file__)
CC_CONFIG_DEFAULT_DIR = HERE
CC_CONFIG_DIR = os.environ.get('CC_CONFIG_DIR', CC_CONFIG_DEFAULT_DIR)

class Ingest_cmipplus(object):
    def __init__(self, project, verbose=False, base_dir=None ):
        if base_dir == None:
          idir = '%s/%s/Tables' % (CC_CONFIG_DIR,project)
        else:
          idir = '%s/%s/Tables' % (base_dir,project)
        assert os.path.isdir( idir ), 'Tables not found for project %s, %s' % (project,idir)
        cv_test = glob.glob( '%s/*_CV.json' % idir )
        assert len( cv_test ) == 1, 'There should be a single *_CV.json file in the Tables directory, %s' % cv_test
        cvfile = cv_test[0]
        self.cvs = json.load( open( cvfile ) )['CV']
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
        if 'table_id' in self.acvs and 'frequency' in self.acvs:
            l1 = [x for x in self.acvs['frequency'][1] if x not in self.acvs['table_id'][1] ] 
            l2 = [x for x in self.acvs['table_id'][1] if x not in self.acvs['frequency'][1] ] 
            ##c1 = all( [x in self.acvs['table_id'] for x in self.acvs['frequency'] ] )
            ##c2 = all( [x in self.acvs['frequency'] for x in self.acvs['table_id'] ] )
            if len(l1) != 0:
                print ('CV error: not all frequencies included in table_id list: %s' % l1 )
            if len(l2) != 0:
                print ('CV error: not all table_ids included in frequency list: %s' % l2 )

                
if __name__ == "__main__":
    ic = Ingest_cmipplus('snapsi',base_dir='.')
