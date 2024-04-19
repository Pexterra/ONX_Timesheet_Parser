import sys, datetime, pandas as pd
from typing import Dict

from datetime import timedelta
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine, QmlElement
from PySide6.QtQuickControls2 import QQuickStyle

QML_IMPORT_NAME = "io.qt.textproperties"
QML_IMPORT_MAJOR_VERSION = 1

class Player(object):
    def __init__(self, name):
        self.name = name
        self.loggedIn = False
        self.loggedTime = datetime.timedelta(0)
        self.logins = []
        self.logouts = []

@QmlElement
class Timesheet(QObject):
    def __init__(self):
        super().__init__()
        self.timesheetString = ""
        self.displayedPlayers = []
        self.timezone = 0

    @Slot(str)
    def loadCSV(self, file):
        xls = pd.ExcelFile(file)
        timezone = xls.parse('Actions', index_col=3, )
        df = xls.parse('Actions', skiprows=3, skipcolumns=1)
        
        playersDictionary: Dict[str, Player] = {name: Player(name) for name in df['Name'].unique()}

        for i in range(0, len(df.Action)):
            player = playersDictionary[df.Name[i]]
            if df.Action[i] == 'Check In' and player.loggedIn == False:
                player.logins.append(df.Time[i] + timedelta(hours=self.timezone))
                player.loggedIn = True
            if df.Action[i] == 'Check Out' and player.loggedIn == True:
                player.logouts.append(df.Time[i]+ timedelta(hours=self.timezone))
                player.loggedIn = False
                # If they were logged in, then logged out we can use last logout and login to calculate time without re-looping
                player.loggedTime = player.loggedTime + (player.logouts[-1] - player.logins[-1])

        self.players = sorted(playersDictionary.values(), key=lambda x: x.loggedTime, reverse=True)
        
        self.timesheetString = ""
        self.displayedPlayers = []
        
        for player in self.players:
            if player.loggedTime > datetime.timedelta(0):
                self.timesheetString += f"{str(player.loggedTime).rjust(17)}     {player.name}\n"
                self.displayedPlayers.append(player.name)

        self.displayedPlayers.append("Overview")
        self.displayedPlayers.reverse()

    @Slot(str)
    def setTimezone(self, timezone):
        self.timezone = int(timezone[-6:-3])

    @Slot(result=str)
    def getTimesheet(self):
        return self.timesheetString

    @Slot(result=list)
    def getPlayers(self):
        return self.displayedPlayers

    @Slot(str, result=str)
    def getPlayerData(self, playerSelection):
        if playerSelection == 'Overview':
            return self.timesheetString
        else:
            output = ""
            for player in self.players:
                if player.name == playerSelection:
                    output += f"{player.name} - clocked time: {str(player.loggedTime).rjust(17)}\n\n"
                    output += f"UTC{self.timezone}" + '\n'
                    for i in range(0, min(len(player.logins),len(player.logouts))):
                        output += f"in: {str(player.logins[i])}  -  out: {str(player.logouts[i])}\n"
            return output

    
if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon('./lib/images/calendar.png'))
    QQuickStyle.setStyle("Material")
    engine = QQmlApplicationEngine()

    qml_file = './lib/qml/gui.qml'
    engine.load(qml_file)

    sys.exit(app.exec())