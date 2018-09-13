import os, stat
import shutil
from scrapper.edx_scrapper import ( scrapper )
from db.edx_coursedb import ( EdxCourses )


def deleteDownloadContent(course):
    print("deleting files ....... ")

    jsonFile = course["path"] + "-syllabus-parsed.json"

    if os.path.exists(jsonFile):
        os.remove(jsonFile)
    else:
        print("The file does not exist")
        return False

    if os.path.exists(course["path"]):
        shutil.rmtree(course["path"])
    else:
        print("The file does not exist")
        return False


if __name__ == '__main__':
    
    courses = EdxCourses()
    print(courses.getDownloadCoursesPaths())
    download_courses = courses.getDownlodCourses()

    for course in download_courses:
        if scrapper(course["courseUrl"]):
            courses.updateProcessedTrue(course)
            print("course download successfull")
            deleteDownloadContent(download_courses[0])
        else:
            courses.updateProcessedFalse(course)
            print("course download Fail")
        