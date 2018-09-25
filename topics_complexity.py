# -*- coding: utf-8 -*-
"""
Created on Fri Sep 14 14:04:53 2018

@author: Anjana
"""


import os
import re
import math
from required import topic_model
from required import text_indexes
import json

def generate_topics_complexity(folder_Path):
    
    resourse_path = folder_Path

    #Files to be read
    data_files = []
    # for file in os.listdir(resourse_path):
    #     if file.endswith(".txt"):
    #         data_files.append(file)
    # print(data_files)

    for root, dirs, files in os.walk(resourse_path):
        for name in files:
            if name.endswith((".txt")):
                path = os.path.join(root, name)
                data_files.append(path)

    print(data_files)
            
    
    #function to read text files in a directory and add that to a array
    def get_files(dir):
        x = 0
        doc_list = []
        for file in dir:
            val = 'file_'
            temp = 'temp_'
            val += 'x'
            temp += 'x'
            with open(file, 'r') as temp:
                val=temp.read().replace('\n', '')
            doc_list.append(val)
            x += 1
        return doc_list
    
    #Get the text bundle
    text = ''.join(get_files(data_files)) 
    
    textWithoutNumbers = ''.join([i for i in text if not i.isdigit()])
    
    test_data = re.sub(r"[\(\[].*?[\)\]]", "", textWithoutNumbers)
    
    
    rake_object = topic_model.Rake("required/SmartStoplist.txt", 5, 3, 4)
    
    keywords = rake_object.run(text)
    keys = []
    for word in keywords:
    #    print(word[0])
        keys.append(word[0])
#    print ("Keywords:", keys)
    
    
    smog_index = text_indexes.smog_index(test_data)
    flesch_kincaid_grade = text_indexes.flesch_kincaid_grade(test_data)
    coleman_liau_index = text_indexes.coleman_liau_index(test_data)
    automated_readability_index = text_indexes.automated_readability_index(test_data)
    gunning_fog = text_indexes.gunning_fog(test_data)
    dale_chall_readability_score = text_indexes.dale_chall_readability_score(test_data)
    flesch_reading_ease = text_indexes.flesch_reading_ease(test_data)
    
    index_sum = smog_index + flesch_kincaid_grade + coleman_liau_index + automated_readability_index + gunning_fog + dale_chall_readability_score + flesch_reading_ease
    
    average_level = (index_sum/47)*7
    
    #print('Sum', index_sum) 
    level = math.ceil(average_level)
#    print('Level', level)
    
    
    courseData = {
            "topics":keys,
            "level":level
        }
    
    jsonData = json.dumps(courseData)
    
#    print('Final Object: ', jsonData)
    #print('flesch_reading_ease', flesch_reading_ease)
    #print('smog_index', smog_index)
    #print('flesch_kincaid_grade', flesch_kincaid_grade)
    #print('coleman_liau_index', coleman_liau_index)
    #print('automated_readability_index', automated_readability_index)
    #print('dale_chall_readability_score', dale_chall_readability_score)
    #print('gunning_fog', gunning_fog)
    
    return jsonData