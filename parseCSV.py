
import sys
import pandas as pd
from datetime import datetime, timedelta
import pprint

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection

import numpy as np

# CLASSES & FUNCTIONS
class Character(object):
    def __init__(self, name):
        self.name = name
        self.loggedIn: bool = False
        self.loggedTime: float = 0     # units: hours
        self.logins  : list = []
        self.logouts : list = []
        self.strangeness: dict = {'crashes': [],
                                  'pre'    : [],
                                  'post'   : [],
                                  'other'  : []}
        self.shift1Time: float = 0
        self.shift2Time: float = 0
        self.shift3Time: float = 0

class Timesheet():
    def __init__(self):
        self.timesheetString = ""
        self.displayedCharacters = []
        #self.timezone  = 0
        self.firsttime = 0
        self.lasttime  = 0

    def loadCSV(self, file):
        self.timesheetString = ""
        self.displayedCharacters = []

        # load excel file
        xls = pd.ExcelFile(file)
        # then parse it:
        # 'Actions' is the sheet name
        # Data headers happen on row 3
        # column 1 is Time data from unknown timezones, so skip it
        df = xls.parse('Actions', skiprows=3, skipcolumns=1)
        # not used?
        #timezone = xls.parse('Actions', index_col=3, )

        # get first and last times
        self.firsttime = df['Time'].min()
        self.lasttime = df['Time'].max()

        # hardcoded shift values
        boundaries = [pd.Timedelta(i,'h') for i in [-15,-7,1,9,17,25,33]]
        nShifts = len(boundaries)-1
        unit = pd.Timedelta(1,'h')

        # get character names
        chars = list(set(df.Name))
        # create the character objects
        self.characters : [Character] = []
        for name in chars:
            self.characters.append(Character(name))

        for character in self.characters:
            chardf = df[df.Name == character.name]
            for index, row in chardf.iterrows():
                # normal check in action
                if row.Action == 'Check In' and not character.loggedIn:
                    character.logins.append(row.Time)
                    character.loggedIn = True
                
                # normal check out action
                elif row.Action == 'Check Out' and character.loggedIn:
                    character.logouts.append(row.Time)
                    character.loggedIn = False
                
                # capture instance where the player checks in while already
                # checked in; likely happening when a crash happens
                elif row.Action == 'Check In' and character.loggedIn:
                    character.strangeness['crashes'].append([index,row])

                # capture instances where the player checked in _before_ the 
                # time period of the CSV
                elif row.Action == 'Check Out' and not character.loggedIn:
                    character.strangeness['pre'].append([index,row])

                # other instances. 
                else:
                    character.strangeness['other'].append([index, 
                                                           self.loggedIn, 
                                                           row])

            # having looped over all events, check if they remain logged in; if
            # so, then add to the log of strangeness
            if character.loggedIn:
                character.strangeness['post'].append([index,row])
        
        ## Prex's original code. No serious changes were made. Just better 
        ## gathering/logging of the weird situations.
        #for i in range(0, len(df.Action)):
        #    for character in self.characters:
        #        if df.Name[i] == character.name:
        #            if df.Action[i] == 'Check In' and character.loggedIn == False:
        #                character.logins.append(df.Time[i] + timedelta(hours=self.timezone))
        #                character.loggedIn = True
        #                break
        #            if df.Action[i] == 'Check Out' and character.loggedIn == True:
        #                character.logouts.append(df.Time[i]+ timedelta(hours=self.timezone))
        #                character.loggedIn = False
        #                break

        # loop over all characters
        for character in self.characters:
            # loop over all shifts (aka a pair of login and logout events)
            for i in range(0, min(len(character.logins),len(character.logouts))):
                # handling total time worked during this shift
                # calculate the dT in units of seconds
                timeworked = character.logouts[i].timestamp() - character.logins[i].timestamp()
                # out of paranoia, make sure we don't have any mismatches
                if timeworked < 0:
                    print(f'{character.name} has a mismatched check in/out pair. printing whole timesheeet')
                    pprint.pp(df[df.Name == character.name])
                    break
                else:
                    # add timeworked with units of hours
                    character.loggedTime += timeworked/60/60

                # handling time worked per EST shift times
                # followed code from:
                # https://stackoverflow.com/questions/73997481/calculate-working-hours-time-python-pandas-hours-worked-total-hours-worked
                start_of_day = character.logins[i].normalize()
                work_time = [0] * nShifts
                for j, (lb, ub) in enumerate(zip(boundaries[:-1],boundaries[1:])):
                    shift_st = start_of_day + lb
                    shift_et = start_of_day + ub
                    t = (min(character.logouts[i], shift_et)
                          - max(character.logins[i], shift_st)) / unit
                    work_time[j] = max(0,t)
                
                # add this login/logout event to shift counters
                if not np.isclose(0,np.abs(np.sum(work_time)-timeworked/60/60.),rtol=1e-3):
                    print(timeworked/60/60, np.sum(work_time), character.name, character.logins[i], character.logouts[i])

                character.shift1Time += work_time[0] # Shift 1 is 9 AM to 5 PM
                character.shift2Time += work_time[1] # shift 2 is 5 AM to 1 AM
                character.shift3Time += work_time[2] # shift 3 is 1 AM to 9 AM
                character.shift1Time += work_time[3] # Shift 1 is 9 AM to 5 PM
                character.shift2Time += work_time[4] # Shift 2 is 5 PM to 1 AM
                character.shift3Time += work_time[5] # shift 3 is 1 AM to 9 AM

        self.characters.sort(key=lambda x: x.loggedTime, reverse=True)
        for character in self.characters:
            if character.loggedTime > 0:
                self.timesheetString +=  f"{character.loggedTime:17.2f}     {character.name}\n"
                self.displayedCharacters.append(character.name)
            else:
                print(character.name, 'has negative loggedTime hours')

        self.displayedCharacters.sort()
        self.displayedCharacters.insert(0, "Overview")

    #def setTimezone(self, timezone):
    #    self.timezone = int(timezone[-6:-3])

    def getTimesheet(self):
        return self.timesheetString

    def getCharacters(self):
        return self.displayedCharacters

    def getCharacterData(self, characterSelection):
        if characterSelection == 'Overview':
            return self.timesheetString
        else:
            output = ""
            for character in self.characters:
                if character.name == characterSelection:
                    output += "{} - clocked time: {}".format(character.name, str(character.loggedTime).rjust(17)) + '\n\n'
                    #output += f"UTC{self.timezone}" + '\n'
                    for i in range(0, min(len(character.logins),len(character.logouts))):
                        output +=  "in: {}  -  out: {}".format(str(character.logins[i]),str(character.logouts[i])) + '\n'
            return output

    def createGanttChart(self, 
                         fig_name = 'gantt_chart.png', 
                         ylim = (-0.1,10.1)):
        """
        """
        figure = plt.figure(figsize=(16,8))
        ax = plt.gca()
        begTime = self.firsttime.timestamp()
        endTime = self.lasttime.timestamp() - begTime

        ax.plot([0,0],[-1,len(self.characters)+1], 'r-', zorder=3)
        ax.plot([endTime,endTime],[-1,len(self.characters)+1], 'r-', zorder=3)

        # loop over all characters
        for i, character in enumerate(self.characters[::-1]):
            # get the name
            name = character.name
            # get the facecolor to draw the rectangles with
            drawColor = list(mpl.colors.XKCD_COLORS.keys())[2**i % 949]
            # loop over all paired events
            for j in range(0,min(len(character.logins),len(character.logouts))):
                # get epoch times for the log in/out event
                st = character.logins[j].timestamp()
                et = character.logouts[j].timestamp()
                # create the rectangle drawing object
                rect = Rectangle((st - begTime, i + 0.1), # (x,y)
                                 (et - st),               # width
                                 0.8,                     # height
                                 facecolor=drawColor,
                                 alpha=0.75,
                                 edgecolor='xkcd:black',
                                 zorder=3)
                # add rectangle object to the canvas
                ax.add_patch(rect)

        # setting y-axis ticks and labels
        ax.set_yticks(np.arange(len(self.characters))+0.5,
                        [character.name for character in self.characters[::-1]])
        ax.set_ylim(ylim)

        # process to get x-axis ticks and labels
        startDate = self.firsttime.date()
        endDate =   self.lasttime.date()
        delta = endDate - startDate
        days = [startDate+timedelta(days=i) for i in range(delta.days + 1)]
        midnights = [int(datetime.combine(day, datetime.min.time()).strftime('%s'))
                         - begTime for day in days]
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%m-%d'))
        ax.set_xticks(midnights, labels = days)
        ax.tick_params(axis='x',pad = -1.)
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=-45,horizontalalignment='left',size='small')
        ax.set_xlim((-endTime*0.01, endTime*1.01))

        # add grid lines for aiding the eye
        plt.grid(axis='y',visible=True,which='major',
                 color='#808080',linestyle='--',alpha=0.75,zorder=1)
        plt.grid(axis='x',visible=True,which='major',
                 color='#808080',linestyle='--',alpha=0.75,zorder=1)

        plt.tight_layout()
        plt.savefig(fig_name, dpi = 300, transparent = True)


# MAIN
if __name__ == '__main__':
    csv_file = sys.argv[1]
    timesheet = Timesheet()
    timesheet.loadCSV(csv_file)
    #print(timesheet.getCharacterData('Overview'))
    with open(csv_file.split('.')[0] + '_overview.csv','w') as outcsv:
        outcsv.write('Name,Time Worked (hrs),Shift 1 (hrs),Shift 2 (hrs),Shift 3 (hrs)\n')
        for character in timesheet.characters:
            outcsv.write(f"{character.name},{character.loggedTime},{character.shift1Time},{character.shift2Time},{character.shift3Time}\n")
#
#
#        for line in timesheet.getCharacterData('Overview').split('\n'):
#            if line.split():
#                temp = line.strip()
#                outcsv.write(f"{temp.split('  ')[-1]},{temp.split('  ')[0]}\n")
#    
    timesheet.createGanttChart(fig_name = csv_file.split('.')[0] 
                                                + '_ganttchart.png',
                               ylim = (-0.1, len(timesheet.characters)+0.1))
#                               ylim = (len(timesheet.characters)-50.1, 
#                                       len(timesheet.characters))
#                               )

