# metaspider
## for CSEC 471: METADATA PROJECT

5.3.1	Page Object
Parameter	Description
URL	url of page
Html_code	Response code from HTTP Request
Sub_urls	Urls found on url website
Soup	BS4 Soup Object
Keywords	Words to look for in sub urls
Html	Raw html of page
Metadata	Page metadata (not file metadata)
Base64_images	Images that are pre-cached on webserver in the url and in base64 form
Imagelink_images	Images which are on webserver as url links
Datapath	Windows Directory to save Information to
Filenames	All downloaded files from website

parse_files_for_metadata()
This function is the main metadata parsing function for the files found on the page, which was passed from parse_metadata (which returns img links, base64 encoded or url form). This function mainly writes information to a file ending in .txt which holds all metadata from the page, and individual files present. The directory structure for this has a file for the entire script run, which holds folders for each URL (named as such without special chars). The url folder will hold all images on that url, and the metafile which this function writes to. 
Once the metafile is opened to write to, the function writes the page metadata information into the file. It then loops through all of the file names in filenames and tries: exiftool regardless of file type, pikepdf if pdf found, and pil.exif() if image is found. If any of these libraries find anything, it is written to a section for each filename in the metadata.txt file. 
download_data()
This function preforms the downloading and decoding of images present on the webpage, after image links are found from parse_metadata(). The function will check if a folder exists for the url and if not create one. It then loops through all image links and preforms a http head request via the requests module to just get the content type of the image (img format ie jpg, png, gif, etc). Once it has this information, it tries to get the image from the image URL with a full http get request via requests and will write the file to the URL directory. The function will then loop through all base64_images which are images preloaded onto the webserver and already encoded as their URL in base-64. To download these images, we don’t need to make any request because the data is already encoded in the URL, so we just pull out the encoded section and convert that to a normal file based on file type and download it. In order to maintain low band width and demand, a wait time of 1 second is used between downloading files (less time is needed between decoding b64 representations though it is still used to ensure enough time between requests to not but demand on company infrastructure). 
find_links()
This function mainly uses the beautiful soup library, which can find individual html elements on a page, to extract all URLs from the page. It first will find all ‘a’ html element with he ‘href’ tag, then it will check its form to see if its an internal or external URL (includes root URL or is path). After it finds out location, it can then format these strings and add them to a final_links list. This list is then returned 
connect()
This is the main http connection method for Page, which mainly uses the requests module to get raw http data which can then be parsed to the respective libraries. This function uses a retry_strategy that is designed to be passive and low demand on the host. The function will call the socket function and connect to the URL, and then set and check the html_code. If the code returns 200/202, the function can grab information from the page and calls the Beautiful Soup parser to parse the html on the page and set the soup value. The function will then also call the find_links function to populate the sub_urls parameter. 
parse_metadata()
This function is the main operation for grabbing image links and metadata from the page. First it grabs the soup object gathered from connect() and finds all image links in the page. The function will then call the extraction library and create an Extractor() to find any metadata information on the page its self. It will also go through all images found within the extraction function, and remove duplicates also found by soup. It will then check its forum (url form, or base64 encoded into url) and add it to the appropriate list and set the parameter to the list found. The function will also call the metadata_parser and find any page metadata that way and add that the the metadata parameter, along with the extraction library. 

5.3.2	MISC / Helper Functions
init()
This is the initialization function for the script, which prints the banner message and also confirms user verification to the use terms (due to using website scraping)
main()
This is the main runner function for the script, which preforms the queued web spider action. The main function will print out the parameters (which are hardcoded into the script, this is because it is only being used and written for data collection on ‘thehappyco.com’) and add the root url to one of three queues. The first queue is the to_parse queue which are the urls not visited yet, but will be (links found on an original webpage). The next queue are the parsed pages, which is where the url once parsed will go to keep track of what has already been visited. We finally have the error queue which is a list of urls which did not return a http 200/202 code, and therefore cannot gather any information from it. 
The main loop for this function runs until the to_parse queue is empty. The loop will first pop a url from the to_parse queue, and create a Page object. It will call the connect() function and test the error code to make sure it is visitable. Once that happens, the url is added to the to_parse page queue so it is not analyzed again, and we start the metadata analysis. If the http code is something other than 200/202, it will add the pages to the error_queue mostly for statistical reasons. The Page object will then have three functions called, first to gather the page metadata which will include sublinks for images, then it downloads the images found, and parses the files for metadata once downloaded and writes the file. 
current_mil_time()
This is a helper function (found here: https://stackoverflow.com/questions/5998245/get-current-time-in-milliseconds-in-python) to print and find the time of the system in milliseconds, used for file names and information printing
info_print()
This is the main function to print information while running to the user and was created for easier reading and formatting in the script. This function was created to be universal and is modification from a previous personal design of a similar function.
keywords_present()
This is helper function to take a list of words and a string, and check to see if any are present in the string. This function was mainly created just for efficiency instead of needing to perform this multiple times in the script individually. 

