import os, stat
import shutil
from scrapper.edx_scrapper import ( scrapper )
from db.edx_coursedb import ( EdxCourses )
import topics_complexity
from predict import ( getVideoStyleValues )


def deleteDownloadContent(course):
    print("deleting files ....... ")

    downloadPath = "Downloaded/" + course["path"]

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

            topicResult = topics_complexity.generate_topics_complexity("Downloaded/" + course["path"])
            courses.updateAbstractTopics(topicResult["topics"], course)
            courses.updateComplexityLevel(topicResult["level"], course)

            video_styles = getVideoStyleValues("Downloaded/" + course["path"])
            courses.updateVideoStyle(video_styles, course)

            courses.updateProcessedTrue(course)
            print("course download successfull")
            deleteDownloadContent(download_courses[0])
        else:
            courses.updateProcessedFalse(course)
            print("course download Fail")
        