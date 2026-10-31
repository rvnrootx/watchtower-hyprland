import QtQuick
import Quickshell

import "services"
ShellRoot {
    ThemeService {
        id: themeService
    }

    Variants {
        model: Quickshell.screens

        PanelWindow {
            required property var modelData

            screen: modelData
            anchors {
                top: true
                left: true
            }

            implicitWidth: 460
            implicitHeight: 120
            color: "transparent"

            Rectangle {
                anchors.fill: parent
                anchors.margins: 12

                radius: themeService.shape.radius
                color: themeService.color("surface")
                border.color: themeService.color("border")
                border.width: themeService.shape.border_width

                Column {
                    anchors.centerIn: parent
                    spacing: 8

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "WATCHTOWER THEME SERVICE"
                        color: themeService.color("foreground")
                        font.pixelSize: 13
                        font.bold: true
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Active: " + themeService.activeTheme
                        color: themeService.color("accent")
                        font.pixelSize: 12
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: themeService.ready
                            ? "Theme loaded successfully"
                            : themeService.loadError || "Waiting for theme..."
                        color: themeService.color("secondary")
                        font.pixelSize: 10
                    }
                }
            }
        }
    }
}
