"""
    This Code, and Resulting Software is Copyright 2010 Stuart Mumford and Keiron Pizzey
    
    PriMaRy JOVE Analysis is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or any later version.

    PriMaRy JOVE Analysis is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PriMaRy JOVE Analysis. If not, see <http://www.gnu.org/licenses/>.
"""
#Import Modules
from numpy import *
import matplotlib.pyplot as plt
import matplotlib.ticker as tick
from scipy.fftpack import *
import scipy.optimize as opt
import pyfits as fits
import subprocess as sub
import shutil, os, time

class Error(Exception):
    """ Simple Error class to allow raising text errrors"""
    def __init__(self,error):
        print "################################"
        print error
        print "################################"

####################################################################################################

def nt_time(nttime):
    """Converts a NT time stamp to unix time.

       NT time is a floating point number used to represent time from some point in the past. (and is the deafult format for .spd files)
       Unix time is seconds since the epoch.
       Input:
           nttime = Input time float.
       Output:
           unix = Output float in unix time
    """
    unix = (nttime - 25569.0) * 86400.0
    return unix

####################################################################################################

class opendata():
    """This is a class which will determine the type of file and open it to a consistent data structure.
    
        A instance of this class will have the following useful attributes:
        x.data -> A list of values
        x.time -> A corresponding list of unix time stamps
        x.header -> if a spd or fits file is opened this will be the header file from it.
    """
    def __init__(self,filename):
        self.filename = filename
        self.Fdata = ''
        self.header = ''
        self.data = ''
        self.time = ''
        #Firstly Check filename exists
        if not os.path.exists(self.filename):
            raise Error("File Does not Exist")
        #Next Determine Type of file
        self.filetype = self.filename[self.filename.rfind('.'):]
        if self.filetype == '.spd': #Sky pipe data format
            self.spd()
            self.timeconvert()
        elif self.filetype == '.csv':
            self.csv()
            self.timeconvert()
        elif self.filetype == '.fits' or '.fit':
            self.import_fits()
            self.timeconvert()
        elif self.filetype == '.txt' or '': # Read .txt and no extension files as a txt
            self.txtload()
            self.timeconvert()
        else: # If it dosent know what it is try and read it as a plain txt
            try:
                self.txtload()
                self.timeconvert()
            except:
                raise Error("Cannot open this file -- Incompatible Type")  #else give up  

    def spd(self):
        #Convert to FITS
        self.convert()
        #Re-Set filename to FITS
        self.filename = self.filename+'.fits'
        #Import FITS
        self.import_fits()

    def csv(self):
        #Read csv
        try:
            self.nttime,self.data = loadtxt(self.filename, delimiter=',')
        except ValueError:
            self.Fdata = loadtxt(self.filename, delimiter=',')
            self.zipdata()
        except:
            Error('Incompatible csv File')
        
    def convert(self):
        """ Convert .spd to .fits using spdfits converter """
        if not os.path.exists('./SPD2FITS'):
            raise Error('SPD2FITS Converter Not Found')
        else:
            #Copy Input file from input location to SPD2FITS folder
            shutil.copy(self.filename,'./SPD2FITS')
            os.chdir('./SPD2FITS')
            sub.call(['spd2fits.bat',self.filename])
            import glob
            print glob.glob("./*")
            #shutil.move(self.filename+'.fits',self.filename+'.fits')
        
    def import_fits(self):
        """ This is te function that reads in fits files.
            SPD2FITS returns fits files with the data in the second HDU """
        #Open fits file
        FF = fits.open(self.filename)
        #Check to see if fits file is SPD2FITS and therefore data is in [1] rather than [0]
        try:
            if len(FF[0].data) != 0:
                raise Error('Data in First HDU .. Reading that')
            #Get Header and check channels = 1
            self.header = FF[1].header
            #Get number of channels from header
            channels = self.header['CHANNELS']
            if not channels == 1:
                raise Error("Please supply a file with only one channel")
            self.Fdata = FF[1].data
            
        except Error:
            print "Now trying non-SPD2FITS read"
            self.header = FF[0].header
            try:
                channels = self.header['CHANNELS']
            except KeyError:
                print("No Channel Information in Header...")
                channels = 0
            self.Fdata = FF[0].data
        finally:
            self.zipdata()
            pass
    
    def txtload(self):
        self.nttime,self.data = loadtxt(self.filename)
        
    def zipdata(self):
        self.nttime, self.data =  [],[]
        for i,val in enumerate(self.Fdata):
            self.nttime.append(val[0])
            self.data.append(val[1])
            print "Now loading sample number %i / %i" %(i,len(self.Fdata))
        print "All samples loaded"
    
    def timeconvert(self):
        self.time = []
        if self.nttime[0] < 1000000:
            for i,t in enumerate(self.nttime):
                self.time.append(nt_time(t))
        else:
            self.time = self.nttime

####################################################################################################


def passfilter(y, filtertype = 'low', lim = 100):
    """Filter function to remove unwanted frequencies.

    Function uses discrete FFT theory to transform from time domain to frequency domain.
    The unwanted frequencies are then set to zero as per the parameters input.

    Inputs:
        Array = Input array to be filtered;
        lim = Limit of the band allowed to pass;
        filtertype = Type of filter, either "high" or "low"
            "low" = All frequencies above lim will be set to zero
            "high" = All frequencies below lim will be set to zero
            
    Output:
        newy = The array y filtered of unwanted frequencies
    """

    if lim > len(y)/2.0:
        raise Error('\nError: lim is too high for this size array!')

    yfft = fft(y)                       # FFT the input data.

    if filtertype.capitalize() == 'Low':
    # Will filter using low pass frequency filter.

        yfft[lim:-lim-1] = 0            # Filters the data as per lim.
        newy = ifft(yfft)               # Inverse FFT the filtered data.
        
    elif filtertype.capitalize() == 'High':
    # Will filter using a high pass frequency filter.    

        yfft[:lim],yfft[-lim-1:] = 0, 0 # Filters the data using lim.
        newy = ifft(yfft)               # Inverse FFT the filtered data.
    else:
        raise Error('Not a correct pass filter type!')
    
    return newy

####################################################################################################

def smooth(x, window_len=11 ,window='hanning'):
    """Window smoothing function.
    
    This method is based on the convolution of a scaled window with the input signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x = Input signal;
        window_len = The dimension of the smoothing window, should be an odd integer greater than 2;
        window = The type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        y = Smoothed signal
    """

    if x.ndim != 1:
        raise Error("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise Error("Input vector needs to be bigger than window size.")

    if (not isodd(window_len)) or (window_len < 3):
        raise Error("Window length is either below 3 or not even.")


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise Error("Window is out of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s = r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]
    
    if window == 'flat': # moving average
        w = ones(window_len,'d')
    else:
        w = eval(window+'(window_len)')

    y = convolve(w/w.sum(),s,mode='same')
    
    return y[window_len-1:-window_len+1]

####################################################################################################

def spd2fits(filename):
    """Function which converts a Skypipe data set into a FITS file using bash commands.

       Uses the python subprocess module to run windows prompt commands"""

    cwd = os.getcwd()

    spd2fitsdir = './SPD2FITS/'
    
    sub.call(spd2fitsdir + 'spd2fits ' + filename)
    
    print 'FITS file created.\n'
    
####################################################################################################
    
def isodd(num):
    """Function which checks whether a number is even or odd.

    Input:
        num = Integer

    Output:
        Boolean output, if number is off then output is True.
    """

    if num != int(num):
        raise Error("Number is not integer!")
    
    return num & 1 and True or False

####################################################################################################

def binner(time, data, bintime = 1.0):
    """Bins an input array and also creates a time-array to reflect this binning.

    Inputs:
        time = Input time-array;
        data = Input data-array;
        bintime = Time length of bins.

    Output:
        fx = Binned time array;
        fy = Binned data array.

    Data binning is done on a smart basis, the array indexes are calculated from the time
    array in such a way that the time of bins is always constant even if the number of elements
    per bin may change. The last data bin, unless it factors in completely, is simply the rest of
    the array averaged.

    The time-array is binned in such a way that the first time of the binned data-array
    is chosen to be the time for that bin.
    
    """

    if len(time) != len(data):
        raise Error("Arrays are not same size")
    
    N = len(time)                                            # Number of items.

    time_bin_list, data_bin_list = [], []                 # Empty lists

    j = 0                                                 # Initial counter

    timeunix = time

    #for i,val in enumerate(time):
    #    timeunix[i] = nt_time(val)

    timex = timeunix - timeunix[0]
    
    for i,val in enumerate(timex):
        if timex[i] > (timex[j] + bintime) or i == N:
            time_bin_list.append(timeunix[j])
            data_bin_list.append(mean(data[j:i]))
            j = i

    time_bin = array(time_bin_list)
    data_bin = array(data_bin_list)
    
    return time_bin, data_bin

####################################################################################################

def normal(p, x):
    """Calculates gaussian function from a set of parameters, p, and data, x.

    Uses the standard gaussian function and an additional vertical offset to return an array
    when given parameters and x data.
    
    !!!!REQUIRED BY RESIDUALS AND GAUSSFIT AMONGST OTHERS!!!!

    Input:
        p = List of parameters
            p[0] = a = Height of peak from base;
            p[1] = b = Centre of peak;
            p[2] = c = Width parameter;
            p[3] = d = Vertical offset
        x = Input array of floats

    Output:
        y = Gaussian array.
    """

    x = real(x)
    
    a, b, c, d = p
    y = (a * exp(-(x - b)**2 / (2.0 * c**2))) + d
    
    return y

####################################################################################################

def residuals(p, y, x):
    """Calculates the residuals between fit gaussian and data.

    Calculates the difference between gaussian fit data and measured data.
    
    !!!!REQUIRED BY GAUSSFIT!!!!

    Input:
        p = List of parameters
            p[0] = a = Height of peak from base;
            p[1] = b = Centre of peak;
            p[2] = c = Width parameter;
            p[3] = d = Vertical offset
        y = Measured data;
        x = Array with which y is measured against;

    Output:
        err = Difference between arrays.
    """
    
    err = y - normal(p, x)
    return err

####################################################################################################

def gaussfit(p0, y):
    """Function which fits a gaussian function to y and returns the parameters needed to recreate the fit.

    Function uses the Levenberg-Marquardt algorithm to fit a gaussian function to input data y.
    LMA is an algorithm which uses non-linear regression to vary the parameters to fit the data.

    Input:
        p0 = Starting parameters (Starting parameters must be a reasonably good guess for the function
                                  otherwise the LMA will find a minimum which may not be the global one)
        y = Measured data

    Output:
        pnew = Fitted parameters which can be plugged into normal(p,x)

    """
    z = range(len(y))

    output = opt.leastsq(residuals, p0, args = (y, z))
    
    pnew = output[0]

    return pnew                

####################################################################################################

def peakfinder(arr, limit):
    """Function designed to automatically find peaks in a data set and fit a gaussian curve to them.

    Function will search through measured data looking for peaks, after finding these peaks it will then
    proceed to use gaussfit to attempt to fit peaks to them and then save all the parameters to an array
    to be output to the user.

    Input:
        arr = Measured data array;
        limit = Float used to choose what is deemed as a peak. A peak is registered if it's tip is greater than
                limit*standard_deviation of the data set.

    Output:
        parameters = List of lists containing parameter data for all peaks found.

    """

    arr = real(arr)             # Removes are imaginary components of the measured data.

    arrmean = mean(arr)         # Calculates average of measured data.
    arrstd = std(arr)           # Calculates standard deviation of measured data.

    peaks = []
    parameters = []

    # for loop will iterate through the data array and search for any peaks.
    # A peak is definsed as a point of inflexion limit*arrstd above arrmean.
    for (i, val) in enumerate(arr):
        if i == len(arr) - 2:   # Stops the iteration if end of array is reached.
            break
        elif arr[i] < arr[i+1] and arr[i+1] > arr[i+2] and arr[i+1] > arrmean + (limit * arrstd):
            peaks.append(i+1)   # Appends the point of inflexion to a list

    print 'Peaks found at %s' % peaks

    # for loop iterates over the points of inflexion and finds the start and end of the peak.
    # The start and end are defined as points of inflexion.
    for peakmid in peaks:

        # Finds end of the peak.
        for (i, val) in enumerate(arr[peakmid:]):
            diff = arr[peakmid+i+1] - arr[peakmid+i]
            if diff > 0:
                peakend = i
                break

        # Finds the start of the peak.
        for (i, val) in enumerate(reversed(arr[peakmid:])):
            diff = arr[peakmid+i+1] - arr[peakmid+i]
            if diff > 0:
                peakstart = i
                break

        # Creates a new array so only fitting gaussian curve over peak data range.                   
        ypeak = arr[peakmid - peakstart : peakmid + peakend]

        # Creates good guesses for starting parameters of the peak.
        pguess = [max(ypeak) - min(ypeak), len(ypeak)/2, len(ypeak)*0.1, min(ypeak)]

        pfit = gaussfit(pguess, ypeak)

        # Defines central position as middle of peak (Instead of index of ypeak)
        pfit[1] = peakmid

        # Appends the parameters to a list to be output to user.
        parameters.append(pfit)
    print "para"
    print parameters

    return parameters

####################################################################################################

def peakrammer(array1,array2):
    if len(array1) != len(array2):
        raise
    arr = zeros(len(array1))
    for i in range(len(array1)):
            a = array1[i]
            b = array2[i]
            if math.isnan(a) and math.isnan(b):
                arr[i] = nan
            elif math.isnan(a) and not math.isnan(b):
                arr[i] = b
            elif not math.isnan(a) and math.isnan(b):
                arr[i] = a
            elif not math.isnan(a) and not math.isnan(b):
                if a > b:
                    arr[i]=a
                elif a < b:
                    arr[i]=b

    return arr

####################################################################################################

def peakplotter(y, para):
    """Plots data and any peaks which have been found using peakfinder.

    Will plot the data and then iterate through para to plot any peaks which have been found.

    Inputs:
        x = Time-array;
        y = Smoothed data;
        para = Parameters of fitted peaks

    Output:
        No output, just a graphing function. 
    """

    z = range(len(y))

    for i,p in enumerate(para):
        exec('array%s = normal(p, z)' % str(i))
        for j,val in enumerate(eval('array%s' % str(i))):
            if val < 1.01*p[3] or val < 0.0:
                exec('array%s[%s] = nan' % (str(i), str(j)))

    N = len(para)                           # Number of peaks

    for i in range(0,N-1):
        if i == N-1:
            break
        exec('array%s = peakrammer(array%s, array%s)' % (str(i+1), str(i+1), str(i)))

    exec('result = array%s' % str(N-1))
        
    return result
    
    

####################################################################################################

def difference(y0, y1):
    """Simple function which calculates the difference between two arrays.

    Input:
        y0 = First array;
        y1 = Second array.

    Output:
        diff = Difference.
    """

    size0, size1 = size(y0), size(y1)           # Calculates array sizes.

    # Checks for irregularities in array sizes.
    if N0 != N1:
        raise Error("Arrays not same size!")

    diff = y0 - y1                              # Calculate difference

    return diff

####################################################################################################

def timegrinder(t):
    """Function to edit a time array to reflect change in seconds since beginning.

    Input:
        t = Time array

    Output:
        tnew = New time array
    """

    start = t[0]

    tnew = t - start

    return tnew

####################################################################################################

def datasaver(arrt, arry, filename, start = 0, end = -1):
    """Function which saves time/data to a text file

    Input:
        t = Time array;
        y = Data array;
        filename = the full save path, or relative save path with filename;
        start = A time to slice the array to, or 0 to start at the begging;
        end = A time to slice the array to, or -1 to stop at the end;
        
    """
    
    # Make sure filename is not blank
    if filename ==  '':
        raise Error('Please speicfy a filename')
    
    # Get filetype from extension on filename
    filetype = filename[filename.rfind('.'):]
    
    #Convert times to index, if needed
    if start == 0:
        startindex = 0
    if end == -1:
        endindex = -1
    else:
        startindex,endindex = timetoindex(arrt,start,end)
    
    # Depending on filetype save to file
    if filetype == '.csv':
        savetxt(filename,[arrt[startindex:endindex],arry[startindex:endindex]],delimiter=',')
    elif filetype == '.txt' or filetype == '':
        savetxt(filename,[arrt[startindex:endindex],arry[startindex:endindex]],delimiter=' ')
    else:
        raise Error('Incorrect File Type')

def timetoindex(arrt,start,end):
    """ This function will convert a time to a index for the time and data arrays """
    timestep = arrt - arrt[0]

    databegin = time.gmtime(arrt[0])                                            # Python time of array beginning.
    beginsec = (databegin[3] * 3600.0) + (databegin[4] * 60.0) + (databegin[5]) # Number of seconds since midnight.

    # Number of seconds since midnight for start and ending of saving range.

    startsec = (start[0] * 3600.0) + (start[1] * 60.0) + (start[2])
    endsec = (end[0] * 3600.0) + (end[1] * 60.0) + (end[2])

    # Takes into account when the saving range crosses over the midnight mark.
    startstep = startsec - beginsec
    if startstep < 0.0:
        startstep = startstep + 86400.0

    endstep = endsec - beginsec
    if endstep < 0.0:
        endstep = endstep + 86400.0

    # Iterates through the time array and sets start/end index.
    
    for i,val in enumerate(timestep):
        if val < startstep:
            startindex = i
        if val < endstep:
            endindex = i
            
    return startindex, endindex
##################################################################################################

def axesformatter(x, pos=None):
    """ This, if called as matplotlib.ticker.FuncFormatter() will format the x axis with string time.
        Otherwise it will convert a unix time to a string of HH:MM:SS"""
    struct_time = time.gmtime(x)
    stringtime = time.strftime("%H:%M:%S",struct_time)
    return stringtime
    
##################################################################################################

def gaussfitsaver(filename,parameters):

    parameters = array(parameters)

    savetxt(filename + '.csv', parameters, delimiter = ',')
