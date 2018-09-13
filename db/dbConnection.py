import pymongo
import configparser
import json

config = configparser.ConfigParser()
with open('./config.json', 'r') as f:
    config = json.load(f)

dbClient = pymongo.MongoClient(config['DB_CLIENT'])
db = dbClient[config['DATABASE']]

# print(db.list_collection_names())