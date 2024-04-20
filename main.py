import sys, datetime, math
import pandas as pd
from typing import Dict, List

from datetime import timedelta
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine, QmlElement
from PySide6.QtQuickControls2 import QQuickStyle

QML_IMPORT_NAME = "io.qt.textproperties"
QML_IMPORT_MAJOR_VERSION = 1

class Player(object):
    def __init__(self, name: str):
        self.name = name
        self.loggedIn = False
        self.loggedTime = datetime.timedelta(0)
        self.logins: List[timedelta] = []
        self.logouts: List[timedelta] = []

@QmlElement
class Timesheet(QObject):
    def __init__(self):
        super().__init__()
        self.timesheetString = ""
        self.displayedPlayers: List[str] = []
        self.timezone = 0
        self.players: Dict[str, Player] = {}

    @Slot(str)
    def loadCSV(self, file: str) -> None:
        xls = pd.ExcelFile(file)
        df = xls.parse('Actions', skiprows=3, skipcolumns=1)

        self.players = {name: Player(name) for name in df['Name'].unique()}

        for i in range(0, len(df.Action)):
            player = self.players[df.Name[i]]
            if df.Action[i] == 'Check In' and player.loggedIn == False:
                player.logins.append(df.Time[i] + timedelta(hours=self.timezone))
                player.loggedIn = True
            if df.Action[i] == 'Check Out' and player.loggedIn == True:
                player.logouts.append(df.Time[i]+ timedelta(hours=self.timezone))
                player.loggedIn = False
                # If they were logged in, then logged out we can use last logout and login to calculate time without re-looping
                player.loggedTime = player.loggedTime + (player.logouts[-1] - player.logins[-1])

        sortedPlayers = sorted(self.players.values(), key=lambda x: x.loggedTime, reverse=True)

        self.timesheetString = ""
        self.displayedPlayers = []

        for player in sortedPlayers:
            if player.loggedTime > datetime.timedelta(0):
                self.timesheetString += self._getTimedeltaStringHM(player.loggedTime).ljust(10) + f"\t - {player.name}\n"
                self.displayedPlayers.append(player.name)

        self.displayedPlayers.append("Overview")
        self.displayedPlayers.reverse()

    @Slot(str)
    def setTimezone(self, timezone: str) -> None:
        self.timezone = int(timezone[-6:-3])

    @Slot(result=str)
    def getTimesheet(self) -> str:
        return self.timesheetString

    @Slot(result=list)
    def getPlayers(self) -> List[str]:
        return self.displayedPlayers

    @Slot(str, result=str)
    def getPlayerData(self, playerSelection: str) -> str:
        if playerSelection == 'Overview':
            return self.timesheetString
        else:
            player = self.players[playerSelection]
            output = (
                f"{player.name} - clocked time: {self._getTimedeltaStringHM(player.loggedTime)}\n\n"
                f"UTC{self.timezone}" + '\n'
            )
            for i in range(0, min(len(player.logins),len(player.logouts))):
                output += (
                    f"in: {player.logins[i]}  -  out: {player.logouts[i]}"
                    f" - {self._getTimedeltaStringHM(player.logouts[i] - player.logins[i])}\n"
                )
            return output

    def _getTimedeltaStringHM(self, delta: timedelta) -> str:
        sec = delta.total_seconds()
        hours, seconds_remaining = divmod(sec, 3600)
        minutes = math.ceil(seconds_remaining / 60)
        return(f'{hours:>5}h {minutes:02}m')

if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon('./lib/images/calendar.png'))
    QQuickStyle.setStyle("Material")
    engine = QQmlApplicationEngine()

    qml_file = './lib/qml/gui.qml'
    engine.load(qml_file)

    sys.exit(app.exec())