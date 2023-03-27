SET GLOBAL LOCAL_INFILE=1;

CREATE DATABASE IF NOT EXISTS restaurants;

USE restaurants;
DROP TABLE IF EXISTS attributes;
DROP TABLE IF EXISTS topjaccard;

CREATE TABLE attributes(
   FIELD1        INTEGER  NOT NULL PRIMARY KEY 
  ,name          VARCHAR(51) NOT NULL
  ,address       VARCHAR(75)
  ,postal_code   INTEGER 
  ,stars         NUMERIC(3,1) NOT NULL
  ,categories    VARCHAR(503) NOT NULL
  ,useful_review VARCHAR(4999) NOT NULL -- TODO: Fix char overflow ruining last col TEXT, SMALL TEXT, BIG TEXT 65000, normalization 
  ,useful_count  INTEGER  NOT NULL 
);
 -- Note: automatically null/0 when userful_review overflows char limit https://stackoverflow.com/questions/23712943/what-happens-when-you-store-a-value-in-a-varchar-which-is-over-the-limit-in-sql

--  load data local infile 'preliminary_work/business_attributes.csv' into table attributes
--  fields terminated by ','
--  enclosed by '"'
--  lines terminated by '\n'
--  (FIELD1, name, address, postal_code, stars, categories, useful_review,useful_count);


CREATE TABLE topjaccard(
   FIELD1  BIT  NOT NULL PRIMARY KEY
  ,1st     VARCHAR(19) NOT NULL
  ,2nd     VARCHAR(19) NOT NULL
  ,3rd     VARCHAR(26) NOT NULL
  ,4th     VARCHAR(17) NOT NULL
  ,5th     VARCHAR(18) NOT NULL
  ,6th     VARCHAR(15) NOT NULL
  ,7th     VARCHAR(17) NOT NULL
  ,8th     VARCHAR(11) NOT NULL
  ,9th     VARCHAR(21) NOT NULL
  ,10th    VARCHAR(37) NOT NULL
  ,11th    VARCHAR(21) NOT NULL
  ,12th    VARCHAR(9) NOT NULL
  ,13th    VARCHAR(27) NOT NULL
  ,14th    VARCHAR(14) NOT NULL
  ,15th    VARCHAR(12) NOT NULL
  ,16th    VARCHAR(29) NOT NULL
  ,17th    VARCHAR(28) NOT NULL
  ,18th    VARCHAR(18) NOT NULL
  ,19th    VARCHAR(26) NOT NULL
  ,20th    VARCHAR(19) NOT NULL
  ,21st    VARCHAR(19) NOT NULL
  ,22nd    VARCHAR(28) NOT NULL
  ,23rd    VARCHAR(25) NOT NULL
  ,24th    VARCHAR(13) NOT NULL
  ,25th    VARCHAR(22) NOT NULL
  ,26th    VARCHAR(17) NOT NULL
  ,27th    VARCHAR(16) NOT NULL
  ,28th    VARCHAR(15) NOT NULL
  ,29th    VARCHAR(22) NOT NULL
  ,30th    VARCHAR(21) NOT NULL
  ,31st    VARCHAR(15) NOT NULL
  ,32nd    VARCHAR(13) NOT NULL
  ,33rd    VARCHAR(12) NOT NULL
  ,34th    VARCHAR(20) NOT NULL
  ,35th    VARCHAR(16) NOT NULL
  ,36th    VARCHAR(27) NOT NULL
  ,37th    VARCHAR(19) NOT NULL
  ,38th    VARCHAR(19) NOT NULL
  ,39th    VARCHAR(23) NOT NULL
  ,40th    VARCHAR(13) NOT NULL
  ,41st    VARCHAR(17) NOT NULL
  ,42nd    VARCHAR(25) NOT NULL
  ,43rd    VARCHAR(19) NOT NULL
  ,44th    VARCHAR(22) NOT NULL
  ,45th    VARCHAR(21) NOT NULL
  ,46th    VARCHAR(23) NOT NULL
  ,47th    VARCHAR(18) NOT NULL
  ,48th    VARCHAR(11) NOT NULL
  ,49th    VARCHAR(22) NOT NULL
  ,50th    VARCHAR(33) NOT NULL
  ,company VARCHAR(20) NOT NULL
);

LOAD DATA LOCAL INFILE '../preliminary_work/business_attributes.csv'  INTO TABLE attributes  FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';

LOAD DATA LOCAL INFILE '../preliminary_work/top_jaccard.csv'  INTO TABLE topjaccard FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';
