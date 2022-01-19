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

### Requirements:

    $ python3 -m pip install -r requirements.txt 

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
      -rs, --re-scrape      Default is only fetch new images since latest Pin ID
                            image to speed up update process. This option disable
                            this behavior and re-scrape all, use it when you feel
                            missing images somewhere.
      -es, --exclude-section
                                Exclude sections if download from username or board.
      -ps HTTPS_PROXY, --https-proxy HTTPS_PROXY
                            Set proxy for https.
      -p HTTP_PROXY, --http-proxy HTTP_PROXY
                            Set proxy for http.

### Example Usage:
    $ python3 pinterest-downloader.py # Prompt for insert path. Note: Only support python 3, not python 2
    $ export PYTHONIOENCODING=utf8; python3 pinterest-downloader.py # If you get "'gbk' codec can't encode character" error
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

### Example Output:
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$ python3 pinterest-downloader.py -d comp https://www.pinterest.com/antonellomiglio/computer/ 
    [...] Getting all images in this board: computer ... [ 74 / ? ]
    [W] This images list is not sorted correctly, fallback to -rs for this list.

    [...] Getting all images in this board: computer ... [ 173 / ? ] [➕] Found 195 image/videos
    Download into directory:  comp/antonellomiglio/Computer
    [✔] Downloaded: |##################################################| 100.0% Complete   
    [i] Time Spent: 0:00:06
    xb@dnxb:~/Downloads/pinterest/pinterest-downloader$

