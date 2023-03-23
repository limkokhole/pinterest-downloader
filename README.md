# pinterest-downloader
Download all images/videos from Pinterest user/board/section.

### Some features:

- [x] Accept input of /username/, /username/boardname/, /username/boardname/section, pin/PinID 
- [x] Accept input of URL link. 
- [x] Able download sections of boards of username. 
- [x] High resolution. 
- [x] Error tolerance. Try second resolution if first resolution error. 
- [x] Able download both image and video. 
- [x] Multi-threads when download images. 
- [x] Media Filename naming in PinID_Title_Description_[Date].Ext meaningful form. With PinID, you can visit https://www.pinterest.com/pin/[PinID] in web browser and get more details in log file (PinID without details will not log). 
- [x] Media Filename truncate to ... fit maximum filename length automatically. -c to cut if you prefer. 
- [x] Log PinID, Title, Description, Link, Metadata, [Date] to log-pinterest-downloader.log file since media filename can't fit. 
- [x] Unique board/log name with timestamp options. 
- [x] Proxies options. 
- [x] Speed up existing folder update without re-fetch all pages. 
- [x] Update all folders option.
- [x] Can accept cookie (token) file in order to download with your account (useful for secret boards). Secret boards can be downloaded only when downloading by user. Example usage: copy your token after login into Pinterest and with its tab selected by using this extension [Get Token Cookie](https://chrome.google.com/webstore/detail/get-token-cookie/naciaagbkifhpnoodlkhbejjldaiffcm) or a similar one of your choice. Paste your token into a file called cookies.txt in the same directory where the pinterest-downloader is. Call the script and add the -co cookies.txt arguments to download your secret galleries

### Requirements:

    $ python3 -m pip install --upgrade -r requirements.txt 

### Usage:

    $ python3 pinterest-downloader.py --help
    usage: pinterest-downloader.py [-h] [-d DIR] [-j THREAD_MAX] [-c CUT] [-bt]
                                [-lt] [-f] [-rs] [-ua] [-es] [-io] [-vo]
                                [-ps HTTPS_PROXY] [-p HTTP_PROXY]
                                [path]

    Download ALL board/section from 🅿️interest by username, username/boardname,
    username/boardname/section or link. Support image and video. Filename compose
    of PinId_Title_Description_Date.Ext. PinId always there while the rest is
    optional. If filename too long will endswith ... and you can check details in
    log-pinterest-downloader.log file.

    positional arguments:
      path                  Pinterest username, or username/boardname, or
                            username/boardname/section, or relevant link( /pin/
                            may include created time ).
    
    optional arguments:
      -h, --help            show this help message and exit
      -d DIR, --dir DIR     Specify folder path/name to store. Default is
                            "images".
      -j THREAD_MAX, --job THREAD_MAX
                            Specify maximum threads when downloading images.
                            Default is number of processors on the machine,
                            multiplied by 5.
      -c CUT, --cut CUT     Specify maximum length of
                            "_TITLE_DESCRIPTION_DATE"(exclude ...) in filename.
      -bt, --board-timestamp
                            Suffix board directory name with unique timestamp.
      -lt, --log-timestamp  Suffix log-pinterest-downloader.log filename with
                            unique timestamp. Default filename is log-pinterest-
                            downloader.log. Note: Pin id without
                            Title/Description/Link/Metadata/Created_at will not
                            write to log.
      -f, --force           Force re-download even if image already exist.
                            Normally used with -rs
      -rs, --re-scrape      Default is only fetch new images since latest(highest)
                           Pin ID local image to speed up update process. This
                           option disable that behavior and re-scrape all, use it
                           when you feel missing images somewhere or incomplete
                           download. This issue is because Pinterest only lists
                           reordered as you see in the webpage which possible
                           newer images reorder below local highest Pin ID image
                           and missed unless fetch all pages.
      -ua, --update-all     Update all folders in current directory recursively
                           based on theirs urls-pinterest-downloader.urls. New
                           section will not download. New board may download if
                           previously download by username. Options other than
                           -c, -j, -rs, -io/vo, -ps/p will ignore. -c must same
                           if provided previously or else filename not same will
                           re-download. Not recommend to use -c at all.
      -es, --exclude-section
                           Exclude sections if download from username or board.
      -io, --image-only     Download image only. Assumed -rs
      -vo, --video-only     Download video only. Assumed -rs
      -ps HTTPS_PROXY, --https-proxy HTTPS_PROXY
                            Set proxy for https.
      -p HTTP_PROXY, --http-proxy HTTP_PROXY
                            Set proxy for http.
      -co COOKIES, --cookies COOKIES
                            Set the cookies file to be used to login into Pinterest. Useful for personal secret boards.

### Example Usage:
    $ python3 pinterest-downloader.py # Prompt for insert path. Note: Only support python 3, not python 2
    $ export PYTHONIOENCODING=utf8; python3 pinterest-downloader.py # If you get "'gbk' codec can't encode character" error
    $ python3 pinterest-downloader.py antonellomiglio -co cookies.txt # need to create the file first
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ 
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -d comp
    $ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/ # or path in last
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -bt -lt -d comp -f -rs # various options
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -c 40 # Default already good enough
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -j 666 # Default already fast enough
    $ python3 pinterest-downloader.py https://www.pinterest.com/Foodrecipessmith/food-recipes/ -ps "socks4://123.123.123.123:12345" -p "socks4://123.123.123.123:12345" # set proxies
    $ pin https://www.pinterest.com/antonellomiglio/computer/  # make alias/function in ~/.bash_aliases(or any shell startup script) to easier type
    $ pin https://www.pinterest.com/Foodrecipessmith/ # Download all boards by username.
    $ pin https://www.pinterest.com/Foodrecipessmith/food-recipes/ # Download all sections and images of boards. But _saved/_created/pins treat as username only.
    $ pin https://www.pinterest.com/Foodrecipessmith/food-recipes/ -es # Exclude sections
    $ pin https://www.pinterest.com/Foodrecipessmith/food-recipes/condiments/ # Download all images of section
    $ pin https://www.pinterest.com/pin/819444094683773705/ # Download specific pin
    $ pin Foodrecipessmith # Download by username with shortform instead of link
    $ pin Foodrecipessmith/food-recipes # Download boards with shortform instead of link
    $ pin Foodrecipessmith/food-recipes/condiments # Download section with shortform instead of link
    $ pin pin/819444094683773705 # Download pin with shortform instead of link
    $ pin https://pin.it/3xa5RlZ # Download pin with shorten/share link

### Example Output:
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/ 
    [i] User Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11
    [...] Getting all images in this board: computer ... [ 173 / ? ] [➕] Found 195 image/videos
    Download into directory:  comp/antonellomiglio/Computer/
    [✔] Downloaded: |##################################################| 100.0% Complete   
    [i] Time Spent: 0:00:06

##### Rerun(ensure same directory) will no new item found since latest pin Id file:
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/
    [i] User Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11
    [i] Job is download single board by username/boardname: antonellomiglio/computer
    [...] Getting all images in this board: computer ... [ 0 / ? ]
    [i] No new item found.
    [i] Time Spent: 0:00:04

##### Rerun in future(upload or delete highest pin id files to test) to fetch new items only which Pin IDs higher than existing Pin ID, speed up without fetch all pages for large board(use -rs if user reordered concerns):
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/
    [i] User Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11
    [i] Job is download single board by username/boardname: antonellomiglio/computer
    [...] Getting all images in this board: computer ... [ 0 / ? ] [➕] Found 5 new image/videos
    Download into directory:  comp/antonellomiglio/Computer/
    [✔] Downloaded: |##################################################| 100.0% Complete   
    [i] Time Spent: 0:00:04

##### URL used by rerun can refer urls-pinterest-downloader.urls file in relevant folder(except downlaod single Pin):
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader/comp/antonellomiglio/Computer$ cat urls-pinterest-downloader.urls 
    Pinterest Downloader: Version 1.9

    Input URL: https://www.pinterest.com/antonellomiglio/computer/
    Folder URL: https://www.pinterest.com/antonellomiglio/computer/

##### Or log-pinterest-downloader.log (only exist if any folder item contains title/description/link/metadata/date).
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$ head -28 comp/antonellomiglio/Computer/log-pinterest-downloader.log 
    Pinterest Downloader: Version 1.9

    Input URL: https://www.pinterest.com/antonellomiglio/computer/
    Folder URL: https://www.pinterest.com/antonellomiglio/computer/

    [ 1 ] Pin Id: 566538828106779478

    Description: I have owned the classic, performa 636cd, performa 6300av.  I still own the cube, Mac Pro G3, G4, G5, first FireWire iPod, iPod video, Apple TV, MacBook Pro 13, ipad 64 gb lte version. 2x iPhone 4S.
    Link: http://cdn.b.design.org/imagecache/blog-full-scale/blog/2011/10/07/maclegacy.jpg

    [ 2 ] Pin Id: 566538828111292022

    Description: Vintage Apple Macintosh SE/30 Computer

    [ 3 ] Pin Id: 566538828111292026

    Description: best part...ALL #iPhone #smartphones can fit in #PortaPocket... no problem. WEAR your cell, loves. xoxo

    [ 4 ] Pin Id: 566538828111292037

    Title: apple-history.com
    Description: Macintosh Color Classic (uno dei miei preferiti!)
    Link: http://apple-history.com/colorclassic

    [ 5 ] Pin Id: 566538828111292039

    Description: "Apple Mac"


### You can also use another python script to run, e.g.:
    import importlib
    pin_dl = importlib.import_module('pinterest-downloader')
    pin_dl.run_library_main('antonellomiglio/computer', '.', 0, -1, False, False, False, False, False, False, False, False, None, None, None)

