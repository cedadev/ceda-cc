"""
Entry point for command line usage -- see ccinit for usage information.
"""
import sys

def main_entry():
  """
   Wrapper around main() for use with setuptools.
   This function will intercept arguments --sum, --unitTest, -v, otherwise pass the commandline to c4_run.main.
  """
  if len(sys.argv) == 1:
      # Show command-line info and report that you must provide arguments
      from ceda_cc import ccinit
      print(ccinit.__doc__)
      print("\nERROR: Please provide command-line arguments.")
      return

  if sys.argv[1] == '--sum':
      from ceda_cc import summary
      summary.summariseLogs()
  elif sys.argv[1] == '-v':
      from .versionConfig import version, versionComment
      print('ceda-cc version %s [%s]' % (version,versionComment))
  elif sys.argv[1] == '--unitTest':
      print("Starting test suite 1")
      from . import unitTestsS1
      print("Starting test suite 2")
      from . import unitTestsS2
      print("Tests completed")
  else:
     from ceda_cc.c4_run import Main
     cmdl = ' '.join( sys.argv )
     m = Main(cmdl=cmdl)
     m.run(printInfo=True)

if __name__ == '__main__':
  main_entry()
