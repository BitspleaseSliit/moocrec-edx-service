import os, stat
import shutil
from scrapper.edx_scrapper import ( scrapper )
from db.edx_coursedb import ( EdxCourses )


def deleteDownloadContent(course):
    print("deleting files ....... ")

    downloadPath = "Downloaded" + course["path"]

    if os.path.exists(downloadPath):
        shutil.rmtree(downloadPath)
    else:
        print("The file does not exist")
        return False


if __name__ == '__main__':
    
    courses = EdxCourses()
    print(courses.getDownloadCoursesPaths())
    download_courses = courses.getDownlodCourses()
    # scrapper("https://courses.edx.org/courses/course-v1:UCSanDiegoX+DSE200x+3T2018/course/")
    for course in download_courses:
        if scrapper(course["courseUrl"]):
            courses.updateProcessedTrue(course)
            print("course download successfull")
            deleteDownloadContent(download_courses[0])
        else:
            courses.updateProcessedFalse(course)
            print("course download Fail")
        