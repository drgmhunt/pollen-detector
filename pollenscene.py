
import shutil

from lxml import etree
import codecs

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt,QPoint
from PyQt5.QtGui import QBrush,  QPen,QImage
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsProxyWidget,
    QGraphicsPixmapItem,
    QInputDialog
)

from database import save_labels_to_database,delete_saved_labels_from_database,save_image_to_database,update_image_filename,connect_saved_model_labels_to_image


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

        items = self.selectedItems()
        for item in items:
            obj_type = type(item)

            if obj_type == QGraphicsTextItem:
                #print("Current selected item is: ", item.type(), " index ", item.data(0), " label ", item.data(1))
                numlabel = 0
                i = 0
                for label in self.labels:
                    if item.data(1) == label:
                        numlabel = i
                    i = i + 1
                classlabel, ok = QInputDialog.getItem(sceneview, "Change Species",
                                                      "Species List", self.labels, numlabel, True)
                if ok and classlabel:
                    # change text on box and data held with label
                    item.setPlainText(classlabel)
                    item.setData(1, classlabel)
                    if  classlabel not in self.labels:
                        self.labels.append(classlabel)
                item.setSelected(False)

            elif obj_type == QGraphicsPixmapItem:
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
        self.rectexists = False

    def save_labels(self,slideid,usertype,fileprefix):
        label_data = []
        if usertype=='user':
            image_path, imageid = save_image_to_database(slideid,fileprefix)
            update_image_filename(imageid,image_path)
        else:
            imageid=0

        bbox_string=""
        for item in self.items():
            obj_type = type(item)
            if not item.data(0)==999999 and obj_type == QGraphicsTextItem and not item.data(2)==None:
                    #need to add the current slideid and imageid
                    #ignore deleted items
                    if item.isVisible():
                        label_tuple=(slideid,imageid,2*item.data(2),2*item.data(3),2*item.data(4),2*item.data(5),item.data(1),item.data(6),usertype)
                        label_data.append(label_tuple)
                        bbox_string=bbox_string+self.bbox_xml(item)

        delete_saved_labels_from_database(imageid,slideid, usertype)
        save_labels_to_database(slideid,label_data)

        if usertype=="user":
            self.clear_scene(True)
            self.save_image_to_file(slideid, image_path)
            connect_saved_model_labels_to_image(slideid,imageid)

            raw_image_path = r"{}".format(image_path)
            y = raw_image_path.split("\\")
            xml_filepath = raw_image_path.replace("jpg", "xml")
            annot_str="<annotation><folder>" +y[len(y) - 2]+ "</folder><filename> " +y[len(y) - 1]+ " </filename>"
            path_str="<path> " +image_path+" </path><source><database> Unknown </database> </source>"
            size_str= "<size><width> 2592 </width><height> 1944 </height><depth> 3 </depth ></size><segmented> 0 </segmented>"

            full_xml=annot_str+path_str+size_str+bbox_string+'</annotation> '
            self.write_xml(full_xml, xml_filepath)




    def save_image_to_file(self,slideid,image_path):
        srcpath = "./working_image.jpg"
        shutil.copy(srcpath, image_path)

    def bbox_xml(self,item):

        obj_header="<object><name>"+item.data(1)+"</name>"
        obj_other="<pose> Unspecified </pose><truncated> 0 </truncated><difficult> 0 </difficult>"
        xminstr="<bndbox><xmin>"+str(2*item.data(2))+"</xmin>"
        yminstr = "<ymin>" + str(2*item.data(3)) + "</ymin>"
        xmaxstr = "<xmax>" + str(2*(item.data(2)+item.data(5))) + "</xmax>"
        ymaxstr = "<ymax>" + str(2*(item.data(3)+item.data(4))) + "</ymax></bndbox>"
        return obj_header+obj_other+xminstr+yminstr+xmaxstr+ymaxstr+"</object>"

    def write_xml(self, full_xml,xml_filepath):

        out_file = codecs.open('temp.xml', 'w', encoding='utf8')
        out_file.write(full_xml)
        out_file.close()
        tree = etree.parse("temp.xml")
        pretty = etree.tostring(tree, encoding="unicode", pretty_print=True)
        # write to xml file in output folder
        out_file = codecs.open(xml_filepath, 'w', encoding='utf8')
        out_file.write(pretty)
        out_file.close()

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
            self.rect.setRect(event.scenePos().x(), event.scenePos().y(), 1, 1)
            self.rectpos = event.scenePos()
            if not self.rectexists:
                self.rect =QGraphicsRectItem()
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
                self.rect.setRect(self.rectpos.x(), self.rectpos.y(), w, h)

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):


        super().mouseDoubleClickEvent(event)

    def draw_box(self, numbox, x, y, h, w ,classlabel,p,userflag ):
        #input paramaters;

        #numbox - index of box within scene to allow management of related graphic items
        #x,y,h,w - position, height and width
        #classlabel - text describing class
        #p - probability returned from object detection (100% if user labelled)


        #create and draw bounding box
        rect = QGraphicsRectItem(x, y, w, h)
        pen = QPen(Qt.black)
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



