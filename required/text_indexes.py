# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 11:14:18 2018

@author: Anjana
"""
from textstat.textstat import  textstat

def smog_index(text):
    
    score = textstat.smog_index(text)
    level = 0
    if 0<score<6:
        level = 1
    elif 6<=score<8:
        level = 2
    elif 8<=score<10:
        level = 3
    elif 10<=score<11:
        level = 4
    elif 11<=score<12:
        level = 5
    elif 12<=score<13:
        level = 6
    elif 13<=score:
        level = 7
        
    return level

def flesch_kincaid_grade(text):
    
    score = textstat.flesch_kincaid_grade(text)
    level = 0
    if 0<score<6:
        level = 1
    elif 6<=score<8:
        level = 2
    elif 8<=score<10:
        level = 3
    elif 10<=score<11:
        level = 4
    elif 11<=score<12:
        level = 5
    elif 12<=score<13:
        level = 6
    elif 13<=score:
        level = 7
        
    return level

def coleman_liau_index(text):
    
    score = textstat.coleman_liau_index(text)
    level = 0
    if 0<score<6:
        level = 1
    elif 6<=score<8:
        level = 2
    elif 8<=score<10:
        level = 3
    elif 10<=score<11:
        level = 4
    elif 11<=score<12:
        level = 5
    elif 12<=score<13:
        level = 6
    elif 13<=score:
        level = 7
        
    return level

def automated_readability_index(text):
    
    score = textstat.automated_readability_index(text)
    level = 0
    if 0<score<6:
        level = 1
    elif 6<=score<8:
        level = 2
    elif 8<=score<10:
        level = 3
    elif 10<=score<11:
        level = 4
    elif 11<=score<12:
        level = 5
    elif 12<=score<13:
        level = 6
    elif 13<=score:
        level = 7
        
    return level


def gunning_fog(text):
    
    score = textstat.gunning_fog(text)
    level = 0
    if 0<score<7:
        level = 1
    elif 7<=score<9:
        level = 2
    elif 9<=score<12:
        level = 3
    elif 12<=score<13:
        level = 4
    elif 13<=score<14:
        level = 5
    elif 14<=score<15:
        level = 6
    elif 15<=score:
        level = 7
        
    return level


def dale_chall_readability_score(text):
    
    score = textstat.dale_chall_readability_score(text)
    level = 0
    if 0<score<4.9:
        level = 1
    elif 5<=score<5.9:
        level = 2
    elif 6<=score<6.9:
        level = 3
    elif 7<=score<7.9:
        level = 4
    elif 8<=score<8.9:
        level = 5
    elif 9<=score<9.9:
        level = 6
    elif 10<=score:
        level = 7
        
    return level


def flesch_reading_ease(text):
    
    score = textstat.flesch_reading_ease(text)
    level = 0
    if 90<=score<100:
        level = 1
    elif 80<=score<90:
        level = 2
    elif 70<=score<80:
        level = 3
    elif 60<=score<70:
        level = 4
    elif 50<=score<60:
        level = 5
    elif 30<=score<50:
        level = 6
    elif 0<=score<30:
        level = 7
        
    return level