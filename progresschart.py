from PyQt5.QtWidgets import (
    QWidget,QMainWindow,QVBoxLayout,QFrame,QProgressBar,QLabel
)

import numpy as np
from PyQt5.QtCore import Qt
from database import get_pollen_counts
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from database import get_model_settings

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class ProgressWidget(QFrame):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setMaximumSize(200,100)
        self.model_name=QLabel()
        self.slide_reference = QLabel()
        self.progress_bar=QProgressBar()
        layout.addWidget(self.model_name)
        layout.addWidget(self.slide_reference)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Panel)

class ProgressGraphWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()


        sc = MplCanvas(self, width=8, height=4, dpi=100)
        toolbar = NavigationToolbar(sc, self)

        settings_dict = get_model_settings()
        print(settings_dict)
        samplename = settings_dict["location"]

        pollencount,pollenclass=get_pollen_counts(samplename,"user")

        y_pos = np.arange(len(pollenclass))

        sc.axes.barh(y_pos, pollencount,  align='center')
        sc.axes.set_yticks(y_pos)
        sc.axes.set_yticklabels(pollenclass)
        sc.axes.invert_yaxis()  # labels read top-to-bottom
        sc.axes.set_xlabel('Count')
        sc.axes.set_title('User Pollen Count - '+samplename)

        sc2 = MplCanvas(self, width=8, height=4, dpi=100)
        model_pollencount, model_pollenclass = get_pollen_counts(samplename, "model")

        y_pos = np.arange(len(model_pollenclass))

        sc2.axes.barh(y_pos, model_pollencount, align='center')
        sc2.axes.set_yticks(y_pos)
        sc2.axes.set_yticklabels(model_pollenclass)
        sc2.axes.invert_yaxis()  # labels read top-to-bottom
        sc2.axes.set_xlabel('Count')
        sc2.axes.set_title('Model Pollen Count - ' + samplename)

        # code to create a stacked bar chart - merges the class list for user and model in case they don't match


        newlist = pollenclass.copy()
        newmodelvalue = []
        newuservalue = []

        for x in model_pollenclass:
            if x not in pollenclass:
                newlist.append(x)


        for x in newlist:
            if x in pollenclass:
                newuservalue.append(pollencount[pollenclass.index(x)])
            else:
                newuservalue.append(0)
        for x in newlist:
            if x in model_pollenclass:
                newmodelvalue.append(model_pollencount[model_pollenclass.index(x)])
            else:
                newmodelvalue.append(0)


        #print (newlist,newuservalue,newmodelvalue)


        #data sorted - need to build the bar chart
        sc3 = MplCanvas(self, width=8, height=4, dpi=100)
        width=.35


        y_pos = np.arange(len(newlist))
        sc3.axes.barh(y_pos - width / 2, newmodelvalue, width, label='Model')
        sc3.axes.barh(y_pos + width / 2, newuservalue, width, label='User')
        sc3.axes.set_yticks(y_pos)
        sc3.axes.set_yticklabels(newlist)
        sc3.axes.invert_yaxis()  # labels read top-to-bottom
        sc3.axes.set_xlabel('Count')
        sc3.axes.set_title('Model vs User Pollen Count - ' + samplename)
        sc3.axes.legend()

        layout.addWidget(toolbar)
        #layout.addWidget(sc)
        #layout.addWidget(sc2)
        layout.addWidget(sc3)

        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)



