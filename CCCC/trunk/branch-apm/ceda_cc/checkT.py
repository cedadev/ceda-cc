
import string


t1 = '19900101'

t2 = ['days since 1980-01-01', '360-day', 3600]

lm = [31,28,31,30,31,30,31,31,30,31,30,31]

## gregorian or standard
## mixed gregorian/julian
## leap if after 1582: gregorian leap-year rule, otherwise julian.

## proleptic_gregorian

  ##  A Gregorian calendar extended to dates before 1582-10-15. That is, a year is a leap year if either (i) it is divisible by 4 but not by 100 or (ii) it is divisible by 400.
## noleap or 365_day; leap = False

## all_leap or 366_day; leap = True

## 360_day; lm=12, no leap

## julian: every 4th year a leap year

class cfCalSupport:

  def __init__(self,calendar):
    self.clist = ['gregorian','proleptic_gregorian','all_leap','360_day','365_day','julian']
    self.alist = ['standard','366_day','noleap']
    self.calias = {'standard':'gregorian', '366_day':'all_leap', 'noleap':'365_day' }
    assert calendar in self.clist + self.alist, 'Calendar %s not recognised' % calendar
    self.calendar = calendar
    self.cal = self.calias.get( calendar, calendar )
    self.lm = lm
    if self.cal == 'all_leap':
      self.lfixed = True
      self.leap = True
      self.ylen = 366
    elif self.cal == '360_day':
      self.lfixed = True
      self.leap = False
      self.ylen = 360
      self.lm = [30,30,30,30,30,30,30,30,30,30,30,30,]
    elif self.cal == '365_day':
      self.lfixed = True
      self.leap = False
      self.ylen = 365
    else:
      self.lfixed = False
      self.ylen0 = sum( self.lm) 
      if self.cal == 'julian':
        self.ylen = 365.25
      elif self.cal == 'proleptic_gregorian':
        self.ylen = 365 + 97./400.
      elif self.cal == 'gregorian':
## compromise between gregorian and julian.
        self.ylen = 365 + 98.5/400.
        self.ylenx = [365.25,365 + 97./400.]
      
    self.alm = [0,]
    for k in range(11):
      self.alm.append( self.alm[k] + self.lm[k] )

  def isleap( self, year ):
    if self.lfixed:
      return self.leap
    elif self.cal == 'julian':
      return self.isJulianLeap(year)
    elif self.cal == 'proleptic_gregorian':
      return self.isProlepticGregorianLeap(year)
    elif year > 1582:
      return self.isProlepticGregorianLeap(year)
    else:
      return self.isJulianLeap(year)

  def isJulianLeap(self,year):
    iy = int(year)
    return (iy/4)*4 == iy

  def isProlepticGregorianLeap(self,year):
    iy = int(year)
    return ( (iy/4)*4 == iy and (iy/100)*100 != iy ) or ( (iy/400)*400 == iy )

  def dayOff(self,year):
    """Returns the number of days since year zero for given year"""
    if self.cal in ['all_leap','360_day','365_day']:
      return year*self.ylen
    else:
      if self.cal == 'julian':
        return  int(1 + round( 365.25*year - 0.51 )  )
      elif self.cal == 'proleptic_gregorian':
## see http://quasar.as.utexas.edu/BillInfo/JulianDatesG.html
        y = year - 1
        a = round(y/100 - 0.5)
        return  int(1 - a + round(a/4 - 0.5) + round( 365.25*year - 0.51 )  )
      elif self.cal == 'gregorian':
        if year <= 1583: 
          return  int(1 + round( 365.25*year - 0.51 )  )
        else:
          y = year - 1
          a = round(y/100 - 0.5)
          return  int(1 - a + round(a/4 - 0.5) + round( 365.25*year - 0.51 )  ) + 12
## proleptic gregorian has 12 fewer leap years than julian.
      else:
        assert False, "not suported yet"
  
  def d2y(self,ybase, d):
    dy = d/float(self.ylen)
    if not self.lfixed:
      #####
      pass
      ############ need some work here to get correct day .....
      ############ need to use known periodicities (4,400 and mixed) as a starting point ###########
    

  def dayDiff(self,year1,year0):
    return self.dayOff(year1) - self.dayOff(year0)

  def dayInYear(self,year,month,day):
    if self.cal == '360_day':
      return (month-1)*30 + day
    x = 0
    if self.isleap(year) and month > 2:
      x = 1
    return x + self.alm[month-1] + day

  def yearLen(self,year):
    if self.lfixed:
      return self.ylen
    x=0
    if self.isleap(year):
      x = 1
    return self.ylen0 + x


  def setBase( self, base ):
    bits = string.split( base )
    assert bits[0] == 'days'
## only support days here -- for more general support coudl use cf-python, introducing dependency on numpy and python netCDF4
    assert bits[1] == 'since'
    assert len(bits) > 2,'Not enough elements in time base specification string %s' % base
    s = re.compile( '^([0-9]{1,4}-[0-9]{1,2}-[0-9]{1,2})($|T(.*))' )
    t = re.compile( '^([0-9]{1,2}):([0-9]{1,2}):([0-9.]*)($|Z$)' )
    bb = s.findall( bits[2] )
    assert len(bb) > 0, 'Failed to parse time base reference year/month/day: %s' % base
    y,m,d = map( int, string.split( bb[0], '-' ) )
    if len(bits) == 3 and len(bb[2]) ==  0:
      h,mn,s = 0,0,0.
    else:
      if len(bits) == 4:
         hms = bits[3]
      else:
         hms = bb[2]
      cc = t.findall( hms )
      h = int(cc[0])
      mn = int(cc[1])
      s = float(cc[2])
    self.base = (y,m,d,h,mn,s)


## method to obtain extended index -- (time-base time)/dt or (time-base time)*freq

def timeUnitsScan( c1 ):
    bits = string.split( c1 )
    assert bits[0] == 'days'
## only support days here -- for more general support coudl use cf-python, introducing dependency on numpy and python netCDF4
    assert bits[1] == 'since'

def jabs( y,m,d,cal ):
  if cal == '360-day':
    return y*360 + m*30 + d

def c1(t1,t2):
  y,m,d = map(int,[t1[:4],t1[4:6],t1[6:]])
  bits = string.split( t2[0] )
  assert bits[0] == 'days'
  assert bits[1] == 'since'

  calendar = t2[1]
  if calendar == '360-day':
    ly = 360
    lm = 30

  bt = bits[2]
  by,bm,bd = map(int,[bt[:4],bt[5:7],bt[8:]])
  j0 = jabs(y,m,d, calendar )
  j1 = jabs(by,bm,bd, calendar ) + t2[2]
  if j0 != j1:
    print 'dates do not match: %s, %s:: %s' % (t1,str(t2),j1-j0)
  else:
    print 'OK'

c1(t1,t2)
