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

#------------------------------ HELPERS ------------------------------
def get_business_attribute_cols():
    column_lst_sql = f"""desc attributes"""
    column_lst_data = mysql_engine.query_selector(column_lst_sql)
    keys = [x[0] for x in column_lst_data]
    return keys

def get_categories():
    """
    Returns a set of all "good" cuisine foods from Yelp's business categories.
    """
    categories_sql = f"""SELECT categories FROM attributes"""
    categories_data = mysql_engine.query_selector(categories_sql)

    category_set = set()
    for x in categories_data:
        cat_lst = x[0].strip().split("|")
        for c in cat_lst:
            category_set.add(c)

    return category_set

def get_restaurant_name(query):
    """
    Returns a string name identifier of a restaurant given some [query].
    Note: Adds escape in front of special characters for sql string comparison 
    """
    matched_restaurant_sql = f"""SELECT company_one FROM scores WHERE LOWER( scores.company_one ) LIKE '{query.lower()}%%' LIMIT 1"""
    matched_restaurant_data = mysql_engine.query_selector(matched_restaurant_sql)
    
    # Extract out searched restaurant from sql data response
    matched_restauarant = ""
    for x in matched_restaurant_data:
        matched_restauarant = x[0]
        break

    # Reformat serached restauarnt string to allow sql comparison with special characters
    matched_restauarant = matched_restauarant.replace("'", "\\'")
    matched_restauarant = matched_restauarant.replace("&", "\&")

    return matched_restauarant

def get_restaurant_attributes(restaurant_name):
    """
    Returns a dictionary containing business attributes for [restaurant_name]
    """
    attributes_sql = f"""SELECT name, address, postal_code, stars, 
    categories FROM attributes WHERE LOWER( name ) LIKE '{restaurant_name.lower()}' limit 1"""
    attributes_data = mysql_engine.query_selector(attributes_sql)
    for x in attributes_data:
        return dict(x)

def find_top_matches_and_attributes(searched_restaurant, blacklist_restaurant, min_rating, k):
    """
    Returns a LegacyCursorResult containing the top k restaurants that are similar
    to [searched_restaurant] and their attributes.
    """
    blacklist_score_subquery = f"""IF( scores.company_two IN (
                SELECT * FROM (
                    SELECT company_two FROM scores
                    WHERE LOWER( scores.company_one ) LIKE '{blacklist_restaurant.lower()}' 
                    ORDER BY (scores.jaccard_score * scores.cosine_score)
                    DESC LIMIT 5
                ) temp_table
                ), 0.98 , 1)"""
    query_sql = f"""SELECT company_two, address, postal_code, stars, 
    categories, top_10_words,
    crunchy, morning, fishy, nightlife, hearty, meaty, homey, fresh, flavorful,
    jaccard_score, cosine_score, svd_score, 
    ((0.3 * jaccard_score) + (0.35 * cosine_score) + (0.3 * svd_score) + 
    {blacklist_score_subquery}) as combined_score 
    FROM scores LEFT OUTER JOIN attributes ON (scores.company_two = attributes.name) 
    WHERE LOWER( scores.company_one ) LIKE '{searched_restaurant.lower()}' 
    AND LOWER( scores.company_two ) NOT LIKE '{blacklist_restaurant.lower()}' 
    AND attributes.stars >= {min_rating}
    ORDER BY combined_score
    DESC limit {k} """
    
    # query_sql = f"""SELECT top_10_words,
    # crunchy, morning, fishy, nightlife, hearty, meaty, homey, fresh, flavorful, 
    # ((0.3 * jaccard_score) + (0.35 * cosine_score) + (0.3 * svd_score) + 
    # {blacklist_score_subquery}) as combined_score 
    # FROM scores LEFT OUTER JOIN attributes ON (scores.company_two = attributes.name) 
    # WHERE LOWER( scores.company_one ) LIKE '{searched_restaurant.lower()}' 
    # AND LOWER( scores.company_two ) NOT LIKE '{blacklist_restaurant.lower()}' 
    # AND attributes.stars >= {min_rating}
    # ORDER BY combined_score
    # DESC limit {k} """
    data = mysql_engine.query_selector(query_sql)
    return data

def is_cuisine(category_name):
    return category_name in get_cuisines()

def is_speciality(category_name):
    return category_name in get_specialty_foods()

def is_establishment(category_name):
    return category_name in get_establishments()

def serialize_result_data(searched_attributes_dict, result_data):
    """
    Returns a reformatted result data. Formatted in a list where the first index
    contains a dictionary of attribute information for the searched restaurant and is followed by a
    list containing dictionaries of attribute and score information for the top k restaurants.

    [ dict of attributes for searched restaurant, [dict of attributes and scores for top 1 match, ... top 2 match ... ]]
    """
    serialized = []
    serialized.append(searched_attributes_dict)
    matches = []
    for x in result_data:
        d = dict(x)
        d["name"] = d["company_two"]
        categories = d["categories"].split("|")
        cuisines = []
        specialities = []
        establishments = []
        for c in categories:
            if is_cuisine(c):
                cuisines.append(c)
            elif is_speciality(c):
                specialities.append(c)
            elif is_establishment(c):
                establishments.append(c)
        d["cuisines"] = cuisines
        d["specialities"] = specialities
        d["establishments"] = establishments

        top_10_words = d["top_10_words"]
        top_words= [x.strip() for x in top_10_words.split(';')]
        d["top_words"] = top_words

        traits = [
            ("crunchy", d["crunchy"]), ("morning", d["morning"]), ("fishy", d["fishy"]),
            ("nightlife", d["nightlife"]), ("hearty", d["hearty"]), ("meaty", d["meaty"]),
            ("homey", d["homey"]), ("fresh", d["fresh"]), ("flavorful", d["flavorful"]),
            ]
        d["traits"] = sorted(traits, key=lambda x: x[1], reverse=True)
        
        d.pop("company_two")
        d.pop("categories")
        d.pop("top_10_words")
        d.pop("crunchy")
        d.pop("morning")
        d.pop("fishy")
        d.pop("nightlife")
        d.pop("hearty")
        d.pop("meaty")
        d.pop("homey")
        d.pop("fresh")
        d.pop("flavorful")
        matches.append(d)
    serialized.append(matches)
    return serialized

def sql_search(input, blacklist, min_rating, k):
    """
    Returns the top k similar results for [input] with conditions [blacklist] and [min_rating].
    """
    # Match input with a restaurant to be our searched restaurant
    searched_restaurant = get_restaurant_name(input)

    # Match blacklist input with a restaurant
    blacklist_restaurant = get_restaurant_name(blacklist)

    # Get matching restaurants and their attributes for the searched restaurant
    result_data = find_top_matches_and_attributes(searched_restaurant, blacklist_restaurant, min_rating, k)
    
    # Get attributes for the searched restaurant
    searched_attributes_dict = get_restaurant_attributes(searched_restaurant)

    # Serialize results for json response
    serialized = serialize_result_data(searched_attributes_dict, result_data)

    print(json.dumps(serialized, default=str))
    return json.dumps(serialized, default=str)
   
#------------------------------ ROUTES ------------------------------
# Main endpoints
@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/results")
def restaurant_search():
    text = request.args.get("title")
    blacklist = request.args.get("blacklist") or " "
    min_rating = request.args.get("min_rating")
    return sql_search(text, blacklist, min_rating, 5)

# Available categories
@app.route("/cuisines")
def get_cuisines():
    """
    Returns a set of all "good" cuisine foods from Yelp's business categories.
    """
    cusines = {'Armenian', 'Israeli', 'Greek', 'Egyptian', 'Mediterranean', 'Indonesian', 'Himalayan/Nepalese', 'Venezuelan', 'Scandinavian', 'Modern European', 'Salvadoran', 'Hawaiian', 'Taiwanese', 'Cambodian', 'American (New)', 'Polish', 'Vietnamese', 'Russian', 'Halal', 'Argentine', 'Colombian', 'Asian Fusion', 'Cajun/Creole', 'Ethiopian', 'Korean', 'Soul Food', 'Pakistani', 'Peruvian', 'Chinese', 'Italian', 'Basque', 'Spanish', 'Thai', 'Indian', 'Szechuan', 'Sicilian', 'Sardinian', 'Mongolian', 'Filipino', 'Bangladeshi', 'Middle Eastern', 'Caribbean', 'Austrian', 'Pan Asian', 'Uzbek', 'Senegalese', 'Shanghainese',  'Ukrainian', 'French', 'Persian/Iranian', 'Afghan', 'Arabic', 'Barbeque', 'Mexican', 'Turkish', 'Cuban', 'Seafood', 'Latin American', 'Honduran', 'Puerto Rican','Hungarian', 'South African', 'Irish', 'Georgian',
              'Brazilian', 'Tex-Mex', 'German', 'Dominican', 'Iberian',  
              'New Mexican Cuisine', 'Australian', 'British', 'Moroccan', 'Hainan', 'American (Traditional)', 
             'Cantonese', 'African', 'Singaporean', 'Portuguese', 'Haitian', 'Malaysian', 'Laotian', 'Japanese', 
            'Belgian', 'Southern', 'Burmese', 'Lebanese'}
    
    return json.dumps(cusines, default=str)
    
@app.route("/specialty")
def get_specialty_foods():
    """
    Returns a set of all "good" specialty foods from Yelp's business categories.
    """
    specialty_foods = {'Cupcakes', 'Teppanyaki', 'Hot Dogs', 'Donuts', 'Ramen', 'Fish & Chips', 'Wraps', 'Bagels', 'Falafel', 'Poke', 'Macarons', 'Shaved Ice', 'Noodles', 'Soup', 'Pretzels', 'Cheesesteaks', 'Kombucha', 'Chicken Wings', 'Japanese Curry', 'Hot Pot', 'Gelato', 'Tacos', 'Salad', 
                     'Burgers', 'Waffles', 'Beer', 'Empanadas', 'Acai Bowls', 'Sandwiches','Kebab', 'Bubble Tea', 'Fondue', 'Coffee & Tea', 'Fruits & Veggies',
                      'Pizza', 'Tapas/Small Plates', 'Ice Cream & Frozen Yogurt', 'Custom Cakes'}
    return json.dumps(specialty_foods, default=str)

@app.route("/dietary")
def get_dietary_restrictions():
    """
    Returns a set of all dietary from Yelp's business categories.
    """
    dietary_restrictions = { 'Vegan', 'Gluten-Free', 'Kosher', 'Vegetarian'}
    return json.dumps(dietary_restrictions, default=str)

@app.route("/establishments")
def get_establishments():
    """
    Returns a set of all "good" establishments from Yelp's business categories.
    """
    establishments = {'Gastropubs', 'Active Life', 'Pasta Shops', 'Supper Clubs', 'Colleges & Universities', 'Bakeries', 'Grocery',  'Delicatessen', 'Dive Bars','Bistros', 'Creperies', 'Speakeasies', 'Fast Food', 'Wine Bars', 'Hookah Bars', 'Themed Cafes', 'Delis', 'Tiki Bars', 'Beer Hall', 'Champagne Bars', 'Distilleries', 'Public Markets', 'Beer Bar', 'Conveyor Belt Sushi', 'Food Trucks', 'Lounges', 'Cocktail Bars', 'Meat Shops',  'Irish Pub',  'Food Banks',  'Desserts', 'Food Court', 'Tapas Bars', 
                     'Farmers Market', 'Patisserie/Cake Shop', 'Comedy Clubs', 'Candy Stores', 'Pop-Up Restaurants', 'Chocolatiers & Shops', 'Tea Rooms', 'Bars', 'Convenience Stores', 'Food Stands', 'Gay Bars', 'Street Vendors', 'Seafood Markets', 'Brasseries',  'Piano Bars', 'Cafes', 'Brewpubs', 'Jazz & Blues', 'Poutineries', 'Cideries', 
                     'Internet Cafes', 'Casinos', 'Breweries', 'Coffee Roasteries','Do-It-Yourself Food', 'Live/Raw Food', 'Cheese Shops','Organic Stores', 
                     'Strip Clubs', 'Chicken Shop', 'Sushi Bars', 'Dim Sum', 'Izakaya', 'Smokehouse', 'Sports Bars',
                     'Butcher', 'Buffets', 'Wineries', 'Juice Bars & Smoothies', 'Steakhouses',
                     'Beer Gardens', 'Diners', 'Cafeteria',  'Karaoke', 'Pubs', 'Whiskey Bars', 'Dinner Theater'}
    return json.dumps(establishments, default=str)

@app.route("/traits")
def get_reviewer_defined_traits():
    """
    Returns a list of all review defined traits (aka vibes) determined using SVD
    """
    traits = ["crunchy", "morning", "fishy", "nightlife", "hearty", "meaty", "homey", "fresh", "flavorful"]
    return json.dumps(traits, default=str)

# Run application
app.run(debug=True)
