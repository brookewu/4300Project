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
db_path = os.path.join(os.environ['ROOT_PATH'],'restaurants.sql')
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


def sql_search(episode):
    # keys = ['company_one', 'company_two', 'address', 'postal_code', 'stars', 'categories', 'useful_review', 'useful_count']
    query_sql = f"""SELECT company_one, company_two, address, postal_code, stars, categories, useful_review, useful_count FROM scores LEFT OUTER JOIN attributes ON (scores.company_two = attributes.name) WHERE LOWER( scores.company_one ) LIKE '%%{episode.lower()}%%' ORDER BY scores.jaccard_score DESC limit 10"""
    data = mysql_engine.query_selector(query_sql)
    query_business_attr_sql = query_sql = f"""SELECT * FROM attributes WHERE LOWER( name ) LIKE '%%{episode.lower()}%%' limit 1"""
    q_data = mysql_engine.query_selector(query_business_attr_sql)
    serialized = []
    for x in q_data:
        serialized.append({
                "name": x[1],
                "address": x[2],
                "postal_code": x[3],
                "stars": x[4],
                "categories": x[5],
                "useful_review": x[6],
                "useful_count": x[7],})
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
        })
    serialized.append(matches)
    return json.dumps(serialized, default=str)


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    return sql_search(text)


app.run(debug=True)
