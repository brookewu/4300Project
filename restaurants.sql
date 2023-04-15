SET GLOBAL LOCAL_INFILE=1;

CREATE DATABASE IF NOT EXISTS restaurants;

USE restaurants;
DROP TABLE IF EXISTS attributes;
DROP TABLE IF EXISTS scores;

CREATE TABLE attributes(
   id            INTEGER  NOT NULL PRIMARY KEY 
  ,name          VARCHAR(51) NOT NULL
  ,address       VARCHAR(75)
  ,postal_code   INTEGER 
  ,stars         FLOAT(3,1) NOT NULL
  ,categories    VARCHAR(503) NOT NULL
  ,useful_review LONGTEXT NOT NULL -- TODO: Fix char overflow ruining last col TEXT, SMALL TEXT, BIG TEXT 65000, normalization 
  ,useful_count  INTEGER  NOT NULL 
);
 -- Note: automatically null/0 when userful_review overflows char limit https://stackoverflow.com/questions/23712943/what-happens-when-you-store-a-value-in-a-varchar-which-is-over-the-limit-in-sql

--  load data local infile 'preliminary_work/business_attributes.csv' into table attributes
--  fields terminated by ','
--  enclosed by '"'
--  lines terminated by '\n'
--  (FIELD1, name, address, postal_code, stars, categories, useful_review,useful_count);


CREATE TABLE scores(
   id             INTEGER NOT NULL PRIMARY KEY
  ,company_one    VARCHAR(51) NOT NULL
  ,company_two    VARCHAR(51) NOT NULL
  ,jaccard_score FLOAT(5,4) NOT NULL
);

LOAD DATA LOCAL INFILE '../preliminary_work/business_attributes.csv'  INTO TABLE attributes  FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';

LOAD DATA LOCAL INFILE '../preliminary_work/top_jaccard_better.csv'  INTO TABLE scores FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';