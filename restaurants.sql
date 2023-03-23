CREATE DATABASE IF NOT EXISTS restaurants;

USE restaurants;
DROP TABLE IF EXISTS attributes;


CREATE TABLE attributes(
   FIELD1        INTEGER  NOT NULL PRIMARY KEY 
  ,name          VARCHAR(51) NOT NULL
  ,address       VARCHAR(75)
  ,postal_code   INTEGER 
  ,stars         NUMERIC(3,1) NOT NULL
  ,categories    VARCHAR(503) NOT NULL
  ,useful_review VARCHAR(4999) NOT NULL
  ,useful_count  INTEGER  NOT NULL
);


LOAD DATA LOCAL INFILE 'preliminary_work/business_attributes.csv'  INTO TABLE attributes  FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
