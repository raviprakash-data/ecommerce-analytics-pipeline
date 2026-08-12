CREATE CATALOG IF NOT EXIST retail_lakehouse;
CREATE SCHEMA IF NOT EXIST retail_lakehouse.bronze;
CREATE SCHEMA IF NOT EXIST  retail_lakehouse.silver;
CREATE SCHEMA IF NOT EXIST retail_lakehouse.gold;
CREATE VOLUME IF NOT EXIST retail_lakehouse.bronze.raw_files;
