from PyQt5.QtSql import QSqlDatabase, QSqlQuery,QSqlTableModel,QSqlRelationalTableModel,QSqlRelation,QSqlRelationalDelegate
import sys
from PyQt5.QtCore import Qt,QSize

from PyQt5.QtWidgets import ( QHBoxLayout, QWidget,QLabel,QTableView,QDataWidgetMapper,
                              QFormLayout,QComboBox,QLineEdit,QPushButton,QVBoxLayout,QProgressBar,QFrame,QCheckBox )
from database import dbcon,get_models

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout=QVBoxLayout()
        form = QFormLayout()
        self.modelname = QComboBox()
        models=get_models()
        self.modelname.addItems(models)
        self.model_location = QComboBox()
        self.model_location.addItems(["local", "remote"])
        self.user_type = QComboBox()
        self.user_type.addItems(["user", "expert"])
        self.input_path= QLineEdit()
        self.output_path = QLineEdit()
        self.current_slide = QLineEdit()


        form.addRow(QLabel("Model"), self.modelname)
        form.addRow(QLabel("Model location"), self.model_location)
        form.addRow(QLabel("User Type"), self.user_type)
        form.addRow(QLabel("Input Image Path"), self.input_path)
        form.addRow(QLabel("Output Image Path"), self.output_path)
        form.addRow(QLabel("Current Slide"), self.current_slide)

        self.model = QSqlTableModel(db=dbcon)
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.modelname, 0)
        self.mapper.addMapping(self.model_location, 1)
        self.mapper.addMapping(self.user_type, 2)
        self.mapper.addMapping(self.input_path, 4)
        self.mapper.addMapping(self.output_path, 5)
        self.mapper.addMapping(self.current_slide, 3)

        self.model.setTable("settings")
        self.model.select()
        self.mapper.toFirst()

        controls = QHBoxLayout()
        save_rec = QPushButton("Save Changes")
        save_rec.clicked.connect(lambda:self.save_changes())
        cancel_rec = QPushButton("Cancel")
        cancel_rec.clicked.connect(lambda:self.close())

        controls.addWidget(save_rec)
        controls.addWidget(cancel_rec)

        layout.addLayout(form)
        layout.addLayout(controls)

        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)

    def save_changes(self):
        self.mapper.submit()

        self.close()