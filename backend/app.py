import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = ""
MYSQL_PORT = 3306
MYSQL_DATABASE = "restaurants"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
# mysql_engine.load_file_into_db()
db_path = os.path.join(os.environ['ROOT_PATH'],'restaurants_old.sql')
mysql_engine.load_file_into_db(file_path = db_path)

app = Flask(__name__)
CORS(app)

# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this

# def select_business_attr_for(name):
#     query_sql = f"""SELECT * FROM attributes WHERE LOWER( name ) LIKE '%%{name.lower()}%%' limit 1"""
#     keys = ["id", "name", "address", "postal_code", "stars", "categories", "useful_review", "useful_count"]
#     data = mysql_engine.query_selector(query_sql)
#     return [dict(zip(keys, i)) for i in data]

# def get_business_attribute_cols():
#     column_lst_sql = f"""desc attributes"""
#     column_lst_data = mysql_engine.query_selector(column_lst_sql)
#     keys = [x[0] for x in column_lst_data]
#     return keys


def sql_search(episode, blacklist, min_rating):
    """
    Example response for query "t"
    [
        {'name': 'Tuna Bar', 'address': '205 Race St', 'postal_code': 19106, 'stars': 4.0, 'categories': 'Sushi Bars|Restaurants|Japanese', 'useful_review': '"Finally got a chance to check this place out for an early dinner on a weeknight and I loved it! I was really craving sushi so when my girlfriend recommended this place I was totally into it. I definitely did not expect to have a new favorite sushi spot!', 'useful_count': 0}, 
        [
            {'name': ' Fairmount- Philadelphia"', 'address': None, 'postal_code': None, 'stars': None, 'categories': None, 'useful_review': None, 'useful_count': None}, 
            {'name': 'México Lindo', 'address': '700 Moore St', 'postal_code': 19148, 'stars': 4.5, 'categories': 'Mexican|Restaurants', 'useful_review': '"What does a one $ sign', 'useful_count': 0}, 
            {'name': 'El Limon', 'address': '4514 City Ave', 'postal_code': 19131, 'stars': 4.0, 'categories': 'Mexican|Restaurants', 'useful_review': '"Absolutely fire. Just thinking about this is making me hungry... damn this diet.', 'useful_count': 0}, 
            {'name': 'Qdoba Mexican Grill', 'address': '1900 Chestnut St', 'postal_code': 19103, 'stars': 3.0, 'categories': 'Restaurants|Mexican', 'useful_review': '"I must have deleted and retyped what I\'m about to say 30 times before hitting post because it sounds extremely erotic in all the wrong ways. But here goes nothing.  Qdoba is stingy with the meat', 'useful_count': 0}, 
            {'name': 'La Fonda De Teresita', 'address': '1446 S 8th St', 'postal_code': 19147, 'stars': 4.0, 'categories': 'Mexican|Restaurants', 'useful_review': '"I don\'t normally jump the fun on reviewing anything but I just had the best steak tortas from here that I have ever had. Seriously', 'useful_count': 0}, 
            {'name': "Teresa's Mesa", 'address': '727 S 2nd St', 'postal_code': 19147, 'stars': 4.0, 'categories': 'Restaurants|Mexican', 'useful_review': '"This is a great new addition to Queen Village! I actually work very close to their other restaurant Los Camaradas. My coworkers and I frequent there often for their happy hour after work. #BestinphillyNACHOS. The first time I came in with my neighbor and noticed on the menu camaradas nachos and was pleasantly surprised to find out it was the same owners!', 'useful_count': 0}, 
            {'name': 'El Guero  Mexican Food Truck', 'address': '1256 W Montgomery Ave', 'postal_code': 19122, 'stars': 5.0, 'categories': 'Restaurants|Mexican', 'useful_review': '"AUTHENTIC Mexican food.  I just had the shrimp tacos', 'useful_count': 0}, 
            {'name': 'Los Jimenez', 'address': '2654 S 6th St', 'postal_code': 19148, 'stars': 4.5, 'categories': 'Restaurants|Mexican', 'useful_review': '"Great decision for a late lunch on Sunday!  My fiancee and I came in with the intent of trying the al pastor tacos that we heard about through philly.com.  ', 'useful_count': 0}, 
            {'name': 'El Purepecha', 'address': '315 N 12th St', 'postal_code': 19107, 'stars': 4.5, 'categories': 'Mexican|Restaurants', 'useful_review': '"Solid Mexican hole in the wall type joint. Friendly staff', 'useful_count': 0}, 
            {'name': 'Smiths Restaurant and Bar', 'address': '"39 S 19th St', 'postal_code': 0, 'stars': 99.9, 'categories': '3.0', 'useful_review': 'American (New)|Bars|Nightlife|Lounges|Restaurants', 'useful_count': 0}]
        ]
    """
    # Get matching restaurants and their attributes for the searched restaurant
    query_sql = f"""SELECT company_one, company_two, address, postal_code, stars, 
    categories, useful_review, useful_count, jaccard_score, cosine_score, 
        (jaccard_score * cosine_score * ( 
            IF( scores.company_two IN (
                SELECT * FROM (
                    SELECT company_two FROM scores
                    WHERE LOWER( scores.company_one ) LIKE '%%{blacklist.lower()}%%' 
                    ORDER BY (scores.jaccard_score * scores.cosine_score)
                    DESC LIMIT 5
                ) temp_table
                ), 0.99 , 1))) as combined_score 
        FROM scores LEFT OUTER JOIN attributes ON (scores.company_two = attributes.name) 
        WHERE LOWER( scores.company_one ) LIKE '{episode.lower()}%%' 
        AND LOWER( scores.company_two ) NOT LIKE '%%{blacklist.lower()}%%' 
        AND attributes.stars >= {min_rating}
        ORDER BY combined_score
        DESC limit 5 """
    
    data = mysql_engine.query_selector(query_sql)
    

    # Get attributes for the searched restaurant
    searched_restaurant = ""
    for x in data:
        searched_restaurant = x[0]
        break
    searched_restaurant = searched_restaurant.replace("'", "\\'")
    searched_restaurant = searched_restaurant.replace("&", "\&")

    query_business_attr_sql = query_sql = f"""SELECT name, address, postal_code, stars, 
    categories, useful_review, useful_count FROM attributes WHERE LOWER( name ) LIKE '{searched_restaurant.lower()}' limit 1"""
    q_data = mysql_engine.query_selector(query_business_attr_sql)
    
    serialized = []
    for x in q_data:
        serialized.append({
                "name": x[0],
                "address": x[1],
                "postal_code": x[2],
                "stars": x[3],
                "categories": x[4],
                "useful_review": x[5],
                "useful_count": x[6],})
    matches = []
    for x in data:
        matches.append({
            "name": x[1],
            "address": x[2],
            "postal_code": x[3],
            "stars": x[4],
            "categories": x[5],
            "useful_review": x[6],
            "useful_count": x[7],
            "jaccard_score": x[8],
            "cosine_score": x[9],
            "combined_score": x[10],
            "searched_company": x[0]
        })
    serialized.append(matches)
    return json.dumps(serialized, default=str)


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    blacklist = request.args.get("blacklist") or " "
    min_rating = request.args.get("min_rating")
    return sql_search(text, blacklist, min_rating)


# app.run(debug=True)
