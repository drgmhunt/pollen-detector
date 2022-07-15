from PyQt5.QtSql import QSqlDatabase, QSqlQuery,QSqlTableModel,QSqlRelationalTableModel,QSqlRelation,QSqlRelationalDelegate
import sys
from PyQt5.QtCore import Qt,QSize

from PyQt5.QtWidgets import ( QHBoxLayout, QWidget,QLabel,QTableView,QDataWidgetMapper,
                              QFormLayout,QComboBox,QLineEdit,QPushButton,QVBoxLayout,QProgressBar,QFrame,QCheckBox )

 # createconnection
dbcon = QSqlDatabase.addDatabase("QSQLITE")
dbcon.setDatabaseName("./pollen.db")

if not dbcon.open():
    print("Unable to connect to the database:",dbcon.databaseName())
    sys.exit(1)

class ProgressWidget(QFrame):
    """
        This "window" is a QWidget. If it has no parent, it
        will appear as a free-floating window as we want.
        """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setMaximumSize(200,100)
        self.slide_reference = QLabel()
        self.progress_bar=QProgressBar()
        layout.addWidget(self.slide_reference)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        frame=QFrame()
        self.setFrameStyle(QFrame.Panel)




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

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout=QVBoxLayout()
        form = QFormLayout()
        self.modelname = QComboBox()
        self.modelname.addItems(["UK Basic", "UK 5"])
        self.model_location = QComboBox()
        self.model_location.addItems(["local", "remote"])
        self.user_type = QComboBox()
        self.user_type.addItems(["user", "expert"])
        self.current_slide = QLineEdit()

        modelname_combo = QComboBox()

        form.addRow(QLabel("Model"), self.modelname)
        form.addRow(QLabel("Model location"), self.model_location)
        form.addRow(QLabel("User Type"), self.user_type)
        form.addRow(QLabel("Current Slide"), self.current_slide)

        self.model = QSqlTableModel(db=dbcon)
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.modelname, 0)
        self.mapper.addMapping(self.model_location, 1)
        self.mapper.addMapping(self.user_type, 2)
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




def get_model_settings():
    print("Database:", dbcon.databaseName(), "Connection:", dbcon.connectionName())
    query = QSqlQuery()
    if query.exec("SELECT settings.modelname ,model_location,user_type,modelfile,labelmapfile,current_slide,slide_reference,sample FROM settings,model,slide  where settings.modelname=model.modelname and slide.slideid=settings.current_slide "):
        modelname,model_location,user_type,modelfile,labelmapfile,current_slide,slide_reference,sample = range(8)
        if query.first():
            settings_dict={
                "modelname": query.value(modelname),
                "model_location": query.value(model_location),
                "user_type":query.value(user_type),
                "modelfile":query.value(modelfile),
                "labelmapfile": query.value(labelmapfile),
                "current_slide":query.value(current_slide),
                "slide_reference":query.value(slide_reference),
                 "location": query.value(sample)
                    }
            print(settings_dict)
            return settings_dict

def get_progress_data(slideid):
    #print("Database:", dbcon.databaseName(), "Connection:", dbcon.connectionName())
    query = QSqlQuery()
    if query.exec("SELECT sample,slide_reference,current_count,target_count from slide where slideid="+str(slideid)):
        location,slide_reference,current_count,target_count = range(4)
        if query.first():
            progress_dict={
                "sample": query.value(location),
                "slide_reference": query.value(slide_reference),
                "current_count":query.value(current_count),
                "target_count":query.value(target_count)
                    }
            print(progress_dict)
            return progress_dict

def get_slide_count(slideid):
    #print("Database:", dbcon.databaseName(), "Connection:", dbcon.connectionName())
    query = QSqlQuery()
    if query.exec("SELECT count(itemid) as current_count  FROM item  where slideid="+str(slideid)):
        query.first()
        current_count = query.value(0)
        print("count ",current_count,"errors",query.lastError().databaseText() )

        return current_count

def set_slide_count(slideid):
    query = QSqlQuery()
    querystring='Update slide set current_count=(select count(*) from item where slideid='+ str(slideid)+') where slideid='+str(slideid)
    print("querystring",querystring)
    query.exec(querystring)
    print("rows affected", query.numRowsAffected(),query.lastError().databaseText())




def save_labels_to_database(slideid,label_data):
    query = QSqlQuery()
    #slide and sample hardcoded currently -tbd
    query.prepare(
    """

    INSERT INTO item (slideid,imageid,x,y,h,w,label,probability,origin)

    VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?)

    """

)


# Use .addBindValue() to insert data

    for slideid,imageid,x,y,h,w,label,probability,origin in label_data:

        query.addBindValue(slideid)
        query.addBindValue(imageid)
        query.addBindValue(x)
        query.addBindValue(y)
        query.addBindValue(h)
        query.addBindValue(w)
        query.addBindValue(label)
        query.addBindValue(probability)
        query.addBindValue(origin)

        query.exec()
        query.finish()

    set_slide_count(slideid)

def insert_new_sample_to_database():
    query = QSqlQuery()
    #slide and sample hardcoded currently -tbd
    query.prepare(
    """

    INSERT INTO slide (sample,slide_reference,depth,current_x,current_y,target_count,current_count,notes,is_current_slide)

    VALUES ( '', '' ,0, 0, 0, 100, 0, '','New')

    """

)

    query.exec()
    query.finish()
    set_new_slide_as_current_in_database()

def set_new_slide_as_current_in_database():
    query = QSqlQuery()
    querystring="Update slide set  is_current_slide='No' where is_current_slide='Yes'"

    query.exec(querystring)

    querystring = "Update slide set is_current_slide='Yes' where is_current_slide='New'"

    query.exec(querystring)

    querystring="Update settings set current_slide=(select slideid from slide where is_current_slide='Yes')"

    query.exec(querystring)

def set_current_slide_in_database(slideid):
    query = QSqlQuery()
    querystring = "Update slide set  is_current_slide='No' where is_current_slide='Yes'"

    query.exec(querystring)


    querystring = "Update slide set is_current_slide='Yes' where slideid="+str(slideid)

    query.exec(querystring)

    querystring = "Update settings set current_slide="+str(slideid)

    query.exec(querystring)