#version 1
#displays a fixed inout file and runs object detection model
#result is a BW image with boxes
#also incldue test custom object as step towards clickable boxes

#imports needed for object detection
import tensorflow._api.v2.compat.v1 as tf
tf.disable_v2_behavior()
import sys
import numpy as np
from PIL import Image
import numpy as np
import os
import six.moves.urllib as urllib
import tarfile
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

# This is needed since the notebook is stored in the object_detection folder.
sys.path.append("..")
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

PATH_TO_LABELS='models/UK-pollen-plus-Lycopodium_label_map.pbtxt'
PATH_TO_CKPT='models/UK-pollen-plus-Lycopodium-graph.pb'

#GUI required imports

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel,QVBoxLayout,QWidget,QGridLayout,QLineEdit
from PyQt5.QtGui import QPixmap,QImage

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')


label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(
    label_map, max_num_classes=90, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)


def run_inference_for_single_image(image, graph):
    with graph.as_default():
        with tf.Session() as sess:
            # Get handles to input and output tensors
            print ("running inference for image")
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {
                output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in [
                'num_detections', 'detection_boxes', 'detection_scores',
                'detection_classes', 'detection_masks'
            ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                        tensor_name)
            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(
                    tensor_dict['detection_boxes'], [0])
                detection_masks = tf.squeeze(
                    tensor_dict['detection_masks'], [0])
# Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(
                    tensor_dict['num_detections'][0], tf.int32)
                detection_boxes = tf.slice(detection_boxes, [0, 0], [
                                           real_num_detection, -1])
                detection_masks = tf.slice(detection_masks, [0, 0, 0], [
                                           real_num_detection, -1, -1])
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, image.shape[0], image.shape[1])
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                    detection_masks_reframed, 0)
            image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

            # Run inference
            output_dict = sess.run(tensor_dict,
                                   feed_dict={image_tensor: np.expand_dims(image, 0)})

            # all outputs are float32 numpy arrays, so convert types as appropriate
            output_dict['num_detections'] = int(
                output_dict['num_detections'][0])
            output_dict['detection_classes'] = output_dict[
                'detection_classes'][0].astype(np.uint8)
            output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
            output_dict['detection_scores'] = output_dict['detection_scores'][0]
            if 'detection_masks' in output_dict:
                output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict

# example custom widget
class EchoText(QWidget):
  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
  
        self.textbox = QLineEdit()
        self.echo_label = QLabel('')
  
        self.textbox.textChanged.connect(self.textbox_text_changed)
  
        self.layout.addWidget(self.textbox, 0, 0)
        self.layout.addWidget(self.echo_label, 1, 0)
  
    def textbox_text_changed(self):
        self.echo_label.setText(self.textbox.text())



# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self, Qimage=None):
        super().__init__()

        self.setWindowTitle("My App")

        self.detectbtn = QPushButton("Detect")

        self.detectbtn.clicked.connect(self.run_object_detection)
        self.displaybtn = QPushButton("Display")

        self.displaybtn.clicked.connect(self.display_image)

        self.imagedisplay = QLabel("")
        self.imagedisplay.setPixmap(QPixmap(QPixmap("")))
        self.imagedisplay.setScaledContents(True)
        self.imagedisplay.setObjectName("imagedisplay")

        self.setFixedSize(QSize(832, 624))
        self.qimage = Qimage
        # Set the central widget of the Window.

        layout = QVBoxLayout()

        layout.addWidget(self.displaybtn)
        layout.addWidget(self.detectbtn)
##added example custom widget
        self.echotext_widget = EchoText()
        layout.addWidget(self.echotext_widget)

        layout.addWidget(self.imagedisplay)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    # code to convert image data into suitable numpy array

    def load_image_into_numpy_array(self,image):
        (im_width, im_height) = image.size
        return np.stack((np.array(image.getdata()),) * 3, axis=-1).reshape(
            (im_height, im_width, 3)).astype(np.uint8)




    def display_image(self):
        print("Display Clicked!")
        self.imagedisplay.setPixmap(QPixmap('image-in/changed_image.jpg'))


    def run_object_detection(self):
        print(f"File: 'image-in/changed_image.jpg' being processed")
    # check its an image file
        image = Image.open('image-in/changed_image.jpg')

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
#plt.figure(figsize=IMAGE_SIZE)
#plt.imshow(image_np)

        assert (np.max(self.image_np) <= 255)
        image8 = self.image_np.astype(np.uint8, order='C', casting='unsafe')
        height, width, colors = image8.shape
        bytesPerLine = 3 * width

        image = QImage(image8.data, width, height, bytesPerLine,
                        QImage.Format_RGB888)

        self.qimage = image
        self.qimage_scaled = self.qimage.scaled(self.imagedisplay.width(), self.imagedisplay.height(), Qt.KeepAspectRatio)

        self.qpixmap = QPixmap.fromImage(self.qimage_scaled)
        self.imagedisplay.setPixmap(self.qpixmap)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()