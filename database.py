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








def get_model_settings():

    query = QSqlQuery()
    if query.exec("SELECT settings.modelname ,model_location,user_type,modelfile,labelmapfile,current_slide,input_path,output_path,slide_reference,sample FROM settings,model,slide  where settings.modelname=model.modelname and slide.slideid=settings.current_slide "):
        modelname,model_location,user_type,modelfile,labelmapfile,current_slide,input_path,output_path,slide_reference,sample = range(10)
        if query.first():
            settings_dict={
                "modelname": query.value(modelname),
                "model_location": query.value(model_location),
                "user_type":query.value(user_type),
                "modelfile":query.value(modelfile),
                "labelmapfile": query.value(labelmapfile),
                "current_slide":query.value(current_slide),
                "input_path": query.value(input_path),
                "output_path": query.value(output_path),
                "slide_reference":query.value(slide_reference),
                 "location": query.value(sample)
                    }

            return settings_dict

def get_pollen_counts(samplename,usertype):

    query = QSqlQuery()
    pollenclass=[]
    pollencount=[]

    SQLString=' select label,count(itemid)  from item where slideid in (select slideid from slide where sample="'+samplename+'") and origin="'+usertype+ '" group by label'

    if query.exec(SQLString):
        while query.next():
            pollenclass.append(query.value(0))
            pollencount.append(query.value(1))

    return pollencount,pollenclass

def get_models():
    query = QSqlQuery()
    models=[]
    SQLString=" select modelname  from model"
    if query.exec(SQLString):
        while query.next():
            models.append(query.value(0))
    return models

def get_progress_data(slideid):

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
            return progress_dict

def get_slide_count(slideid):
    query = QSqlQuery()
    if query.exec("SELECT count(itemid) as current_count  FROM item  where slideid="+str(slideid) +' and origin="user"'):
        query.first()
        current_count = query.value(0)
        return current_count

def set_slide_count(slideid):
    query = QSqlQuery()
    querystring='Update slide set current_count=(select count(*) from item where slideid='+ str(slideid)+ ' and origin="user") where slideid='+str(slideid)

    query.exec(querystring)


def delete_saved_labels_from_database(imageid,slideid,usertype):
    query = QSqlQuery()
    querystring = 'delete from item where slideid=' + str(slideid) + ' and imageid=' + str(imageid) + ' and origin="'+usertype+'"'

    query.exec(querystring)


def save_labels_to_database( slideid,label_data):
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

def save_image_to_database(slideid,fileprefix):
    query = QSqlQuery()
    querystring = "INSERT INTO image (slideid,filename) VALUES ( "+str(slideid)+", '')"
    query.exec(querystring)
    query.finish()

    if query.exec("SELECT max(imageid),output_path  FROM image,settings  where slideid="+str(slideid) +" group by output_path "):
        query.first()
        filename=str(query.value(1))+'\\'+fileprefix+ str(query.value(0))+'.jpg'
        imageid=query.value(0)
        return filename,imageid

def update_image_filename(imageid,filename):
    query = QSqlQuery()
    querystring = "update image set filename='"+filename+"' where imageid="+str(imageid)

    query.exec(querystring)

def connect_saved_model_labels_to_image(slideid,imageid):
    query = QSqlQuery()
    querystring = "update item set imageid=" + str(imageid) + " where imageid=0  and slideid=" + str(slideid)

    query.exec(querystring)


