
class Course(object):

    def __init__(self, id, name, url, state):

        self.id = id
        self.name = name
        self.url = url
        self.state = state

    def __repr__(self):
        url = self.url if self.url else "None"
        return self.name + ": " + url


class Section(object):

    def __init__(self, position, name, url, subsections):

        self.position = position
        self.name = name
        self.url = url
        self.subsections = subsections


class SubSection(object):

    def __init__(self, position, name, url):

        self.position = position
        self.name = name
        self.url = url

    def __repr__(self):
        return self.name + ": " + self.url

class Unit(object):

    def __init__(self, videos, resources_urls):

        self.videos = videos
        self.resources_urls = resources_urls


class Video(object):

    def __init__(self, video_youtube_url, available_subs_url,
                 sub_template_url, mp4_urls):

        self.video_youtube_url = video_youtube_url
        self.available_subs_url = available_subs_url
        self.sub_template_url = sub_template_url
        self.mp4_urls = mp4_urls


class ExitCode(object):

    OK = 0
    MISSING_CREDENTIALS = 1
    WRONG_EMAIL_OR_PASSWORD = 2
    MISSING_COURSE_URL = 3
    INVALID_COURSE_URL = 4
    UNKNOWN_PLATFORM = 5
    NO_DOWNLOADABLE_VIDEO = 6


YOUTUBE_DL_CMD = ['youtube-dl', '--ignore-config']
DEFAULT_CACHE_FILENAME = 'edx-dl.cache'
DEFAULT_FILE_FORMATS = ['e?ps', 'pdf', 'txt', 'doc', 'xls', 'ppt',
                        'docx', 'xlsx', 'pptx', 'odt', 'ods', 'odp', 'odg',
                        'zip', 'rar', 'gz', 'mp3', 'R', 'Rmd', 'ipynb', 'py']
