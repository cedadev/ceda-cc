"""Some exceptions used in the code"""

class abortChecks(Exception):
  """Raised when checks are aborted following failure of a critical test (e.g. file name cannot be parsed)."""
  pass
class loggedException(Exception):
  """Raised after an exception has been caught and logged in a checking class, allowing execution to fall back to the loop over files."""
  pass

class baseException(Exception):
  """Basic exception for general use in code."""

  def __init__(self,msg):
    self.msg = 'utils_c4:: %s' % msg

  def __str__(self):
        return unicode(self).encode('utf-8')

  def __repr__(self):
    return self.msg

  def __unicode__(self):
        return self.msg % tuple([force_unicode(p, errors='replace')
                                 for p in self.params])
