BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "image" (
	"imageid"	INTEGER NOT NULL,
	"slideid"	INTEGER NOT NULL,
	"filename"	TEXT,
	PRIMARY KEY("imageid" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "item" (
	"itemid"	INTEGER NOT NULL,
	"slideid"	INTEGER NOT NULL,
	"imageid"	INTEGER NOT NULL,
	"x"	REAL,
	"y"	REAL,
	"h"	REAL,
	"w"	REAL,
	"label"	TEXT,
	"probability"	INTEGER,
	"origin"	TEXT,
	PRIMARY KEY("itemid" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "model" (
	"modelname"	TEXT,
	"modelfile"	TEXT,
	"labelmapfile"	TEXT
);
CREATE TABLE IF NOT EXISTS "settings" (
	"modelname"	TEXT,
	"model_location"	TEXT,
	"user_type"	TEXT,
	"current_slide"	INTEGER
);
CREATE TABLE IF NOT EXISTS "slide" (
	"slideid"	INTEGER NOT NULL,
	"sample"	TEXT NOT NULL,
	"slide_reference"	TEXT,
	"depth"	INTEGER,
	"current_x"	INTEGER,
	"current_y"	INTEGER,
	"target_count"	INTEGER,
	"current_count"	INTEGER,
	"notes"	TEXT,
	"is_current_slide"	INTEGER,
	PRIMARY KEY("slideid" AUTOINCREMENT)
);
COMMIT;
