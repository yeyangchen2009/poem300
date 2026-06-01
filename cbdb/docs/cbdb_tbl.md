## table 资料

https://cbdb.sunan.me/

## ADDR\_BELONGS\_DATA

ADDR\_BELONGS\_DATA
2
CREATE TABLE "ADDR\_BELONGS\_DATA" (
"c\_addr\_id" INTEGER(11) NOT NULL,
"c\_belongs\_to" INTEGER(11) NOT NULL,
"c\_firstyear" smallint(6) NOT NULL,
"c\_lastyear" smallint(6) NOT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_addr\_id", "c\_belongs\_to", "c\_firstyear", "c\_lastyear")
)

## ADDR\_CODES

ADDR\_CODES
589
CREATE TABLE "ADDR\_CODES" (
"c\_addr\_id" INTEGER(11) NOT NULL,
"c\_name" varchar(255) DEFAULT NULL,
"c\_name\_chn" varchar(255) DEFAULT NULL,
"c\_firstyear" smallint(6) DEFAULT NULL,
"c\_lastyear" smallint(6) DEFAULT NULL,
"c\_admin\_type" varchar(255) DEFAULT NULL,
"c\_admin\_cat\_code" smallint(6) NOT NULL DEFAULT 0,
"x\_coord" REAL DEFAULT NULL,
"y\_coord" REAL DEFAULT NULL,
"CHGIS\_PT\_ID" INTEGER(11) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_alt\_names" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_addr\_id")
)

## ADMIN\_CAT\_CODES

ADMIN\_CAT\_CODES
1175
CREATE TABLE "ADMIN\_CAT\_CODES" (
"c\_admin\_cat\_code" smallint(6) NOT NULL,
"c\_admin\_cat\_py" varchar(255) DEFAULT NULL,
"c\_admin\_cat\_hz" varchar(255) DEFAULT NULL,
"c\_admin\_cat\_trans" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_admin\_cat\_code")
)

## ADMIN\_CAT\_CODE\_TYPE\_REL

ADMIN\_CAT\_CODE\_TYPE\_REL
1180
CREATE TABLE "ADMIN\_CAT\_CODE\_TYPE\_REL" (
"c\_admin\_cat\_code" smallint(6) NOT NULL,
"c\_admin\_cat\_type\_code" varchar(255) NOT NULL,
PRIMARY KEY ("c\_admin\_cat\_code", "c\_admin\_cat\_type\_code")
)

## ADMIN\_CAT\_TYPES

ADMIN\_CAT\_TYPES
1182
CREATE TABLE "ADMIN\_CAT\_TYPES" (
"c\_admin\_cat\_type\_code" varchar(255) NOT NULL,
"c\_admin\_cat\_type\_hz" varchar(255) DEFAULT NULL,
"c\_admin\_cat\_type\_trans" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_admin\_cat\_type\_code")
)

## ALTNAME\_CODES

ALTNAME\_CODES
1184
CREATE TABLE "ALTNAME\_CODES" (
"c\_name\_type\_code" smallint(6) NOT NULL,
"c\_name\_type\_desc" varchar(255) DEFAULT NULL,
"c\_name\_type\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_name\_type\_code")
)

## ALTNAME\_DATA

ALTNAME\_DATA
1186
CREATE TABLE "ALTNAME\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_alt\_name" varchar(255) DEFAULT NULL,
"c\_alt\_name\_chn" varchar(255) NOT NULL,
"c\_alt\_name\_type\_code" smallint(6) NOT NULL,
"c\_sequence" smallint(6) DEFAULT 0,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_alt\_name\_chn", "c\_alt\_name\_type\_code", "c\_personid")
)

## APPOINTMENT\_CODES

APPOINTMENT\_CODES
6272
CREATE TABLE "APPOINTMENT\_CODES" (
"c\_appt\_code" smallint(6) NOT NULL,
"c\_appt\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_appt\_desc" varchar(255) DEFAULT NULL,
"c\_appt\_desc\_chn\_alt" varchar(255) DEFAULT NULL,
"c\_appt\_desc\_alt" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_appt\_code")
)

## APPOINTMENT\_CODE\_TYPE\_REL

APPOINTMENT\_CODE\_TYPE\_REL
6276
CREATE TABLE "APPOINTMENT\_CODE\_TYPE\_REL" (
"c\_appt\_type\_code" varchar(255) NOT NULL,
"c\_appt\_code" smallint(6) NOT NULL,
PRIMARY KEY ("c\_appt\_code", "c\_appt\_type\_code")
)

## APPOINTMENT\_TYPES

APPOINTMENT\_TYPES
6280
CREATE TABLE "APPOINTMENT\_TYPES" (
"c\_appt\_type\_code" varchar(255) NOT NULL,
"c\_appt\_type\_desc" varchar(255) DEFAULT NULL,
"c\_appt\_type\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_appt\_type\_code")
)

## ASSOC\_CODES

ASSOC\_CODES
6282
CREATE TABLE "ASSOC\_CODES" (
"c\_assoc\_code" smallint(6) NOT NULL,
"c\_assoc\_pair" smallint(6) DEFAULT NULL,
"c\_assoc\_pair2" smallint(6) DEFAULT NULL,
"c\_assoc\_desc" varchar(255) DEFAULT NULL,
"c\_assoc\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_assoc\_role\_type" varchar(255) DEFAULT NULL,
"c\_sortorder" smallint(6) DEFAULT NULL,
"c\_example" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_assoc\_code")
)

## ASSOC\_CODE\_TYPE\_REL

ASSOC\_CODE\_TYPE\_REL
6295
CREATE TABLE "ASSOC\_CODE\_TYPE\_REL" (
"c\_assoc\_code" smallint(6) NOT NULL,
"c\_assoc\_type\_code" varchar(255) NOT NULL,
PRIMARY KEY ("c\_assoc\_code", "c\_assoc\_type\_code")
)

## ASSOC\_DATA

ASSOC\_DATA
6301
CREATE TABLE "ASSOC\_DATA" (
"c\_assoc\_code" smallint(6) NOT NULL,
"c\_personid" INTEGER(11) NOT NULL,
"c\_kin\_code" smallint(6) NOT NULL,
"c\_kin\_id" INTEGER(11) NOT NULL,
"c\_assoc\_id" INTEGER(11) NOT NULL,
"c\_assoc\_kin\_code" smallint(6) NOT NULL,
"c\_assoc\_kin\_id" INTEGER(11) NOT NULL,
"c\_tertiary\_personid" INTEGER(11) DEFAULT NULL,
"c\_tertiary\_type\_notes" TEXT DEFAULT NULL,
"c\_assoc\_count" smallint(6) NOT NULL DEFAULT 1,
"c\_sequence" smallint(6) DEFAULT 0,
"c\_assoc\_first\_year" smallint(6) NOT NULL DEFAULT -9999,
"c\_assoc\_last\_year" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_assoc\_fy\_nh\_code" smallint(6) DEFAULT NULL,
"c\_assoc\_fy\_nh\_year" smallint(6) DEFAULT NULL,
"c\_assoc\_fy\_range" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_nh\_code" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_nh\_year" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_range" smallint(6) DEFAULT NULL,
"c\_addr\_id" INTEGER(11) DEFAULT NULL,
"c\_litgenre\_code" smallint(6) DEFAULT NULL,
"c\_occasion\_code" smallint(6) DEFAULT NULL,
"c\_topic\_code" smallint(6) DEFAULT NULL,
"c\_inst\_code" smallint(6) DEFAULT 0,
"c\_inst\_name\_code" smallint(6) DEFAULT 0,
"c\_text\_title" varchar(255) NOT NULL DEFAULT '',
"c\_assoc\_claimer\_id" INTEGER(11) DEFAULT NULL,
"c\_assoc\_fy\_intercalary" smallint(6) DEFAULT NULL,
"c\_assoc\_fy\_month" smallint(6) DEFAULT NULL,
"c\_assoc\_fy\_day" smallint(6) DEFAULT NULL,
"c\_assoc\_fy\_day\_gz" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_intercalary" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_month" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_day" smallint(6) DEFAULT NULL,
"c\_assoc\_ly\_day\_gz" smallint(6) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_assoc\_code", "c\_assoc\_id", "c\_assoc\_kin\_code", "c\_assoc\_kin\_id", "c\_kin\_code", "c\_kin\_id", "c\_personid", "c\_text\_title", "c\_assoc\_first\_year")
)

## ASSOC\_TYPES

ASSOC\_TYPES
15204
CREATE TABLE "ASSOC\_TYPES" (
"c\_assoc\_type\_code" varchar(255) NOT NULL,
"c\_assoc\_type\_desc" varchar(255) DEFAULT NULL,
"c\_assoc\_type\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_assoc\_type\_parent\_id" varchar(255) DEFAULT NULL,
"c\_assoc\_type\_level" smallint(6) DEFAULT NULL,
"c\_assoc\_type\_sortorder" smallint(6) DEFAULT NULL,
"c\_assoc\_type\_short\_desc" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_assoc\_type\_code")
)

## ASSUME\_OFFICE\_CODES

ASSUME\_OFFICE\_CODES
15207
CREATE TABLE "ASSUME\_OFFICE\_CODES" (
"c\_assume\_office\_code" smallint(6) NOT NULL,
"c\_assume\_office\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_assume\_office\_desc" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_assume\_office\_code")
)

## BIOG\_ADDR\_CODES

BIOG\_ADDR\_CODES
15209
CREATE TABLE "BIOG\_ADDR\_CODES" (
"c\_addr\_type" smallint(6) NOT NULL,
"c\_addr\_desc" varchar(255) DEFAULT NULL,
"c\_addr\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_addr\_note" varchar(255) DEFAULT NULL,
"c\_index\_addr\_rank" smallint(6) DEFAULT NULL,
"c\_index\_addr\_default\_rank" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_addr\_type")
)

## BIOG\_ADDR\_DATA

BIOG\_ADDR\_DATA
15211
CREATE TABLE "BIOG\_ADDR\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_addr\_id" INTEGER(11) NOT NULL DEFAULT 0,
"c\_addr\_type" smallint(6) NOT NULL,
"c\_sequence" smallint(6) NOT NULL,
"c\_firstyear" smallint(6) DEFAULT NULL,
"c\_lastyear" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_fy\_nh\_code" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_code" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_year" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_year" smallint(6) DEFAULT NULL,
"c\_fy\_range" smallint(6) DEFAULT NULL,
"c\_ly\_range" smallint(6) DEFAULT NULL,
"c\_natal" INTEGER(11) DEFAULT NULL /\* Indicates whether the recorded address refers to a woman’s natal (maternal) family location rather than her married residence. Primarily applicable to female records. NULL should be used when natal origin is not explicitly documented. \*/,
"c\_fy\_intercalary" smallint(6) DEFAULT NULL,
"c\_ly\_intercalary" smallint(6) DEFAULT NULL,
"c\_fy\_month" smallint(6) DEFAULT NULL,
"c\_ly\_month" smallint(6) DEFAULT NULL,
"c\_fy\_day" smallint(6) DEFAULT NULL,
"c\_ly\_day" smallint(6) DEFAULT NULL,
"c\_fy\_day\_gz" smallint(6) DEFAULT NULL,
"c\_ly\_day\_gz" smallint(6) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_delete" smallint(6) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_personid", "c\_addr\_id", "c\_addr\_type", "c\_sequence")
)

## BIOG\_INST\_CODES

BIOG\_INST\_CODES
28058
CREATE TABLE "BIOG\_INST\_CODES" (
"c\_bi\_role\_code" smallint(6) NOT NULL,
"c\_bi\_role\_desc" varchar(255) DEFAULT NULL,
"c\_bi\_role\_chn" varchar(255) DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_bi\_role\_code")
)

## BIOG\_INST\_DATA

BIOG\_INST\_DATA
28060
CREATE TABLE "BIOG\_INST\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_inst\_name\_code" smallint(6) NOT NULL,
"c\_inst\_code" smallint(6) NOT NULL,
"c\_bi\_role\_code" smallint(6) NOT NULL,
"c\_bi\_begin\_year" smallint(6) DEFAULT NULL,
"c\_bi\_by\_nh\_code" smallint(6) DEFAULT NULL,
"c\_bi\_by\_nh\_year" smallint(6) DEFAULT NULL,
"c\_bi\_by\_range" smallint(6) DEFAULT NULL,
"c\_bi\_end\_year" smallint(6) DEFAULT NULL,
"c\_bi\_ey\_nh\_code" smallint(6) DEFAULT NULL,
"c\_bi\_ey\_nh\_year" smallint(6) DEFAULT NULL,
"c\_bi\_ey\_range" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_bi\_role\_code", "c\_inst\_code", "c\_inst\_name\_code", "c\_personid")
)

## BIOG\_MAIN

BIOG\_MAIN
28079
CREATE TABLE "BIOG\_MAIN" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_name" varchar(255) DEFAULT NULL /\* Hanyu Pinyin full name; auto-generated: c\_surname + " " + c\_mingzi */,
"c\_name\_chn" varchar(255) DEFAULT NULL /* Chinese full name; auto-generated: c\_surname\_chn + c\_mingzi\_chn (no space) */,
"c\_index\_year" smallint(6) DEFAULT NULL,
"c\_index\_year\_type\_code" varchar(255) DEFAULT NULL,
"c\_index\_year\_source\_id" INTEGER(11) DEFAULT NULL,
"c\_female" smallint(6) DEFAULT NULL,
"c\_index\_addr\_id" INTEGER(11) DEFAULT 0,
"c\_index\_addr\_type\_code" smallint(6) DEFAULT NULL,
"c\_ethnicity\_code" smallint(6) DEFAULT NULL,
"c\_household\_status\_code" smallint(6) DEFAULT NULL,
"c\_tribe" varchar(255) DEFAULT NULL,
"c\_birthyear" smallint(6) DEFAULT NULL,
"c\_by\_nh\_code" smallint(6) DEFAULT NULL,
"c\_by\_nh\_year" smallint(6) DEFAULT NULL,
"c\_by\_range" smallint(6) DEFAULT NULL,
"c\_deathyear" smallint(6) DEFAULT NULL,
"c\_dy\_nh\_code" smallint(6) DEFAULT NULL,
"c\_dy\_nh\_year" smallint(6) DEFAULT NULL,
"c\_dy\_range" smallint(6) DEFAULT NULL,
"c\_death\_age" smallint(6) DEFAULT NULL,
"c\_death\_age\_range" smallint(6) DEFAULT NULL,
"c\_fl\_earliest\_year" smallint(6) DEFAULT NULL,
"c\_fl\_ey\_nh\_code" smallint(6) DEFAULT NULL,
"c\_fl\_ey\_nh\_year" smallint(6) DEFAULT NULL,
"c\_fl\_ey\_notes" TEXT DEFAULT NULL,
"c\_fl\_latest\_year" smallint(6) DEFAULT NULL,
"c\_fl\_ly\_nh\_code" smallint(6) DEFAULT NULL,
"c\_fl\_ly\_nh\_year" smallint(6) DEFAULT NULL,
"c\_fl\_ly\_notes" TEXT DEFAULT NULL,
"c\_surname" varchar(255) DEFAULT NULL /* Hanyu Pinyin romanization of the person's surname; auto-generated from c\_surname\_chn via pinyin lookup table */,
"c\_surname\_chn" varchar(255) DEFAULT NULL /* Chinese surname; split from c\_name\_chn by matching longest known surname in pinyin table */,
"c\_mingzi" varchar(255) DEFAULT NULL /* Hanyu Pinyin romanization of the person's given name (excluding surname); auto-generated from c\_mingzi\_chn */,
"c\_mingzi\_chn" varchar(255) DEFAULT NULL /* Chinese given name (excluding surname); remainder of c\_name\_chn after surname extraction */,
"c\_dy" smallint(6) DEFAULT NULL,
"c\_choronym\_code" smallint(6) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_by\_intercalary" smallint(6) DEFAULT NULL,
"c\_dy\_intercalary" smallint(6) DEFAULT NULL,
"c\_by\_month" smallint(6) DEFAULT NULL,
"c\_dy\_month" smallint(6) DEFAULT NULL,
"c\_by\_day" smallint(6) DEFAULT NULL,
"c\_dy\_day" smallint(6) DEFAULT NULL,
"c\_by\_day\_gz" smallint(6) DEFAULT NULL,
"c\_dy\_day\_gz" smallint(6) DEFAULT NULL,
"c\_surname\_proper" varchar(255) DEFAULT NULL /* Surname in the person's native language (non-Chinese), if applicable; user-editable */,
"c\_mingzi\_proper" varchar(255) DEFAULT NULL /* Given name in the person's native language (non-Chinese, excluding surname), if applicable; user-editable */,
"c\_name\_proper" varchar(255) DEFAULT NULL /* Full name in the person's native language; auto-generated: c\_mingzi\_proper + " " + c\_surname\_proper (given-name-first order) */,
"c\_surname\_rm" varchar(255) DEFAULT NULL /* Non-Pinyin romanization of the person's surname (e.g. Wade-Giles, McCune-Reischauer), if applicable; user-editable */,
"c\_mingzi\_rm" varchar(255) DEFAULT NULL /* Non-Pinyin romanization of the person's given name (excluding surname), if applicable; user-editable */,
"c\_name\_rm" varchar(255) DEFAULT NULL /* Non-Pinyin romanized full name; auto-generated: c\_mingzi\_rm + " " + c\_surname\_rm (given-name-first order) \*/,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_personid")
)

## BIOG\_SOURCE\_DATA

BIOG\_SOURCE\_DATA
56237
CREATE TABLE "BIOG\_SOURCE\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_textid" INTEGER(11) NOT NULL,
"c\_pages" varchar(255) NOT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_main\_source" smallint(6) DEFAULT NULL,
"c\_self\_bio" smallint(6) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_pages", "c\_personid", "c\_textid")
)

## BIOG\_TEXT\_DATA

BIOG\_TEXT\_DATA
86233
CREATE TABLE "BIOG\_TEXT\_DATA" (
"c\_textid" INTEGER(11) NOT NULL,
"c\_personid" INTEGER(11) NOT NULL,
"c\_role\_id" smallint(6) NOT NULL,
"c\_year" smallint(6) DEFAULT NULL,
"c\_nh\_code" smallint(6) DEFAULT NULL,
"c\_nh\_year" smallint(6) DEFAULT NULL,
"c\_range\_code" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_personid", "c\_role\_id", "c\_textid")
)

## CHORONYM\_CODES

CHORONYM\_CODES
87227
CREATE TABLE "CHORONYM\_CODES" (
"c\_choronym\_code" smallint(6) NOT NULL,
"c\_choronym\_desc" varchar(255) DEFAULT NULL,
"c\_choronym\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_choronym\_code")
)

## COUNTRY\_CODES

COUNTRY\_CODES
87231
CREATE TABLE "COUNTRY\_CODES" (
"c\_country\_code" smallint(6) NOT NULL,
"c\_country\_desc" varchar(255) DEFAULT NULL,
"c\_country\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_country\_code")
)

## DYNASTIES

DYNASTIES
87233
CREATE TABLE "DYNASTIES" (
"c\_dy" smallint(6) NOT NULL,
"c\_dynasty" varchar(255) DEFAULT NULL,
"c\_dynasty\_chn" varchar(255) DEFAULT NULL,
"c\_start" smallint(6) NOT NULL DEFAULT 0,
"c\_end" smallint(6) NOT NULL DEFAULT 0,
"c\_sort" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_dy")
)

## ENTRY\_CODES

ENTRY\_CODES
87235
CREATE TABLE "ENTRY\_CODES" (
"c\_entry\_code" smallint(6) NOT NULL,
"c\_entry\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_entry\_desc\_chn" varchar(255) NOT NULL DEFAULT '',
PRIMARY KEY ("c\_entry\_code")
)

## ENTRY\_CODE\_TYPE\_REL

ENTRY\_CODE\_TYPE\_REL
87242
CREATE TABLE "ENTRY\_CODE\_TYPE\_REL" (
"c\_entry\_code" smallint(6) NOT NULL,
"c\_entry\_type" varchar(255) NOT NULL,
PRIMARY KEY ("c\_entry\_code", "c\_entry\_type")
)

## ENTRY\_DATA

ENTRY\_DATA
87244
CREATE TABLE "ENTRY\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_entry\_code" smallint(6) NOT NULL,
"c\_sequence" smallint(6) NOT NULL,
"c\_exam\_rank" varchar(255) DEFAULT NULL,
"c\_kin\_code" smallint(6) NOT NULL,
"c\_kin\_id" INTEGER(11) NOT NULL,
"c\_assoc\_code" smallint(6) NOT NULL,
"c\_assoc\_id" INTEGER(11) NOT NULL,
"c\_year" smallint(6) NOT NULL,
"c\_age" smallint(6) DEFAULT NULL,
"c\_entry\_nh\_id" smallint(6) DEFAULT NULL,
"c\_entry\_nh\_year" smallint(6) DEFAULT NULL,
"c\_entry\_dy" smallint(6) DEFAULT NULL,
"c\_entry\_range" smallint(6) DEFAULT NULL,
"c\_inst\_code" smallint(6) NOT NULL DEFAULT 0,
"c\_inst\_name\_code" smallint(6) NOT NULL DEFAULT 0,
"c\_exam\_field" varchar(255) DEFAULT NULL,
"c\_entry\_addr\_id" INTEGER(11) DEFAULT NULL,
"c\_parental\_status\_code" smallint(6) DEFAULT NULL,
"c\_attempt\_count" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_posting\_notes" varchar(255) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_assoc\_code", "c\_assoc\_id", "c\_entry\_code", "c\_inst\_code", "c\_inst\_name\_code", "c\_kin\_code", "c\_kin\_id", "c\_personid", "c\_sequence", "c\_year")
)

## ENTRY\_TYPES

ENTRY\_TYPES
94505
CREATE TABLE "ENTRY\_TYPES" (
"c\_entry\_type" varchar(255) NOT NULL,
"c\_entry\_type\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_entry\_type\_desc\_chn" varchar(255) NOT NULL DEFAULT '',
"c\_entry\_type\_parent\_id" varchar(255) DEFAULT NULL,
"c\_entry\_type\_level" smallint(6) DEFAULT NULL,
"c\_entry\_type\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_entry\_type")
)

## ETHNICITY\_TRIBE\_CODES

ETHNICITY\_TRIBE\_CODES
94507
CREATE TABLE "ETHNICITY\_TRIBE\_CODES" (
"c\_ethnicity\_code" smallint(6) NOT NULL,
"c\_group\_code" smallint(6) DEFAULT NULL,
"c\_subgroup\_code" smallint(6) DEFAULT NULL,
"c\_altname\_code" smallint(6) DEFAULT NULL,
"c\_name\_chn" varchar(255) DEFAULT NULL,
"c\_name" varchar(255) DEFAULT NULL,
"c\_ethno\_legal\_cat" varchar(255) DEFAULT NULL,
"c\_romanized" varchar(255) DEFAULT NULL,
"c\_surname" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_ethnicity\_code")
)

## EVENTS\_ADDR

EVENTS\_ADDR
94527
CREATE TABLE "EVENTS\_ADDR" (
"c\_event\_code" smallint(6) NOT NULL DEFAULT 0,
"c\_personid" INTEGER(11) NOT NULL,
"c\_sequence" smallint(6) NOT NULL DEFAULT 0,
"c\_addr\_id" INTEGER(11) NOT NULL,
"c\_year" smallint(6) DEFAULT NULL,
"c\_nh\_code" smallint(6) DEFAULT NULL,
"c\_nh\_year" smallint(6) DEFAULT NULL,
"c\_yr\_range" smallint(6) DEFAULT NULL,
"c\_intercalary" smallint(6) DEFAULT NULL,
"c\_month" smallint(6) DEFAULT NULL,
"c\_day" smallint(6) DEFAULT NULL,
"c\_day\_ganzhi" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_addr\_id", "c\_personid", "c\_sequence", "c\_event\_code")
)

## EVENTS\_DATA

EVENTS\_DATA
94529
CREATE TABLE "EVENTS\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_sequence" smallint(6) NOT NULL DEFAULT 0,
"c\_event\_code" smallint(6) NOT NULL,
"c\_role" varchar(255) DEFAULT NULL,
"c\_year" smallint(6) DEFAULT NULL,
"c\_nh\_code" smallint(6) DEFAULT NULL,
"c\_nh\_year" smallint(6) DEFAULT NULL,
"c\_yr\_range" smallint(6) DEFAULT NULL,
"c\_intercalary" smallint(6) DEFAULT NULL,
"c\_month" smallint(6) DEFAULT NULL,
"c\_day" smallint(6) DEFAULT NULL,
"c\_day\_ganzhi" smallint(6) DEFAULT NULL,
"c\_addr\_id" INTEGER(11) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_event" TEXT DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_personid", "c\_sequence", "c\_event\_code")
)

## EVENT\_CODES

EVENT\_CODES
94549
CREATE TABLE "EVENT\_CODES" (
"c\_event\_code" smallint(6) NOT NULL,
"c\_event\_name\_chn" varchar(255) DEFAULT NULL,
"c\_event\_name" varchar(255) DEFAULT NULL,
"c\_fy\_yr" smallint(6) DEFAULT NULL,
"c\_ly\_yr" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_code" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_code" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_yr" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_yr" smallint(6) DEFAULT NULL,
"c\_fy\_intercalary" smallint(6) DEFAULT NULL,
"c\_fy\_month" smallint(6) DEFAULT NULL,
"c\_ly\_intercalary" smallint(6) DEFAULT NULL,
"c\_ly\_month" smallint(6) DEFAULT NULL,
"c\_fy\_range" smallint(6) DEFAULT NULL,
"c\_ly\_range" smallint(6) DEFAULT NULL,
"c\_addr\_id" INTEGER(11) DEFAULT NULL,
"c\_dy" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_event\_notes" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_event\_code")
)

## EXTANT\_CODES

EXTANT\_CODES
94553
CREATE TABLE "EXTANT\_CODES" (
"c\_extant\_code" smallint(6) NOT NULL,
"c\_extant\_desc" varchar(255) DEFAULT NULL,
"c\_extant\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_extant\_code")
)

## GANZHI\_CODES

GANZHI\_CODES
94555
CREATE TABLE "GANZHI\_CODES" (
"c\_ganzhi\_code" smallint(6) NOT NULL,
"c\_ganzhi\_chn" varchar(255) NOT NULL DEFAULT '',
"c\_ganzhi\_py" varchar(255) NOT NULL DEFAULT '',
PRIMARY KEY ("c\_ganzhi\_code")
)

## HOUSEHOLD\_STATUS\_CODES

HOUSEHOLD\_STATUS\_CODES
94557
CREATE TABLE "HOUSEHOLD\_STATUS\_CODES" (
"c\_household\_status\_code" smallint(6) NOT NULL,
"c\_household\_status\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_household\_status\_desc\_chn" varchar(255) NOT NULL DEFAULT '',
PRIMARY KEY ("c\_household\_status\_code")
)

## INDEXYEAR\_TYPE\_CODES

INDEXYEAR\_TYPE\_CODES
94559
CREATE TABLE "INDEXYEAR\_TYPE\_CODES" (
"c\_index\_year\_type\_code" varchar(191) NOT NULL DEFAULT '',
"c\_index\_year\_type\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_index\_year\_type\_hz" varchar(255) NOT NULL DEFAULT '',
"c\_notes" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_index\_year\_type\_code")
)

## KINSHIP\_CODES

KINSHIP\_CODES
94561
CREATE TABLE "KINSHIP\_CODES" (
"c\_kincode" smallint(6) NOT NULL,
"c\_kin\_pair1" smallint(6) NOT NULL DEFAULT 0,
"c\_kin\_pair2" smallint(6) NOT NULL DEFAULT 0,
"c\_kin\_pair\_notes" varchar(255) DEFAULT NULL,
"c\_kinrel\_chn" varchar(255) NOT NULL DEFAULT '',
"c\_kinrel" varchar(255) NOT NULL DEFAULT '',
"c\_kinrel\_alt" varchar(255) DEFAULT NULL,
"c\_pick\_sorting" smallint(6) DEFAULT NULL,
"c\_upstep" smallint(6) NOT NULL DEFAULT 0,
"c\_dwnstep" smallint(6) NOT NULL DEFAULT 0,
"c\_marstep" smallint(6) NOT NULL DEFAULT 0,
"c\_colstep" smallint(6) NOT NULL DEFAULT 0,
"c\_kinrel\_simplified" varchar(255) NOT NULL DEFAULT '',
PRIMARY KEY ("c\_kincode")
)

## KIN\_DATA

KIN\_DATA
94574
CREATE TABLE "KIN\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_kin\_id" INTEGER(11) NOT NULL,
"c\_kin\_code" smallint(6) NOT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_autogen\_notes" TEXT DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_kin\_code", "c\_kin\_id", "c\_personid")
)

## KIN\_MOURNING

KIN\_MOURNING
107892
CREATE TABLE "KIN\_MOURNING" (
"c\_kinrel" varchar(255) NOT NULL,
"c\_kinrel\_alt" varchar(255) DEFAULT NULL,
"c\_kinrel\_chn" varchar(255) DEFAULT NULL,
"c\_mourning" varchar(255) DEFAULT NULL,
"c\_mourning\_chn" varchar(255) DEFAULT NULL,
"c\_kindist" varchar(255) DEFAULT NULL,
"c\_kintype" varchar(255) DEFAULT NULL,
"c\_kintype\_desc" varchar(255) DEFAULT NULL,
"c\_kintype\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_kinrel")
)

## KIN\_MOURNING\_STEPS

KIN\_MOURNING\_STEPS
107897
CREATE TABLE "KIN\_MOURNING\_STEPS" (
"c\_kinrel" varchar(255) NOT NULL,
"c\_upstep" smallint(6) NOT NULL DEFAULT 0,
"c\_dwnstep" smallint(6) NOT NULL DEFAULT 0,
"c\_marstep" smallint(6) NOT NULL DEFAULT 0,
"c\_colstep" smallint(6) NOT NULL DEFAULT 0,
PRIMARY KEY ("c\_kinrel")
)

## LITERARYGENRE\_CODES

LITERARYGENRE\_CODES
107899
CREATE TABLE "LITERARYGENRE\_CODES" (
"c\_lit\_genre\_code" smallint(6) NOT NULL,
"c\_lit\_genre\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_lit\_genre\_desc\_chn" varchar(255) NOT NULL DEFAULT '',
"c\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_lit\_genre\_code")
)

## MEASURE\_CODES

MEASURE\_CODES
107901
CREATE TABLE "MEASURE\_CODES" (
"c\_measure\_code" smallint(6) NOT NULL,
"c\_measure\_desc" varchar(255) DEFAULT NULL,
"c\_measure\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_measure\_code")
)

## MERGED\_PERSON\_DATA

MERGED\_PERSON\_DATA
107903
CREATE TABLE "MERGED\_PERSON\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_merged\_from\_personid" INTEGER(11) NOT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_personid", "c\_merged\_from\_personid")
)

## NIAN\_HAO

NIAN\_HAO
107983
CREATE TABLE "NIAN\_HAO" (
"c\_nianhao\_id" smallint(6) NOT NULL,
"c\_dy" smallint(6) DEFAULT NULL,
"c\_dynasty\_chn" varchar(255) DEFAULT NULL,
"c\_nianhao\_chn" varchar(255) DEFAULT NULL,
"c\_nianhao\_pin" varchar(255) DEFAULT NULL,
"c\_firstyear" smallint(6) DEFAULT NULL,
"c\_lastyear" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_nianhao\_id")
)

## OCCASION\_CODES

OCCASION\_CODES
107995
CREATE TABLE "OCCASION\_CODES" (
"c\_occasion\_code" smallint(6) NOT NULL,
"c\_occasion\_desc" varchar(255) DEFAULT NULL,
"c\_occasion\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_occasion\_code")
)

## OFFICE\_CATEGORIES

OFFICE\_CATEGORIES
107997
CREATE TABLE "OFFICE\_CATEGORIES" (
"c\_office\_category\_id" smallint(6) NOT NULL,
"c\_category\_desc" varchar(255) DEFAULT NULL,
"c\_category\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_office\_category\_id")
)

## OFFICE\_CODES

OFFICE\_CODES
107999
CREATE TABLE "OFFICE\_CODES" (
"c\_office\_id" INTEGER(11) NOT NULL,
"c\_dy" smallint(6) NOT NULL DEFAULT 0,
"c\_office\_pinyin" varchar(255) DEFAULT NULL,
"c\_office\_chn" varchar(255) DEFAULT NULL,
"c\_office\_pinyin\_alt" varchar(255) DEFAULT NULL,
"c\_office\_chn\_alt" varchar(255) DEFAULT NULL,
"c\_office\_trans" varchar(255) DEFAULT NULL,
"c\_office\_trans\_alt" varchar(255) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_office\_id")
)

## OFFICE\_CODE\_TYPE\_REL

OFFICE\_CODE\_TYPE\_REL
108833
CREATE TABLE "OFFICE\_CODE\_TYPE\_REL" (
"c\_office\_id" INTEGER(11) NOT NULL,
"c\_office\_tree\_id" varchar(255) NOT NULL,
PRIMARY KEY ("c\_office\_id", "c\_office\_tree\_id")
)

## OFFICE\_TYPE\_TREE

OFFICE\_TYPE\_TREE
109214
CREATE TABLE "OFFICE\_TYPE\_TREE" (
"c\_office\_type\_node\_id" varchar(255) NOT NULL,
"c\_office\_type\_desc" varchar(255) DEFAULT NULL,
"c\_office\_type\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_parent\_id" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_office\_type\_node\_id")
)

## PARENTAL\_STATUS\_CODES

PARENTAL\_STATUS\_CODES
109271
CREATE TABLE "PARENTAL\_STATUS\_CODES" (
"c\_parental\_status\_code" smallint(6) NOT NULL,
"c\_parental\_status\_desc" varchar(255) DEFAULT NULL,
"c\_parental\_status\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_parental\_status\_code")
)

## POSSESSION\_ACT\_CODES

POSSESSION\_ACT\_CODES
109273
CREATE TABLE "POSSESSION\_ACT\_CODES" (
"c\_possession\_act\_code" smallint(6) NOT NULL,
"c\_possession\_act\_desc" varchar(255) DEFAULT NULL,
"c\_possession\_act\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_possession\_act\_code")
)

## POSSESSION\_ADDR

POSSESSION\_ADDR
109275
CREATE TABLE "POSSESSION\_ADDR" (
"c\_possession\_record\_id" INTEGER(11) NOT NULL,
"c\_personid" INTEGER(11) NOT NULL,
"c\_addr\_id" INTEGER(11) NOT NULL,
PRIMARY KEY ("c\_addr\_id", "c\_personid", "c\_possession\_record\_id")
)

## POSSESSION\_DATA

POSSESSION\_DATA
109277
CREATE TABLE "POSSESSION\_DATA" (
"c\_personid" INTEGER(11) DEFAULT NULL,
"c\_possession\_record\_id" INTEGER(11) NOT NULL,
"c\_sequence" smallint(6) DEFAULT NULL,
"c\_possession\_act\_code" smallint(6) DEFAULT NULL,
"c\_possession\_desc" varchar(255) DEFAULT NULL,
"c\_possession\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_quantity" varchar(255) DEFAULT NULL,
"c\_measure\_code" smallint(6) DEFAULT NULL,
"c\_possession\_yr" smallint(6) DEFAULT NULL,
"c\_possession\_nh\_code" smallint(6) DEFAULT NULL,
"c\_possession\_nh\_yr" smallint(6) DEFAULT NULL,
"c\_possession\_yr\_range" smallint(6) DEFAULT NULL,
"c\_addr\_id" INTEGER(11) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_possession\_record\_id")
)

## POSTED\_TO\_ADDR\_DATA

POSTED\_TO\_ADDR\_DATA
109282
CREATE TABLE "POSTED\_TO\_ADDR\_DATA" (
"c\_posting\_id" INTEGER(11) NOT NULL,
"c\_personid" INTEGER(11) DEFAULT NULL,
"c\_office\_id" INTEGER(11) NOT NULL,
"c\_addr\_id" INTEGER(11) NOT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_addr\_id", "c\_office\_id", "c\_posting\_id")
)

## POSTED\_TO\_OFFICE\_DATA

POSTED\_TO\_OFFICE\_DATA
114545
CREATE TABLE "POSTED\_TO\_OFFICE\_DATA" (
"c\_personid" INTEGER(11) DEFAULT NULL,
"c\_office\_id" INTEGER(11) NOT NULL,
"c\_posting\_id" INTEGER(11) NOT NULL,
"c\_sequence" smallint(6) DEFAULT NULL,
"c\_firstyear" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_code" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_year" smallint(6) DEFAULT NULL,
"c\_fy\_range" smallint(6) DEFAULT NULL,
"c\_lastyear" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_code" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_year" smallint(6) DEFAULT NULL,
"c\_ly\_range" smallint(6) DEFAULT NULL,
"c\_appt\_code" smallint(6) NOT NULL DEFAULT 0,
"c\_assume\_office\_code" smallint(6) DEFAULT NULL,
"c\_inst\_code" smallint(6) DEFAULT 0,
"c\_inst\_name\_code" smallint(6) DEFAULT 0,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_office\_id\_backup" INTEGER(11) DEFAULT NULL,
"c\_office\_category\_id" smallint(6) DEFAULT NULL,
"c\_fy\_intercalary" smallint(6) DEFAULT NULL,
"c\_fy\_month" smallint(6) DEFAULT NULL,
"c\_ly\_intercalary" smallint(6) DEFAULT NULL,
"c\_ly\_month" smallint(6) DEFAULT NULL,
"c\_fy\_day" smallint(6) DEFAULT NULL,
"c\_ly\_day" smallint(6) DEFAULT NULL,
"c\_fy\_day\_gz" smallint(6) DEFAULT NULL,
"c\_ly\_day\_gz" smallint(6) DEFAULT NULL,
"c\_dy" smallint(6) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_office\_id", "c\_posting\_id")
)

## POSTING\_DATA

POSTING\_DATA
131754
CREATE TABLE "POSTING\_DATA" (
"c\_personid" INTEGER(11) DEFAULT NULL,
"c\_posting\_id" INTEGER(11) NOT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_posting\_id")
)

## SCHOLARLYTOPIC\_CODES

SCHOLARLYTOPIC\_CODES
136465
CREATE TABLE "SCHOLARLYTOPIC\_CODES" (
"c\_topic\_code" smallint(6) NOT NULL,
"c\_topic\_desc" varchar(255) DEFAULT NULL,
"c\_topic\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_topic\_type\_code" smallint(6) DEFAULT NULL,
"c\_topic\_type\_desc" varchar(255) DEFAULT NULL,
"c\_topic\_type\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_topic\_code")
)

## SOCIAL\_INSTITUTION\_ADDR

SOCIAL\_INSTITUTION\_ADDR
136468
CREATE TABLE "SOCIAL\_INSTITUTION\_ADDR" (
"c\_inst\_name\_code" smallint(6) NOT NULL,
"c\_inst\_code" smallint(6) NOT NULL,
"c\_inst\_addr\_type\_code" smallint(6) NOT NULL,
"c\_inst\_addr\_begin\_year" smallint(6) DEFAULT NULL,
"c\_inst\_addr\_end\_year" smallint(6) DEFAULT NULL,
"c\_inst\_addr\_id" INTEGER(11) NOT NULL,
"inst\_xcoord" REAL NOT NULL,
"inst\_ycoord" REAL NOT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_inst\_addr\_id", "c\_inst\_addr\_type\_code", "c\_inst\_code", "c\_inst\_name\_code", "inst\_xcoord", "inst\_ycoord")
)

## SOCIAL\_INSTITUTION\_ADDR\_TYPES

SOCIAL\_INSTITUTION\_ADDR\_TYPES
136588
CREATE TABLE "SOCIAL\_INSTITUTION\_ADDR\_TYPES" (
"c\_inst\_addr\_type\_code" smallint(6) NOT NULL,
"c\_inst\_addr\_type\_desc" varchar(255) DEFAULT NULL,
"c\_inst\_addr\_type\_chn" varchar(255) DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_inst\_addr\_type\_code")
)

## SOCIAL\_INSTITUTION\_ALTNAME\_CODES

SOCIAL\_INSTITUTION\_ALTNAME\_CODES
136590
CREATE TABLE "SOCIAL\_INSTITUTION\_ALTNAME\_CODES" (
"c\_inst\_altname\_type" smallint(6) DEFAULT NULL,
"c\_inst\_altname\_desc" varchar(255) DEFAULT NULL,
"c\_inst\_altname\_chn" varchar(255) DEFAULT NULL,
"c\_notes" varchar(255) DEFAULT NULL
)

## SOCIAL\_INSTITUTION\_ALTNAME\_DATA

SOCIAL\_INSTITUTION\_ALTNAME\_DATA
136591
CREATE TABLE "SOCIAL\_INSTITUTION\_ALTNAME\_DATA" (
"c\_inst\_name\_code" smallint(6) DEFAULT NULL,
"c\_inst\_code" smallint(6) DEFAULT NULL,
"c\_inst\_altname\_type" smallint(6) DEFAULT NULL,
"c\_inst\_altname\_hz" varchar(255) DEFAULT NULL,
"c\_inst\_altname\_py" varchar(255) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL
)

## SOCIAL\_INSTITUTION\_CODES

SOCIAL\_INSTITUTION\_CODES
136592
CREATE TABLE "SOCIAL\_INSTITUTION\_CODES" (
"c\_inst\_name\_code" smallint(6) NOT NULL,
"c\_inst\_code" smallint(6) NOT NULL,
"c\_inst\_type\_code" smallint(6) DEFAULT NULL,
"c\_inst\_begin\_year" smallint(6) DEFAULT NULL,
"c\_by\_nianhao\_code" smallint(6) DEFAULT NULL,
"c\_by\_nianhao\_year" smallint(6) DEFAULT NULL,
"c\_by\_year\_range" smallint(6) DEFAULT NULL,
"c\_inst\_begin\_dy" smallint(6) DEFAULT NULL,
"c\_inst\_floruit\_dy" smallint(6) DEFAULT NULL,
"c\_inst\_first\_known\_year" smallint(6) DEFAULT NULL,
"c\_inst\_end\_year" smallint(6) DEFAULT NULL,
"c\_ey\_nianhao\_code" smallint(6) DEFAULT NULL,
"c\_ey\_nianhao\_year" smallint(6) DEFAULT NULL,
"c\_ey\_year\_range" smallint(6) DEFAULT NULL,
"c\_inst\_end\_dy" smallint(6) DEFAULT NULL,
"c\_inst\_last\_known\_year" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_inst\_code", "c\_inst\_name\_code")
)

## SOCIAL\_INSTITUTION\_NAME\_CODES

SOCIAL\_INSTITUTION\_NAME\_CODES
136712
CREATE TABLE "SOCIAL\_INSTITUTION\_NAME\_CODES" (
"c\_inst\_name\_code" smallint(6) NOT NULL,
"c\_inst\_name\_hz" varchar(255) NOT NULL DEFAULT '',
"c\_inst\_name\_py" varchar(255) NOT NULL DEFAULT '',
PRIMARY KEY ("c\_inst\_name\_code")
)

## SOCIAL\_INSTITUTION\_TYPES

SOCIAL\_INSTITUTION\_TYPES
136744
CREATE TABLE "SOCIAL\_INSTITUTION\_TYPES" (
"c\_inst\_type\_code" smallint(6) NOT NULL,
"c\_inst\_type\_py" varchar(255) DEFAULT NULL,
"c\_inst\_type\_hz" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_inst\_type\_code")
)

## STATUS\_CODES

STATUS\_CODES
136746
CREATE TABLE "STATUS\_CODES" (
"c\_status\_code" smallint(6) NOT NULL,
"c\_status\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_status\_desc\_chn" varchar(255) NOT NULL DEFAULT '',
PRIMARY KEY ("c\_status\_code")
)

## STATUS\_CODE\_TYPE\_REL

STATUS\_CODE\_TYPE\_REL
136751
CREATE TABLE "STATUS\_CODE\_TYPE\_REL" (
"c\_status\_code" smallint(6) NOT NULL,
"c\_status\_type\_code" varchar(255) NOT NULL,
PRIMARY KEY ("c\_status\_code", "c\_status\_type\_code")
)

## STATUS\_DATA

STATUS\_DATA
136753
CREATE TABLE "STATUS\_DATA" (
"c\_personid" INTEGER(11) NOT NULL,
"c\_sequence" smallint(6) NOT NULL,
"c\_status\_code" smallint(6) NOT NULL,
"c\_firstyear" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_code" smallint(6) DEFAULT NULL,
"c\_fy\_nh\_year" smallint(6) DEFAULT NULL,
"c\_fy\_range" smallint(6) DEFAULT NULL,
"c\_lastyear" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_code" smallint(6) DEFAULT NULL,
"c\_ly\_nh\_year" smallint(6) DEFAULT NULL,
"c\_ly\_range" smallint(6) DEFAULT NULL,
"c\_supplement" varchar(255) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_personid", "c\_sequence", "c\_status\_code")
)

## STATUS\_TYPES

STATUS\_TYPES
138220
CREATE TABLE "STATUS\_TYPES" (
"c\_status\_type\_code" varchar(255) NOT NULL,
"c\_status\_type\_desc" varchar(255) DEFAULT NULL,
"c\_status\_type\_chn" varchar(255) DEFAULT NULL,
"c\_status\_type\_parent\_code" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_status\_type\_code")
)

## TEXT\_BIBLCAT\_CODES

TEXT\_BIBLCAT\_CODES
138222
CREATE TABLE "TEXT\_BIBLCAT\_CODES" (
"c\_text\_cat\_code" smallint(6) NOT NULL,
"c\_text\_cat\_desc" varchar(255) NOT NULL DEFAULT '',
"c\_text\_cat\_desc\_chn" varchar(255) NOT NULL DEFAULT '',
"c\_text\_cat\_pinyin" varchar(255) NOT NULL DEFAULT '',
"c\_text\_cat\_parent\_id" varchar(255) DEFAULT NULL,
"c\_text\_cat\_level" varchar(255) DEFAULT NULL,
"c\_text\_cat\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_text\_cat\_code")
)

## TEXT\_BIBLCAT\_CODE\_TYPE\_REL

TEXT\_BIBLCAT\_CODE\_TYPE\_REL
138227
CREATE TABLE "TEXT\_BIBLCAT\_CODE\_TYPE\_REL" (
"c\_text\_cat\_code" smallint(6) NOT NULL,
"c\_text\_cat\_type\_id" varchar(255) NOT NULL,
PRIMARY KEY ("c\_text\_cat\_code", "c\_text\_cat\_type\_id")
)

## TEXT\_BIBLCAT\_TYPES

TEXT\_BIBLCAT\_TYPES
138229
CREATE TABLE "TEXT\_BIBLCAT\_TYPES" (
"c\_text\_cat\_type\_id" varchar(255) NOT NULL,
"c\_text\_cat\_type\_desc" varchar(255) DEFAULT NULL,
"c\_text\_cat\_type\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_text\_cat\_type\_parent\_id" varchar(255) DEFAULT NULL,
"c\_text\_cat\_type\_level" smallint(6) DEFAULT NULL,
"c\_text\_cat\_type\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_text\_cat\_type\_id")
)

## TEXT\_CODES

TEXT\_CODES
138231
CREATE TABLE "TEXT\_CODES" (
"c\_textid" INTEGER(11) NOT NULL,
"c\_title\_chn" varchar(255) DEFAULT NULL,
"c\_title" varchar(255) DEFAULT NULL,
"c\_title\_trans" varchar(255) DEFAULT NULL,
"c\_text\_type\_id" varchar(128) DEFAULT NULL,
"c\_text\_year" smallint(6) DEFAULT NULL,
"c\_text\_nh\_code" smallint(6) DEFAULT NULL,
"c\_text\_nh\_year" smallint(6) DEFAULT NULL,
"c\_text\_range\_code" smallint(6) DEFAULT NULL,
"c\_bibl\_cat\_code" smallint(6) DEFAULT 0,
"c\_extant" smallint(6) DEFAULT NULL,
"c\_text\_country" smallint(6) DEFAULT NULL,
"c\_text\_dy" smallint(6) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_url\_api" varchar(255) DEFAULT NULL,
"c\_url\_api\_coda" varchar(255) DEFAULT NULL,
"c\_url\_homepage" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_title\_alt\_chn" varchar(255) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_textid")
)

## TEXT\_INSTANCE\_DATA

TEXT\_INSTANCE\_DATA
140262
CREATE TABLE "TEXT\_INSTANCE\_DATA" (
"c\_textid" INTEGER(11) NOT NULL,
"c\_text\_edition\_id" smallint(6) NOT NULL,
"c\_text\_instance\_id" smallint(6) NOT NULL,
"c\_instance\_title\_chn" varchar(255) DEFAULT NULL,
"c\_instance\_title" varchar(255) DEFAULT NULL,
"c\_instance\_title\_trans" varchar(255) DEFAULT NULL,
"c\_part\_of\_instance" INTEGER(11) DEFAULT NULL,
"c\_part\_of\_instance\_notes" varchar(255) DEFAULT NULL,
"c\_pub\_country" smallint(6) DEFAULT NULL,
"c\_pub\_dy" smallint(6) DEFAULT NULL,
"c\_pub\_year" smallint(6) DEFAULT NULL,
"c\_pub\_nh\_code" smallint(6) DEFAULT NULL,
"c\_pub\_nh\_year" smallint(6) DEFAULT NULL,
"c\_pub\_range\_code" smallint(6) DEFAULT NULL,
"c\_pub\_loc" varchar(255) DEFAULT NULL,
"c\_publisher" varchar(255) DEFAULT NULL,
"c\_print" varchar(255) DEFAULT NULL,
"c\_pub\_notes" varchar(255) DEFAULT NULL,
"c\_source" INTEGER(11) DEFAULT NULL,
"c\_pages" varchar(255) DEFAULT NULL,
"c\_extant" smallint(6) DEFAULT NULL,
"c\_url\_api" varchar(255) DEFAULT NULL,
"c\_url\_homepage" varchar(255) DEFAULT NULL,
"c\_notes" TEXT DEFAULT NULL,
"c\_number" varchar(255) DEFAULT NULL,
"c\_counter" varchar(255) DEFAULT NULL,
"c\_title\_alt\_chn" varchar(255) DEFAULT NULL,
"c\_created\_by" varchar(255) DEFAULT NULL,
"c\_modified\_by" varchar(255) DEFAULT NULL,
"c\_created\_date" TEXT DEFAULT NULL,
"c\_modified\_date" TEXT DEFAULT NULL,
PRIMARY KEY ("c\_textid", "c\_text\_edition\_id", "c\_text\_instance\_id")
)

## TEXT\_ROLE\_CODES

TEXT\_ROLE\_CODES
140596
CREATE TABLE "TEXT\_ROLE\_CODES" (
"c\_role\_id" smallint(6) NOT NULL,
"c\_role\_desc" varchar(255) DEFAULT NULL,
"c\_role\_desc\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_role\_id")
)

## TEXT\_TYPE

TEXT\_TYPE
140598
CREATE TABLE "TEXT\_TYPE" (
"c\_text\_type\_code" varchar(255) NOT NULL,
"c\_text\_type\_desc" varchar(255) DEFAULT NULL,
"c\_text\_type\_desc\_chn" varchar(255) DEFAULT NULL,
"c\_text\_type\_parent\_id" varchar(255) DEFAULT NULL,
"c\_text\_type\_level" smallint(6) DEFAULT NULL,
"c\_text\_type\_sortorder" smallint(6) DEFAULT NULL,
PRIMARY KEY ("c\_text\_type\_code")
)

## YEAR\_RANGE\_CODES

YEAR\_RANGE\_CODES
140603
CREATE TABLE "YEAR\_RANGE\_CODES" (
"c\_range\_code" smallint(6) NOT NULL,
"c\_range" varchar(255) DEFAULT NULL,
"c\_range\_chn" varchar(255) DEFAULT NULL,
"c\_approx" varchar(255) DEFAULT NULL,
"c\_approx\_chn" varchar(255) DEFAULT NULL,
PRIMARY KEY ("c\_range\_code")
)

| table\_name                         | count     |
| :---------------------------------- | :-------- |
| ADDR\_BELONGS\_DATA                 | 37,117    |
| ADDR\_CODES                         | 30,099    |
| ADMIN\_CAT\_CODES                   | 211       |
| ADMIN\_CAT\_CODE\_TYPE\_REL         | 0         |
| ADMIN\_CAT\_TYPES                   | 0         |
| ALTNAME\_CODES                      | 21        |
| ALTNAME\_DATA                       | 207,074   |
| APPOINTMENT\_CODES                  | 116       |
| APPOINTMENT\_CODE\_TYPE\_REL        | 109       |
| APPOINTMENT\_TYPES                  | 13        |
| ASSOC\_CODES                        | 498       |
| ASSOC\_CODE\_TYPE\_REL              | 463       |
| ASSOC\_DATA                         | 188,413   |
| ASSOC\_TYPES                        | 45        |
| ASSUME\_OFFICE\_CODES               | 6         |
| BIOG\_ADDR\_CODES                   | 22        |
| BIOG\_ADDR\_DATA                    | 457,656   |
| BIOG\_INST\_CODES                   | 26        |
| BIOG\_INST\_DATA                    | 559       |
| BIOG\_MAIN                          | 658,339   |
| BIOG\_SOURCE\_DATA                  | 1,215,572 |
| BIOG\_TEXT\_DATA                    | 52,078    |
| CHORONYM\_CODES                     | 173       |
| COUNTRY\_CODES                      | 11        |
| DYNASTIES                           | 85        |
| ENTRY\_CODES                        | 272       |
| ENTRY\_CODE\_TYPE\_REL              | 280       |
| ENTRY\_DATA                         | 263,685   |
| ENTRY\_TYPES                        | 29        |
| ETHNICITY\_TRIBE\_CODES             | 498       |
| EVENTS\_ADDR                        | 4         |
| EVENTS\_DATA                        | 427       |
| EVENT\_CODES                        | 117       |
| EXTANT\_CODES                       | 4         |
| GANZHI\_CODES                       | 61        |
| HOUSEHOLD\_STATUS\_CODES            | 34        |
| INDEXYEAR\_TYPE\_CODES              | 31        |
| KINSHIP\_CODES                      | 479       |
| KIN\_DATA                           | 556,767   |
| KIN\_MOURNING                       | 159       |
| KIN\_MOURNING\_STEPS                | 159       |
| LITERARYGENRE\_CODES                | 12        |
| MEASURE\_CODES                      | 7         |
| MERGED\_PERSON\_DATA                | 2,374     |
| NIAN\_HAO                           | 682       |
| OCCASION\_CODES                     | 10        |
| OFFICE\_CATEGORIES                  | 15        |
| OFFICE\_CODES                       | 34,052    |
| OFFICE\_CODE\_TYPE\_REL             | 43,671    |
| OFFICE\_TYPE\_TREE                  | 2,739     |
| PARENTAL\_STATUS\_CODES             | 7         |
| POSSESSION\_ACT\_CODES              | 4         |
| POSSESSION\_ADDR                    | 62        |
| POSSESSION\_DATA                    | 60        |
| POSTED\_TO\_ADDR\_DATA              | 463,162   |
| POSTED\_TO\_OFFICE\_DATA            | 588,294   |
| POSTING\_DATA                       | 588,263   |
| SCHOLARLYTOPIC\_CODES               | 32        |
| SOCIAL\_INSTITUTION\_ADDR           | 3,857     |
| SOCIAL\_INSTITUTION\_ADDR\_TYPES    | 2         |
| SOCIAL\_INSTITUTION\_ALTNAME\_CODES | 1         |
| SOCIAL\_INSTITUTION\_ALTNAME\_DATA  | 0         |
| SOCIAL\_INSTITUTION\_CODES          | 4,010     |
| SOCIAL\_INSTITUTION\_NAME\_CODES    | 2,601     |
| SOCIAL\_INSTITUTION\_TYPES          | 7         |
| STATUS\_CODES                       | 284       |
| STATUS\_CODE\_TYPE\_REL             | 284       |
| STATUS\_DATA                        | 71,257    |
| STATUS\_TYPES                       | 13        |
| TEXT\_BIBLCAT\_CODES                | 144       |
| TEXT\_BIBLCAT\_CODE\_TYPE\_REL      | 144       |
| TEXT\_BIBLCAT\_TYPES                | 51        |
| TEXT\_CODES                         | 61,070    |
| TEXT\_INSTANCE\_DATA                | 9,817     |
| TEXT\_ROLE\_CODES                   | 12        |
| TEXT\_TYPE                          | 126       |
| YEAR\_RANGE\_CODES                  | 6         |

