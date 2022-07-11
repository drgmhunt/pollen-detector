from PyQt5.QtSql import QSqlDatabase, QSqlQuery
import sys

 # createconnection
dbcon = QSqlDatabase.addDatabase("QSQLITE")
dbcon.setDatabaseName("./pollen.db")

if not dbcon.open():
    print("Unable to connect to the database:",dbcon.databaseName())
    sys.exit(1)

def get_settings():
    #print("Database:", dbcon.databaseName(), "Connection:", dbcon.connectionName())
    query = QSqlQuery()
    if query.exec("SELECT model,target_count,model_location,user_type FROM settings"):
        model,target_count,model_location,user_type = range(4)
        if query.first():
            settings_dict={
                "model": query.value(model),
                "target_count": query.value(target_count),
                "model_location": query.value(model_location),
                "user_type":query.value(user_type)
                    }
            print(settings_dict)
            return settings_dict


def save_labels_to_database(label_data):
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