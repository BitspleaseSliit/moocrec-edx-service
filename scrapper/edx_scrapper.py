

"""
sajeeva - edx main
"""

import argparse
import getpass
import json
import logging
import os
import pickle
import re
import sys

from functools import partial
from multiprocessing.dummy import Pool as ThreadPool

from six.moves.http_cookiejar import CookieJar
from six.moves.urllib.error import HTTPError, URLError
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import (
    urlopen,
    build_opener,
    install_opener,
    HTTPCookieProcessor,
    Request,
    urlretrieve,
)

from ._version import __version__

# Login Details
USERNAME = "bitpleasesliit@gmail.com"
PASSWORD = "sliit_bitplease1"

from .common import (
    YOUTUBE_DL_CMD,
    DEFAULT_CACHE_FILENAME,
    Unit,
    Video,
    ExitCode,
    DEFAULT_FILE_FORMATS,
)
from .parsing import (
    edx_json2srt,
    get_page_extractor,
    is_youtube_url,
)
from .utils import (
    clean_filename,
    directory_name,
    execute_command,
    get_filename_from_prefix,
    get_page_contents,
    get_page_contents_as_json,
    mkdir_p,
    remove_duplicates,
)


OPENEDX_SITES = {
    'edx': {
        'url': 'https://courses.edx.org',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'edge': {
        'url': 'https://edge.edx.org',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'stanford': {
        'url': 'https://lagunita.stanford.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'usyd-sit': {
        'url': 'http://online.it.usyd.edu.au',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'fun': {
        'url': 'https://www.fun-mooc.fr',
        'courseware-selector': ('section', {'aria-label': 'Menu du cours'}),
    },
    'gwu-seas': {
        'url': 'http://openedx.seas.gwu.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'gwu-open': {
        'url': 'http://mooc.online.gwu.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'mitxpro': {
        'url': 'https://mitxpro.mit.edu',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    },
    'bits':{
        'url':'http://any-learn.bits-pilani.ac.in',
        'courseware-selector': ('nav', {'aria-label': 'Course Navigation'}),
    }
}
BASE_URL = OPENEDX_SITES['edx']['url']
EDX_HOMEPAGE = BASE_URL + '/login_ajax'
LOGIN_API = BASE_URL + '/login_ajax'
DASHBOARD = BASE_URL + '/dashboard'
COURSEWARE_SEL = OPENEDX_SITES['edx']['courseware-selector']


def change_openedx_site(site_name):
    """
    Changes the openedx website for the given one via the key
    """
    global BASE_URL
    global EDX_HOMEPAGE
    global LOGIN_API
    global DASHBOARD
    global COURSEWARE_SEL

    sites = sorted(OPENEDX_SITES.keys())
    if site_name not in sites:
        logging.error("OpenEdX platform should be one of: %s", ', '.join(sites))
        sys.exit(ExitCode.UNKNOWN_PLATFORM)

    BASE_URL = OPENEDX_SITES[site_name]['url']
    EDX_HOMEPAGE = BASE_URL + '/login_ajax'
    LOGIN_API = BASE_URL + '/login_ajax'
    DASHBOARD = BASE_URL + '/dashboard'
    COURSEWARE_SEL = OPENEDX_SITES[site_name]['courseware-selector']


def _display_courses(courses):
    """
    List the courses that the user has enrolled.
    """
    logging.info('You can access %d courses', len(courses))

    for i, course in enumerate(courses, 1):
        logging.info('%2d - %s [%s]', i, course.name, course.id)
        logging.info('     %s', course.url)


def get_courses_info(url, headers):
    """
    Extracts the courses information from the dashboard.
    """
    logging.info('Extracting course information from dashboard.')

    page = get_page_contents(url, headers)
    page_extractor = get_page_extractor(url)
    courses = page_extractor.extract_courses_from_html(page, BASE_URL)

    logging.debug('Data extracted: %s', courses)

    return courses


def _get_initial_token(url):
    """
    Create initial connection to get authentication token for future
    requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    logging.info('Getting initial CSRF token.')

    cookiejar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookiejar))
    install_opener(opener)
    opener.open(url)

    for cookie in cookiejar:
        if cookie.name == 'csrftoken':
            logging.info('Found CSRF token.')
            return cookie.value

    logging.warn('Did not find the CSRF token.')
    return ''


def get_available_sections(url, headers):
    """
    Extracts the sections and subsections from a given url
    """
    logging.debug("Extracting sections for :" + url)

    page = get_page_contents(url, headers)
    page_extractor = get_page_extractor(url)
    sections = page_extractor.extract_sections_from_html(page, BASE_URL)

    logging.debug("Extracted sections: " + str(sections))
    return sections


def edx_get_subtitle(url, headers,
                     get_page_contents=get_page_contents,
                     get_page_contents_as_json=get_page_contents_as_json):
    """
    Return a string with the subtitles content from the url or None if no
    subtitles are available.
    """
    try:
        if ';' in url:  
            return get_page_contents(url, headers)
        else:
            json_object = get_page_contents_as_json(url, headers)
            return edx_json2srt(json_object)
    except URLError as exception:
        logging.warn('edX subtitles (error: %s)', exception)
        return None
    except ValueError as exception:
        logging.warn('edX subtitles (error: %s)', exception.message)
        return None


def edx_login(url, headers, username, password):
    """
    Log in user into the openedx website.
    """
    logging.info('Logging into Open edX site: %s', url)

    post_data = urlencode({'email': username,
                           'password': password,
                           'remember': False}).encode('utf-8')

    request = Request(url, post_data, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))

    return resp


def parse_args():
    """
    Parse the arguments/options passed to the program on the command line.
    """
    parser = argparse.ArgumentParser(prog='edx-dl',
                                     description='Get videos from the OpenEdX platform',
                                     epilog='For further use information,'
                                     'see the file README.md',)
    # positional
    parser.add_argument('course_urls',
                        nargs='*',
                        action='store',
                        default=[],
                        help='target course urls '
                        '(e.g., https://courses.edx.org/courses/BerkeleyX/CS191x/2013_Spring/info)')

    # optional
    parser.add_argument('-u',
                        '--username',
                        # required=True,
                        action='store',
                        help='your edX username (email)')

    parser.add_argument('-p',
                        '--password',
                        action='store',
                        help='your edX password, '
                        'beware: it might be visible to other users on your system')

    parser.add_argument('-f',
                        '--format',
                        dest='format',
                        action='store',
                        default=None,
                        help='format of videos to download')

    parser.add_argument('-s',
                        '--with-subtitles',
                        dest='subtitles',
                        action='store_true',
                        default=False,
                        help='download subtitles with the videos')

    parser.add_argument('-o',
                        '--output-dir',
                        action='store',
                        dest='output_dir',
                        help='store the files to the specified directory',
                        default='Downloaded')

    parser.add_argument('-i',
                        '--ignore-errors',
                        dest='ignore_errors',
                        action='store_true',
                        default=False,
                        help='continue on download errors, to avoid stopping large downloads')

    sites = sorted(OPENEDX_SITES.keys())
    parser.add_argument('-x',
                        '--platform',
                        action='store',
                        dest='platform',
                        help='OpenEdX platform, one of: %s' % ', '.join(sites),
                        default='edx')

    parser.add_argument('--list-courses',
                        dest='list_courses',
                        action='store_true',
                        default=False,
                        help='list available courses')

    parser.add_argument('--filter-section',
                        dest='filter_section',
                        action='store',
                        default=None,
                        help='filters sections to be downloaded')

    parser.add_argument('--list-sections',
                        dest='list_sections',
                        action='store_true',
                        default=False,
                        help='list available sections')

    parser.add_argument('--youtube-dl-options',
                        dest='youtube_dl_options',
                        action='store',
                        default='',
                        help='set extra options to pass to youtube-dl')

    parser.add_argument('--prefer-cdn-videos',
                        dest='prefer_cdn_videos',
                        action='store_true',
                        default=False,
                        help='prefer CDN video downloads over youtube (BETA)')

    parser.add_argument('--export-filename',
                        dest='export_filename',
                        default=None,
                        help='filename where to put an exported list of urls. '
                        'Use dash "-" to output to stdout. '
                        'Download will not be performed if this option is '
                        'present')

    parser.add_argument('--export-format',
                        dest='export_format',
                        default='%(url)s',
                        help='export format string. Old-style python formatting '
                        'is used. Available variables: %%(url)s. Default: '
                        '"%%(url)s"')

    parser.add_argument('--list-file-formats',
                        dest='list_file_formats',
                        action='store_true',
                        default=False,
                        help='list the default file formats extracted')

    parser.add_argument('--file-formats',
                        dest='file_formats',
                        action='store',
                        default=None,
                        help='appends file formats to be extracted (comma '
                        'separated)')

    parser.add_argument('--overwrite-file-formats',
                        dest='overwrite_file_formats',
                        action='store_true',
                        default=False,
                        help='if active overwrites the file formats to be '
                        'extracted')

    parser.add_argument('--cache',
                        dest='cache',
                        action='store_true',
                        default=False,
                        help='create and use a cache of extracted resources')

    parser.add_argument('--dry-run',
                        dest='dry_run',
                        action='store_true',
                        default=False,
                        help='makes a dry run, only lists the resources')

    parser.add_argument('--sequential',
                        dest='sequential',
                        action='store_true',
                        default=False,
                        help='extracts the resources from the pages sequentially')

    parser.add_argument('--quiet',
                        dest='quiet',
                        action='store_true',
                        default=False,
                        help='omit as many messages as possible, only printing errors')

    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        default=False,
                        help='print lots of debug information')

    parser.add_argument('--version',
                        action='version',
                        version=__version__,
                        help='display version and exit')

    args = parser.parse_args()


    # Initialize the logging system first so that other functions
    # can use it right away.
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(name)s[%(funcName)s] %(message)s')
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR,
                            format='%(name)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(message)s')

    return args


def edx_get_headers():
    """
    Build the Open edX headers to create future requests.
    """
    logging.info('Building initial headers for future requests.')

    headers = {
        'User-Agent': 'edX-downloader/0.01',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': _get_initial_token(EDX_HOMEPAGE),
    }

    logging.debug('Headers built: %s', headers)
    return headers


def extract_units(url, headers, file_formats):
    """
    Parses a webpage and extracts its resources e.g. video_url, sub_url, etc.
    """
    logging.info("Processing '%s'", url)

    page = get_page_contents(url, headers)
    page_extractor = get_page_extractor(url)
    units = page_extractor.extract_units_from_html(page, BASE_URL, file_formats)

    return units


def extract_all_units_in_sequence(urls, headers, file_formats):

    logging.info('Extracting all units information in sequentially.')
    logging.debug('urls: ' + str(urls))

    units = [extract_units(url, headers, file_formats) for url in urls]
    all_units = dict(zip(urls, units))

    return all_units


def extract_all_units_in_parallel(urls, headers, file_formats):

    logging.info('Extracting all units information in parallel.')
    logging.debug('urls: ' + str(urls))

    mapfunc = partial(extract_units, file_formats=file_formats, headers=headers)
    pool = ThreadPool(16)
    units = pool.map(mapfunc, urls)
    pool.close()
    pool.join()
    all_units = dict(zip(urls, units))

    return all_units


def _display_sections_menu(course, sections):

    num_sections = len(sections)

    logging.info('%s [%s] has %d sections so far', course.name, course.id, num_sections)
    for i, section in enumerate(sections, 1):
        logging.info('%2d - Download %s videos', i, section.name)


def _filter_sections(index, sections):

    num_sections = len(sections)

    logging.info('Filtering sections')

    if index is not None:
        try:
            index = int(index)
            if index > 0 and index <= num_sections:
                logging.info('Sections filtered to: %d', index)
                return [sections[index - 1]]
            else:
                pass  # log some info here
        except ValueError:
            pass   # log some info here
    else:
        pass  # log some info here

    return sections


def _display_sections(sections):

    logging.info('Downloading %d section(s)', len(sections))

    for section in sections:
        logging.info('Section %2d: %s', section.position, section.name)
        for subsection in section.subsections:
            logging.info('  %s', subsection.name)


def parse_courses(args, available_courses):

    if args.list_courses:
        _display_courses(available_courses)
        exit(ExitCode.OK)

    if len(args.course_urls) == 0:
        logging.error('You must pass the URL of at least one course, check the correct url with --list-courses')
        exit(ExitCode.MISSING_COURSE_URL)

    selected_courses = [available_course
                        for available_course in available_courses
                        for url in args.course_urls
                        if available_course.url == url]
    if len(selected_courses) == 0:
        logging.error('You have not passed a valid course url, check the correct url with --list-courses')
        exit(ExitCode.INVALID_COURSE_URL)
    return selected_courses


def parse_sections(args, selections):

    if args.list_sections:
        for selected_course, selected_sections in selections.items():
            _display_sections_menu(selected_course, selected_sections)
        exit(ExitCode.OK)

    if not args.filter_section:
        return selections

    filtered_selections = {selected_course:
                           _filter_sections(args.filter_section, selected_sections)
                           for selected_course, selected_sections in selections.items()}
    return filtered_selections


def parse_file_formats(args):

    file_formats = DEFAULT_FILE_FORMATS

    if args.list_file_formats:
        logging.info(file_formats)
        exit(ExitCode.OK)

    if args.overwrite_file_formats:
        file_formats = []

    if args.file_formats:
        new_file_formats = args.file_formats.split(",")
        file_formats.extend(new_file_formats)

    logging.debug("file_formats: %s", file_formats)
    return file_formats


def _display_selections(selections):

    for selected_course, selected_sections in selections.items():
        logging.info('Downloading %s [%s]',
                     selected_course.name, selected_course.id)
        _display_sections(selected_sections)


def parse_units(all_units):

    flat_units = [unit for units in all_units.values() for unit in units]
    if len(flat_units) < 1:
        logging.warn('No downloadable video found.')
        exit(ExitCode.NO_DOWNLOADABLE_VIDEO)


def get_subtitles_urls(available_subs_url, sub_template_url, headers):

    if available_subs_url is not None and sub_template_url is not None:
        try:
            available_subs = get_page_contents_as_json(available_subs_url,
                                                       headers)
        except HTTPError:
            available_subs = ['en']

        return {sub_lang: sub_template_url % sub_lang
                for sub_lang in available_subs}

    elif sub_template_url is not None:
        try:
            available_subs = get_page_contents(sub_template_url,
                                                       headers)
        except HTTPError:
            available_subs = ['en']

        return {'en': sub_template_url}

    return {}


def _build_subtitles_downloads(video, target_dir, filename_prefix, headers):

    downloads = {}
    filename = get_filename_from_prefix(target_dir, filename_prefix)

    if filename is None:
        logging.warn('No video downloaded for %s', filename_prefix)
        return downloads
    if video.sub_template_url is None:
        logging.warn('No subtitles downloaded for %s', filename_prefix)
        return downloads

    re_is_subtitle = re.compile(r'(.*)(?:\.[a-z]{2})')
    match_subtitle = re_is_subtitle.match(filename)
    if match_subtitle:
        filename = match_subtitle.group(1)

    subtitles_download_urls = get_subtitles_urls(video.available_subs_url,
                                                 video.sub_template_url,
                                                 headers)
    for sub_lang, sub_url in subtitles_download_urls.items():
        subs_filename = os.path.join(target_dir,
                                     filename + '.' + sub_lang + '.srt')
        downloads[sub_url] = subs_filename
    return downloads


def _build_url_downloads(urls, target_dir, filename_prefix):

    downloads = {url:
                 _build_filename_from_url(url, target_dir, filename_prefix)
                 for url in urls}
    return downloads


def _build_filename_from_url(url, target_dir, filename_prefix):

    if is_youtube_url(url):
        filename_template = filename_prefix + "-%(title)s-%(id)s.%(ext)s"
        filename = os.path.join(target_dir, filename_template)
    else:
        original_filename = url.rsplit('/', 1)[1]
        filename = os.path.join(target_dir,
                                filename_prefix + '-' + original_filename)

    return filename


def download_url(url, filename, headers, args):

    if is_youtube_url(url):
        download_youtube_url(url, filename, headers, args)
    else:
        import ssl
        import requests
        
        try:
            if 'zip' in url and 'mitxpro' in url:
                urlretrieve(url, filename)
            else:
                r = requests.get(url, headers=headers)
                with open(filename, 'wb') as fp:
                    fp.write(r.content)
        except Exception as e:
            logging.warn('Got SSL/Connection error: %s', e)
            if not args.ignore_errors:
                logging.warn('Hint: if you want to ignore this error, add '
                             '--ignore-errors option to the command line')
                raise e
            else:
                logging.warn('SSL/Connection error ignored: %s', e)


def download_youtube_url(url, filename, headers, args):

    logging.info('Downloading video with URL %s from YouTube.', url)
    video_format_option = args.format + '/mp4' if args.format else 'mp4'
    cmd = YOUTUBE_DL_CMD + ['-o', filename, '-f', video_format_option]

    if args.subtitles:
        cmd.append('--all-subs')
    cmd.extend(args.youtube_dl_options.split())
    cmd.append(url)

    execute_command(cmd, args)


def download_subtitle(url, filename, headers, args):

    subs_string = edx_get_subtitle(url, headers)
    if subs_string:
        full_filename = os.path.join(os.getcwd(), filename)
        with open(full_filename, 'wb+') as f:
            f.write(subs_string.encode('utf-8'))


def skip_or_download(downloads, headers, args, f=download_url):

    for url, filename in downloads.items():
        if os.path.exists(filename):
            logging.info('[skipping] %s => %s', url, filename)
            continue
        else:
            logging.info('[download] %s => %s', url, filename)
        if args.dry_run:
            continue
        f(url, filename, headers, args)


def download_video(video, args, target_dir, filename_prefix, headers):
    if args.prefer_cdn_videos or video.video_youtube_url is None:
        mp4_downloads = _build_url_downloads(video.mp4_urls, target_dir,
                                             filename_prefix)
        skip_or_download(mp4_downloads, headers, args)
    else:
        if video.video_youtube_url is not None:
            youtube_downloads = _build_url_downloads([video.video_youtube_url],
                                                     target_dir,
                                                     filename_prefix)
            skip_or_download(youtube_downloads, headers, args)

    if args.subtitles:
        sub_downloads = _build_subtitles_downloads(video, target_dir,
                                                   filename_prefix, headers)
        skip_or_download(sub_downloads, headers, args, download_subtitle)


def download_unit(unit, args, target_dir, filename_prefix, headers):

    if len(unit.videos) == 1:
        download_video(unit.videos[0], args, target_dir, filename_prefix,
                       headers)
    else:
        for i, video in enumerate(unit.videos, 1):
            new_prefix = filename_prefix + ('-%02d' % i)
            download_video(video, args, target_dir, new_prefix, headers)

    res_downloads = _build_url_downloads(unit.resources_urls, target_dir,
                                         filename_prefix)
    skip_or_download(res_downloads, headers, args)


def download(args, selections, all_units, headers):

    logging.info("Output directory: " + args.output_dir)

    for selected_course, selected_sections in selections.items():
        coursename = directory_name(selected_course.name)
        for selected_section in selected_sections:
            section_dirname = "%02d-%s" % (selected_section.position,
                                           selected_section.name)
            target_dir = os.path.join(args.output_dir, coursename,
                                      clean_filename(section_dirname))
            mkdir_p(target_dir)
            counter = 0
            for subsection in selected_section.subsections:
                units = all_units.get(subsection.url, [])
                for unit in units:
                    counter += 1
                    filename_prefix = "%02d" % counter
                    download_unit(unit, args, target_dir, filename_prefix,
                                  headers)


def remove_repeated_urls(all_units):

    existing_urls = set()
    filtered_units = {}
    for url, units in all_units.items():
        reduced_units = []
        for unit in units:
            videos = []
            for video in unit.videos:
                video_youtube_url = None
                if video.video_youtube_url not in existing_urls:
                    video_youtube_url = video.video_youtube_url
                    existing_urls.add(video_youtube_url)

                mp4_urls, existing_urls = remove_duplicates(video.mp4_urls, existing_urls)

                if video_youtube_url is not None or len(mp4_urls) > 0:
                    videos.append(Video(video_youtube_url=video_youtube_url,
                                        available_subs_url=video.available_subs_url,
                                        sub_template_url=video.sub_template_url,
                                        mp4_urls=mp4_urls))

            resources_urls, existing_urls = remove_duplicates(unit.resources_urls, existing_urls)

            if len(videos) > 0 or len(resources_urls) > 0:
                reduced_units.append(Unit(videos=videos,
                                          resources_urls=resources_urls))

        filtered_units[url] = reduced_units
    return filtered_units


def num_urls_in_units_dict(units_dict):
    num_urls = 0

    for units in units_dict.values():
        for unit in units:
            for video in unit.videos:
                num_urls += int(video.video_youtube_url is not None)
                num_urls += int(video.available_subs_url is not None)
                num_urls += int(video.sub_template_url is not None)
                num_urls += len(video.mp4_urls)
            num_urls += len(unit.resources_urls)

    return num_urls


def extract_all_units_with_cache(all_urls, headers, file_formats,
                                 filename=DEFAULT_CACHE_FILENAME,
                                 extractor=extract_all_units_in_parallel):
    cached_units = {}

    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            cached_units = pickle.load(f)

    # we filter the cached urls
    new_urls = [url for url in all_urls if url not in cached_units]
    logging.info('loading %d urls from cache [%s]', len(cached_units.keys()),
                 filename)
    new_units = extractor(new_urls, headers, file_formats)
    all_units = cached_units.copy()
    all_units.update(new_units)

    return all_units


def write_units_to_cache(units, filename=DEFAULT_CACHE_FILENAME):
    logging.info('writing %d urls to cache [%s]', len(units.keys()),
                 filename)
    with open(filename, 'wb') as f:
        pickle.dump(units, f)


def extract_urls_from_units(all_units, format_):
    all_urls = set()

    # Collect all urls into a set to remove duplicates
    for units in all_units.values():
        for unit in units:
            if isinstance(unit, Unit):
                for video in unit.videos:
                    if isinstance(video, Video):
                        for url in video.mp4_urls:
                            all_urls.add('%s\n' % (format_ % {'url': url}))
                    else:
                        raise TypeError('Unknown unit video type (%s) occured '
                                        'while exporting urls' % type(video))
                for url in unit.resources_urls:
                    all_urls.add('%s\n' % (format_ % {'url': url}))
            else:
                raise TypeError('Unknown unit type (%s) occured while '
                                'exporting urls' % type(unit))
    return list(all_urls)


def save_urls_to_file(urls, filename):
    file_ = sys.stdout if filename == '-' else open(filename, 'w')
    file_.writelines(urls)
    file_.close()

# 01
def main(course_url):
    args = parse_args()
    
    args.username = USERNAME
    args.password = PASSWORD
    args.course_urls = [course_url]

    file_formats = parse_file_formats(args)

    print(args)

    change_openedx_site(args.platform)

    # Prepare Headers
    headers = edx_get_headers()

    # Login
    resp = edx_login(LOGIN_API, headers, args.username, args.password)
    if not resp.get('success', False):
        logging.error(resp.get('value', "Wrong Email or Password."))
        return False

    # Parse and select the available courses
    courses = get_courses_info(DASHBOARD, headers)
    available_courses = [course for course in courses if course.state == 'Started']
    selected_courses = parse_courses(args, available_courses)

    # Parse the sections and build the selections dict filtered by sections
    if args.platform == 'edx':
        all_selections = {selected_course:
                          get_available_sections(selected_course.url.replace('info', 'course'), 
                                                 headers)
                          for selected_course in selected_courses}
    else:
        all_selections = {selected_course:
                          get_available_sections(selected_course.url.replace('info', 'courseware'), 
                                                 headers)
                          for selected_course in selected_courses}

    selections = parse_sections(args, all_selections)
    _display_selections(selections)

    # Extract the unit information (downloadable resources)
    # This parses the HTML of all the subsection.url and extracts
    # the URLs of the resources as Units.
    all_urls = [subsection.url
                for selected_sections in selections.values()
                for selected_section in selected_sections
                for subsection in selected_section.subsections]

    extractor = extract_all_units_in_parallel
    if args.sequential:
        extractor = extract_all_units_in_sequence

    if args.cache:
        all_units = extract_all_units_with_cache(all_urls, headers,
                                                 file_formats,
                                                 extractor=extractor)
    else:
        all_units = extractor(all_urls, headers, file_formats)

    parse_units(selections)

    if args.cache:
        write_units_to_cache(all_units)

    filtered_units = remove_repeated_urls(all_units)
    num_all_urls = num_urls_in_units_dict(all_units)
    num_filtered_urls = num_urls_in_units_dict(filtered_units)
    logging.warn('Removed %d duplicated urls from %d in total',
                 (num_all_urls - num_filtered_urls), num_all_urls)

    # finally we download or export all the resources
    if args.export_filename is not None:
        logging.info('exporting urls to file %s', args.export_filename)
        urls = extract_urls_from_units(filtered_units, args.export_format)
        save_urls_to_file(urls, args.export_filename)
    else:
        download(args, selections, filtered_units, headers)

    return True

def scrapper(course_url):
    try:
        main(course_url)
    except KeyboardInterrupt:
        logging.warn("\n\nCTRL-C detected, shutting down....")
        sys.exit(ExitCode.OK)