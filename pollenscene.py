
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt,QPoint
from PyQt5.QtGui import QBrush,  QPen
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsProxyWidget,
    QGraphicsPixmapItem,
    QInputDialog
)

from database import save_labels_to_database

class LabelScene(QGraphicsScene):
    rectexists = False
    rect = QGraphicsRectItem()
    rectpos = QPoint()
    drawstatus = False

    def __init__(self):
        super().__init__()
        self.labels = []
        self.selectionChanged.connect(lambda: self.graphics_selected(self.labels))
        self.setSceneRect(0, 0, 1296, 972)


    def graphics_selected(self, labels):
        sceneview=self.views()[0]
        print(sceneview)
        items = self.selectedItems()
        for item in items:
            obj_type = type(item)

            if obj_type == QGraphicsTextItem:
                print("Current selected item is: ", item.type(), " index ", item.data(0), " label ", item.data(1))
                numlabel = 0
                i = 0
                for label in self.labels:
                    if item.data(1) == label:
                        numlabel = i
                    i = i + 1
                classlabel, ok = QInputDialog.getItem(sceneview, "select input dialog",
                                                      "list of languages", self.labels, numlabel, True)
                if ok and classlabel:
                    print(classlabel)
                    # change text on box and data held with label
                    item.setPlainText(classlabel)
                    item.setData(1, classlabel)
                item.setSelected(False)

            elif obj_type == QGraphicsPixmapItem:
                print("Trash")
                allitems = self.items()
                for checkitem in allitems:
                    if checkitem.data(0) == item.data(0):
                        if checkitem.isVisible():
                            checkitem.setVisible(False)
                        else:
                            checkitem.setVisible(True)
                # use flag help on pixmap to decide what icon to diplay
                if item.data(1):
                    item.setPixmap(QPixmap("./icons/untrash.png"))
                    item.setData(1, False)
                else:
                    item.setPixmap(QPixmap("./icons/trash.png"))
                    item.setData(1, True)
                item.setVisible(True)
                item.setSelected(False)


    def draw_mode(self,newdrawstatus):

        self.drawstatus=newdrawstatus
        sceneview = self.views()[0]
        cursor = Qt.CrossCursor
        sceneview.setCursor(cursor)

    def clear_scene(self,clear_image):
        for item in self.items():
            if not type(item)==QGraphicsProxyWidget:
                if not item.data(0)==999999:
                    self.removeItem(item)
                else:
                    if clear_image:
                        item.setPixmap(QPixmap(""))


    def save_labels(self):
        print("Save labels")
        label_data = []
        for item in self.items():
            obj_type = type(item)
            if not item.data(0)==999999 and obj_type == QGraphicsTextItem and not item.data(2)==None:
                    #need to add the current slideid and imageid
                    label_tuple=(1,1,item.data(2),item.data(3),item.data(4),item.data(5),item.data(1),item.data(6),item.data(7))
                    label_data.append(label_tuple)
        save_labels_to_database(label_data)
            #if self.settings_dict=="expert":
                #code to save image and XML
               # print("saving image and XML)")
        #set clear_image=True to clear the picture ready for another one
        self.clear_scene(True)

    def mouseReleaseEvent(self, event):
        if self.drawstatus:
            x = self.rectpos.x()
            y = self.rectpos.y()
            w = abs(self.rectpos.x() - event.scenePos().x())
            h = abs(self.rectpos.y() - event.scenePos().y())
            numbox = len(self.items()) + 1
            #replace rectangle with labelled box
            self.draw_box(numbox, x, y, h, w, "Label?", "100", "user")
            self.rect.setVisible(False)
            self.drawstatus = False
            #reset cursor and draw mode
            sceneview = self.views()[0]
            cursor = Qt.ArrowCursor
            sceneview.setCursor(cursor)

        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        if self.drawstatus:
            print("press", event.scenePos().x(), event.scenePos().y())

            self.rect.setRect(event.scenePos().x(), event.scenePos().y(), 1, 1)
            self.rectpos = event.scenePos()
            print("rectpos", self.rectpos.x(), self.rectpos.y())
            if not self.rectexists:
                self.addItem(self.rect)
                self.rectexists = True
            else:
                self.rect.setVisible(True)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawstatus:
            if self.rectexists:
                w = abs(self.rectpos.x() - event.scenePos().x())
                h = abs(self.rectpos.y() - event.scenePos().y())
                # print ("w, h ",w,h)
                self.rect.setRect(self.rectpos.x(), self.rectpos.y(), w, h)

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):

        print("double click", event.scenePos())
        super().mouseDoubleClickEvent(event)

    def draw_box(self, numbox, x, y, h, w ,classlabel,p,userflag ):
        #input paramaters;

        #numbox - index of box within scene to allow management of related graphic items
        #x,y,h,w - position, height and width
        #classlabel - text describing class
        #p - probability returned from object detection (100% if user labelled)


        #create and draw bounding box
        rect = QGraphicsRectItem(x, y, w, h)
        pen = QPen(Qt.red)
        rect.setPen(pen)
        brush = QBrush(Qt.NoBrush)
        rect.setBrush(brush)
        rect.setData(0, numbox)
        self.addItem(rect)

        #create delete icon - bottom right hand corner
        trashicon = QPixmap("./icons/trash.png")
        trashbutton = self.addPixmap(trashicon)
        trashbutton.setPos(x+w-44, y+h-44)
        trashbutton.setData(0,numbox)
        #usrd to manage Delete/Undo icon display
        trashbutton.setData(1, True)
        trashbutton.setFlags(QGraphicsItem.ItemIsSelectable)

        #create class label
        classtext=QGraphicsTextItem(classlabel)
        classtext.setPos(x,y)
        classtext.setFlags( QGraphicsItem.ItemIsSelectable)

        #using classlabel to carry the data required for outputting label xmls

        classtext.setData(0, numbox)
        classtext.setData(1, classlabel)
        classtext.setData(2, float(round(x,1)))
        classtext.setData(3, float(round(y,1)))
        classtext.setData(4, float(round(h,1)))
        classtext.setData(5, float(round(w,1)))
        classtext.setData(6, p)
        classtext.setData(7, userflag)
        self.addItem(classtext)
        #displaying probability returned from object detection- - top right hand corner

        probtext=QGraphicsTextItem(p+"%")
        probtext.setPos(x+w-60, y)
        probtext.setData(0, numbox)
        self.addItem(probtext)





