import json
import os
import collections
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
    crunchy, morning, fishy, nightlife, hearty, meaty, homey, fresh, flavorful, categories, top_10_words
    FROM attributes WHERE LOWER( name ) LIKE '{restaurant_name.lower()}' limit 1"""
    attributes_data = mysql_engine.query_selector(attributes_sql)
    for x in attributes_data:
        d = reformat_attributes(dict(x))
        return d
    
def get_disliked_similar_subquery(disliked):
    disliked_similar_subquery = f"""SELECT * FROM (
                    SELECT company_two as name FROM scores
                    WHERE LOWER( scores.company_one ) LIKE '{disliked.lower()}' 
                    ORDER BY (scores.jaccard_score * scores.cosine_score)
                    DESC LIMIT 5) temp_table """
    return disliked_similar_subquery

def get_disliked_score_subquery(disliked):
    disliked_similar_subquery = get_disliked_similar_subquery(disliked)
    disliked_score_subquery = f"""IF( scores.company_two IN ({disliked_similar_subquery} ), 0.98 , 1)"""
    return disliked_score_subquery

def get_input_score(trait, liked, diff = .02):
    """
    Gets the score for the inputted trait. 
    if liked = False then 'diff' will be subtracted to restaurants that have the trait 
    """
    
    liked_subquery = f"""SELECT name FROM attributes 
                    WHERE attributes.categories LIKE '%%{trait.lower()}%%' """
    
    if not liked : 
        diff *= -1
    score_subquery = f"""IF (scores.company_two IN ({liked_subquery}), {diff}, 0) """

    return score_subquery
    


def find_top_matches_and_attributes(preferred, disliked, min_rating, pos_cuisine, pos_specialty, 
                        pos_establishment, neg_cuisine, neg_specialty, neg_establishment, k):
    """
    Returns a LegacyCursorResult containing the top k restaurants that are similar
    to [searched_restaurant] and their attributes.
    """
    # disliked_score_subquery = f"""IF( scores.company_two IN (
    #             SELECT * FROM (
    #                 SELECT company_two FROM scores
    #                 WHERE LOWER( scores.company_one ) LIKE '{disliked.lower()}' 
    #                 ORDER BY (scores.jaccard_score * scores.cosine_score)
    #                 DESC LIMIT 5
    #             ) temp_table
    #             ), 0.98 , 1)"""
    
    disliked_score_subquery = get_disliked_score_subquery(disliked)
    liked_cuisine = get_input_score(pos_cuisine, True)
    liked_specialty = get_input_score(pos_specialty, True)
    liked_establishment = get_input_score(pos_establishment, True)
    
    disliked_cuisine = get_input_score(neg_cuisine, False)
    disliked_specialty = get_input_score(neg_specialty, False)
    disliked_establishment = get_input_score(neg_establishment, False)

    # TODO: Incorporate inputs pos_cuisine, pos_specialty, pos_establishment, 
    # neg_cuisine, neg_specialty, neg_establishment to weights
    # done ???
    
    query_sql = f"""SELECT company_two as name, address, postal_code, stars, 
        categories, top_10_words,
        crunchy, morning, fishy, nightlife, hearty, meaty, homey, fresh, flavorful,
        jaccard_score, cosine_score, svd_score, 
    ((0.3 * jaccard_score) + (0.35 * cosine_score) + (0.3 * svd_score) + 
    {disliked_score_subquery} + {liked_cuisine} + {liked_specialty} + {liked_establishment}
    + {disliked_cuisine} + {disliked_specialty} + {disliked_establishment} ) 
    as combined_score 
    FROM scores LEFT OUTER JOIN attributes ON (scores.company_two = attributes.name) 
    WHERE LOWER( scores.company_one ) LIKE '{preferred.lower()}' 
    AND LOWER( scores.company_two ) NOT LIKE '{disliked.lower()}' 
    AND attributes.stars >= {min_rating}
    ORDER BY combined_score
    DESC limit {k} """
    data = mysql_engine.query_selector(query_sql)
    return data

def is_cuisine(category_name):
    return category_name in get_cuisines()

def is_speciality(category_name):
    return category_name in get_specialty_foods()

def is_establishment(category_name):
    return category_name in get_establishments()

def reformat_attributes(d):
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

    return d


def generate_metrics(d, s, d_traits, s_traits_top):
    """
    Returns a list strings w facts about the output restaurant [d]
    """
    metrics_lst = []
    metrics_lst.append("We have estimated that "+ d.get("name") + " is a "+ 
                     str(round(d_traits[0][1]*100))+
                     "% match to the " + d_traits[0][0] + " trait, " + str(round(d_traits[1][1]*100))+
                     "% match to the " + d_traits[1][0] + " trait, and " + str(round(d_traits[2][1]*100))+
                     "% match to the " + d_traits[2][0] + " trait")
    
    total_trait_score = 0
    matching_trait_score = 0
    for t in d_traits:
        total_trait_score += t[1]
        if t[0] in s_traits_top:
            matching_trait_score += t[1]

    matching_total = round(((matching_trait_score*100)/(total_trait_score*100))*100)
    # (sum of top input traits scores in outputted restaurant) / (sum of all scores of outputted restaurant)
    metrics_lst.append("There is a " + str(matching_total) + "%" + " similarity to the top 3 traits of " + s.get("name"))

    return metrics_lst

def generate_favorable(d, s, d_traits_top, s_traits_top, pos_cuisine, pos_specialty, pos_establishment,):
    """
    Returns a list two dictionaries. One for favorable traits between both the 
    input and output and another for user-input preferances.
    """
    favorable_traits = []
    intersection_cuisines = (collections.Counter(d.get("cuisines")) & collections.Counter(s.get("cuisines"))).keys()
    intersection_specialities = (collections.Counter(d.get("specialities")) & collections.Counter(s.get("specialities"))).keys()
    intersection_establishments = (collections.Counter(d.get("establishments")) & collections.Counter(s.get("establishments"))).keys()
    intersection_top_words = (collections.Counter(d.get("top_words")) & collections.Counter(s.get("top_words"))).keys()
    intersection_top_traits = (collections.Counter(d_traits_top) & collections.Counter(s_traits_top)).keys()
    
    both_favorable = []
    if len(intersection_cuisines) != 0:
        both_favorable.append("Feature cuisine from " + ",".join(list(intersection_cuisines)))
    if len(intersection_specialities) != 0:
        both_favorable.append("Offer specialities like " + ",".join(list(intersection_specialities)))
    if len(intersection_establishments) != 0:
        both_favorable.append("Considered as " + ",".join(list(intersection_establishments)))
    if len(intersection_top_words) != 0:
        both_favorable.append("Are commonly described as " + ",".join(list(intersection_top_words)))
    if len(intersection_top_traits) != 0:
        both_favorable.append("Share traits " + ",".join(list(intersection_top_traits)))

    if len(both_favorable) > 0:
        both_dict = {
            "intro" : "Both "+ d.get("name")+ " and " + s.get("name")+ "...",
            "points": both_favorable
        }
        favorable_traits.append(both_dict)
    
    # TODO: Incorporate inputs pos_cuisine, pos_specialty, pos_establishment 
    # to favorable_traits when applicable
    # done??
    single_dict = {}
    user_inputted = []
    if pos_cuisine != "":
        d_cuisines = d.get("cuisines")
        if pos_cuisine in d_cuisines:
            user_inputted.append(d.get("name") + " specializes in " + pos_cuisine)
        
    if pos_establishment != "":
        d_est = d.get("establishments")
        if pos_establishment in d_est:
            user_inputted.append(d.get("name") + " is a " + pos_establishment)

    if pos_specialty != "":
        d_spec = d.get("specialities")
        if pos_specialty in d_spec:
            user_inputted.append(d.get("name") + " serves " + pos_specialty)

    single_dict["pos_inputs"] = user_inputted

    favorable_traits.append(single_dict)
    return favorable_traits


def generate_unfavorable(d, s, disliked_restaurant, neg_cuisine, neg_specialty, neg_establishment):
    """
    Returns a list two dictionaries. One for favorable traits between both the 
    input and output and another for user-input preferances.
    """
    unfavorable_traits = []

    disliked_similar_subquery = get_disliked_similar_subquery(disliked_restaurant)
    data = mysql_engine.query_selector(disliked_similar_subquery)

    for x in data:
        sim_dislike = dict(x)
        if d.get("name") == sim_dislike.get("name"):
            unfavorable_traits.append("It is similar to the disliked restaurant " + disliked_restaurant)
    
    # TODO: Incorporate inputs neg_cuisine, neg_specialty, neg_establishment
    # to unfavorable_traits when applicable
    # done ??

    single_dict = {}
    user_inputted = []
    if neg_cuisine != "":
        d_cuisines = d.get("cuisines")
        if neg_cuisine in d_cuisines:
            user_inputted.append(d.get("name") + " features " + neg_cuisine + " cuisine")
        
    if neg_establishment != "":
        d_est = d.get("establishments")
        if neg_establishment in d_est:
            user_inputted.append(d.get("name") + " is a " + neg_establishment)

    if neg_specialty != "":
        d_spec = d.get("specialities")
        if neg_specialty in d_spec:
            user_inputted.append(d.get("name") + " serves " + neg_specialty)

    single_dict["neg_inputs"] = user_inputted

    unfavorable_traits.append(single_dict)
    return unfavorable_traits


def generate_description(s, d, disliked_restaurant, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment):
    """
    Returns a description of facts, favorable, and unfavorable aspects of the outputted restaurant.
    """
    description = {}
    d_traits = d.get("traits")
    s_traits = s.get("traits")
    s_traits_top = [t[0] for t in s_traits][0:3]
    d_traits_top = [t[0] for t in d_traits][0:3]

    metrics_lst = generate_metrics(d, s, d_traits, s_traits_top)
    favorable_traits = generate_favorable(d, s, d_traits_top, s_traits_top, pos_cuisine, pos_specialty, pos_establishment,)
    unfavorable_traits = generate_unfavorable(d, s, disliked_restaurant, neg_cuisine, neg_specialty, neg_establishment)

    # Build final description dictionary
    description["facts"] = {
        "intro": "Metrics...",
        "points": metrics_lst
    }
    description["favorable"] = {
        "intro": "You may also like " + d.get("name") + " because...",
        "points": favorable_traits
    }
    description["unfavorable"] = {
        "intro": "However, note the following...",
        "points": unfavorable_traits
    }
    
    return description

def serialize_result_data(searched_attributes_dict, result_data, disliked_restaurant, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment):
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
        d = reformat_attributes(dict(x))
        d["description"] = generate_description(searched_attributes_dict, d, disliked_restaurant, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment,)
        matches.append(d)
    serialized.append(matches)
    return serialized

def sql_search(input, disliked, min_rating, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment, k):
    """
    Returns the top k similar results for [input] with conditions [blacklist] and [min_rating].
    """
    # Match input with a restaurant to be our searched restaurant
    searched_restaurant = get_restaurant_name(input)

    # Match disliked input with a restaurant
    disliked_restaurant = get_restaurant_name(disliked)

    # Get matching restaurants and their attributes for the searched restaurant
    result_data = find_top_matches_and_attributes(searched_restaurant, disliked_restaurant, min_rating, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment, k)
    
    # Get attributes for the searched restaurant
    searched_attributes_dict = get_restaurant_attributes(searched_restaurant)

    # Serialize results for json response
    serialized = serialize_result_data(searched_attributes_dict, result_data, disliked_restaurant, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment,)

    print(json.dumps(serialized, default=str))
    return json.dumps(serialized, default=str)
   
#------------------------------ ROUTES ------------------------------
# Main endpoints
@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/results")
def restaurant_search():
    """
    Returns top results.

    Args:
        preferred: String of user input for preferred restaurant
        disliked: String of user input for disliked restaurant
        min_rating: Integer of minimum star rating
        pos_cuisine: String of desired cusine selected
        pos_specialty: String of desired specialty selected
        pos_establishment: String of desired establishment selected
        neg_cuisine: String of disliked cusine selected
        neg_specialty: String of disliked specialty selected
        neg_establishment: String of disliked establishment selected
        traits:
    """
    preferred = request.args.get("preferred")
    disliked = request.args.get("disliked") or " "
    min_rating = request.args.get("min_rating")
    pos_cuisine = request.args.get("pos_cuisine") or " "
    pos_specialty = request.args.get("pos_specialty") or " "
    pos_establishment = request.args.get("pos_establishment") or " "
    neg_cuisine = request.args.get("neg_cuisine") or " "
    neg_specialty = request.args.get("neg_specialty") or " "
    neg_establishment = request.args.get("neg_establishment") or " "

    return sql_search(preferred, disliked, min_rating, pos_cuisine, pos_specialty, pos_establishment, neg_cuisine, neg_specialty, neg_establishment, 5)

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
