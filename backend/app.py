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

def select_business_attr_for(name):
    query_sql = f"""SELECT * FROM attributes WHERE LOWER( name ) LIKE '%%{name.lower()}%%' limit 1"""
    keys = ["id", "name", "address", "postal_code", "stars", "categories", "useful_review", "useful_count"]
    data = mysql_engine.query_selector(query_sql)
    return [dict(zip(keys, i)) for i in data]

def get_business_attribute_cols():
    column_lst_sql = f"""desc attributes"""
    column_lst_data = mysql_engine.query_selector(column_lst_sql)
    keys = [x[0] for x in column_lst_data]
    return keys


def sql_search(episode):

    query_sql = f"""SELECT * FROM scores LEFT OUTER JOIN attributes ON (scores.company_one = attributes.name) WHERE LOWER( attributes.name ) LIKE '%%{episode.lower()}%%' ORDER BY scores.jaccard_score DESC limit 10"""
    data = mysql_engine.query_selector(query_sql)
    keys = get_business_attribute_cols()

    # mapping = [dict(zip(keys, i)) for i in data][0]
    # # mysql_engine.query_ender()
    # seialized_mapping = {}



    # query = "INSERT INTO tablename (text_for_field1, text_for_field2, text_for_field3, text_for_field4) VALUES (%s, %s, %s, %s)"


    # company_attr = select_business_attr_for(mapping['company'])[0]
    # company_attr = select_business_attr_for("5 fresh burger stop")[0]
    # seialized_mapping['company'] = { "name": mapping['company'], "useful_review":  company_attr["useful_review"]}
    # seialized_mapping['company'] = { "name":"5 fresh burger stop", "useful_review":  company_attr["useful_review"]}

    # for d_key in desired_keys:
    #     attr = select_business_attr_for(mapping[d_key])
    #     seialized_mapping[d_key] = mapping[d_key]
    




    # query_sql = f"""SELECT * FROM attributes WHERE LOWER( name ) LIKE '%%{episode.lower()}%%' limit 10"""
    # query_sql = f"""SELECT * FROM topjaccard WHERE LOWER( company ) LIKE '%%{episode.lower()}%%' limit 10"""
    # keys = ["id", "title", "descr"]
    # keys = ["id", "name", "address", "postal_code", "stars", "categories", "useful_review", "useful_count"]


    # data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data], default=str)
    # return json.dumps([seialized_mapping], default=str)


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/episodes")
def episodes_search():
    text = request.args.get("title")
    return sql_search(text)


app.run(debug=True)
