#version 1 user interface allows display of image, draws boxes with annotation, allows edit and delete of boxes.
# version 3 allows user to set 'mode' to add their own annotation - have to set mode each time.
# version 4 - adding object detection

import sys
import os
import shutil
from PIL import Image
import numpy as np

from classify import run_inference_for_single_image, detection_graph, category_index
from database import get_settings,save_labels_to_database

from object_detection.utils import visualization_utils as vis_util

from PyQt5.QtCore import QPointF, Qt, QVariant
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView, QApplication
from PyQt5.QtGui import QBrush, QPainter, QPen, QPixmap, QPolygonF,QImage

from PyQt5.QtCore import Qt, QVariant, QPoint
from PyQt5.QtGui import QBrush, QPainter, QPen,QCursor
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

class LabelScene(QGraphicsScene):
    rectexists = False
    rect = QGraphicsRectItem()
    rectpos=QPoint()
    drawstatus=False

    def draw_mode(self,newdrawstatus):
        print("draw mode set to  : ", newdrawstatus)
        self.drawstatus=newdrawstatus

    def clear_scene(self,clear_image):
        for item in self.items():
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
            x=self.rectpos.x()
            y=self.rectpos.y()
            w = abs(self.rectpos.x() - event.scenePos().x())
            h = abs(self.rectpos.y() - event.scenePos().y())
            numbox=len(self.items())+1
            self.draw_box(numbox,x,y,h,w,"Label?","100","user")
            self.rect.setVisible(False)
            #call draw_box here
            print("putting a labelled box where the rectangle was")
            self.drawstatus=False

        print("release ",event.scenePos())
        super().mouseReleaseEvent(event)


    def mousePressEvent(self, event):
        if self.drawstatus:
            print("press", event.scenePos().x(),event.scenePos().y())

            self.rect.setRect(event.scenePos().x(),event.scenePos().y(),1,1)
            self.rectpos=event.scenePos()
            print("rectpos", self.rectpos.x(), self.rectpos.y())
            if not self.rectexists:
                self.addItem(self.rect)
                self.rectexists=True
            else:
                self.rect.setVisible(True)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawstatus:
            if self.rectexists:
                w=abs(self.rectpos.x()-event.scenePos().x())
                h=abs(self.rectpos.y()-event.scenePos().y())
                #print ("w, h ",w,h)
                self.rect.setRect(self.rectpos.x(), self.rectpos.y(), w ,h)

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):

        print("double click", event.scenePos())
        super().mouseDoubleClickEvent(event)

    def draw_box(self, numbox, x, y, h, w ,classlabel,p,userflag ):
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
        trashbutton = self.addPixmap(trashicon)
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
        classtext.setData(2, float(round(x,1)))
        classtext.setData(3, float(round(y,1)))
        classtext.setData(4, float(round(h,1)))
        classtext.setData(5, float(round(w,1)))
        classtext.setData(6, p)
        classtext.setData(7, userflag)

        #displaying probability returned from object detection- - top right hand corner

        probtext=QGraphicsTextItem(p+"%")
        probtext.setPos(x+w-60, y)
        probtext.setData(0, numbox)

        #adding all graphics items to scene

        self.addItem(rect)
        self.addItem(classtext)
        self.addItem(probtext)

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

        #get settigns from database
        settings_dict=get_settings()
        print ("In window",settings_dict)

        # Defining a scene rect of 400x200, with it's origin at 0,0.
        # If we don't set this on creation, we can set it later with .setSceneRect
        # Actual resolution is 2592 x 1944
        #to-do
        #set up screen layout properly ie fixed w,h etc

        self.scene = LabelScene()
        self.scene.setSceneRect(0, 0, 1296, 972)
        #set up a blank pixmap as background
        pixmap = QPixmap("")
        self.pixmapitem = self.scene.addPixmap(pixmap.scaled(1296,972))
        self.pixmapitem.setPos(0, 0)
        self.pixmapitem.setData(0,999999)

        self.output_dict={}

        # Define our layout.
        vbox = QVBoxLayout()

        displaybtn = QPushButton("Load Image")
        displaybtn.clicked.connect(self.display_image)
        vbox.addWidget(displaybtn)

        detectbtn = QPushButton("Classify")
        detectbtn.clicked.connect(self.run_object_detection)
        vbox.addWidget(detectbtn)

        modebtn = QPushButton("Add Labels")
        modebtn.clicked.connect(lambda: self.scene.draw_mode(True))
        vbox.addWidget(modebtn)

        drawbtn = QPushButton("Save")
        drawbtn.clicked.connect(lambda: self.scene.save_labels())
        vbox.addWidget(drawbtn)

        #temporary extra button so I have two stes of graphics data to manage
        draw2btn = QPushButton("Draw Box 2")
        draw2btn.clicked.connect(lambda: self.scene.draw_box(96, 65,221,98,271, 'Tilia', "30%"))
        vbox.addWidget(draw2btn)


        view = QGraphicsView(self.scene)

        hbox = QHBoxLayout(self)
        hbox.addLayout(vbox)
        hbox.addWidget(view)

        self.setLayout(hbox)

        #code to identify when a graphics item is selected
        labels=["Alnus","Lycopodium","Tilia"]
        self.scene.selectionChanged.connect(lambda:self.graphics_selected(labels))


    def display_image(self):
    #checks in ./image-in for a file - if one exists displays it and deletes the file
        items = self.scene.items()
        for item in items:
            if item.data(0)==999999:
                filelist = os.listdir("./image-in/")
                for filename in filelist:
                    srcpath="./image-in/"+filename
                    dstpath="./working_image.jpg"
                    print("src path",srcpath, "dstpath", dstpath)
                    item.setPixmap(QPixmap(srcpath).scaled(1296,972))
                    shutil.copy(srcpath, dstpath)
                    os.remove(srcpath)

    def detect_classes(self):
        print("detecting")


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

    def load_image_into_numpy_array(self,image):
        (im_width, im_height) = image.size
        return np.stack((np.array(image.getdata()),) * 3, axis=-1).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

    def run_object_detection(self):
        self.scene.clear_scene(False)

    # check its an image file - this is temp code to be replaced when hook up to microscope direct
        image = Image.open('./working_image.jpg')

    # required image size
        size = (416, 312)

    # the array based representation of the image will be used later in order to prepare the
    # result image with boxes and labels on it. Image is converted to grayscale and resized to size to
    # match images used to train model and reduce processing
        self.pre_image=image.convert('L').resize(size)
        print("Initial array shape ", self.pre_image.size)
        self.image_np = self.load_image_into_numpy_array(self.pre_image)
        print("Array shape ", self.image_np.size)
# Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(self.image_np, axis=0)
# Actual detection.
        output_dict = run_inference_for_single_image(self.image_np, detection_graph)
# Visualization of the results of a detection.
        vis_util.visualize_boxes_and_labels_on_image_array(
            self.image_np,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            category_index,
            instance_masks=output_dict.get('detection_masks'),
            use_normalized_coordinates=True,
            line_thickness=8)

        boxes = np.squeeze(output_dict['detection_boxes'])
        scores = np.squeeze(output_dict['detection_scores'])
        classes=np.squeeze(output_dict['detection_classes'])
        # set a min thresh score, say 0.8
        min_score_thresh = 0.8
        bboxes = boxes[scores > min_score_thresh]
        # get image size
        im_width=self.scene.width()
        im_height=self.scene.height()
        final_box = []
        for box in bboxes:
            ymin, xmin, ymax, xmax = box
            final_box.append([xmin * im_width, xmax * im_width, ymin * im_height, ymax * im_height])
        i = 0

        for box in final_box:
            #print("label",category_index[classes[i]]["name"])
            #print ("index",i,"x ",box[0],"y",box[2],"w",box[1]-box[0],"h" ,box[3]-box[2],"class",classes[i],"p",scores[i])
            self.scene.draw_box(i, box[0], box[2], box[3] - box[2], box[1] - box[0],category_index[classes[i]]["name"],str(round(scores[i] * 100)),"model")
            i=i+1

app = QApplication(sys.argv)

#cursor change code - leave as a bug for now
#drawstatus=True
#if drawstatus:
   # app.setOverrideCursor(QCursor(Qt.CrossCursor))
#else:
   #app.setOverrideCursor(QCursor(Qt.ArrowCursor))

gui_window = Window()
gui_window.show()

app.exec()