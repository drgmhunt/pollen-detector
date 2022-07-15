#version 1 user interface allows display of image, draws boxes with annotation, allows edit and delete of boxes.
# version 3 allows user to set 'mode' to add their own annotation - have to set mode each time.
# version 4 - restructures GUI and code to perform same functions as v3 but in a more organised layout
# todo: add databse edit/view facilities for settings, samples etc

import sys,os, shutil
from PIL import Image
import numpy as np
#imports needed for object detection

import tensorflow._api.v2.compat.v1 as tf
tf.disable_v2_behavior()

from object_detection.utils import visualization_utils as vis_util

from PyQt5.QtCore import  QSize
from PyQt5.QtGui import QIcon,QKeySequence,QImageWriter,QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QAction,
    QStatusBar,
    QToolBar,
    QMessageBox
)

#modified version of qt.py from http://www.touptek.com/download/showdownload.php?lang=en&id=32
#displays feed from camera - clicking the Save button saves the feed as a bmp file

from camera import CameraWin
from pollenscene import LabelScene
from database import get_model_settings,save_labels_to_database,SampleWindow,SettingsWindow,ProgressWidget,get_progress_data
from classify import run_inference_for_single_image, setup_model


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pollen Detection Prototype")

        # get settings from database
        settings_dict = get_model_settings()
        #setup model for detection based on settings


        self.detection_graph=setup_model(self,settings_dict["modelfile"],settings_dict["labelmapfile"])


        #set up actions for toolbar,menu and buttons

        edit_settings = QAction(QIcon("./icons/settings.png"), "&Settings", self)
        edit_settings.setStatusTip("Change model and target count settings")
        edit_settings.triggered.connect(self.onEditSettingsButtonClick)

        load_image_action = QAction(QIcon("./icons/load.png"), "&Load Image", self)
        load_image_action.setStatusTip("Load new image file")
        load_image_action.triggered.connect(self.onLoadImageButtonClick)
        load_image_action.setShortcut(QKeySequence("Ctrl+f"))

        use_live_feed=QAction(QIcon("./icons/microscope.png"), "&Live Feed", self)
        use_live_feed.setStatusTip("Switch to live feed from microscope")
        use_live_feed.triggered.connect(self.onLiveFeedClick)
        use_live_feed.setCheckable(True)

        classify_image_action=QAction(QIcon("./icons/robot.png"), "&Classify Image", self)
        classify_image_action.setStatusTip("USe model to classify pollen")
        classify_image_action.triggered.connect(self.onClassifyImageButtonClick)
        classify_image_action.setShortcut(QKeySequence("Ctrl+c"))

        label_image_action=QAction(QIcon("./icons/label.png"), "&Label Image", self)
        label_image_action.setStatusTip("Add labels to image")
        label_image_action.triggered.connect(self.onLabelImageButtonClick)
        label_image_action.setShortcut(QKeySequence("Ctrl+l"))
        #label_image_action.setCheckable(True)

        show_progress_action=QAction(QIcon("./icons/bar.png"), "&View Progress", self)
        show_progress_action.setStatusTip("Show progress of pollen count")
        show_progress_action.triggered.connect(self.onDisplayProgressButtonClick)
        show_progress_action.setShortcut(QKeySequence("Ctrl+p"))

        sample_slide_action=QAction(QIcon("./icons/slide.png"), "&Choose Slide", self)
        sample_slide_action.setStatusTip("Current sample details")
        sample_slide_action.triggered.connect(self.onEditSampleButtonClick)


        save_labels_action = QAction(QIcon("./icons/save.png"), "&Save Labels", self)
        save_labels_action.setStatusTip("Save labels from current screen")
        save_labels_action.triggered.connect(self.onSaveLabelsButtonClick)
        save_labels_action.setShortcut(QKeySequence("Ctrl+s"))

        save_as_VOC=QAction("&VOC",self)
        save_as_TF = QAction("&TF", self)
        save_as_Tilia = QAction("&Tilia", self)
        help_how_to = QAction("&How to", self)
        help_about = QAction("&About", self)


# set up toolbar

        toolbar = QToolBar("Main toolbar")
        toolbar.setIconSize(QSize(44, 44))
        self.addToolBar(toolbar)

        toolbar.addAction(edit_settings)
        toolbar.addAction(load_image_action)
        toolbar.addAction(use_live_feed)
        toolbar.addAction(classify_image_action)
        toolbar.addAction(label_image_action)

        toolbar.addAction(save_labels_action)
        toolbar.addSeparator()
        toolbar.addAction(show_progress_action)
        toolbar.addAction(sample_slide_action)

        #create status bar
        self.setStatusBar(QStatusBar(self))

        #set up menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(edit_settings)
        file_menu.addSeparator()
        file_submenu = file_menu.addMenu("Export")
        file_submenu.addAction(save_as_VOC)
        file_submenu.addAction(save_as_TF)
        file_submenu.addAction(save_as_Tilia)

        file_menu = menu.addMenu("&Action")
        file_menu.addAction(load_image_action)
        file_menu.addAction(use_live_feed)
        file_menu.addAction(classify_image_action)
        file_menu.addAction(label_image_action)
        file_menu.addAction(save_labels_action)


        file_menu = menu.addMenu("&Slide")
        file_menu.addAction(sample_slide_action)
        file_menu.addAction(show_progress_action)

        file_menu = menu.addMenu("&Help")
        file_menu.addAction(help_how_to)
        file_menu.addAction(help_about)

        #set up layout

        vbox = QVBoxLayout()

        self.progresswidget=ProgressWidget()
        self.update_progress(settings_dict["current_slide"])
        vbox.addWidget(self.progresswidget)
        displaybtn = QPushButton("Load Image")
        displaybtn.clicked.connect(load_image_action.trigger)
        vbox.addWidget(displaybtn)
        classifybtn = QPushButton("Classify")
        classifybtn.clicked.connect(classify_image_action.trigger)
        vbox.addWidget(classifybtn)
        modebtn = QPushButton("Add Labels")
        #modebtn.setCheckable(True)
        modebtn.clicked.connect( label_image_action.trigger)
        vbox.addWidget(modebtn)
        savebtn = QPushButton("Save")
        savebtn.clicked.connect(save_labels_action.trigger)
        vbox.addWidget(savebtn)



        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        self.scene = LabelScene()

        labels=[]
        print(self.category_index)
        for labelkey in self.category_index:
            labels.append(self.category_index[labelkey]["name"])
        self.scene.labels=labels

        view = QGraphicsView(self.scene)

        self.camwin = CameraWin()
        self.camwin.setVisible(False)
        self.scene.addWidget(self.camwin)

        # set up a blank pixmap to hold an image file
        pixmap = QPixmap("")
        self.pixmapitem = self.scene.addPixmap(pixmap.scaled(1296, 972))
        self.pixmapitem.setPos(0, 0)
        self.pixmapitem.setData(0, 999999)

        hbox.addWidget(view)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_widget.setLayout(hbox)

    def onEditSettingsButtonClick(self, s):
        print("edit settings", s)
        self.w = SettingsWindow()
        self.w.show()



    def onLoadImageButtonClick(self, s):

        #looks in folder for files, loads the first one it finds, deletes it and copies to the working file
        self.scene.clear_scene(True)
        filelist = os.listdir("./image-in/")
        i=1
        for filename in filelist:
            if i==1:
                srcpath="./image-in/"+filename
                dstpath="./working_image.jpg"
                self.pixmapitem.setPixmap(QPixmap(srcpath).scaled(1296,972))
                self.pixmapitem.setVisible(True)
                shutil.copy(srcpath, dstpath)
                os.remove(srcpath)
            i=i+1

    def onClassifyImageButtonClick(self, s):
        print("classify image", s)
        print(QImageWriter.supportedImageFormats())
        if self.camwin.label.isVisible():
            self.camwin.label.pixmap().save("./working_image.jpg","JPEG")
        settings_dict = get_model_settings()
        self.detection_graph = setup_model(self, settings_dict["modelfile"], settings_dict["labelmapfile"])
        self.run_object_detection()

    def onLabelImageButtonClick(self, s):
        print("label image", s)
        #put in draw mode when checked, turn off when unchecked
        #self.scene.draw_mode(s)
        #change of plan - button/action sets draw to true. turned off after box drawn
        self.scene.draw_mode(True)

    def onDisplayProgressButtonClick(self, s):
        print("show progress", s)

        self.w =ProgressWidget()
        self.w.show()

    def onEditSampleButtonClick(self, s):
        print("edit sample", s)
        settings_dict = get_model_settings()
        self.w = SampleWindow(settings_dict["current_slide"])
        self.w.show()
        settings_dict = get_model_settings()
        self.update_progress(settings_dict["current_slide"])

    def onSaveLabelsButtonClick(self, s):
        print("save labels", s)
        settings_dict = get_model_settings()
        self.scene.save_labels(settings_dict["current_slide"])
        self.update_progress(settings_dict["current_slide"])

    def onCancelLabelsButtonClick(self, s):
        print("cancel labels", s)

    def onLiveFeedClick(self, s):
        #make live feed visible or invisible
        self.scene.clear_scene(False)
        if self.camwin.label.isVisible():
            self.camwin.setVisible(False)
            self.pixmapitem.setVisible(True)
        else:
            self.camwin.setVisible(True)
            self.pixmapitem.setVisible(False)

    def update_progress(self,slideid):
        progress_dict = get_progress_data(slideid)

        self.progresswidget.slide_reference.setText(progress_dict["sample"] + ":" + progress_dict["slide_reference"])
        self.progresswidget.progress_bar.setRange(0,progress_dict["target_count"])

        if progress_dict["current_count"]>= progress_dict["target_count"]:
            button = QMessageBox.information(self, "Target Count", "Pollen Target Count Reached for "+progress_dict["sample"] + ":" + progress_dict["slide_reference"])
            self.progresswidget.progress_bar.setValue(progress_dict["target_count"])
        else:
            self.progresswidget.progress_bar.setValue(progress_dict["current_count"])

    def load_image_into_numpy_array(self,image):
        (im_width, im_height) = image.size
        return np.stack((np.array(image.getdata()),) * 3, axis=-1).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

    def run_object_detection(self):
        self.scene.clear_scene(False)

    # load image file - microscope feed functionality copies feed to the same file
        image = Image.open('./working_image.jpg')

    # required image size for model
        size = (416, 312)

    # the array based representation of the image will be used later in order to prepare the
    # result image with boxes and labels on it. Image is converted to grayscale and resized to size to
    # match images used to train model and reduce processing
        self.pre_image=image.convert('L').resize(size)
        self.image_np = self.load_image_into_numpy_array(self.pre_image)
# Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(self.image_np, axis=0)
# Actual detection.
        output_dict = run_inference_for_single_image(self.image_np, self.detection_graph)
# Visualization of the results of a detection.
        vis_util.visualize_boxes_and_labels_on_image_array(
            self.image_np,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            self.category_index,
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
            self.scene.draw_box(i, box[0], box[2], box[3] - box[2], box[1] - box[0],self.category_index[classes[i]]["name"],str(round(scores[i] * 100)),"model")
            i=i+1

        if i <1:
            button = QMessageBox.information(self, "Object Detection", "No objects detected")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
