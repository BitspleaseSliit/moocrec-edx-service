import pymongo
from bson.objectid import ObjectId
from dbConnection import ( db )


class Courses:

    # self.courses = db["test_courses"]

    def __init__(self):
        self.courses = db["test_courses"]

    def getAll(self):
        courses_array = []
        try:
            for course in self.courses.find({"logo": "coursera"}):
                # print(course["_id"])
                courses_array.append(course)
            return courses_array
        except pymongo.errors.PyMongoError as e:
            print(e)
            return []
        

    def getDownlodCourses(self):
        download_courses_array = []
        try:
            for course in self.courses.find({"logo": "edx", "processed": False, "download": True}):
                download_courses_array.append(course)
                # print(download_courses_array)
            return download_courses_array
        except pymongo.errors.PyMongoError as e:
            print(e)
            return []
        

    def updateVideoStyle(self, video_style, course):
        try:
            select_query = { "_id": ObjectId(course["_id"])}
            insert_value = { "$set": { "videoStyle": video_style} }
            result = self.courses.update_one(select_query, insert_value)
            return result.matched_count > 0 
        except pymongo.errors.PyMongoError as e:
            print(e)
            return False

    def updateAbstractTopics(self, abstract_topics, course):
        try:
            select_query = { "_id": ObjectId(course["_id"])}
            insert_value = { "$set": { "abstractTopics": abstract_topics} }
            result = self.courses.update_one(select_query, insert_value)
            return result.matched_count > 0 
        except pymongo.errors.PyMongoError as e:
            print(e)
            return False  

    def updateLinguisticComplexity(self, linguistic_complexity, course):
        try:
            select_query = { "_id": ObjectId(course["_id"])}
            insert_value = { "$set": { "linguisticComplexity": linguistic_complexity} }
            result = self.courses.update_one(select_query, insert_value)
            return result.matched_count > 0 
        except pymongo.errors.PyMongoError as e:
            print(e)
            return False

    def updateProcessedTrue(self, course):
        try:
            select_query = { "_id": ObjectId(course["_id"])}
            insert_value = { "$set": { "processed": True } }
            result = self.courses.update_one(select_query, insert_value)
            return result.matched_count > 0 
        except pymongo.errors.PyMongoError as e:
            print(e)
            return False

    def updateProcessedFalse(self, course):
        try:
            select_query = { "_id": ObjectId(course["_id"])}
            insert_value = { "$set": { "processed": False } }
            result = self.courses.update_one(select_query, insert_value)
            return result.matched_count > 0 
        except pymongo.errors.PyMongoError as e:
            print(e)
            return False

    def getDownloadCoursesPaths(self):
        download_courses = self.getDownlodCourses()
        if download_courses.count == 0:
            return []
        else:
            courses_path = []
            for course in download_courses:
                courses_path.append(course["path"])
            return courses_path


    # mycourse = getAll()[0]
    # print(mycourse)
    # videoStyle = {}
    # videoStyle["talkingHead"] = 30
    # videoStyle["slide"] = 10
    # videoStyle["code"] = 60
    # videoStyle["conversation"] = 0
    # videoStyle["animation"] = 0
    # videoStyle["whiteboard"] = 0
    # print(videoStyle)
    # updateVideoStyle(videoStyle, mycourse)