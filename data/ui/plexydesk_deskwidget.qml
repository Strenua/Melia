import Qt 4.7

import "plexydesk_deskwidget_scripts.js" as Scripts

Rectangle {
    id: mainwin
    width: 1000
    height: 650    
    
    Rectangle {
        id: mediaapps
        color: "blue"  
        anchors.leftMargin: 0
        anchors.topMargin: 0
        border.color: "black"
        border.width: 2
        width: 300
        height: 300
        radius: 5
        //anchors.Left: parent.Left
        //anchors.Top: parent.Top
        
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: Scripts.onEnteredDo(mediaapps)
            onExited: Scripts.onExitedDo(mediaapps)
            onClicked: Scripts.buttonClicked(mainwin,mediaapps)
        }
        Text {
            text: "Media Apps"
            color: "#fff"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Rectangle {
        id: internetapps
        color: "blue"  
        anchors.left: mediaapps.right
        anchors.topMargin: 0
        anchors.leftMargin: 10
        border.color: "black"
        border.width: 2
        width: 300
        height: 300
        radius: 5
        
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: Scripts.onEnteredDo(internetapps)
            onExited: Scripts.onExitedDo(internetapps)
            onClicked: Scripts.buttonClicked(mainwin,internetapps)
        }
        Text {
            text: "Internet Apps"
            color: "#fff"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
