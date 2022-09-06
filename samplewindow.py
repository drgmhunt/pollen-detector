from PyQt5.QtSql import QSqlDatabase, QSqlQuery,QSqlTableModel,QSqlRelationalTableModel,QSqlRelation,QSqlRelationalDelegate
import sys
from PyQt5.QtCore import Qt,QSize

from PyQt5.QtWidgets import ( QHBoxLayout, QWidget,QLabel,QTableView,QDataWidgetMapper,
                              QFormLayout,QComboBox,QLineEdit,QPushButton,QVBoxLayout,QProgressBar,QFrame,QCheckBox )

from database import dbcon,insert_new_sample_to_database,set_current_slide_in_database

class SampleWindow(QWidget):
    def __init__(self,current_slideid):
        super().__init__()

        layout=QVBoxLayout()
        form = QFormLayout()
        self.slideid = QLineEdit()
        self.slideid.setVisible(False)
        self.sample=QLineEdit()
        self.slide_reference = QLineEdit()
        self.depth = QLineEdit()
        self.current_x = QLineEdit()
        self.current_y = QLineEdit()
        self.target_count = QLineEdit()
        self.current_count = QLineEdit()
        self.current_count.setReadOnly(True)
        self.notes = QLineEdit()
        self.is_current_slide=QLineEdit()
        self.is_current_slide.setReadOnly(True)

        #form.addRow(QLabel("Sample"), self.slideid)
        form.addRow(QLabel("Sample"), self.sample)
        form.addRow(QLabel("Slide"), self.slide_reference)
        form.addRow(QLabel("Depth"), self.depth)
        form.addRow(QLabel("Transect x"), self.current_x)
        form.addRow(QLabel("Transect y"), self.current_y)
        form.addRow(QLabel("Current Count"), self.current_count)
        form.addRow(QLabel("Target Count"), self.target_count)
        form.addRow(QLabel("Notes"), self.notes)
        form.addRow(QLabel("Current Slide?"), self.is_current_slide)


        self.model = QSqlRelationalTableModel(db=dbcon)
        self.model.setTable("slide")
        self.model.select()


        #set up the mapper
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.slideid, 0)
        self.mapper.addMapping(self.sample, 1)
        self.mapper.addMapping(self.slide_reference, 2)
        self.mapper.addMapping(self.depth, 3)
        self.mapper.addMapping(self.current_x, 4)
        self.mapper.addMapping(self.current_y, 5)
        self.mapper.addMapping(self.current_count, 7)
        self.mapper.addMapping(self.notes, 8)
        self.mapper.addMapping(self.is_current_slide, 9)
        self.mapper.addMapping(self.target_count, self.model.fieldIndex("target_count"))
        self.mapper.toFirst()

        while not self.is_current_slide.text()=='Yes':
           self.mapper.toNext()

        controls = QHBoxLayout()
        prev_rec = QPushButton("Previous")
        prev_rec.clicked.connect(self.mapper.toPrevious)
        next_rec = QPushButton("Next")
        next_rec.clicked.connect(self.mapper.toNext)

        save_rec = QPushButton("Save Changes")
        save_rec.clicked.connect(lambda:self.save_changes())
        cancel_rec = QPushButton("Cancel")
        cancel_rec.clicked.connect(lambda:self.close())

        controls.addWidget(prev_rec)
        controls.addWidget(next_rec)
        controls.addWidget(save_rec)
        controls.addWidget(cancel_rec)

        controlsrow2 = QHBoxLayout()
        new_rec = QPushButton("New")
        new_rec.clicked.connect(lambda: self.new_sample())
        current_rec = QPushButton("Set Current")
        current_rec.clicked.connect(lambda: self.set_current())
        controlsrow2.addWidget(new_rec)
        controlsrow2.addWidget(current_rec)

        layout.addLayout(form)
        layout.addLayout(controls)
        layout.addLayout(controlsrow2)

        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)

    def save_changes(self):
        self.mapper.submit()
        self.close()

    def new_sample(self):
        insert_new_sample_to_database()
        self.close()

    def set_current(self):
        set_current_slide_in_database(self.slideid.text())
        self.close()

