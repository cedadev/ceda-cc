"""c4.py
##########
Entry point for command line usage -- see ccinit for usage information.
"""
import sys, string

def main_entry():
  """
   Wrapper around main() for use with setuptools.
  """
  if len(sys.argv) == 1:
      # Show command-line info and report that you must provide arguments
      import ccinit
      print ccinit.__doc__
      print "\nERROR: Please provide command-line arguments."
      return

  if sys.argv[1] == '--sum':
      import summary
      summary.summariseLogs()
  elif sys.argv[1] == '-v':
      from versionConfig import version, versionComment
      print 'ceda-cc version %s [%s]' % (version,versionComment)
  elif sys.argv[1] == '--unitTest':
      print "Starting test suite 1"
      import unitTestsS1
      print "Starting test suite 2"
      import unitTestsS2
      print "Tests completed"
  else:
     from c4_run import main
     cmdl = string.join( sys.argv )
     main(printInfo=True, cmdl=cmdl)

if __name__ == '__main__':
  main_entry()
