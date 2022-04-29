####################################################################################
# METADATA SPIDER 3.5     |                   CSEC 471 - METADATA PROJECT          #
# Written by (and authorized user) : Kenyon Litt                                   #
#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - #
# Script custom written for The Happy Co, using against this                       #
# domain only for parties with specified permission                                #
####################################################################################

# ----------------------------------REQUIRED LIBRARIES-------------------------- 
from curses import meta
import re
from numpy import imag
import pyfiglet
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
from bs4 import BeautifulSoup
import metadata_parser
import extraction
import time
import os
import base64
from PIL import Image
from PIL.ExifTags import TAGS
import sys
import pikepdf
from exiftool import ExifToolHelper
from colorama import Fore, Style
from datetime import datetime
# -------------------------------- GLOBAL PARAMETERS -----------------------------

def current_milli_time():
    # Helper function to get time, found on stackexchange
    return round(time.time() * 1000)


FILE_NAME_TIME = 'RUN_' + str(current_milli_time())

# PARAMETERS FOR PROGRAM. NO need for user input, though this could be asked via sys.argv in theory
# The website to visit
ROOT_URL = 'https://www.thehappyco.com/' 
# keywords to look for in url, main one is happyco and domain name variations. Also used in metadata analaysis 
KEYWORDS = ['thehappyco', 'THEHAPPYCO', 'TheHappyCo', 'TheHappyco', 'happyco','Elepreneurs', 'david', 'litt', 'davidlitt', 'tony', 'chaplin', 'tonychaplin', 'chris', 'sylvia', 'TX', 'texas'] 

# ------------------------------ MAIN PAGE OBJECT ----------------------------------------
class Page:
    # Page object which holds all info for page, and preforems operations on data found in them
    def __init__(self,url, keywords):
        # <CONSTRUCTOR> 
        self.url = url # url of web page
        self.html_code = '1' # http code from requests, set to 1 just in case
        self.sub_urls = [] # http/s links found on page
        self.soup = 'None' # soup obj   
        self.keywords = keywords # keywords to look for in metadata and links 
        self.html = '' # html representation of page (raw fourm)
        self.metadata = [] # metadata list of page, from extraction and metadata parrser
        self.base64_images = [] # base64 tuple of images
        self.imagelink_images =[] # url, type of images
        self.datapath = '' # datapath used for base directory (based on working directory)
        self.filenames = [] # url, type of images completed


    def parse_files_for_metadata(self):
        # This function is the main metadata parsing function for the files found on the page, which was passed from parse_metadata (which returns img links, base64 encoded or url form). 
        # This function mainly writes information to a file ending in .txt which holds all metadata from the page, and individual files present. 
        # The directory structure for this has a file for the entire script run, which holds folders for each URL (named as such without special chars). 
        # The url folder will hold all images on that url, and the metafile which this function writes to. 
        try:
            temp = self.datapath.split('\\')
            metadata_file = self.datapath + temp[len(temp)-2] + '.txt'
            prtstr= ' Writing metadatafile ' + metadata_file
            info_print('function_start', 'page-parse_file_metadata()', prtstr)
            meta_file = open(metadata_file, 'w', encoding='utf-8')
            meta_file.write('########################################### MAIN FILE INFO ####################################################\n')
            info = '[' + self.url + '] - METAFILE:' + metadata_file + '\n'
            info += 'base64_decoded_images=' + str(len(self.base64_images)) + '\n'
            info += 'downloaded_images=' + str(len(self.imagelink_images)) + '\n'
            meta_file.write(info)
            meta_file.write('______________________________________________________________________________________________\n')
            meta_file.write('[METADATA FROM URL]\n')
            try:
                if 'pdf' not in self.url:
                    for each_line in self.metadata:
                        for each_tuple in each_line:
                            line = str(each_tuple) + '\n'
                            meta_file.write(line)
            except:
                pass
            meta_file.write('############################################ SUB IMAGE META INFO ###################################################\n')
            info_print('function_info', 'page-parse_file_metadata()', 'RUNNING EXIFTOOL.exe')
            for filetype, filename in self.filenames:
                try:
                    # try exiftool.exe
                    with ExifToolHelper() as et:
                        for d in et.get_metadata(filename):
                            for k, v in d.items():
                                line = f'\t[{k}]    ---   [{v}]'
                                if keywords_present(self.keywords, line):
                                    line += '\t\t\t --> HIGH VALUE FOUND <--'
                                line += "\n"
                                meta_file.write(line)
                except:
                    continue
                # try other libraries for metadata
                if filetype == 'jpg' or filetype == 'png' or filetype == 'gif':
                    meta_file.write('---------------[IMG]--------------------\n')
                    fn = ">-- FILENAME: " + filename + '\n'
                    ft = '> -- FILETYPE: ' + filetype + '\n'
                    meta_file.write(fn)
                    meta_file.write(ft)
                    # USE PIL for images
                    image = Image.open(filename)
                    exifdata = image.getexif()
                    for tagid in exifdata:
                        tagname = TAGS.get(tagid, tagid)
                        value = exifdata.get(tagid)
                        line = str(tagname) + '  :  ' + str(value) + '\n'
                        meta_file.write(line)
                elif filetype == 'pdf':
                    #https://www.thepythoncode.com/article/extract-pdf-metadata-in-python
                    meta_file.write('---------------[PDF]--------------------\n')
                    fn = ">-- FILENAME: " + filename + '\n'
                    ft = '> -- FILETYPE: ' + filetype + '\n'
                    meta_file.write(fn)
                    meta_file.write(ft)
                    pdf = pikepdf.Pdf.open(filename)
                    docinfo = pdf.docinfo
                    for key, value in docinfo.items():
                        line = str(key) + "  :  " + str(value) + '\n'
                        meta_file.write(line)
                #https://sylikc.github.io/pyexiftool/examples.html
              
            info_print('function_stop_done', 'page-parse_file_metadata()', 'done')
        except Exception as e:
            prtstr= 'ERROR!' + str(e)
            info_print('function_stop_error', 'page-parse_file_metadata()', 'done')
            pass
        

    def download_data(self):
        # This function preforms the downloading and decoding of images present on the webpage, after image links are found from parse_metadata(). 
        info_print('function_start', 'page-download_data()', ' Starting')
        dirname = self.url.replace('/', '')
        dirname = dirname.replace('.','')
        dirname = dirname.replace(':', '')
        dirname = dirname.replace('?','')
        dirname = dirname.replace('=','')
        path = str(os.getcwd()) + '\data\\' + FILE_NAME_TIME + '\\' +  dirname + "\\"
        prtstr = ' Dwonloading to path ' + path 
        info_print('function_info', 'page-download_data()', prtstr)
        if not os.path.exists(path):
            os.makedirs(path)
        self.datapath = path
        # send message head to see filetype
        for each_imagelink in self.imagelink_images:
            filename = each_imagelink[1].replace(':','')
            filename = filename.replace('/', '')
            filename = filename.replace('//', '')
            filename = filename.replace(';','')
            filename = filename.replace('.','')
            resp = requests.head(each_imagelink[1])
            contentType = resp.headers['content-type']
            filetype = ''
            if 'jpeg' in contentType:
                filetype = 'jpg'
            elif 'png' in contentType:
                filetype = 'png'
            elif 'gif' in contentType:
                filetype = 'gif'
            elif 'pdf' in contentType:
                filetype = 'pdf'
            elif 'html' in contentType:
                filetype = 'html'
            elif 'svg' in contentType:
                filetype = 'svg'
            else:
                print('ERR UNKNOWN FILETYPE')
                print(contentType)
                raise Exception
            filename += '.' + filetype
            filename = path + filename
            #print(filename)
            #print(each_imagelink)p
            prtstr = ' downloading image file - ' + filename
            info_print('function_info', 'page-download_data()', prtstr)
            try:
                imgdata = requests.get(each_imagelink[1]).content
                with open(filename, 'wb') as f:
                    f.write(imgdata)
                self.filenames.append((filetype, filename))
            except Exception as e:
                prtstr = ' error downloading file - ' + filename + ' - ' + str(e)
                info_print('function_stop_error', 'page-download_data()', prtstr)
                continue
            
            time.sleep(1) # as we are doing a request here, want timeout so no DOS
        # BASE 64 images
        for each_item in self.base64_images:
            if each_item:
                if 'data' in each_item[0]:
                    filetype =''
                    if each_item[1][0] == '/':
                        filetype='jpg'
                    elif each_item[1][0] == 'i':
                        filetype='png'
                    elif each_item[1][0] == 'R':
                        filetype='gif'
                    elif each_item[1][0] == 'U':
                        filetype ='webp'
                    else:
                        if 'svg' in each_item[0]:
                            filetype = 'svg'
                        else:
                            filetype='UNKNOWN'
                    filename = each_item[0].replace(':','')
                    filename = filename.replace('/', '')
                    filename = filename.replace(';','')
                    filename += each_item[1][4:25].replace('/', '')
                    timestr = str(current_milli_time())
                    filename += str(timestr) + '.' + filetype
                    filename = path+filename
                    prtstr = ' downloading (b64 decode) file - ' + filename 
                    info_print('function_info', 'page-download_data()', prtstr)
                    time.sleep(.1)
                    with open(filename, 'wb') as f:
                        f.write(base64.b64decode(each_item[1]))
                    self.filenames.append((filetype, filename))
        info_print('function_stop_done', 'page-download_data()', ' Download Completed')


    def find_links(self,soup):
            # This function mainly uses the beautiful soup library, which can find individual html elements on a page, to extract all URLs from the page. 
            all_links = []
            final_links = []
            for link in soup.find_all('a'):
                raw_link = link.get('href')
                if raw_link != None:
                    #print(raw_link)
                    if 'url=' in raw_link:
                        #print("splitting")
                        link = raw_link.split('url=')
                        raw_link = link[1]
                    if 'http' in raw_link:
                        all_links.append(raw_link)
                    if raw_link[0] == "/":
                        if keywords_present(self.keywords, self.url):
                            new_link = ROOT_URL + raw_link[1:]
                            all_links.append(new_link)
            for each_link in all_links:
                if keywords_present(self.keywords, each_link):
                    final_links.append(each_link)
            return list(set(final_links))


    def connect(self):
        # This is the main http connection method for Page, which mainly uses the requests module to get raw http data which can then be parsed to the respective libraries. 
        # This function uses a retry_strategy that is designed to be passive and low demand on the host.
        soup = False
        try:
            headers = {}
            headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'
            retry_strategy = Retry(
                total=2,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http = requests.Session()
            http.mount("https://", adapter)
            http.mount("http://", adapter)

            reqs = http.get(self.url, headers=headers, timeout=5)
            self.html_code = reqs.status_code
            #print(reqs.headers)
            #print(reqs.reason)
            prtstr = 'url=' + self.url + " - HTMLCODE=" + str(self.html_code)
            info_print('function_start', 'page-connect()', prtstr)
            if self.html_code == 200 or self.html_code == 202:
                self.html = reqs.text
                soup = BeautifulSoup(reqs.text, 'html.parser')
                prtstr = 'url=' + self.url + " HTML CODE OK, Parsing SUBURLS..."
                info_print('function_info', 'page-connect()', prtstr)
                self.sub_urls = self.find_links(soup)
                #print(self.sub_urls)
                self.soup = soup
        except Exception as e:
            prtstr = 'url=' + self.url + " UNABLE TO CONNECT -" + str(e)
            info_print('function_stop_error', 'page-connect()', prtstr)
    

    def parse_metadata(self):
        # This function is the main operation for grabbing image links and metadata from the page. 
        # It will not look in files or downlad them, just meta tags and such
        info_print('function_start', 'page-parse_md()', 'starting...')
        metadata_final = []
        all_images = []
        try:
            for each in self.soup.findAll('img'):
                image_link = False
                #print(each)
                try:
                    image_link = each["data-srcset"]

                except:
                    try:
                        image_link = each["data-src"]
                    except:
                        try:
                            image_link = each["data-fallback-src"]
                        except:
                            try:
                                image_link = each["src"]
                            except:
                                pass
                if image_link != False:
                    all_images.append(image_link)
            #print(len(all_images))
            meta_parser1 = metadata_parser.MetadataParser(html=self.html)
            metadata = meta_parser1.metadata
            extracted = extraction.Extractor().extract(self.html, source_url=self.url)
    
            for each in extracted.images:
                if each not in all_images:
                    all_images.append(each)
            all_images = list(set(all_images))
            #print(len(all_images))

            for each_image in all_images:
                if each_image:
                    if 'data:' in each_image:
                        temp = each_image.split(',', 1)
                        obj = (temp[0], temp[1])
                        if obj not in self.base64_images:
                            self.base64_images.append(obj)
                    elif 'http' in each_image:
                        obj = ('imagelink', each_image)
                        if obj not in self.imagelink_images:
                            self.imagelink_images.append(obj)
                    elif each_image[0] == '/':
                        url = ROOT_URL + each_image[1:]
                        obj = ('imagelink', url)
                        if obj not in metadata_final:
                            metadata_final.append(obj)
            for each_title in extracted.titles:
                metadata_final.append(('title', each_title))
            for each_desc in extracted.descriptions:
                metadata_final.append(('desc', each_desc))
            for item in metadata.items():
                metadata_final.append(item)
            self.metadata = metadata_final
            self.base64_images = list(set(self.base64_images))
            info_print('function_stop_done', 'page-parse_md()', 'done!')
        except Exception as e:
            prtstr = 'error! ' + str(e)
            info_print('function_stop_error', 'page-parse_md()', prtstr)



# ----------------------------- HELPER FUNCTIONS -------------------------------------
def info_print(print_type, location, information):
    # PRINT FUNCTION : A universal inteprretation of a function I made in a preveous project. 
    #                  -> will print based on colors and info inputed, makes less repeditive print statements and inconsisent formatting
    printtype_color = None
    print_str = ''
    padded_space = 28 - len(location)
    if padded_space > 0:
        now = str(datetime.now().time())
        if print_type == 'function_info':
            printtype_color = Fore.BLUE

            print_str = f'[{now}]-{printtype_color}[{location}]{Style.RESET_ALL}:'
            for counter in range (0, padded_space):
                print_str += ' '
            print_str += f'{information}'
        elif print_type == 'function_start' or print_type == 'function_stop_done':

            printtype_color = Fore.GREEN
            print_str = f'[{now}]-{printtype_color}[{location}]{Style.RESET_ALL}:'
            for counter in range (0, padded_space):
                print_str += ' '
            print_str += f'{information}'
        elif print_type == 'function_stop_error':
            printtype_color = Fore.RED
            #print_str = f'[{now}]-{printtype_color}[{location}]:\t{information}{Style.RESET_ALL}'
            print_str = f'[{now}]-{printtype_color}[{location}]:'
            for counter in range (0, padded_space):
                print_str += ' '
            print_str += f'{information}{Style.RESET_ALL}'
        else:
            printtype_color = Fore.BLACK
        print(print_str)


def keywords_present(keywords, string):
    # Helper fucntion to just loop all keywords, recuces script size
    flag = False
    for each_kw in keywords:
        if each_kw in string:
            flag = True
    return flag


def init():
    # Init function
    # -Prints banner
    # -User permission auth
    print('[start] ...')
    print("#########################################################################################################################################")
    title = pyfiglet.figlet_format("    -- METADATA SCRAPER -- ", font="slant", width = 500)
    version = pyfiglet.figlet_format("    V.3 ", font="slant", width = 300)
    print(title)
    print(version)
    print("Created by Kenyon Litt")
    print("[WARNING] Use of this strictly to be for educational purposes only and with permission from website owner!")
    print("#########################################################################################################################################")
    print('--------------------------- [ AUTHORIZATION ] -----------------------------')
    input('By pressing any key, you agree to the terms of use [PRESS ANY KEY TO AGREE]')
    print('[init] \t\t Authorization completed.')

    
def main():
    # Main RUNNER FUNCTION
    # This is the main runner function for the script, which preforms the queued web spider action. T
    # he main function will print out the parameters (which are hardcoded into the script, this is because it is only being used and written for data collection on ‘thehappyco.com’) and add the root url to one of three queues. 
    # - The first queue is the to_parse queue which are the urls not visited yet, but will be (links found on an original webpage). 
    # - The next queue are the parsed pages, which is where the url once parsed will go to keep track of what has already been visited. 
    # - The error queue which is a list of urls which did not return a http 200/202 code, and therefore cannot gather any information from it. 
    init()
    root_url = ROOT_URL
    
    print('[stats]')
    print('\t\t\t Root url: ' + root_url)
    print('\t\t\t Keywords:')
    for each in KEYWORDS:
        print('\t\t\t\t' + each)

    to_parse_pages =[root_url]
    parsed_pages = []
    error_pages = []
    info_print('function_start', 'main', 'starting recursive spider process....')
    print("_______________________________________________________________")
    try:
        while to_parse_pages:
            todo = str(len(to_parse_pages))
            done = str(len(parsed_pages))
            err = str(len(error_pages))
            prtstr = '\t urls_parsed=' + done + ' urls_todo=' + todo + ' urls_error=' + err
            info_print('function_info', 'main', prtstr)
            time.sleep(2) # to make sure no timeouts
            url = to_parse_pages.pop()
            if url not in parsed_pages or url not in error_pages:
                p = Page(url, KEYWORDS)
                p.connect()
                if p.html_code == 200 or p.html_code == 202:
                    parsed_pages.append(url)
                    if '.pdf' in p.url:
                        p.imagelink_images.append(('imagelink', p.url))
                    try:
                        p.parse_metadata()
                        p.download_data()
                        p.parse_files_for_metadata()
                    except Exception as e:
                        prtstr = ' Error getting metadata for url ' + url + ' - ' + str(e)
                        info_print('function_stop_error', 'main', prtstr)
                    #print(p.filenames)
                    for each_link in p.sub_urls:
                        if each_link not in to_parse_pages and each_link not in parsed_pages and each_link not in error_pages:
                            to_parse_pages.append(each_link)
                else:
                    error_pages.append(url)
    except KeyboardInterrupt:
        print('[OPERATION STOPPED PREMATURELY!]')
        pass
    info_print('function_stop_done', 'main', 'Metaspider Completed!!! ...')
    print('\n\n\n[main]\tOperation completed.')
    print("--------------------------------------------------------------------")
    print('[stats]')
    print('\t\t\t Root url: ' + root_url)
    print('\t\t\t Keywords:')
    for each in KEYWORDS:
        print('\t\t\t\t' + each)
    print('\t\t\t Total Pages Processed without errors:' + str(len(parsed_pages)))
    print('\t\t\t Total Pages Processed with errors:' + str(len(error_pages)))
    #print('\t\t\t Output Directory Path:' + parsed_pages[0].datapath)
    

if __name__ == '__main__':
    # Call main
    main()