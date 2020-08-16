# pinterest-downloader
Download all images/videos from Pinterest user/board/section.

### Some features:

- [x] Accept input as /username/, /username/boardname/, /username/boardname/section, 
- [x] Accept input as link of /username/, /username/boardname/, /username/boardname/section, and /pin/
- [x] Able download sections of boards of username.
- [x] High resolution. 
- [x] Error tolerance. Try second resolution if first resolution error.
- [x] Able download both image and video.
- [x] Multi-threads when download images.
- [x] Media Filename naming in PinID_Title_Description_[Date].Ext meaningful form. With PinID, you can visit https://www.pinterest.com/pin/<PinID> in web browser and get more details in log (PinID without details will not log). 
- [x] Media Filename truncate to ... fit maximum filename length automatically. -c to cut if you prefer.
- [x] Log PinID, Title, Description, Link, Metadata, [Date] to log-pinterest-downloader.log file since media filename can't fit.
- [x] Unique board/log name with timestamp options.
- [x] Proxies options.

### Usage:

    $ python3 pinterest-downloader.py --help
    usage: pinterest-downloader.py [-h] [-d DIR] [-j THREAD_MAX] [-c CUT] [-bt]
                                [-lt] [-f] [-es]
                                [path]

    Download ALL board/section from 🅿️interest by username, username/boardname,
    username/boardname/section or link. Support image and video. Filename compose
    of PinId_Title_Description_Date.Ext. PinId always there while the rest is
    optional. If filename too long will endswith ... and you can check details in
    log-pinterest-downloader.log file.

    positional arguments:
      path                  Pinterest username, or username/boardname, or link(
                            /pin/ may include created time )
    
    optional arguments:
      -h, --help            show this help message and exit
      -d DIR, --dir DIR     Specify folder path/name to store. Default is "images"
      -j THREAD_MAX, --job THREAD_MAX
                            Specify maximum threads when downloading images.
                            Default is number of processors on the machine,
                            multiplied by 5
      -c CUT, --cut CUT     Specify maximum length of
                            "_TITLE_DESCRIPTION_DATE"(exclude ...) in filename.
      -bt, --board-timestamp
                            Suffix board directory name with unique timestamp
      -lt, --log-timestamp  Suffix log-pinterest-downloader.log filename with
                            unique timestamp. Default filename is log-pinterest-
                            downloader.log. Note: Pin id without
                            Title/Description/Link/Metadata/Created_at will not
                            write to log.
      -f, --force           Force re-download even if image already exist
      -es, --exclude-section
                            Exclude sections if download from username or board.
      -ps HTTPS_PROXY, --https-proxy HTTPS_PROXY
                            Set proxy for https
      -p HTTP_PROXY, --http-proxy HTTP_PROXY
                            Set proxy for http

### Example Usage:
    $ python3 pinterest-downloader.py # Prompt for insert path
    $ export PYTHONIOENCODING=utf8; python3 pinterest-downloader.py # If you get "'gbk' codec can't encode character" error
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ 
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -d comp
    $ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/ # or path in last
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -bt -lt -d comp -f
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -c 40 # Default already good enough
    $ python3 pinterest-downloader.py https://www.pinterest.com/antonellomiglio/computer/ -j 666 # Default already fast enough
    $ python3 pinterest-downloader.py https://www.pinterest.com/Foodrecipessmith/food-recipes/ -es # Exclude sections
    $ python3 pinterest-downloader.py https://www.pinterest.com/Foodrecipessmith/food-recipes/ -ps 'socks4://123.123.123.123:12345' -p 'socks4://123.123.123.123:12345' # set proxies
    $ pin https://www.pinterest.com/antonellomiglio/computer/  # make alias/function in ~/.bash_aliases(or any shell startup script) to easier type

### Example Output:
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/ 
    [i] Job is download single board by username/boardname: antonellomiglio/computer
    [...] Getting all images in this board: computer ... [ 173 / ? ] [➕] Found estimated 195 images
    [✔] Downloaded: |##################################################| 100.0% Complete   
    [i] Time Spent: 0:00:06
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$

