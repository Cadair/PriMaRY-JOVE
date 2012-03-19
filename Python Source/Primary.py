print """
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
print "Now loading PriMaRy Jove Analysis by Stuart Mumford and Keiron Pizzey .... "
import time
time.clock()
import sys
from PyQt4 import QtCore, QtGui
import os,math,epic
#Import GUI's from file
from MainWindow1 import Ui_MainWindow
from about import Ui_AboutDialog
from plotcontrol import Ui_PlotDialog
print "Loaded in %s s" %time.clock()
print "Watch this command window for errors, and progress information."

##############################################################################

class About(QtGui.QDialog):
    """ Class to display the about window"""
    def __init__(self,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.about = Ui_AboutDialog()
        self.about.setupUi(self)
        
class PlotControl(QtGui.QDialog):
    """ This class controls the custom plot settings """
    def __init__(self,x,y,parent=None):
        #Deafult Init Stuffs:
        QtGui.QDialog.__init__(self,parent)
        self.plotcontrol = Ui_PlotDialog()
        self.plotcontrol.setupUi(self)
        #Rename plot to make life easier
        self.plt = epic.plt
        #Define Varibles:
        self.x = x
        self.y = y
        self.xlabel = ''
        self.ylabel = ''
        self.title = ''
        self.firstrun = True
        #Connect Some stuff:
        conn = QtCore.QObject.connect
        ui = self.plotcontrol
        #Plot Button
        conn(ui.PlotButton, QtCore.SIGNAL("clicked()"), self.ploty)
        #Plot Title
        conn(ui.Title, QtCore.SIGNAL('textChanged(QString)'), self.titley)
        #Plot xlabel
        conn(ui.xLabel, QtCore.SIGNAL('textChanged(QString)'), self.xlabely)
        #Plot ylabel
        conn(ui.yLabel, QtCore.SIGNAL('textChanged(QString)'), self.ylabely)
        
    #Define some functions
    def titley(self,text):
        self.title = str(text)
        
    def xlabely(self,text):
        self.xlabel = str(text)
        
    def ylabely(self,text):
        self.ylabel = str(text)
        
    def ploty(self):
        self.plt.close()
        fig = self.plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(self.x,self.y,'g',linewidth = 0.25)
        ax.xaxis.set_major_formatter(epic.tick.FuncFormatter(epic.axesformatter))
        self.firstrun = False
        self.plt.title(self.title)
        self.plt.xlabel(self.xlabel)
        self.plt.ylabel(self.ylabel)
        self.plt.show()

class Main(QtGui.QMainWindow):
    """This is the Main window class """

    def __init__(self,parent=None):

        #Deafult Initalistion and display form
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.statusbar.showMessage('Ready')
        self.file = ''
        #This is the current data in use by the user, not the original file data that is self.file.data
        self.data = ''
        self.currentdata = ''
        self.time = ''
        self.currenttime = ''
        self.peakplot = ''
        self.starttime = () #Set deafult start and end times, so if left unmodified it will export
        self.endtime = ()  #From begging or end of array.
        self.peaks = []
        #Other instance varibles that need defining: These are the deafult values in the form.
        self.binval = 1
        self.FFTlim = 10
        self.FFTtype = 'low'
        self.winlength = 11
        self.wintype = 'hanning'
        self.peakcutoff = 2.0
    #Shortcuts
        conn = QtCore.QObject.connect
        self.mpl  = self.ui.mplwidget
    #Create Plot Stuffs
        self.fig = self.mpl.figure
        self.ax1 = self.fig.add_subplot(111)
    #Connect About box
        conn(self.ui.pushButtonAbout, QtCore.SIGNAL("clicked()"), self.about)
    #Connect Custom Plot box
        conn(self.ui.CustomPlot, QtCore.SIGNAL("clicked()"), self.customplot)
    #Connect Open box
        conn(self.ui.pushButtonOpen, QtCore.SIGNAL("clicked()"), self.open)
    #Connect Plot Button
        conn(self.ui.pushButtonPlotRaw, QtCore.SIGNAL("clicked()"),self.plotdata)
    #Connect Save Graph Button
        conn(self.ui.SaveGraphButton, QtCore.SIGNAL("clicked()"),self.savedata)
    #Connect Clear Button
        conn(self.ui.ClearButton, QtCore.SIGNAL("clicked()"),self.clearbutton)
    #Connect External Plot Button
        conn(self.ui.ExternalPlot, QtCore.SIGNAL("clicked()"), self.externalplot)
    #Connect Binning Button and Spin Box
        conn(self.ui.BinButton, QtCore.SIGNAL("clicked()"),self.binning)
        conn(self.ui.BinNumber, QtCore.SIGNAL("valueChanged(int)"),self.binvalue)
    #Connect FFT Button and spin box and combo box
        conn(self.ui.FFTbutton, QtCore.SIGNAL("clicked()"),self.fft)
        conn(self.ui.FFTlim, QtCore.SIGNAL("valueChanged(int)"),self.fftlimit)
        conn(self.ui.FFTtype, QtCore.SIGNAL("currentIndexChanged(const QString)"),self.ffttype)
    #Connect Window function
        conn(self.ui.WindowLength, QtCore.SIGNAL("valueChanged(int)"),self.windowlength)
        conn(self.ui.WindowType, QtCore.SIGNAL("currentIndexChanged(const QString)"),self.windowtype)
        conn(self.ui.WindowButton, QtCore.SIGNAL("clicked()"), self.window)
    #Connect Peak Fit / Find
        conn(self.ui.PeakFitCutoff, QtCore.SIGNAL("valueChanged(double)"),self.peakfitcutoff)
        conn(self.ui.FindPeaks, QtCore.SIGNAL("clicked()"), self.findpeaks)
        conn(self.ui.PlotPeaks, QtCore.SIGNAL("clicked()"), self.plotpeaks)
        conn(self.ui.AutomatedAnalysis, QtCore.SIGNAL("clicked()"), self.automatedanalysis)
    #Connect the save whole file button
        conn(self.ui.SavetoFile, QtCore.SIGNAL("clicked()"), self.savetofile)
    #Connect the time start and end and the part save button
        conn(self.ui.StartTime, QtCore.SIGNAL("textChanged(QString)"), self.starttimef)
        conn(self.ui.EndTime, QtCore.SIGNAL("textChanged(QString)"), self.endtimef)
        conn(self.ui.PartSave, QtCore.SIGNAL("clicked()"), self.partsave)
        conn(self.ui.SavePeaks, QtCore.SIGNAL("clicked()"),self.savepeaks)
    def about(self):
        """ Opens the About window """
        ab = About()
        ab.exec_()
    def customplot(self):
        """Opens the custom plot window, and feeds it current time and data """
        cp = PlotControl(self.currenttime,self.currentdata)
        cp.exec_()
    def plot(self,x,y):
        """ Simplyfies a simple x,y plot"""
        self.mpl.axes.cla()
        self.mpl.axes.plot(x,y)
        self.mpl.axes.xaxis.set_major_formatter(epic.tick.FuncFormatter(epic.axesformatter))
        self.mpl.draw()
    def open(self):
        """ This opens a file using the opendata class in epic """
        #Set status Bar
        self.ui.statusbar.showMessage('Opening File .... Please Wait')
        #Create a open file box, looking only for spd fits and csv files.
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open data file','./',"Data Files (*.spd *.fits *.fit *.csv *.txt)")
        #Set filename to box in UI
        self.ui.lineEditCurrentFile.setText(filename)
        #Run open data class
        self.file = epic.opendata(str(filename))
        #Set current in use data to the file data on Open
        self.data = self.file.data
        self.time = self.file.time
        #Get start and end time, format them to be pretty.
        self.starttime = self.file.time[0]
        self.endtime = self.file.time[-1]
        self.prettystart = time.strftime("%d %b %Y %H:%M:%S",time.gmtime(self.starttime))
        self.prettyend = time.strftime("%d %b %Y %H:%M:%S",time.gmtime(self.endtime))
        self.lentime = self.endtime - self.starttime
        #Set them into the boxes
        self.ui.lineEditFileStart.setText(self.prettystart)
        self.ui.lineEditFileEnd.setText(self.prettyend)
        #Set lengths and Number of samples
        self.ui.LengthofFile.setText(str(math.ceil(self.lentime / 60.0))) # Convert seconds to minutes.
        self.ui.NumberofSamples.setText(str(len(self.file.data)))
        #plt the data
        self.plotdata()
        #Set status bar to finished.
        self.ui.statusbar.showMessage('Ready')
    def plotdata(self):
        """ This is the raw data file plotting, it sets the current data files to the original data and plots """
        self.currentdata = self.file.data
        self.currenttime = self.file.time
        self.plot(self.currenttime,self.currentdata)
    def externalplot(self):
        """ This plots the current data object in an external window, it also checks for peak fitting to be run """
        if self.peakplot != '': # If peak finding has been run then self.peakplot will be populated and therefore both things need plotting
            fig = epic.plt.figure()
            ax = fig.add_subplot(111)
            ax.plot(self.currenttime,self.currentdata,'b', linewidth = 0.25)
            ax.plot(self.currenttime,self.peakplot)
            ax.xaxis.set_major_formatter(epic.tick.FuncFormatter(epic.axesformatter))
            fig.show()
        else:    
            fig = epic.plt.figure()
            ax = fig.add_subplot(111)
            ax.plot(self.currenttime,self.currentdata,'g',linewidth = 0.25)
            ax.xaxis.set_major_formatter(epic.tick.FuncFormatter(epic.axesformatter))
            fig.show()
        
    def savedata(self):
        """ This saves the current data and time """
        self.data = self.currentdata
        self.time = self.currenttime
    def clearbutton(self):
        """ This plots the saved data, replacing the current data and clears peakplot for good measure """
        self.plot(self.time, self.data)
        self.peakplot = ''
    #Binning
    def binvalue(self,i):
        """ Set Bin value """
        self.binval = i
    def binning(self):
        """ Binning routine, binns and plots """
        self.ui.statusbar.showMessage('Binning Data')
        self.currenttime,self.currentdata = epic.binner(self.time,self.data,self.binval)
        self.plot(self.currenttime,self.currentdata)
        self.ui.statusbar.showMessage('Ready')
    #FFT Smoothing
    def fft(self):
        """ Run the band pass filter on the saved data set """
        self.ui.statusbar.showMessage('Pass Filter Smoothing')
        self.currentdata = epic.passfilter(self.data,self.FFTtype,self.FFTlim)
        self.plot(self.currenttime,self.currentdata)
        self.ui.statusbar.showMessage('Ready')
    def fftlimit(self,i):
        """ Set frequency limit """
        self.FFTlim = i
    def ffttype(self,FFTtype):
        """ Set pass filter type to eith high or low """
        self.FFTtype = str(FFTtype)
    #Window Smoothing
    def windowlength(self,i):
        """ Set window smoothing window length"""
        self.winlength = i
    def windowtype(self,wintype):
        """ Set Window Smooothing Type """
        self.wintype = str(wintype)
    def window(self):
        """ Window smoothing function, again with plot """
        self.ui.statusbar.showMessage('Window Smoothing Data')
        self.currentdata = epic.smooth(self.data,self.winlength,self.wintype)
        self.plot(self.currenttime,self.currentdata)
        self.ui.statusbar.showMessage('Ready')
    #Peak Finder
    def peakfitcutoff(self,i):
        """ Set the peak cut off varible from the input """
        self.peakcutoff = i
    def findpeaks(self):
        """ This runs the peak finding routine, then prints out the time of each peak in a message box """
        self.ui.statusbar.showMessage('Finding Peaks')
        self.peaks = epic.peakfinder(self.data, self.peakcutoff)
        peaktime = []
        prettypeak = []
        for i,each in enumerate(self.peaks):
            peaktime.append(str(self.time[each[1]]))
            t = self.time[each[1]]
            prettypeak.append(time.strftime("%H:%M:%S",time.gmtime(t)))
        foundpeaks = "Peaks have been found at the following times: \n %s" %(prettypeak)
        reply = QtGui.QMessageBox.question(self, 'Message', foundpeaks, QtGui.QMessageBox.Ok)
        self.ui.statusbar.showMessage('Ready')
    def plotpeaks(self):
        """ This Finds the peaks, then plots both the data and the compressed peaks on the graph"""
        self.ui.statusbar.showMessage('Finding Peaks')
        self.peaks = epic.peakfinder(self.data,self.peakcutoff)
        self.peakplot = epic.peakplotter(self.data,self.peaks)
        self.mpl.axes.cla()
        self.mpl.axes.plot(self.currenttime,self.peakplot,self.currenttime,self.currentdata,'--')
        self.mpl.axes.xaxis.set_major_formatter(epic.tick.FuncFormatter(epic.axesformatter))
        self.mpl.draw()
        self.ui.statusbar.showMessage('Ready')
    def automatedanalysis(self):
        """ This is quite simple, it runs the three best processes, saves the data after each one."""
        #Reset to Original file data
        self.currentdata = self.file.data
        self.currenttime = self.file.time
        #Run bin,fft and plopeaks
        self.binning()
        self.savedata()
        self.fft()
        self.savedata()
        self.plotpeaks()
        self.savedata()
    def starttimef(self,time):
        h = str(time[:2])
        m = str(time[3:5])
        s = str(time[-2:])
        self.starttime = (int(h),int(m),int(s))
    def endtimef(self,time):
        h = str(time[:2])
        m = str(time[3:5])
        s = str(time[-2:])
        self.endtime = (int(h),int(m),int(s))
    def partsave(self):
        self.ui.statusbar.showMessage('Saving File')
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Partial Data Array','./',"Data Files (*.txt *.csv)")
        epic.datasaver(self.time,self.data,str(filename),self.starttime,self.endtime)
        self.ui.statusbar.showMessage('Ready')
    def savetofile(self):
        self.ui.statusbar.showMessage('Saving File')
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Data Array','./',"Data Files (*.txt *.csv)")
        epic.datasaver(self.time,self.data,str(filename))
        self.ui.statusbar.showMessage('Ready')
    def savepeaks(self):
        self.ui.statusbar.showMessage('Saving File')
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Peak Parameters','./',"Comma Seperated Varible (*.csv)")
        epic.gaussfitsaver(str(filename),self.peaks)
        self.ui.statusbar.showMessage('Ready')
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())
