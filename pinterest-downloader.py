#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Lim Kok Hole'
__copyright__ = 'Copyright 2020'
__credits__ = ['Inspired by https://github.com/SevenLines/pinterest-board-downloader', 'S/O']
__license__ = 'MIT'
# Version increase if the output file/dir naming incompatible with existing
#, which might re-download for some files of previous version because of dir/filename not match
# Or log files structure changed reference.
__version__ = 1.9
__maintainer__ = 'Lim Kok Hole'
__email__ = 'limkokhole@gmail.com'
__status__ = 'Production'

# Note: Support python 3 but not python 2

import sys, os, traceback
from pathlib import PurePath
import platform
plat = platform.system().lower()
if ('window' in plat) or plat.startswith('win'):
    # Darwin should treat as Linux
    IS_WIN = True
    # https://stackoverflow.com/questions/16755142/how-to-make-win32-console-recognize-ansi-vt100-escape-sequences
    # Even though ANSI escape sequence can be enable via `REG ADD HKCU\CONSOLE /f /v VirtualTerminalLevel /t REG_DWORD /d 1`
    # But since this is not big deal to hide logo testing for this project, so no need.
    ANSI_CLEAR = '\r' # Default cmd settings not support ANSI sequence
    ANSI_END_COLOR = ''
    ANSI_BLUE = ''
else:
    IS_WIN = False
    ANSI_CLEAR = '\r\x1b[0m\x1b[K'
    ANSI_END_COLOR = '\x1b[0m\x1b[K'
    ANSI_BLUE = '\x1b[1;44m'
try:
    import readline #to make input() edit-able by LEFT key
except ModuleNotFoundError:
    if not IS_WIN: #pyreadline for Windows? overkill
        print('Please install readline module.')
        raise

#IS_WIN = True # TESTING PURPOSE

from termcolor import cprint
import colorama
from colorama import Fore
colorama.init() # Windows need this

HIGHER_GREEN = Fore.LIGHTGREEN_EX
HIGHER_RED = Fore.LIGHTRED_EX
HIGHER_YELLOW = Fore.LIGHTYELLOW_EX
BOLD_ONLY = ['bold']

def quit(msgs, exit=True):
    if not isinstance(msgs, list):
        msgs = [msgs]
    if exit:
        msgs[-1]+= ' Abort.'
    for msg in msgs:
        if msg == '\n':
            print('\n')
        else:
            cprint(''.join([ HIGHER_RED, '%s' % (msg) ]), attrs=BOLD_ONLY, end='\n' )

try:
    x_tag = '✖'
    done_tag = '✔'
    plus_tag = '➕'
    pinterest_logo = '🅿️'
    # Test Windows unicode capability by printing logo, throws if not:
    print(pinterest_logo, end=ANSI_CLEAR, flush=True)
except Exception: #UnicodeEncodeError: # Will error later if not do this, so better quit() early
    cprint(''.join([ HIGHER_RED, '%s' % ('Please run `export PYTHONIOENCODING=utf-8;` to support Unicode.') ]), attrs=BOLD_ONLY, end='\n' )
    quit('')
    sys.exit(1)

import argparse
import time
from datetime import datetime, timedelta

from collections import OrderedDict
import json
import lxml.html as html

import urllib
from urllib.parse import unquote
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed

from http.cookies import SimpleCookie
from requests.cookies import cookiejar_from_dict

from fake_useragent import UserAgent
ua = UserAgent()
# RIP UA, https://groups.google.com/a/chromium.org/forum/m/#!msg/blink-dev/-2JIRNMWJ7s/yHe4tQNLCgAJ
#UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.0.0 Safari/537.36'
UA = ua.chrome

# MAX_PATH 260 need exclude 1 terminating null character <NUL>
# if prefix \\?\ + abspath to use Windows extented-length(i.e. in my case, individual filename/dir can use full 259, no more 259 is fit full path), then the MAX_PATH is 259 - 4 = 255
#[DEPRECATED] no more 259 since always -el now AND Windows 259 - \\?\ == 255 normal Linux
WIN_MAX_PATH = 255 # MAX_PATH 260 need exclude 1 terminating null character <NUL>

# https://stackoverflow.com/a/34325723/1074998
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#'):
    '''
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    '''
    if total != 0: # ZeroDivisionError: float division by zero
        percent = ('{0:.' + str(decimals) + 'f}').format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        #sys.stdout.write('\r{} |{}| {}%% {}'.format(prefix, bar, percent, suffix))
        cprint(''.join([ HIGHER_GREEN, '%s' % ('\r{} |{}| {}% {}'.format(prefix, bar, percent, suffix)) ]), attrs=BOLD_ONLY, end='' )
        sys.stdout.flush()

#imgs:
#source_url=%2Fmistafisha%2Fanimals%2F&data=%7B%22options%22%3A%7B%22isPrefetch%22%3Afalse%2C%22board_id%22%3A
#%2253761857990790784%22%2C%22board_url%22%3A%22%2Fmistafisha%2Fanimals%2F%22%2C%22field_set_key%22%3A%22react_grid_pin
#%22%2C%22filter_section_pins%22%3Atrue%2C%22sort%22%3A%22default%22%2C%22layout%22%3A%22default%22%2C%22page_size
#%22%3A25%2C%22redux_normalize_feed%22%3Atrue%7D%2C%22context%22%3A%7B%7D%7D&_=1592340515565
# unquote:
#'source_url=/mistafisha/animals/&data={"options":{"isPrefetch":false,"board_id":"53761857990790784"
#,"board_url":"/mistafisha/animals/","field_set_key":"react_grid_pin","filter_section_pins":true,"sort":"default"
#,"layout":"default","page_size":25,"redux_normalize_feed":true},"context":{}}&_=1592340515565
VER = (None, 'c643827', '4c8c36f')
def get_session(ver_i, proxies, cookie_file):
    s = requests.Session()
    s.proxies = proxies

    try:
        with open(cookie_file) as f:
            rawdata = f.read()

        my_cookie = SimpleCookie()
        my_cookie.load(rawdata)
        cookies = {key: morsel.value for key, morsel in my_cookie.items()}

    except:
        cookies = None

    try:
        s.cookies = cookiejar_from_dict(cookies)
    except:
        pass

    if ver_i == 0:
        s.headers = {
            #'Host': 'www.pinterest.com',
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        }
    elif ver_i == 3:
        s.headers = {
            #'Host': 'www.pinterest.com', #Image can be https://i.pinimg.com, so let it auto or else fail
            'User-Agent': UA,
            'Accept': 'image/webp,*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.pinterest.com/',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers'
        }

    elif ver_i == 4:
        # 'https://v.pinimg.com/videos/mc/hls/8a/99/7d/8a997df97cab576795be2a4490457ea3.m3u8'
        s.headers = {
            'User-Agent': UA,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://www.pinterest.com',
            'DNT': '1',
            'Referer': 'https://www.pinterest.com/',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

    else: # == 1, 2
        s.headers = {
            #'Host': 'www.pinterest.com',
            'User-Agent': UA,
            'Accept': 'application/json, text/javascript, */*, q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.pinterest.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'X-APP-VERSION': VER[ver_i],
            'X-Pinterest-AppState': 'active',
            #'X-Pinterest-Source-Url': '/ackohole/a/sec2/', #[todo:0]
            'X-Pinterest-PWS-Handler': 'www/[username]/[slug]/[section_slug].js',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'Trailers'
        }

    return s

def dj(j, tag=None):
    if tag:
        print('### [' + tag + '] ###')
    print(json.dumps(j, sort_keys=True, indent=4))

def get_pin_info(pin_id, arg_timestamp_log, url_path
    , arg_force_update, arg_img_only, arg_v_only
    , arg_dir, arg_cut, arg_el, fs_f_max
    , IMG_SESSION, V_SESSION, PIN_SESSION, proxies
    , cookie_file, get_data_only):

    scripts = []
    is_success = False
    image = None
    for t in (15, 30, 40, 50, 60):
        #print('https://www.pinterest.com/pin/{}/'.format(pin_id))

        try:
            with open(cookie_file) as f:
                rawdata = f.read()
            my_cookie = SimpleCookie()
            my_cookie.load(rawdata)
            cookies = {key: morsel.value for key, morsel in my_cookie.items()}
            cookies = cookiejar_from_dict(cookies)
        except:
            cookies = None

        try:
            r = PIN_SESSION.get('https://www.pinterest.com/pin/{}/'.format(pin_id), timeout=(t, t), cookies=cookies)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            #print('[E1][pin] Failed. Retry after 5 seconds...')
            time.sleep(5)
            PIN_SESSION = get_session(0, proxies, cookies)
            continue

        root = html.fromstring(r.content)
        #print(r.content)
        try:
            #tag = root.xpath("//script[@id='initial-state']")[0]
            scripts = root.xpath('//script/text()')
        except IndexError: #list index out of range
            time.sleep(5)
            PIN_SESSION = get_session(0, proxies, cookies)
            continue

        indexErr = False
        for script in scripts:
            try:
                data = json.loads(script)
                if 'initialReduxState' in data:
                    pins = data['initialReduxState']['pins']
                    try:
                        image = pins[list(pins.keys())[0]]
                        is_success = True
                        break
                    except IndexError: # Sometime `"pins":{}``, need retry
                        indexErr = True
            except json.decoder.JSONDecodeError:
                pass

        if not is_success:
            if indexErr:
                print('\n[Retry] Getting error pin id: ' + repr(pin_id) + '...\n\n')
            continue

    if not is_success:
        if not get_data_only: # get data error show later
            print('### HTML START ###')
            print(r.content)
            print('### HTML END ###\n\nPlease report this issue at https://github.com/limkokhole/pinterest-downloader/issues , thanks.\n\n')
            cprint(''.join([ HIGHER_RED, '%s %s%s' % ('\n[' + x_tag
                + '] Get this pin id failed :', pin_id, '\n') ]), attrs=BOLD_ONLY, end='' )
        return

    if get_data_only:
        return image
    try:
        # This is the User Responsibilities to ensure -d is not too long
        # Program can't automate for you, imagine -d already 2045th bytes in full path
        #, is unwise if program make dir in parent directory.
        create_dir(arg_dir)
        write_log( arg_timestamp_log, url_path, None, arg_img_only, arg_v_only, arg_dir, [image], image['id'], arg_cut, False )
        print('[i] Download Pin id: ' + str(image['id']) + ' into directory: ' + arg_dir.rstrip(os.sep) + os.sep)
        printProgressBar(0, 1, prefix='[...] Downloading:', suffix='Complete', length=50)
        download_img(image, arg_dir, arg_force_update, arg_img_only, arg_v_only, IMG_SESSION, V_SESSION, PIN_SESSION, proxies, cookie_file, arg_cut, arg_el, fs_f_max)
        printProgressBar(1, 1, prefix='[' + done_tag + '] Downloaded:', suffix='Complete   ', length=50)
    except KeyError:
        return quit(traceback.format_exc())
    print()

def get_board_info(board_or_sec_path, exclude_section, section, board_path, proxies, cookie_file, retry=False):
    try:
        with open(cookie_file) as f:
            rawdata = f.read()
        my_cookie = SimpleCookie()
        my_cookie.load(rawdata)
        cookies = {key: morsel.value for key, morsel in my_cookie.items()}
        cookies = cookiejar_from_dict(cookies)
    except:
        cookies = None

    s = get_session(0, proxies, cookies)
    #s.cookies = cookies

    #dj(data, 'board main')
    boards = {}
    sections = []

    is_success = False
    #print('https://www.pinterest.com/{}/'.format(board_or_sec_path))
    for t in (15, 30, 40, 50, 60):
        try:
            with open(cookie_file) as f:
                rawdata = f.read()
            my_cookie = SimpleCookie()
            my_cookie.load(rawdata)
            cookies = {key: morsel.value for key, morsel in my_cookie.items()}
            cookies = cookiejar_from_dict(cookies)
        except:
            cookies = None
        try:
            r = s.get('https://www.pinterest.com/{}/'.format(board_or_sec_path), timeout=(t, t), cookies=cookies)
            is_success = True
            break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            #print('[E1][pin] Failed. Retry after 5 seconds...')
            time.sleep(5)
            s = get_session(0, proxies, cookies)

    if is_success:
        root = html.fromstring(r.content)
        #print(str(r.content))
        #tag = root.xpath("//script[@id='initial-state']")[0]
        scripts = root.xpath('//script/text()')
        board_d = {}
        for script in scripts:
            try:
                data = json.loads(script)
                if 'initialReduxState' in data:
                    #dj(data)
                    board_d = data['initialReduxState']['boards']
                    #dj(board_d)
                    board_sec_d = data['initialReduxState']['boardsections']
                    #dj(board_sec_d)
                    is_success = True
                    break
            except json.decoder.JSONDecodeError:
                is_success = False

    if not is_success:
        cprint(''.join([ HIGHER_RED, '%s %s%s' % ('\n[' + x_tag
            + '] Get this board/section failed :', board_or_sec_path, '\n') ]), attrs=BOLD_ONLY, end='' )
        if section:
            return boards
        else:
            return boards, sections

    board_dk = list(board_d.keys())
    if section:
        path_to_compare = board_path
    else:
        path_to_compare = board_or_sec_path
    for k in board_dk:
        if unquote(board_d[k].get('url', '').strip('/')) == unquote(path_to_compare):
            b_dk = board_d[k]
            board_d_map = {}
            board_d_map['url'] = b_dk.get('url', '')
            #board_d_map['modified_at'] = b_dk.get('board_order_modified_at', '')
            #print('Board modified: ' + repr(board_d_map['modified_at']))
            #dj(b_dk, 'board d') # [todo:0] board_order_modified_at help decide re-scrape?
            board_d_map['id'] = b_dk.get('id', '')
            board_d_map['name'] = b_dk.get('name', '')
            board_d_map['section_count'] = b_dk.get('section_count', '')
            boards['board'] = board_d_map;
            break

    if not exclude_section:
        board_sec_dk = list(board_sec_d.keys())
        for k in board_sec_dk:
            b_dk = board_sec_d[k]
            sec_d_map = {}
            #dj(b_dk)
            sec_slug = unquote(b_dk.get('slug', ''))
            if section and (sec_slug != section):
                continue

            #sec_d_map['modified_at'] = b_dk.get('board_order_modified_at', '')
            #print('Section modified: ' + repr(sec_d_map['modified_at']))

            sec_d_map['slug'] = sec_slug
            sec_d_map['id'] = b_dk.get('id', '')
            sec_d_map['title'] = b_dk.get('title', '')

            if section:
                boards['section'] = sec_d_map
            else:
                sections.append(sec_d_map)

    #dj(board_d, 'board raw')
    #dj(boards, 'boarded')
    #dj(board_sec_d, 'sect raw')
    #dj(sections, 'sectioned')

    if section:
        return boards
    else:
        return boards, sections

def fetch_boards(uname, proxies, cookie_file):

    try:
        with open(cookie_file) as f:
            rawdata = f.read()
        my_cookie = SimpleCookie()
        my_cookie.load(rawdata)
        cookies = {key: morsel.value for key, morsel in my_cookie.items()}
        cookies = cookiejar_from_dict(cookies)
    except:
        cookies = None

    s = get_session(1, proxies, cookies)
    #s.cookies = cookies

    bookmark = None
    boards = []

    #print('Username: ' + uname)

    #if url != '/mistafisha/animals/':
    #    continue

    while bookmark != '-end-':

        options = {
        'isPrefetch': 'false',
        'privacy_filter': 'all',
        'sort': 'alphabetical',
        'field_set_key': 'profile_grid_item',
        'username': uname,
        'page_size': 25,
        'group_by': 'visibility',
        'include_archived': 'true',
        'redux_normalize_feed': 'true',
        }

        if bookmark:
            options.update({
                'bookmarks': [bookmark],
            })

        b_len = len(boards) - 1
        if b_len < 0:
            b_len = 0
        # Got end='' here to make flush work
        print('\r[...] Getting all boards [ ' + str(b_len) + ' / ? ]' , end='')
        sys.stdout.flush()

        post_d = urllib.parse.urlencode({
            'source_url': uname,
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22') \
        .replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        #print('[boards] called headers: ' + repr(s.headers))

        is_success = False
        for t in (15, 30, 40, 50, 60):
            try:
                with open(cookie_file) as f:
                    rawdata = f.read()
                my_cookie = SimpleCookie()
                my_cookie.load(rawdata)
                cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                cookies = cookiejar_from_dict(cookies)
            except:
                cookies = None
            try:
                r = s.get('https://www.pinterest.com/resource/BoardsResource/get/', params=post_d, timeout=(t, t), cookies=cookies)
                is_success = True
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                time.sleep(5)
                s = get_session(1, proxies, cookies)
                #s.cookies = cookies
        if not is_success:
            cprint(''.join([ HIGHER_RED, '%s %s%s' % ('\n[' + x_tag
                + '] Get this username failed :', uname, '\n') ]), attrs=BOLD_ONLY, end='' )
            break
        #print('[Boards url]: ' + r.url)
        data = r.json()
        #print('res data: ' + repr(data))
        try:
            boards.extend(data['resource_response']['data'])
            bookmark = data['resource']['options']['bookmarks'][0]
        except TypeError: # Normal if invalid username
            cprint(''.join([ HIGHER_RED, '%s' % ('\n[' + x_tag + '] Possible invalid username.\n\n') ]), attrs=BOLD_ONLY, end='' )
            break

    b_len = len(boards)
    print('[' + plus_tag + '] Found {} Board{}.'.format(b_len, 's' if b_len > 1 else ''))

    return boards

def sanitize(path):
    # trim multiple whitespaces # ".." is the responsibilities of get max path

    # Use PurePath instead of os.path.basename  https://stackoverflow.com/a/31273488/1074998 , e.g.:
    #>>> PurePath( '/home/iced/..'.replace('..', '') ).parts[-1] # get 'iced'
    #>>> os.path.basename('/home/iced/..'.replace('..', '')) # get empty ''
    # Ensure .replace('..', '') is last replacement before .strip() AND not replace back to dot '.'
    # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file

    # [todo:0] Handle case sensitive and reserved file names in Windows like Chrome "Save page as" do
    # For portable to move filename between linux <-> win, should use IS_WIN only (but still can't care if case sensitive filename move to case in-sensitive filesystem).
    # IS_WIN:
    path = path.replace('<', '').replace('>', '').replace('"', '\'').replace('?', '').replace('*', '').replace('/', '_').replace('\\', '_').replace('|', '_').replace(':', '_').replace('.', '_').strip()
    # Linux:
    #path.replace('/', '|').replace(':', '_').replace('.', '_').strip()

    # Put this after replace patterns above bcoz 2 distinct spaces may merge together become multiple-spaces, e.g. after ' ? ' replace to '  '
    # If using .replace('  ', ' ') will only replace once round, e.g. '    ' become
    path = ' '.join(path.split())

    p = PurePath( path )

    if p.parts:
        return p.parts[-1]
    else:
        return ''

# The filesystem limits is 255(normal) , 242(docker) or 143((eCryptfs) bytes
# So can't blindly [:] slice without encode first (which most downloaders do the wrong way)
# And need decode back after slice
# And to ensure mix sequence byte in UTF-8 and work
#, e.g. abc𪍑𪍑𪍑
# , need try/catch to skip next full bytes of "1" byte ascii" OR "3 bytes 我" or "4 bytes 𪍑"
# ... by looping 4 bytes(UTF-8 max) from right to left
# HTML5 forbid UTF-16, UTF-16/32 not encourage to use in web page
# So only encode/decode in utf-8
# https://stackoverflow.com/questions/13132976
# https://stackoverflow.com/questions/50385123
# https://stackoverflow.com/questions/11820006

def get_max_path(arg_cut, fs_f_max, fpart_excluded_immutable, immutable):
    #print('before f: ' + fpart_excluded_immutable)
    if arg_cut >= 0:
        fpart_excluded_immutable = fpart_excluded_immutable[:arg_cut]
    if immutable:
        # immutable shouldn't limit to 1 byte(may be change next time or next project), so need encode also
        immutable_len = len(immutable.encode('utf-8'))
    else:
        immutable_len = 0

    space_remains = fs_f_max - immutable_len
    if space_remains < 1:
        return '' # No more spaces to trim(bcoz directories name too long), so only shows PinID.jpg

    # range([start], stop[, step])
    # -1 step * 4 loop = -4, means looping 4 bytes(UTF-8 max) from right to left
    for gostan in range(space_remains, space_remains - 4, -1):
        try:
            fpart_excluded_immutable = fpart_excluded_immutable.encode('utf-8')[: gostan ].decode('utf-8')
            break # No break still same result, but waste
        except UnicodeDecodeError:
            pass #print('Calm down, this is normal: ' + str(gostan) + ' f: ' + fpart_excluded_immutable)
    #print('after f: ' + fpart_excluded_immutable)
    # Last safety resort, in case any bug:
    fpart_excluded_immutable_base = sanitize ( fpart_excluded_immutable )
    if fpart_excluded_immutable_base != fpart_excluded_immutable.strip(): # Original need strip bcoz it might cut in space
        cprint(''.join([ HIGHER_RED, '\n[! A] Please report to me which Link/scenario it print this log.\
            Thanks:\n{} # {} # {} # {} # {}\n\n'
            .format(arg_cut, fs_f_max, repr(fpart_excluded_immutable), repr(fpart_excluded_immutable_base), immutable) ]), attrs=BOLD_ONLY, end='' )
    return fpart_excluded_immutable_base

def get_output_file_path(url, arg_cut, fs_f_max, image_id, human_fname, save_dir):

    pin_id_str = sanitize(str(image_id))
    basename = os.path.basename(url) # basename not enough to handle '..', but will sanitize later
    # throws ValueError is fine bcoz it's not normal

    # Test case need consider what if multiple dots in basename
    #human_fname_unused = '.'.join(basename.split('.')[:-1]) # this project already has human_fname, but other project can use this
    ext = basename.split('.')[-1]

    ext = sanitize(ext)
    if not ext.strip(): # Ensure add hard-coded extension to avoid empty id and leave single dot in next step
        ext = 'unknown'
    # Currently not possible ..jpg here bcoz above must single '.' do not throws
    # , even replace ..jpg to _.jpg is fine, just can't preview in explorer only
    immutable = sanitize( pin_id_str + '.' +  ext )

    fpart_excluded_ext_before  = sanitize( human_fname )
    #print( 'get output f:' + repr(fpart_excluded_ext_before) )

    # [DEPRECATED, now always use extended length which apply to single component instead of full path]
    #if IS_WIN: # Windows MAX_PATH 260 is full path not single component (https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file , https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file#maximum-path-length-limitation)
    #    immutable_file_path = os.path.abspath( os.path.join(save_dir, '{}'.format( immutable)) )
    #    fpart_excluded_ext = get_max_path(arg_cut, fs_f_max, fpart_excluded_ext_before
    #        , immutable_file_path)
    #else:
    fpart_excluded_ext = get_max_path(arg_cut, fs_f_max, fpart_excluded_ext_before
            , immutable)
    if fpart_excluded_ext:
        if fpart_excluded_ext_before == fpart_excluded_ext: # means not truncat
            # Prevent confuse when trailing period become '..'ext and looks like '...'
            if fpart_excluded_ext[-1] == '.':
                fpart_excluded_ext = fpart_excluded_ext[:-1]
        else: # Truncated
            # No need care if two/three/... dots, overkill to trim more and loss information
            if fpart_excluded_ext[-1] == '.':
                fpart_excluded_ext = fpart_excluded_ext[:-1]

            #if IS_WIN: # [DEPRECATED] Now always use -el
            #    # Need set ... here, not abspath below which trimmed ... if ... at the end.
            #    # Also ensures sanitize replace single '.', not '..' which causes number not equal after added ... later
            #    immutable = sanitize( pin_id_str + '....' +  ext )
            #    immutable_file_path = os.path.abspath( os.path.join(save_dir, '{}'.format( immutable)) )
            #    fpart_excluded_ext = get_max_path(arg_cut, fs_f_max, fpart_excluded_ext_before
            #            , immutable_file_path)
            #else:
            fpart_excluded_ext = get_max_path(arg_cut, fs_f_max, fpart_excluded_ext
                , '...' + immutable)

            fpart_excluded_ext = fpart_excluded_ext + '...'

    # To make final output path consistent with IS_WIN's abspath above, so also do abspath here:
    # (Please ensure below PurePath's file_path checking is using abspath if remove abspath here in future)
    file_path = os.path.abspath( os.path.join(save_dir, '{}'.format( pin_id_str + fpart_excluded_ext + '.' +  ext)) )
    #if '111' in file_path:
    #    print('last fp: ' + file_path + ' len: ' + str(len(file_path.encode('utf-8'))))
    try:
        # Note this is possible here if only . while the rest is empty, e.g. './.'
        # But better throws and inform me if that abnormal case.
        if PurePath(os.path.abspath(save_dir)).parts[:] != PurePath(file_path).parts[:-1]:
            cprint(''.join([ HIGHER_RED, '\n[! B] Please report to me which Link/scenario it print this log.\
                Thanks: {} # {} # {} # {} # {} \n\n'
                .format(arg_cut, fs_f_max, pin_id_str + fpart_excluded_ext + '.' +  ext, save_dir, file_path) ]), attrs=BOLD_ONLY, end='' )
            file_path = os.path.join(save_dir, '{}'.format( sanitize(pin_id_str + fpart_excluded_ext + '.' +  ext)))
            if PurePath(os.path.abspath(save_dir)).parts[:] != PurePath(file_path).parts[:-1]:
                cprint(''.join([ HIGHER_RED, '\n[! C] Please report to me which Link/scenario it print this log.\
                    Thanks: {} # {} # {} # {} # {} \n\n'
                    .format(arg_cut, fs_f_max, pin_id_str + fpart_excluded_ext + '.' +  ext, save_dir, file_path) ]), attrs=BOLD_ONLY, end='' )
                raise
    except IndexError:
        cprint(''.join([ HIGHER_RED, '\n[! D] Please report to me which Link/scenario it print this log.\
            Thanks: {} # {} # {}\n\n'
            .format(arg_cut, fs_f_max, pin_id_str + fpart_excluded_ext + '.' +  ext) ]), attrs=BOLD_ONLY, end='' )
        raise
    #print('final f: ' + file_path)
    return file_path

def isVideoExist(image):
    #dj(image)
    if ('videos' in image) and image['videos']: # image['videos'] may None
        return 1 # Video type 1 in 'V_720P'
    elif 'story_pin_data' in image and image['story_pin_data'] and ('pages' in image['story_pin_data']): # image['story_pin_data'] may null
        pg = image['story_pin_data']['pages']
        if (len(pg) > 0) and ('blocks' in pg[0]):
            blocks = pg[0]['blocks']
            if len(blocks) > 0 and 'video' in blocks[0] and ('video_list' in blocks[0]['video']):
                return 2 # Video type 2 in 'V_EXP7'
    return 0 # No video

def download_img(image, save_dir, arg_force_update, arg_img_only, arg_v_only, IMG_SESSION, V_SESSION, PIN_SESSION, proxies, cookie_file, arg_cut, arg_el, fs_f_max):

    try:
        # Using threading.Lock() if necessary
        if 'id' not in image:
            print('\n\nSkip no id\n\n')
            return
        image_id = image['id']

        human_fname = ''
        if ('grid_title' in image) and image['grid_title']:
            human_fname = '_' + image['grid_title']
        # Got case NoneType
        if ('closeup_unified_description' in image) and image['closeup_unified_description'] and image['closeup_unified_description'].strip():
            human_fname = '_'.join((human_fname, image['closeup_unified_description'].strip()))
        elif ('description' in image) and image['description'] and image['description'].strip():
            human_fname = '_'.join((human_fname, image['description'].strip()))
        if ('created_at' in image) and image['created_at']:
            # Don't want ':' become '..' later, so remove ':' early
            img_created_at = image['created_at'].replace(':', '').replace(' +0000', '')
            # Trim `Tue, 01 Sep 2015 011033` to 01Sep2015 to save space in filename
            #, can check log if want details
            img_created_at_l = img_created_at.split(' ')
            if len(img_created_at_l) == 5:
                img_created_at = ''.join(img_created_at_l[1:4])
            human_fname = '_'.join([human_fname, img_created_at])
        # Avoid DD/MM/YYYY truncated when do basename
        # But inside get_output_file_path got sanitize also # So no need do here
        # human_fname = human_fname.replace('/', '|').replace(':', '_')

        #print(human_fname)

        if not arg_v_only and ('images' in image):
            url = image['images']['orig']['url']

            #hn_bk = human_fname # TESTING -el
            #human_fname = human_fname + 'A'*500 # TESTING -el
            file_path = get_output_file_path(url, arg_cut, fs_f_max, image_id, human_fname, save_dir)
            #human_fname = hn_bk # TESTING -el
            if arg_el:
                file_path = '\\\\?\\' + os.path.abspath(file_path)

            if not os.path.exists(file_path) or arg_force_update:
                #print(IMG_SESSION.headers)

                #url = 'https://httpbin.org/get'
                is_ok = False
                for t in (15, 30, 40, 50, 60):
                    try:
                        with open(cookie_file) as f:
                            rawdata = f.read()
                        my_cookie = SimpleCookie()
                        my_cookie.load(rawdata)
                        cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                        cookies = cookiejar_from_dict(cookies)
                    except:
                        cookies = None
                    try:
                        r = IMG_SESSION.get(url, stream=True, timeout=(t, t), cookies=cookies)
                        is_ok = True
                        #raise(requests.exceptions.ConnectionError)
                        break
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                        # Shouldn't print bcoz quite common
                        time.sleep(5)
                        IMG_SESSION = get_session(3, proxies, cookies)
                        #cprint(''.join([ HIGHER_RED, '{}'.format('\n[' + x_tag + '] Image Timeout (Retry next).\n') ]), attrs=BOLD_ONLY, end='' )

                #print(url + ' ok? '  + str(r.ok))

                #print('https://www.pinterest.com/pin/' + image['id'])
                if is_ok and r.ok: # not `or`, 1st check is ensure no throws, 2nd check is ensure valid url
                    #print(r.text)
                    try:
                        with open(file_path, 'wb') as f:
                            for chunk in r:
                                f.write(chunk)
                                #raise(requests.exceptions.ConnectionError)
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                            is_success = False
                            for t in (15, 30, 40, 50, 60):
                                time.sleep(5)
                                try:
                                    with open(cookie_file) as f:
                                        rawdata = f.read()
                                    my_cookie = SimpleCookie()
                                    my_cookie.load(rawdata)
                                    cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                                    cookies = cookiejar_from_dict(cookies)
                                except:
                                    cookies = None
                                try:
                                    IMG_SESSION_RETY = get_session(3, proxies, cookies)
                                    r = IMG_SESSION_RETY.get(url, stream=True, timeout=(t, t), cookies=cookies) # Need higher timeout
                                    with open(file_path, 'wb') as f:
                                        for chunk in r:
                                            f.write(chunk)
                                            #raise(requests.exceptions.ConnectionError)
                                    is_success = True
                                    break
                                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                                    pass
                            if not is_success:
                                cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this image at'
                                , file_path, 'failed URL:', url, '\n') ]), attrs=BOLD_ONLY, end='' )
                                cprint(''.join([ HIGHER_RED, '%s' % ('\n[e1] You may want to delete this image manually and retry later(with -rs or try with single pin '
                                + ('https://www.pinterest.com/pin/' + repr(image['id']).strip("'")  ) + ').\n\n') ]), attrs=BOLD_ONLY, end='' )
                    except OSError: # e.g. File name too long
                        cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this image at'
                            , file_path, 'failed :', url, '\n') ]), attrs=BOLD_ONLY, end='' )
                        cprint(''.join([ HIGHER_RED, '%s' % ('\nYou may want to use -c <Maximum length of filename>\n\n') ]), attrs=BOLD_ONLY, end='' )
                        return quit(traceback.format_exc())

                else:
                    #cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this image at'
                    #, file_path, 'failed :', url, '\n') ]), attrs=BOLD_ONLY, end='' )
                    imgDimens = []
                    imgDimensD = {}
                    for ik, iv in image['images'].items():
                        if 'x' in ik:
                            imgDimens.append(iv['width'])
                            imgDimensD[iv['width']] =  iv['url']
                    if imgDimens:
                        imgDimens.sort(key=int)
                        url = imgDimensD[int(imgDimens[-1])]
                        #double \n\n to make if unlikely same line behind thread progress bar
                        #cprint('\n\n[...] Retry with second best quality url: {}'.format(url), attrs=BOLD_ONLY)

                        file_path = get_output_file_path(url, arg_cut, fs_f_max, image_id, human_fname, save_dir)
                        if arg_el:
                            file_path = '\\\\?\\' + os.path.abspath(file_path)

                        if not os.path.exists(file_path) or arg_force_update:
                            is_ok = False
                            for t in (15, 30, 40, 50, 60):
                                try:
                                    with open(cookie_file) as f:
                                        rawdata = f.read()
                                    my_cookie = SimpleCookie()
                                    my_cookie.load(rawdata)
                                    cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                                    cookies = cookiejar_from_dict(cookies)
                                except:
                                    cookies = None
                                try:
                                    # timeout=(connect_timeout, read_timeout)
                                    # https://github.com/psf/requests/issues/3099#issuecomment-215498005

                                    r = IMG_SESSION.get(url, stream=True, timeout=(t, t), cookies=cookies)
                                    is_ok = True
                                    break
                                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                                    time.sleep(5)
                                    IMG_SESSION = get_session(3, proxies, cookies)
                            if is_ok and r.ok:

                                try:
                                    with open(file_path, 'wb') as f:
                                        for chunk in r:
                                            f.write(chunk)
                                        #raise(requests.exceptions.ConnectionError)
                                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                                    is_success = False
                                    for t in (15, 30, 40, 50, 60):
                                        time.sleep(5)
                                        try:
                                            with open(cookie_file) as f:
                                                rawdata = f.read()
                                            my_cookie = SimpleCookie()
                                            my_cookie.load(rawdata)
                                            cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                                            cookies = cookiejar_from_dict(cookies)
                                        except:
                                            cookies = None
                                        try:
                                            IMG_SESSION_RETY = get_session(3, proxies, cookies)
                                            r = IMG_SESSION_RETY.get(url, stream=True, timeout=(t, t), cookies=cookies)
                                            with open(file_path, 'wb') as f:
                                                for chunk in r:
                                                    f.write(chunk)
                                                #raise(requests.exceptions.ConnectionError)
                                            is_success = True
                                            break
                                        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                                            pass
                                    if not is_success:
                                        cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this image at'
                                            , file_path, 'failed :', url, '\n') ]), attrs=BOLD_ONLY, end='' )
                                        cprint(''.join([ HIGHER_RED, '%s' % ('\n[e2] You may want to delete this image manually and retry later.\n\n') ]), attrs=BOLD_ONLY, end='' )

                                except OSError: # e.g. File name too long
                                    cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Retried this image at'
                                        , file_path, 'failed :', url, '\n') ]), attrs=BOLD_ONLY, end='' )
                                    cprint(''.join([ HIGHER_RED, '%s' % ('\nYou may want to use -c <Maximum length of filename>\n\n') ]), attrs=BOLD_ONLY, end='' )
                                    return quit(traceback.format_exc())

                                #print('\n\n[' + plus_tag + '] ', end='') # konsole has issue if BOLD_ONLY with cprint with plus_tag
                                # Got case replace /originals/(detected is .png by imghdr)->covert to .png replace 736x bigger size than orig's png (but compare quality is not trivial), better use orig as first choice
                                # e.g. https://www.pinterest.com/antonellomiglio/computer/ 's https://i.pinimg.com/736x/3d/f0/88/3df088200b94f0b6b8325ae0a118b401--apple-computer-next-computer.jpg
                                #cprint('\nRetried with second best quality url success :D {} saved to {}\n'.format(url, file_path), attrs=BOLD_ONLY)
                            else:
                                cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Retried this image at'
                                , file_path, 'failed :', url, '\n') ]), attrs=BOLD_ONLY, end='' )
                        else:
                            pass #cprint('\nFile at {} already exist.\n'.format(file_path), attrs=BOLD_ONLY)

        else:
            pass #print('No image found in this image index. This is normal (may be 1))')

        if not arg_img_only:
            video_type = isVideoExist(image)
            if video_type == 0: # No video
                return

            #dj(image, 'before override') # override m3u8-only data with pin details page mp4
            v_pin_id = image['id']
            image = get_pin_info(v_pin_id, None, None, None, False, False, None, None, None, None, IMG_SESSION, V_SESSION, PIN_SESSION, proxies, cookie_file, True)
            #dj(image, 'after override') # [todo:0] Rich Metadata for video write to log (only pin can get)
            if not image:
                cprint(''.join([ HIGHER_RED, '%s %s%s' % ('\n[' + x_tag
                    + '] Get this video pin id failed :', v_pin_id, '\n') ]), attrs=BOLD_ONLY, end='' )
                return
            if video_type == 1:
                v_d = image['videos']['video_list']
            elif video_type == 2: # Already check index/key in isVideoExist()
                v_d_unsort = image['story_pin_data']['pages'][0]['blocks'][0]['video']['video_list']
                v_d = OrderedDict(sorted(v_d_unsort.items(), key=lambda t: t[0])) # Sort by V_EXP{3-7} (V_HLSV3_MOBILE will ignore below since not .mp4)
            #dj(v_d)
            vDimens = []
            vDimensD = {}
            for v_format, v_v in v_d.items():
                if 'url' in v_v and v_v['url'].endswith('mp4'):
                    vDimens.append(v_v['width'])
                    vDimensD[v_v['width']] =  v_v['url']
            if vDimens:
                vDimens.sort(key=int)
                vurl = vDimensD[int(vDimens[-1])]
                #print('\n' + vurl)
                #cprint('\n\n[...] Try with best quality video: {}'.format(vurl), attrs=BOLD_ONLY)

                file_path = get_output_file_path(vurl, arg_cut, fs_f_max, image_id, human_fname, save_dir)
                #print(file_path)

                # We MUST get correct file_path first to avoid final filename != trimmed filename
                # ... which causes `not os.path.exists(file_path)` failed and re-download
                if arg_el:
                    file_path = '\\\\?\\' + os.path.abspath(file_path)

                if not os.path.exists(file_path) or arg_force_update:

                    is_ok = False
                    for t in (15, 30, 40, 50, 60):
                        try:
                            with open(cookie_file) as f:
                                rawdata = f.read()
                            my_cookie = SimpleCookie()
                            my_cookie.load(rawdata)
                            cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                            cookies = cookiejar_from_dict(cookies)
                        except:
                            cookies = None
                        try:
                            r = V_SESSION.get(vurl, stream=True, timeout=(t, t), cookies=cookies)
                            is_ok = True
                            break
                        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                            # Shouldn't print bcoz quite common
                            time.sleep(5) #cprint(''.join([ HIGHER_RED, '{}'.format('\n[' + x_tag + '] Video Timeout (Retry next).\n') ]), attrs=BOLD_ONLY, end='' )
                            V_SESSION = get_session(4, proxies, cookies)

                    #print(vurl + ' ok? '  + str(r.ok))

                    if is_ok and r.ok:
                        #print(r.text)
                        try:
                            with open(file_path, 'wb') as f:
                                for chunk in r:
                                    f.write(chunk)
                                    #raise(requests.exceptions.ConnectionError)
                        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                            # requests.exceptions.ChunkedEncodingError: ("Connection broken: ConnectionResetError(104, 'Connection reset by peer')", ConnectionResetError(104, 'Connection reset by peer'))
                            is_success = False
                            for t in (15, 30, 40, 50, 60):
                                time.sleep(5)
                                try:
                                    with open(cookie_file) as f:
                                        rawdata = f.read()
                                    my_cookie = SimpleCookie()
                                    my_cookie.load(rawdata)
                                    cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                                    cookies = cookiejar_from_dict(cookies)
                                except:
                                    cookies = None
                                try:
                                    V_SESSION_RETY = get_session(4, proxies, cookies)
                                    r = V_SESSION_RETY.get(vurl, stream=True, timeout=(t, t), cookies=cookies)
                                    with open(file_path, 'wb') as f:
                                        for chunk in r:
                                            f.write(chunk)
                                            #raise(requests.exceptions.ConnectionError)
                                    is_success = True
                                    break
                                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                                    pass
                            if not is_success:
                                cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this video at'
                                    , file_path, 'failed :', vurl, '\n') ]), attrs=BOLD_ONLY, end='' )
                                cprint(''.join([ HIGHER_RED, '%s' % ('\n[e3] You may want to delete this video manually and retry later.\n\n') ]), attrs=BOLD_ONLY, end='' )
                        except OSError: # e.g. File name still too long
                            cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this video at'
                                , file_path, 'failed :', vurl, '\n') ]), attrs=BOLD_ONLY, end='' )
                            cprint(''.join([ HIGHER_RED, '%s' % ('\nYou may want to use -c <Maximum length of filename>\n\n') ]), attrs=BOLD_ONLY, end='' )
                            return quit(traceback.format_exc())

                    else:
                        cprint(''.join([ HIGHER_RED, '%s %s %s %s%s' % ('\n[' + x_tag + '] Download this video at'
                            , save_dir, 'failed :', vurl, '\n') ]), attrs=BOLD_ONLY, end='' )

    except: # Need catch inside job, or else it doesn't throws
        print()
        return quit(traceback.format_exc())

def create_dir(save_dir):

    try:
        if IS_WIN:
            os.makedirs('\\\\?\\' + os.path.abspath(save_dir))
        else:
            os.makedirs(save_dir)
    except FileExistsError: # Check this first to avoid OSError cover this
        pass # Normal if re-download
    except OSError: # e.g. File name too long

        # Only need to care for individual path component
        #, i.e. os.statvfs('./').f_namemax = 255(normal fs), 242(docker) or 143(eCryptfs) )
        #, not full path( os.statvfs('./').f_frsize - 1 = 2045)
        # Overkill seems even you do extra work to truncate path, then what if user give arg_dir at
        # ... 2045th path? how is it possible create new dir/file from that point?
        # So only need to care for individual component
        #... which max total(estimate) is uname 100 + (boardname 50*4)+( section 50*3) = ~450 bytes only.
        # Then add max file 255 bcome 705, still far away from 2045th byte(or 335 4_bytes utf-8)
        # So you direct throws OSError enough to remind that user don't make insane fs hier

        cprint(''.join([ HIGHER_RED, '%s' % ('\nIt might causes by too long(2045 bytes) in full path.\
        You may want to to use -d <other path> OR -c <Maximum length of folder & filename>.\n\n') ]), attrs=BOLD_ONLY, end='' )
        raise

def write_log(arg_timestamp_log, url_path, shortform
    , arg_img_only, arg_v_only
    , save_dir, images, pin, arg_cut, break_from_latest_pin):

    got_img = False

    if arg_timestamp_log:
        if pin:
            log_timestamp = 'log-pinterest-downloader_' + str(pin) + '_' + datetime.now().strftime('%Y-%m-%d %H.%M.%S')
        else: # None
            log_timestamp = 'log-pinterest-downloader_' + datetime.now().strftime('%Y-%m-%d %H.%M.%S')
    else:
        if pin:
            log_timestamp = 'log-pinterest-downloader_' + str(pin)
        else:
            log_timestamp = 'log-pinterest-downloader'
    # sanitize enough, no nid max path in case PIN id too long, throws err (too long path)
    # to inform me better than silently guess to slice [:100] early and hide this issue
    # Currently possible long non-number A8pQTwIQQLQGWEacY5vc6og pin id
    log_path = os.path.join(save_dir, '{}'.format( sanitize(log_timestamp) + '.log' ))

    if not pin:
        # Since no image will not log, so need separate file store for urls
        # Don't want combine with old log or else you need open the file to see got title/desc or not even though no content.
        log_url_path = os.path.join(save_dir, 'urls-pinterest-downloader.urls')

        with open(log_url_path, 'w', encoding="utf-8") as f:
            f.write('Pinterest Downloader: Version ' + str(__version__)  + '\n\n') # Easy to recognize if future want to change something
            # Ensure -ua same parsing format
            f.write('Input URL: https://www.pinterest.com/' + url_path.rstrip('/')  + '/\n') # Reuse/refer when want to update
            if shortform: # single pin no need
                f.write('Folder URL: https://www.pinterest.com/' + shortform.rstrip('/') + '/\n\n') # Reuse/refer when want to update specific folder only

    if images:
        #dj(images)
        #print('len(images) IF: ' + str(len(images)))
        index_last = 0
        existing_indexes = []

        if break_from_latest_pin and not arg_timestamp_log:
            try:
                with open(log_path, encoding="utf-8") as f:
                    index_line = [l for l in f.readlines() if l.startswith('[ ')]
                    index_last_tmp = index_line[-1].split('[ ')[1].split(' ]')[0]
                    if index_last_tmp.isdigit():
                        index_last = int(index_last_tmp)
                    for l in index_line:
                        existing_indexes.append(l.split('[ ')[1].split(' ] Pin Id: ')[1].strip())
            except (FileNotFoundError, OSError, KeyError, TypeError):
                cprint(''.join([ HIGHER_YELLOW, '%s' % ('\nWrite log increment from last log stored index failed. Fallback to -lt\n\n') ]), attrs=BOLD_ONLY, end='' )
                log_timestamp = 'log-pinterest-downloader_' + datetime.now().strftime('%Y-%m-%d %H.%M.%S')
                log_path = os.path.join(save_dir, '{}'.format( sanitize(log_timestamp) + '.log' ))
                with open(log_path, 'w', encoding='utf-8') as f: # Refer below else:
                    f.write('Pinterest Downloader: Version ' + str(__version__)  + '\n\n')
        else:

            if pin:
                img_total = 1
            elif break_from_latest_pin: # Already cut last non-image, so no need -1
                img_total = len(images) # possible single video without extra padding, so still need loop all+check id/image/video to get real total count
            else:
                img_total = len(images) - 1
                if img_total == 0:
                    if ( (not arg_img_only and isVideoExist(images[0])) \
                        or (not arg_v_only and ('images' in images[0])) ):
                        img_total = 1 # 1st index may valid item if single video in board
            if img_total == 0: # No need create log when empty folder, but still created .urls above
                return False
            else:
                with open(log_path, 'w', encoding='utf-8') as f: # Reset before append
                    f.write('Pinterest Downloader: Version ' + str(__version__)  + '\n\n') # Easy to recognize if future want to change something
                    f.write('Input URL: https://www.pinterest.com/' + url_path.rstrip('/')  + '/\n') # Reuse/refer when want to update
                    if shortform: # single pin no need
                        f.write('Folder URL: https://www.pinterest.com/' + shortform.rstrip('/') + '/\n\n') # Reuse/refer when want to update specific folder only
                    else:
                        f.write('\n')
        skipped_total = 0
        #print(existing_indexes)
        for log_i, image in enumerate(images):
            if 'id' not in image:
                #dj(image)
                skipped_total+=1
                continue
            got_img = True
            image_id = image['id']
            #print('valid id:' + str(image_id))
            if image_id in existing_indexes:
                print('dup image_id ' + str(image_id))
                # Still got_img True to try re-download flow since only want to ensure log don't want duplicated if reorder
                continue
            # Exclude image log if --video-only, and vice-versa.
            if not ( (not arg_img_only and isVideoExist(image)) \
                    or (not arg_v_only and ('images' in image)) ):
                skipped_total+=1
                continue

            #print('last:'+str(index_last) + ' curr_i:' + str(log_i) + ' curr:' + str(skipped_total))

            #dj(image)
            #print('got img: ' + image_id) # Possible got id but empty section
            #, so still failed to use got_img to skip showing estimated 1 image if actually empty
            story = ''
            #print(image)
            #print(image_id)
            # if use 'title' may returns dict {'format': 'Find more ideas', 'text': None, 'args': []}
            if ('grid_title' in image) and image['grid_title']:
                story = '\nTitle: ' + image['grid_title'].replace('\n', ' ').strip()
            # Got case NoneType
            if ('closeup_unified_description' in image) and image['closeup_unified_description'] and image['closeup_unified_description'].strip():
                story += '\nDescription: ' + image['closeup_unified_description'].replace('\n', ' ').strip()
            elif ('description' in image) and image['description'] and image['description'].strip():
                story += '\nDescription: ' + image['description'].replace('\n', ' ').strip()
            if ('created_at' in image) and image['created_at']:
                story += '\nCreated at: ' + image['created_at'].replace('\n', ' ').strip()
            if ('link' in image) and image['link']:
                story += '\nLink: ' + image['link'].replace('\n', ' ').strip()
            if ('rich_metadata' in image) and image['rich_metadata']:
                story += '\n\nMetadata: ' + repr(image['rich_metadata']).replace('\n', ' ').strip()
            if story:
                try:
                    # Windows need utf-8
                    with open(log_path, 'a', encoding='utf-8') as f:
                        #print('last index:'+ str(index_last) + ' curr_i:' + str(log_i) + ' curr:' + str(skipped_total))
                        #print('last log:'+ str(index_last + log_i + 1 - skipped_total))
                        f.write('[ ' + str(index_last + log_i + 1 - skipped_total) + ' ] Pin Id: ' + str(image_id) + '\n')
                        f.write(story + '\n\n')
                except OSError: # e.g. File name too long
                    cprint(''.join([ HIGHER_RED, '%s' % ('\nYou may want to use -c <Maximum length of filename>\n\n') ]), attrs=BOLD_ONLY, end='' )
                    return quit(traceback.format_exc())
            else:
                skipped_total+=1
                continue

    return got_img

def sort_func(x):
    prefix = x.split('.')[0].split('_')[0]
    if prefix.isdigit():
       return int(prefix)
    return 0

def get_latest_pin(save_dir):
    # Currently possible long non-number A8pQTwIQQLQGWEacY5vc6og pin id but should rare case and ignore/re-scrape is fine
    latest_pin = '0'
    depth = 1
    # rf: https://stackoverflow.com/a/42720847/1074998 # Don't use expanduser and expandvars for arbitrary input
    # [1] abspath() already acts as normpath() to remove trailing os.sep
    #, and we need ensures trailing os.sep not exists to make slicing accurate.
    # [2] abspath() also make /../ and ////, "." get resolved even though os.walk can returns it literally.
    walk_dir = os.path.abspath(save_dir)
    for root, dirs, files in os.walk(walk_dir):
        if root[len(walk_dir):].count(os.sep) < depth:
            imgs_f = [_ for _ in files if _.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.mp4', '.mkv', '.webp', '.svg', '.m4a', '.mp3', '.flac', '.m3u8', '.wmv', '.webm', '.mov', '.flv', '.m4v', '.ogg', '.avi', '.wav', '.apng', '.avif' )) ] # paranoid list
            imgs_f_sorted = sorted(imgs_f, key=sort_func)
            if not imgs_f_sorted: # only 1 depth
                break
            latest_pin = imgs_f_sorted[-1].split('.')[0].split('_')[0]

    # if latest pin deleted remote then will acts as -rs
    #print('latest_pin: ' + latest_pin)
    return latest_pin

def fetch_imgs(board, uname, board_slug, section_slug, is_main_board
    , arg_timestamp, arg_timestamp_log, url_path
    , arg_force_update, arg_rescrape, arg_img_only, arg_v_only
    , arg_dir, arg_thread_max
    , IMGS_SESSION, IMG_SESSION, V_SESSION, PIN_SESSION, proxies
    , cookie_file, arg_cut, arg_el, fs_f_max):

    bookmark = None
    images = []

    if is_main_board:
        shortform = uname
    else:
        if section_slug:
            shortform = '/'.join((uname, board_slug, section_slug))
        else:
            shortform = '/'.join((uname, board_slug))

    if arg_timestamp:
        timestamp_d = '_' + datetime.now().strftime('%Y-%m-%d %H.%M.%S') + '.d'
    else:
        timestamp_d = ''
    try:
        #dj(board, 'fetch imgs')
        if 'owner' in board:
            #uname = board['owner']['username']
            #save_dir = os.path.join(arg_dir, uname, board['name'] + timestamp_d)
            #url = board['url']
            bid = board['id']
            # Might unicode, so copy from web browser become %E4%Bd
            #... which is not the board filename I want
            board_name_folder = board['name']
            #print('root bname: ' + repr(board_name_folder))
        elif 'board' in board:
            #uname = board['pinner']['username']
            #save_dir = os.path.join(arg_dir, uname, board['board']['name'] + timestamp_d)
            #url = board['board']['url']
            bid = board['board']['id']
            board_name_folder = board['board']['name']
            #print('child bname: ' + repr(board_name_folder))
            if section_slug:
                try:
                    section_id = board['section']['id']
                except (KeyError, TypeError):
                    return quit('{}'.format('\n[' + x_tag + '] Section may not exist.\n') )
                section_folder = board['section']['title']
        else:
            return quit('{}'.format('\n[' + x_tag + '] No item found.\n\
Please ensure your username/boardname/[section] or link has media item.\n') )
    except (KeyError, TypeError):
        cprint(''.join([ HIGHER_RED, '%s %s %s' % ('\n[' + x_tag + '] Failed. Path:', shortform, '\n\n') ]), attrs=BOLD_ONLY, end='' )
        return quit(traceback.format_exc() + '\n[!] Something wrong with Pinterest URL. Please report this issue at https://github.com/limkokhole/pinterest-downloader/issues , thanks.')

    fs_d_max = fs_f_max
    #if IS_WIN: # [DEPRECATED] since always -el now AND Windows 259 - \\?\ = 255 normal Linux
    #    if arg_el: # Directory cannot use -el
    #        fs_d_max = WIN_MAX_PATH

    if section_slug:
        # Put -1 fot arg_cut arg bcoz don't want cut on directory
        # to avoid cut become empty (or provide new arg -c-cut-directory
        # , but overcomplicated and in reality who want to cut dir?
        # ... Normally only want cut filename bcoz of included title/description )
        save_dir = os.path.join( arg_dir,  get_max_path(-1, fs_d_max, sanitize(uname), None)
            , get_max_path(-1, fs_d_max, sanitize(board_name_folder + timestamp_d), None)
            , get_max_path(-1, fs_d_max, sanitize(section_folder), None) )
        # Impossible is_main_board here
        url = '/' + '/'.join((uname, board_slug, section_slug)) + '/'
    else:
        save_dir = os.path.join( arg_dir,  get_max_path(-1, fs_d_max, sanitize(uname), None)
            , get_max_path(-1, fs_d_max, sanitize(board_name_folder + timestamp_d), None))
        # If boardname in url is lowercase but title startswith ' which quotes to %22 and cause err
        #... So don't use board_name_folder as board_name in url below to call API
        if is_main_board:
            url = uname
        else:
            url = '/'.join((uname, board_slug))

    #if not section_slug:
    #   print('[Board id]: '+ repr(bid))

    if not arg_rescrape:
        latest_pin = get_latest_pin(save_dir)

    break_from_latest_pin = False
    sorted_api = True
    while bookmark != '-end-':

        if section_slug:

            options = {
            'isPrefetch': 'false',
            'field_set_key': 'react_grid_pin',
            'is_own_profile_pins': 'false',
            'page_size': 25,
            'redux_normalize_feed': 'true',
            'section_id': section_id,
            }

        else:
            options = {
            'isPrefetch': 'false',
            'board_id': bid,
            'board_url': url,
            'field_set_key': 'react_grid_pin',
            'filter_section_pins': 'true',
            #'order': 'DESCENDING',#'oldest',#'default',
            #'order': 'default',
            #'sort':'last_pinned_to',
            #'sortDirection': 'newest',
            #'most_recent_board_sort_order': 'first_pinned_to',
            'layout':'default',
            'page_size': 25,#10,#25,
            'redux_normalize_feed': 'true',
            }

        #print('bookmark: ' + repr(bookmark))
        if bookmark:
            options.update({
                'bookmarks': [bookmark],
            })

        i_len = len(images) - 1
        if i_len < 0:
            i_len = 0
        # Got end='' here also not able make flush work
        if section_slug:
            print('\r[...] Getting all images in this section: {}/{} ... [ {} / ? ]'
                .format(board_slug, section_slug, str(i_len)), end='')
        else:
            print('\r[...] Getting all images in this board: {} ... [ {} / ? ]'
                .format(board_slug, str(i_len)), end='')
        sys.stdout.flush()

        post_d = urllib.parse.urlencode({
            'source_url': url,
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22') \
        .replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        #print(post_d)
        #print('[imgs] called headers: ' + repr(IMGS_SESSION.headers))

        for t in (15, 30, 40, 50, 60):
            try:
                if section_slug:
                    try:
                        with open(cookie_file) as f:
                            rawdata = f.read()
                        my_cookie = SimpleCookie()
                        my_cookie.load(rawdata)
                        cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                        cookies = cookiejar_from_dict(cookies)
                    except:
                        cookies = None
                    r = IMGS_SESSION.get('https://www.pinterest.com/resource/BoardSectionPinsResource/get/'
                        , params=post_d, timeout=(t, t), cookies=cookies)
                else:
                    try:
                        with open(cookie_file) as f:
                            rawdata = f.read()
                        my_cookie = SimpleCookie()
                        my_cookie.load(rawdata)
                        cookies = {key: morsel.value for key, morsel in my_cookie.items()}
                        cookies = cookiejar_from_dict(cookies)
                    except:
                        cookies = None
                    r = IMGS_SESSION.get('https://www.pinterest.com/resource/BoardFeedResource/get/'
                        , params=post_d, timeout=(t, t), cookies=cookies)
                data = r.json()
                if data['resource_response']['data'] is None:
                    cprint(''.join([ HIGHER_YELLOW, '%s' % ('Failed. Retry after 30 seconds.') ]), attrs=BOLD_ONLY, end='\n' )
                    time.sleep(30)
                    IMGS_SESSION = get_session(2, proxies, cookies)
                    continue # Retry for issues #19
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                time.sleep(5)
                IMGS_SESSION = get_session(2, proxies, cookies)

        #print('Imgs url ok: ' + str(r.ok))
        #print('Imgs url: ' + r.url)
        #dj(data, 'imgs loop raw')
        # Useful for debug with print only specific id log
        #if 'e07614d79a22d22c83d51649e2e01e43' in repr(data):
        #    print('res data: ' + repr(data))
        imgs_round = data['resource_response']['data']

        #print()
        #for img in imgs_round:
        #    print('before img: ' + repr(img['id']))

        reach_lastest_pin = False
        if not arg_rescrape and sorted_api and (latest_pin != '0'):
            img_prev = 0
            on_hold_break = False
            # Video + thumbnails has 2 same id files with diff extension
            #, but API only return single item, so no nid handle equal flow
            for img_round_i, img in enumerate(imgs_round):
                #print('Check: ' + repr(img['id']))
                if (isVideoExist(img)) or 'images' in img:
                    if img['id'].isdigit():
                        img_curr = img['id']
                        if img_prev and (int(img_curr) > int(img_prev)):
                            cprint(''.join([ HIGHER_YELLOW, '%s' % ('\n[W] This images list is not sorted(Due to user reorder), fallback to -rs for this list.\n\n') ]), attrs=BOLD_ONLY, end='' )
                            sorted_api = False
                            reach_lastest_pin = False
                            if on_hold_break:
                                imgs_round = data['resource_response']['data'] # replaced back below
                            break
                        if latest_pin == img_curr:
                            #print('\nAlready scroll to latest downloaded pin. Break.')
                            #print('bookmark: ' + repr(bookmark))
                            imgs_round = imgs_round[:img_round_i]
                            reach_lastest_pin = True
                            # Next check all 25 items in current page to know owner recently has reorder habit or not
                            on_hold_break = True
                        img_prev = img_curr
                    else:
                        cprint(''.join([ HIGHER_YELLOW, '%s' % ('\n[W] This images list is not sorted(Due to alphanumeric pin ID), fallback to -rs for this list.\n\n') ]), attrs=BOLD_ONLY, end='' )
                        sorted_api = False
                        reach_lastest_pin = False
                        imgs_round = data['resource_response']['data'] # replaced back above
                        break
                else:
                    pass #print('Not media.')
        #for img in imgs_round:
        #    print('real img: ' + repr(img['id']))
        images.extend(imgs_round)
        if reach_lastest_pin:
            break_from_latest_pin = True
            break

        #dj(data['resource_response']['data'], 'img raw')
        #print(data.keys())
        #dj(data['client_context'], 'img raw')
        #dj(data['resource'], 'img raw')
        #dj(data['request_identifier'], 'img raw') # "<ID>" only
        #dj(data['resource_response'], 'img raw')
        bookmark = data['resource']['options']['bookmarks'][0]

        #break # hole: testing purpose # Remember remove this after test lolr

    if sorted_api:
        images = images[::-1] # reverse order to oldest pin id -> latest pin id for -u to work
    #for img in images:
    #    print(img['id'])

    create_dir(save_dir)
    got_img = write_log(arg_timestamp_log, url_path, shortform, arg_img_only, arg_v_only, save_dir, images, None, arg_cut, break_from_latest_pin)

    if got_img:
        # Always got extra index is not media, so -1 # [UPDATE] single video board might a media
        # Didn't bring loop above detect early
        if break_from_latest_pin: # Already check got video/image for images, so no need -1
            img_total = len(images)
        else:
            img_total = len(images) - 1
            if img_total == 0:
                if ( (not arg_img_only and isVideoExist(images[0])) \
                    or (not arg_v_only and ('images' in images[0])) ):
                    img_total = 1 # 1st index may valid item if single video in board
        if img_total == 0:
            print('\n[i] No {}item found.'.format('new ' if break_from_latest_pin else  ''))
            return
        print( (' [' + plus_tag + '] Found {} {}image/video' + ('s' if img_total > 1 else '') )
            .format(img_total, 'new ' if break_from_latest_pin else  ''))
        print('Download into directory:  ' + save_dir.rstrip(os.sep) + os.sep)
    else:
        print('\n[i] No {}item found.'.format('new ' if break_from_latest_pin else  ''))
        return

    if arg_thread_max < 1:
        arg_thread_max = None # Use default: "number of processors on the machine, multiplied by 5"

    with ThreadPoolExecutor(max_workers = arg_thread_max) as executor:

        # Create threads
        futures = {executor.submit(download_img, image, save_dir, arg_force_update, arg_img_only, arg_v_only
                , IMG_SESSION, V_SESSION, PIN_SESSION, proxies, cookie_file, arg_cut, arg_el, fs_f_max) for image in images}

        # as_completed() gives you the threads once finished
        for index, f in enumerate(as_completed(futures)):
            # Get the results
            # rs = f.result()
            # print('done')
            printProgressBar(index + 1, len(images), prefix='[...] Downloading:'
                , suffix='Complete', length=50)

    # Need suffix with extra 3 spaces to replace previous longer ... + Downloading->ed line
    # ... to avoid see wrong word "Complete"
    printProgressBar(len(images), len(images), prefix='[' + done_tag + '] Downloaded:'
        , suffix='Complete   ', length=50)

    print()


def update_all( arg_thread_max :int, arg_cut :int, arg_rescrape :bool
    , arg_img_only, arg_v_only
    , arg_https_proxy :str, arg_http_proxy :str, arg_cookies :str):

    bk_cwd = os.path.abspath(os.getcwd())
    cwd_component_total = len(PurePath(os.path.abspath(bk_cwd)).parts[:])
    imgs_f = []
    for root, dirs, files in os.walk(bk_cwd):
        #print('#r: ' + repr(root) + ' #d: ' + repr(dirs) + ' #f: ' + repr(files))
        imgs_f.extend( [os.path.join(root, _) for _ in files if (_ == 'urls-pinterest-downloader.urls') ] )

    urls_map = {}
    cd_back_fixed_range = (1, 2, 3)
    for f in imgs_f:
        r = open(f, "r")
        input_url = None
        folder_url = None
        for line in r:
            l_strip = line.strip()
            if l_strip.startswith('Input URL: '): #re.search('^Input URL: ', line):
                input_url = l_strip.split('Input URL: ')[1].strip()
            elif l_strip.startswith('Folder URL: '):
                folder_url = l_strip.split('Folder URL: ')[1].strip()
            if input_url and folder_url:
                cd_back_count = len(folder_url.split('/')[3:]) -1 # -1 is trailing '/'
                if cd_back_count not in cd_back_fixed_range:
                    return quit( ['[E1][-ua] Input url: ' + input_url + '\nFolder url: ' + folder_url
                        , 'Something is not right. Please report this issue at https://github.com/limkokhole/pinterest-downloader/issues , thanks.'])
                # +1 is the upper path to run script previously
                dir_origin = os.path.abspath( os.path.join(f, '../'*(cd_back_count+1) ) )
                dir_split = PurePath(dir_origin).parts[:]
                # Safeguard to avoid travel to parent of current directory
                if len(dir_split) < cwd_component_total:
                    cprint(''.join([ HIGHER_YELLOW, '%s' % ('\n' + 'Update from parent directory of current directory is forbidden. Skipped.\n'
                        + 'You should cd to parent directory to update this folder:'
                        + '\nurls file: ' + f + '\nInput url: '+ input_url + '\nFolder url: ' + folder_url
                        + '\nParent directory: ' + dir_origin
                        + '\nCurrent directory: ' + bk_cwd + '\n\n') ]))
                    break
                if dir_origin in urls_map:
                    # cd_back_count: 3 means section, 2 means board, 1 means username
                    # section separate scrape, not by username/board, while board filter by username below
                    # -es force later so no section repeat.
                    # So not included new created section(new board possible if got username)
                    if cd_back_count in (2, 3):
                        urls_map[dir_origin]['info'].append(  {'url': folder_url, 'cd': cd_back_count} )
                        #print(urls_map[dir_origin])
                    elif cd_back_count  == 1:
                        urls_map[dir_origin]['username'] = True

                else:
                    urls_map[dir_origin] = {'info': [ {'url': input_url, 'cd': cd_back_count} ], 'username': True if (cd_back_count == 1) else False}
                break # Only read headers

    pre_calc_total = 0
    for i, (dir_origin, map_d) in enumerate(urls_map.items()):
        got_username = map_d['username']
        for info in map_d['info']:
            if got_username and info['cd'] == 2:
                #print('Skip board ' + info['url'] + ' since got username already.')
                continue
            pre_calc_total+=1
    real_run_index = 1
    for i, (dir_origin, map_d) in enumerate(urls_map.items()):
        os.chdir(dir_origin)
        got_username = map_d['username']
        for info in map_d['info']:
            if got_username and info['cd'] == 2:
                #print('Skip board ' + info['url'] + ' since got username already.')
                continue
            #if info['cd'] == 2:
            #    print('THIS board can use bcoz no username!')
            print('\n' + ANSI_BLUE + '[U] Updating [ ' + str(real_run_index) + ' / ' + str(pre_calc_total) + ' ] \n' + ANSI_END_COLOR + ANSI_BLUE + '[U] Changed to directory: ' + str(dir_origin).rstrip(os.sep) + os.sep + ANSI_END_COLOR)
            real_run_index+=1
            input_url = info['url']
            #print('run URL:' + input_url)
            while 1:
                try:
                    run_library_main(input_url, '.',  arg_thread_max, arg_cut, False, False, False, True, arg_rescrape, arg_img_only, arg_v_only, False, arg_https_proxy, arg_http_proxy, arg_cookies)
                    break
                except requests.exceptions.ReadTimeout:
                    cprint(''.join([ HIGHER_RED, '{}'.format('\n[' + x_tag + '] [U] Suddenly not able to connect. Please check your network.\n') ]), attrs=BOLD_ONLY, end='' )
                    time.sleep(5)
                except requests.exceptions.ConnectionError:
                    cprint(''.join([ HIGHER_RED, '{}'.format('\n[' + x_tag + '] [U] Not able to connect. Please check your network.\n') ]), attrs=BOLD_ONLY, end='' )
                    time.sleep(5)

# Caller script example:
# import importlib
# pin_dl = importlib.import_module('pinterest-downloader')
# pin_dl.run_library_main('antonellomiglio/computer', '.', 0, -1, False, False, False, False, False, False, False, False, None, None)

def run_library_main(arg_path :str, arg_dir :str, arg_thread_max :int, arg_cut :int
    , arg_board_timestamp :bool, arg_log_timestamp :bool
    , arg_force :bool, arg_exclude_section :bool, arg_rescrape :bool
    , arg_img_only :bool, arg_v_only :bool, arg_update_all :bool
    , arg_https_proxy :str, arg_http_proxy :str, arg_cookies :str):

    # Not feasible update based on latest pin if v/img only
    # , unless download zero size img if video only(vice-versa) which seems not desired.
    if arg_img_only or arg_v_only:
        arg_rescrape = True

    if arg_update_all:
        return update_all(arg_thread_max, arg_cut, arg_rescrape, arg_img_only, arg_v_only, arg_https_proxy, arg_http_proxy, arg_cookies)

    start_time = int(time.time())

    if not arg_path:
        return quit('Path cannot be empty. ')

    proxies = dict(http=arg_http_proxy, https=arg_https_proxy)
    cookies = str(arg_cookies)
    print('[i] User Agent: ' + UA)

    arg_path = arg_path.strip()
    if arg_path.startswith('https://pin.it/'):
        print('[i] Try to expand shorten url')
        SHARE_SESSION = get_session(0, proxies, cookies)
        r = SHARE_SESSION.get(arg_path, timeout=(15, 15))
        if (r.status_code == 200) and '/sent' in r.url:
            arg_path = r.url.split('/sent')[0]
            print('[i] Pin url is: ' + arg_path + '/') # may err without trailing '/'

    url_path = arg_path.split('?')[0].split('#')[0]
    # Convert % format of unicode url when copied from Firefox
    # This is important especially section need compare the section name later
    url_path = unquote(url_path).rstrip('/')
    if '://' in url_path:
        url_path = '/'.join( url_path.split('/')[3:] )
        if not url_path:
            return quit('{} {} {}'.format('\n[' + x_tag + '] Neither username/boardname nor valid link: ', arg_path, '\n') )
    url_path = url_path.lstrip('/')
    slash_path = url_path.split('/')
    if '.' in slash_path[0]:
        # Impossible dot in username, so it means host without https:// and nid remove
        slash_path = slash_path[1:]
    if len(slash_path) == 0:
        return quit('{} {} {}'.format('\n[' + x_tag + '] Neither username/boardname nor valid link: ', arg_path, '\n') )
    elif len(slash_path) > 3:
        return quit('[!] Something wrong with Pinterest URL. Please report this issue at https://github.com/limkokhole/pinterest-downloader/issues , thanks.')

    fs_f_max = None
    if IS_WIN:
        #if arg_extended_len >= 0:
        #    fs_f_max = arg_extended_len
        arg_el = True
        #else: [DEPRECATED] now always -el now AND Windows 259 - \\?\ == 255 normal Linux
        fs_f_max = WIN_MAX_PATH
    else:
        arg_el = False
        #  255 bytes is normaly fs max, 242 is docker max, 143 bytes is eCryptfs max
        # https://github.com/moby/moby/issues/1413 , https://unix.stackexchange.com/questions/32795/
        # To test eCryptfs: https://unix.stackexchange.com/questions/426950/
        # If IS_WIN check here then need add \\?\\ for WIN-only
        for fs_f_max_i in (255, 242, 143):
            try:
                with open('A'*fs_f_max_i, 'r') as f:
                    fs_f_max = fs_f_max_i # if got really this long A exists will come here
                    break
            except FileNotFoundError:
                # Will throws OSError first if both FileNotFoundError and OSError met
                # , BUT if folder not exist then will throws FileNotFoundError first
                # But current directory already there, so can use this trick
                # In worst case just raise it
                fs_f_max = fs_f_max_i # Normally came here in first loop
                break
            except OSError: # e.g. File name too long
                pass #print('Try next') # Or here first if eCryptfs
        #print('fs filename max len is ' + repr(fs_f_max))
        # https://github.com/ytdl-org/youtube-dl/pull/25475
        # https://stackoverflow.com/questions/54823541/what-do-f-bsize-and-f-frsize-in-struct-statvfs-stand-for
        if fs_f_max is None: # os.statvfs ,ay not avaiable in Windows, so lower priority
            #os.statvfs('.').f_frsize - 1 = 4095 # full path max bytes
            fs_f_max = os.statvfs('.').f_namemax

    if len(slash_path) == 2:
        # may copy USERNAME/boards/ links
        # _saved and _created only shows instead of boards if logged in, e.g. user maryellengolden
        # pins under _saved, e.g. user maryellengolden
        if slash_path[-1].strip() in ('boards', '_saved', '_created', 'pins'):
            slash_path = slash_path[:-1]
        elif slash_path[-2].strip() == 'pin':
            print('[i] Job is download video/image of single pin page.')
            pin_id = slash_path[-1] #bk first before reset
            slash_path = [] # reset for later in case exception
            PIN_SESSION = get_session(0, proxies, cookies)
            IMG_SESSION = get_session(3, proxies, cookies)
            V_SESSION = get_session(4, proxies, cookies)
            get_pin_info(pin_id.strip(), arg_log_timestamp, url_path, arg_force, arg_img_only, arg_v_only, arg_dir, arg_cut, arg_el, fs_f_max, IMG_SESSION, V_SESSION, PIN_SESSION, proxies, cookies, False)

    if len(slash_path) == 3:
        sec_path = '/'.join(slash_path)
        board_path = '/'.join(slash_path[:-1])
        print('[i] Job is download single section by username/boardname/section: {}'.format(sec_path))
        # Will err if try to create section by naming 'more_ideas'
        if ( slash_path[-3] in ('search', 'categories', 'topics') ) or ( slash_path[-1] in ['more_ideas'] ):
            return quit('{}'.format('\n[' + x_tag + '] Search, Categories, Topics, more_ideas are not supported.\n') )
        board = get_board_info(sec_path, False, slash_path[-1], board_path, proxies, cookies) # need_get_section's True/False not used
        try:
            PIN_SESSION = get_session(0, proxies, cookies)
            IMGS_SESSION = get_session(2, proxies, cookies)
            IMG_SESSION = get_session(3, proxies, cookies)
            V_SESSION = get_session(4, proxies, cookies)
            fetch_imgs( board, slash_path[-3], slash_path[-2], slash_path[-1], False
                , arg_board_timestamp, arg_log_timestamp, url_path
                , arg_force, arg_rescrape, arg_img_only, arg_v_only
                , arg_dir, arg_thread_max
                , IMGS_SESSION, IMG_SESSION, V_SESSION, PIN_SESSION, proxies
                , cookies, arg_cut, arg_el, fs_f_max )
        except KeyError:
            return quit(traceback.format_exc())

    elif len(slash_path) == 2:
        board_path = '/'.join(slash_path)
        print('[i] Job is download single board by username/boardname: {}'.format(board_path))
        if slash_path[-2] in ('search', 'categories', 'topics'):
            return quit('{}'.format('\n[' + x_tag + '] Search, Categories and Topics not supported.\n') )
        board, sections = get_board_info(board_path, arg_exclude_section, None, None, proxies, cookies)
        try:
            PIN_SESSION = get_session(0, proxies, cookies)
            IMGS_SESSION = get_session(2, proxies, cookies)
            IMG_SESSION = get_session(3, proxies, cookies)
            V_SESSION = get_session(4, proxies, cookies)
            fetch_imgs( board, slash_path[-2], slash_path[-1], None, False
                , arg_board_timestamp, arg_log_timestamp, url_path
                , arg_force, arg_rescrape, arg_img_only, arg_v_only
                , arg_dir, arg_thread_max
                , IMGS_SESSION, IMG_SESSION, V_SESSION, PIN_SESSION, proxies
                , cookies, arg_cut, arg_el, fs_f_max )
            if (not arg_exclude_section) and sections:
                sec_c = len(sections)
                print('[i] Trying to get ' + str(sec_c) + ' section{}'.format('s' if sec_c > 1 else ''))
                for sec in sections:
                    sec_path = board_path + '/' + sec['slug']
                    board = get_board_info(sec_path, False, sec['slug'], board_path, proxies, cookies) # False not using bcoz sections not [] already
                    fetch_imgs( board, slash_path[-2], slash_path[-1], sec['slug'], False
                        , arg_board_timestamp, arg_log_timestamp, url_path
                        , arg_force, arg_rescrape, arg_img_only, arg_v_only
                        , arg_dir, arg_thread_max
                        , IMGS_SESSION, IMG_SESSION, V_SESSION, PIN_SESSION, proxies
                        , cookies, arg_cut, arg_el, fs_f_max )

        except KeyError:
            return quit(traceback.format_exc())

    elif len(slash_path) == 1:
        print('[i] Job is download all boards by username: {}'.format(slash_path[-1]))
        if slash_path[-1] in ('search', 'categories', 'topics'):
            return quit('{}'.format('\n[' + x_tag + '] Search, Categories and Topics not supported.\n') )
        try:
            boards = fetch_boards( slash_path[-1], proxies, cookies)
            PIN_SESSION = get_session(0, proxies, cookies)
            IMGS_SESSION = get_session(2, proxies, cookies)
            IMG_SESSION = get_session(3, proxies, cookies)
            V_SESSION = get_session(4, proxies, cookies)
            # Multiple logs saved inside relevant board dir
            for index, board in enumerate(boards):
                if 'name' not in board:
                    print('Skip no name')
                    continue

                #dj(board)
                # E.g. /example/commodore-computers/ need trim to example/commodore-computers
                board_path = board['url'].strip('/')
                # fetch_imgs() should use url style `A-B`` instead of Title `A B``(board['name'])
                #print(board_path)
                if '/' in board_path:
                    board_slug = board_path.split('/')[1]
                    is_main_board = False
                else: # username main board
                    board_slug = board_path
                    is_main_board = True
                board['owner']['id'] = board['id'] # hole: [todo:0] remove this

                fetch_imgs( board, slash_path[-1], board_slug, None, is_main_board
                    , arg_board_timestamp, arg_log_timestamp, url_path
                    , arg_force, arg_rescrape, arg_img_only, arg_v_only
                    , arg_dir, arg_thread_max
                    , IMGS_SESSION, IMG_SESSION, V_SESSION, PIN_SESSION, proxies
                    , cookies, arg_cut, arg_el, fs_f_max )
                if (not arg_exclude_section) and (board['section_count'] > 0):
                    sec_c = board['section_count']
                    print('[i] Trying to get ' + str(sec_c) + ' section{}'.format('s' if sec_c > 1 else ''))
                    # ags.es placeholder below always False bcoz above already check (not arg_exclude_section)
                    board, sections = get_board_info(board_path, False, None, None, proxies, cookies)
                    for sec in sections:
                        sec_path = board_path + '/' + sec['slug']
                        board = get_board_info(sec_path, False, sec['slug'], board_path, proxies, cookies)
                        sec_uname, sec_bname = board_path.split('/')
                        fetch_imgs( board, sec_uname, sec_bname, sec['slug'], False
                            , arg_board_timestamp, arg_log_timestamp, url_path
                            , arg_force, arg_rescrape, arg_img_only, arg_v_only
                            , arg_dir, arg_thread_max
                            , IMGS_SESSION, IMG_SESSION, V_SESSION, PIN_SESSION, proxies
                            , cookies, arg_cut, arg_el, fs_f_max )

        except KeyError:
            return quit(traceback.format_exc())

    end_time = int(time.time())
    try:
        print('[i] Time Spent: ' + str(timedelta(seconds= end_time - start_time)))
    except OverflowError:
        # after 999999999 days OR ~2,739,726 years, test case: str(timedelta(seconds= 86400000000000))
        print('Can you revive me please? Thanks.')

def run_direct_main():

    arg_parser = argparse.ArgumentParser(description='Download ALL board/section from ' + pinterest_logo +  'interest by username, username/boardname, username/boardname/section or link. Support image and video.\n\
        Filename compose of PinId_Title_Description_Date.Ext. PinId always there while the rest is optional.\n\
        If filename too long will endswith ... and you can check details in log-pinterest-downloader.log file.')
    arg_parser.add_argument('path', nargs='?', help='Pinterest username, or username/boardname, or username/boardname/section, or relevant link( /pin/ may include created time ).')
    arg_parser.add_argument('-d', '--dir', dest='dir', type=str, default='images', help='Specify folder path/name to store. Default is "images".')
    arg_parser.add_argument('-j', '--job', dest='thread_max', type=int, default=0, help='Specify maximum threads when downloading images. Default is number of processors on the machine, multiplied by 5.')
    # Username or Boardname might longer than 255 bytes
    # Username max is 100(not allow 3 bytes unicode)
    # Section/Boardname(Title) max are 50(count as singe char(i.e. 3 bytes unicode same as 1 byte ASCII), not bytes)
    # Board not possible create 4 bytes UTF-8 (become empty // or trim, lolr)
    # Description is 500, source_url(link) is 2048 (but not able save even though no error)
    # Pin Title is max 100 , which emoji count as 2 bytes per glyph (Chinese char still count as 1 per glyph)
    # [UPDATE] now --cut is per glyph, not byte, which is most users expected
    #, whereas bytes should detect by program (255/242/143) or raise by simply use -c <short value> to solve
    arg_parser.add_argument('-c', '--cut', type=int, default=-1, help='Specify maximum length of "_TITLE_DESCRIPTION_DATE"(exclude ...) in filename.')
    # Disable since better become default (so no more calc full path for 259(-el is exclude \\?\ = 255), instead only single path 259):
    #arg_parser.add_argument('-el', '--extended-length', dest='extended_len', type=int, default=-1, help='Specify Windows extended-length by prefix \\\\?\\ in output path. E.g. 339 work in my system.')
    arg_parser.add_argument('-bt', '--board-timestamp', dest='board_timestamp', action='store_true', help='Suffix board directory name with unique timestamp.')
    arg_parser.add_argument('-lt', '--log-timestamp', dest='log_timestamp', action='store_true', help='Suffix log-pinterest-downloader.log filename with unique timestamp. Default filename is log-pinterest-downloader.log.\n\
        Note: Pin id without Title/Description/Link/Metadata/Created_at will not write to log.')
    arg_parser.add_argument('-co', '--cookies', help='Set the cookies file to be used to login into Pinterest. Useful for personal secret boards.')
    arg_parser.add_argument('-f', '--force', action='store_true', help='Force re-download even if image already exist. Normally used with -rs')
    # Need reverse images order(previously is latest to oldest) to avoid abort this need re-download in-between missing images.
    arg_parser.add_argument('-rs', '--re-scrape', dest='rescrape', action='store_true', help='Default is only fetch new images since latest(highest) Pin ID local image to speed up update process.\n\
        This option disable that behavior and re-scrape all, use it when you feel missing images somewhere or incomplete download.\n\
        This issue is because Pinterest only lists reordered as you see in the webpage which possible newer images reorder below local highest Pin ID image and missed unless fetch all pages.')
    arg_parser.add_argument('-ua', '--update-all', dest='update_all', action='store_true', help='Update all folders in current directory recursively based on theirs urls-pinterest-downloader.urls.\n\
        New section will not download. New board may download if previously download by username.\n\
        Options other than -c, -j, -rs, -io/vo, -ps/p will ignore.\n\
        -c must same if provided previously or else filename not same will re-download. Not recommend to use -c at all.')
    arg_parser.add_argument('-es', '--exclude-section', dest='exclude_section', action='store_true', help='Exclude sections if download from username or board.')
    arg_parser.add_argument('-io', '--image-only', dest='img_only', action='store_true', help='Download image only. Assumed -rs')
    arg_parser.add_argument('-vo', '--video-only', dest='v_only', action='store_true', help='Download video only. Assumed -rs')
    arg_parser.add_argument('-ps', '--https-proxy', help='Set proxy for https.')
    arg_parser.add_argument('-p', '--http-proxy', help='Set proxy for http.')
    try:
        args, remaining  = arg_parser.parse_known_args()
    except SystemExit: # Normal if --help, catch here to avoid main() global ex catch it
        return
    if remaining:
        return quit( ['You type redundant options: ' + ' '.join(remaining)
            , 'Please check your command or --help to see options manual.' ])

    if not args.update_all and not args.path:
        args.path = input('Username/Boardname/Section or Link: ').strip()

    return run_library_main(args.path, args.dir, args.thread_max, args.cut
                            , args.board_timestamp, args.log_timestamp
                            , args.force, args.exclude_section, args.rescrape
                            , args.img_only, args.v_only, args.update_all
                            , args.https_proxy, args.http_proxy, args.cookies)

if __name__ == '__main__':
    try:
        run_direct_main()
    except requests.exceptions.ReadTimeout:
        cprint(''.join([ HIGHER_RED, '{}'.format('\n[' + x_tag + '] Suddenly not able to connect. Please check your network.\n') ]), attrs=BOLD_ONLY, end='' )
        quit('')
    except requests.exceptions.ConnectionError:
        cprint(''.join([ HIGHER_RED, '{}'.format('\n[' + x_tag + '] Not able to connect. Please check your network.\n') ]), attrs=BOLD_ONLY, end='' )
        quit('')
    except:
        quit(traceback.format_exc())