#########################################################
# METADATA SPIDER 1.0     | CSEC 471 - METADATA PROJECT #
# Kenyon Litt                                           #
#########################################################
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


def current_milli_time():
    return round(time.time() * 1000)


ROOT_URL = 'https://www.thehappyco.com/'



def keywords_present(keywords, string):
    flag = False
    for each_kw in keywords:
        if each_kw in string:
            flag = True
    return flag

class Page:
    def __init__(self,url, keywords):
        self.url = url
        self.html_code = '1'
        self.sub_urls = []
        self.soup = 'None'
        self.keywords = keywords
        self.html = ''
        self.metadata = []
        self.base64_images = []
        self.imagelink_images =[]

    def download_data(self):
        dirname = self.url.replace('/', '')
        dirname = dirname.replace('.','')
        dirname = dirname.replace(':', '')
        dirname = dirname.replace('?','')
        dirname = dirname.replace('=','')

        path = str(os.getcwd()) + '\data\\' +  dirname + "\\"
        if not os.path.exists(path):
            os.makedirs(path)

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
            else:
                print('ERR')
                print(contentType)
                raise Exception
            filename += '.' + filetype
            filename = path + filename
            print(filename)
            print(each_imagelink)
            print("[page:imgdownloader] \t downloading file " + filename)
            try:
                imgdata = requests.get(each_imagelink[1]).content
                with open(filename, 'wb') as f:
                    f.write(imgdata)
            except Exception as e:
                print('[page:imagdownloader] ERROR')
                print(e)
                continue
            time.sleep(1)
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
                    print('[page:base64downloader] decoding file ' + filename)
                    time.sleep(.1)
                    with open(filename, 'wb') as f:
                        f.write(base64.b64decode(each_item[1]))
        # Normal Image Links


    def find_links(self,soup):

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
            print('[page-connect]\t url=' + self.url + " - HTMLCODE=" + str(self.html_code))
            if self.html_code == 200 or self.html_code == 202:
                self.html = reqs.text
                soup = BeautifulSoup(reqs.text, 'html.parser')
                print('[page-connect]\t url=' + self.url + " HTML CODE OK, Parsing SUBURLS...")
                self.sub_urls = self.find_links(soup)
                #print(self.sub_urls)
                self.soup = soup
        except Exception as e:
            print('[page-connect]ERROR! \t url=' + self.url + " UNABLE TO CONNECT")
            print(e)
    
    def parse_metadata(self):
        print('[page-parse_metadata]\t starting...')
        metadata_final = []
        all_images = []
        try:
            for each in self.soup.findAll('img'):
                image_link = False
                #print(each)
                try:
                    # In image tag ,searching for "data-srcset"
                    image_link = each["data-srcset"]
                    
                # then we will search for "data-src" in img
                # tag and so on..
                except:
                    try:
                        # In image tag ,searching for "data-src"
                        image_link = each["data-src"]
                    except:
                        try:
                            # In image tag ,searching for "data-fallback-src"
                            image_link = each["data-fallback-src"]
                        except:
                            try:
                                # In image tag ,searching for "src"
                                image_link = each["src"]

                            # if no Source URL found
                            except:
                                pass
                if image_link != False:
                    all_images.append(image_link)
            print(len(all_images))
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
        except Exception as e:
            print(e)












def init():
    print('[start]...')
    print("#########################################################################################################################################")
    msg = pyfiglet.figlet_format("    -- METADATA SCRAPER -- ", font="slant", width = 500)
    print(msg)
    print("Created by Kenyon Litt")
    print("[WARNING] Use of this strictly to be for educational purposes only and with permission from website owner!")
    print("#########################################################################################################################################")

def main():
    init()
    root_url = 'https://www.thehappyco.com/'
    KEYWORDS = ['thehappyco', 'THEHAPPYCO', 'TheHappyCo', 'TheHappyco', 'happyco','Elepreneurs']
    
    to_parse_pages =[root_url]
    parsed_pages = []
    error_pages = []
    
    while to_parse_pages:
        todo = str(len(to_parse_pages))
        done = str(len(parsed_pages))
        print('[main]\t\t\t urls_parsed=' + done + ' urls_todo=' + todo)
        time.sleep(2) # to make sure no timeouts
        url = to_parse_pages.pop()
        if url not in parsed_pages or url not in error_pages:
            p = Page(url, KEYWORDS)
            p.connect()
            if p.html_code == 200 or p.html_code == 202:
                parsed_pages.append(url)
                if '.pdf' in p.url:
                    p.imagelink_images.append(('imagelink', p.url))
                p.parse_metadata()
                p.download_data()
                for each_link in p.sub_urls:
                    if each_link not in to_parse_pages and each_link not in parsed_pages and each_link not in error_pages:
                        to_parse_pages.append(each_link)
            else:
                error_pages.append(url)

    





if __name__ == '__main__':
    main()