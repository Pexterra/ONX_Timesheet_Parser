import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.1
import QtQuick.Window 2.1
import QtQuick.Controls.Material 2.1
import QtQuick.Dialogs

import TimesheetParser 1.0

ApplicationWindow {
    id: page
    width: 900
    height: 600
    minimumHeight: 600
    minimumWidth: 900
    visible: true
    Material.theme: Material.Dark
    Material.accent: Material.Purple
    title: qsTr("ONX Excel Parser")

    Timesheet {
        id: timesheet
    }

    FileDialog {
        id: fileDialog
        onAccepted: {
            output.text = "something went wrong"
            timesheet.loadCSV(selectedFile)
            output.text = timesheet.getTimesheet()
            citizenSelection.model = timesheet.getPlayers()
            citizenSelection.visible = true
            citizenSelectionLabel.visible = true
        }
    }
    RowLayout {
        anchors.fill: parent
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            Layout.maximumWidth: 300
            Layout.minimumWidth: 300
            spacing: 10
            ComboBox {
                id: timezones
                Layout.leftMargin: 10
                Layout.topMargin: 10
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: parent.width
                model: ['UTC+14:00', 'UTC+13:00', 'UTC+12:45', 'UTC+12:00','UTC+11:00', 'UTC+10:30', 'UTC+10:00', 'UTC+09:30', 'UTC+09:00', 'UTC+08:45', 'UTC+08:00', 
                'UTC+07:00', 'UTC+06:30', 'UTC+06:00', 'UTC+05:45', 'UTC+05:30', 'UTC+05:00', 'UTC+04:00', 'UTC+03:30', 'UTC+03:00', 'UTC+02:00', 'UTC+01:00',
                'UTC-00:00', 'UTC-01:00', 'UTC-02:00', 'UTC-03:00', 'UTC-03:30', 'UTC-04:00', 'UTC-05:00', 'UTC-06:00', 'UTC-07:00', 'UTC-08:00', 'UTC-09:00', 
                'UTC-09:30', 'UTC-10:00', 'UTC-11:00', 'UTC-12:00' ]
                currentIndex: 22
                onActivated: {
                    timesheet.setTimezone(currentText)
                }
            }
            Button {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                text: qsTr("Load Excel file...")
                onClicked: {
                    fileDialog.open()
                }
            }
            Text {
                id: citizenSelectionLabel
                Layout.alignment: Qt.AlignHCenter
                text: 'Select Player'
                font.pixelSize: 15
                color: "pink"
                visible: false
            }
            ComboBox {
                id: citizenSelection
                Layout.leftMargin: 10
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: parent.width
                model: []
                onActivated: {
                    output.text = timesheet.getPlayerData(currentText)
                }
                visible: false
            }
        }
        Flickable {
            id: flickable
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 20

            TextArea.flickable: TextArea {
                id: output
                text: ""
                wrapMode: TextArea.Wrap
                font.letterSpacing: 1
            }

            ScrollBar.vertical: ScrollBar { }
        }
    }
}