from PyQt5.QtCore import QPointF, Qt, QVariant
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView, QApplication
from PyQt5.QtGui import QBrush, QPainter, QPen, QPixmap, QPolygonF
import sys

from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QBrush, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QGraphicsTextItem,
    QGraphicsPixmapItem,
    QCheckBox,
    QGraphicsItemGroup,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QFormLayout,
    QLineEdit,
    QInputDialog
)



class EditDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__()

        self.setWindowTitle("Edit Bounding Box")

        dlgLayout = QVBoxLayout()

        # Create a form layout and add widgets

        formLayout = QFormLayout()

        formLayout.addRow("Label:", QLineEdit())

        # Add a button box

        btnBox = QDialogButtonBox()
        deletebtn=QPushButton("Delete")
        btnBox.setStandardButtons(

            QDialogButtonBox.Ok | QDialogButtonBox.Cancel |QDialogButtonBox.Discard

        )

        # Set the layout on the dialog

        dlgLayout.addLayout(formLayout)

        dlgLayout.addWidget(btnBox)

        self.setLayout(dlgLayout)






class Window(QWidget):
    def __init__(self):
        super().__init__()

        # Defining a scene rect of 400x200, with it's origin at 0,0.
        # If we don't set this on creation, we can set it later with .setSceneRect
        # Actual resolution is 2592 x 1944
        #to-do
        #set up screen layout properly ie fixed w,h etc

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 1296, 972)
        #set up a blank pixmap as background
        pixmap = QPixmap("./image-in/AJ_LR180005.jpg")
        self.pixmapitem = self.scene.addPixmap(pixmap.scaled(1296,972))
        self.pixmapitem.setPos(0, 0)



        # Define our layout.
        vbox = QVBoxLayout()

        displaybtn = QPushButton("Display")
        displaybtn.clicked.connect(self.display_image)
        vbox.addWidget(displaybtn)

        detectbtn = QPushButton("Detect")
        detectbtn.clicked.connect(self.detect_classes)
        vbox.addWidget(detectbtn)

        drawbtn = QPushButton("Draw Box")
        drawbtn.clicked.connect(lambda: self.draw_box(95,1000,500,200,200,'Alnus',"75%"))
        vbox.addWidget(drawbtn)

        #temporary extra button so I have two stes of graphics data to manage
        draw2btn = QPushButton("Draw Box 2")
        draw2btn.clicked.connect(lambda: self.draw_box(96, 500,500,300,200, 'Tilia', "30%"))
        vbox.addWidget(draw2btn)

        editbtn = QPushButton("Edit")
        editbtn.clicked.connect(self.button_clicked)
        vbox.addWidget(editbtn)

        view = QGraphicsView(self.scene)

        hbox = QHBoxLayout(self)
        hbox.addLayout(vbox)
        hbox.addWidget(view)

        self.setLayout(hbox)

        #code to identify when a graphics item is selected
        labels=["Alnus","Lycopodium","Tilia"]
        self.scene.selectionChanged.connect(lambda:self.graphics_selected(labels))


    def display_image(self):
        #display jpeg file in pixmap
        #self.scene.pixmapitem.setPixmap("./image-in/changed_image.jpg")

        items = self.scene.items()
        for item in items:
            item.setPixmap(QPixmap("./image-in/changed_image.jpg").scaled(1296,972))
    def detect_classes(self):
        cb = QCheckBox('Auto Exposure', self)
        cb.move(80,60)
        self.scene.addItem(cb)

    def draw_box(self, numbox, x, y, h, w ,classlabel,p ):
        #input paramaters;

        #numbox - index of box within scene to allow management of related graphic items
        #x,y,h,w - position, height and width
        #classlabel - text describing class
        #p - probability returned from object detection (? if user labelled?)

        #to-do
        #   need to deal with probability when user has created box
        #   need to manage offsets of different graphic items to arrange nicely

        #create and draw bounding box
        rect = QGraphicsRectItem(x, y, w, h)
        pen = QPen(Qt.red)
        rect.setPen(pen)
        brush = QBrush(Qt.NoBrush)
        rect.setBrush(brush)
        rect.setData(0, numbox)

        #create delete icon - bottom right hand corner
        trashicon = QPixmap("./icons/trash.png")
        trashbutton = self.scene.addPixmap(trashicon)
        print(" x: ",x,"y:",y, " w:",w , "h:",h)
        print(" x icon: ", x+w-44, "y: icon", y+h-44)
        trashbutton.setPos(x+w-44, y+h-44)
        trashbutton.setData(0,numbox)
        #usrd to manage Delete/Undo icon display
        trashbutton.setData(1, True)
        trashbutton.setFlags(QGraphicsItem.ItemIsSelectable)
        print("button pos ", trashbutton.pos())

        #create class label
        classtext=QGraphicsTextItem(classlabel)
        classtext.setPos(x,y)
        classtext.setFlags( QGraphicsItem.ItemIsSelectable)

        #using classlabel to carry the data required for outputting label xmls

        classtext.setData(0, numbox)
        classtext.setData(1, classlabel)
        classtext.setData(2, x)
        classtext.setData(3, y)
        classtext.setData(4, h)
        classtext.setData(5, w)

        #displaying probability returned from object detection- - top right hand corner

        probtext=QGraphicsTextItem(p)
        probtext.setPos(x+w-60, y)
        probtext.setData(0, numbox)

        #adding all graphics items to scene

        self.scene.addItem(rect)
        self.scene.addItem(classtext)
        self.scene.addItem(probtext)



    def button_clicked(self, s):
        print("click", s)

        dlg = EditDialog(self)
        if dlg.exec():
            print("Success!")
        else:
            print("Cancel!")


    def graphics_selected(self,labels):
        print("graphics item selected")
        items = self.scene.selectedItems()
        for item in items:
            obj_type=type(item)
            ## this works#

            if obj_type==QGraphicsRectItem:
                print ("Rectangle")
            elif obj_type==QGraphicsTextItem:
                print("class label")
                print("Current selected item is: ", item.type(), " index ", item.data(0)," label ", item.data(1))
                numlabel=0;
                i=0;
                for label in labels:
                    if item.data(1)==label:
                        numlabel=i
                    i=i+1
                classlabel, ok = QInputDialog.getItem(self, "select input dialog",
                                                      "list of languages", labels, numlabel, True)
                if ok and classlabel:
                    print(classlabel)
                    # change text on box and data held with label
                    item.setPlainText(classlabel)
                    item.setData(1,classlabel)
                item.setSelected(False)

            elif obj_type == QGraphicsPixmapItem:
                print("Trash")
                allitems = self.scene.items()
                for checkitem in allitems:
                    if checkitem.data(0)==item.data(0):
                        if checkitem.isVisible():
                            checkitem.setVisible(False)
                        else:
                            checkitem.setVisible(True)
                #use flag help on pixmap to decide what icon to diplay
                if item.data(1):
                    item.setPixmap(QPixmap("./icons/untrash.png"))
                    item.setData(1,False)
                else:
                    item.setPixmap(QPixmap("./icons/trash.png"))
                    item.setData(1,True)
                item.setVisible(True)
                item.setSelected(False)

app = QApplication(sys.argv)

gui_window = Window()
gui_window.show()

app.exec()