

class abortChecks(Exception):
  pass
class loggedException(Exception):
  pass
class baseException1(Exception):
  pass

class baseException(Exception):

  def __init__(self,msg):
    self.msg = 'utils_c4:: %s' % msg

  def __str__(self):
        return unicode(self).encode('utf-8')

  def __repr__(self):
    return self.msg

  def __unicode__(self):
        return self.msg % tuple([force_unicode(p, errors='replace')
                                 for p in self.params])
