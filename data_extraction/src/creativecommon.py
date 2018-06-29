import sys
import gzip
import json
import urllib.parse
import urllib.request
import chardet
from datetime import datetime
from io import BytesIO

class CreativeCommon:

    month_keys = [ '2018-05', '2018-04', '2018-03', '2018-02', '2018-01', '2017-12', '2017-11', '2017-10', '2017-09', '2017-08', '2017-07', '2017-06', '2017-05', '2017-04', '2017-03', '2017-02', '2017-01', '2016-12', '2016-10', '2016-09', '2016-08', '2016-07', '2016-06', '2016-05', '2016-04', '2016-02', '2015-11', '2015-09', '2015-08', '2015-07', '2015-06', '2015-05', '2015-04', '2015-03', '2015-02', '2015-01', '2014-12', '2014-11', '2014-10', '2014-09', '2014-08', '2014-07', '2014-04', '2014-03', '2014-02', '2013-10' ]
    month_ids = [ '2018-22', '2018-17', '2018-13', '2018-09', '2018-05', '2017-51', '2017-47', '2017-43', '2017-39', '2017-34', '2017-30', '2017-26', '2017-22', '2017-17', '2017-13', '2017-09', '2017-04', '2016-50', '2016-44', '2016-40', '2016-36', '2016-30', '2016-26', '2016-22', '2016-18', '2016-07', '2015-48', '2015-40', '2015-35', '2015-32', '2015-27', '2015-22', '2015-18', '2015-14', '2015-11', '2015-06', '2014-52', '2014-49', '2014-42', '2014-41', '2014-35', '2014-23', '2014-15', '2014-10', '2013-48', '2013-20' ]
    index_url_prefix = 'http://index.commoncrawl.org/CC-MAIN-'
    data_url = 'https://commoncrawl.s3.amazonaws.com/'
    index_url_suffix = '%2F&output=json'

    def __init__(self):
        self.month_keys_dic = dict([ (self.month_keys[i], i) for i in range(0, len(self.month_keys))])

    def download(self, url, month, backward=True):
        """
        Returns html from a url using Commow Crawl (CC).
            url = page to retrieve
            month = month of the page in format = YYYY-MM
            backward = whether to search backward in time if page isn't found (if false, search forward)
            Returns (response, date), where response is the html as a string, and the date the page
            was originally retrieved (datetime object).
        """
        idx = 0
        step = int(backward)*2-1
        if month in self.month_keys_dic.keys():
            idx = self.month_keys_dic[month]

        while 0 <= idx and idx < len(self.month_keys):
            month_id = self.month_ids[idx]
            iurl = self.index_url_prefix + month_id + '-index?url=' + urllib.parse.quote_plus(url) + self.index_url_suffix
            try:
                # Find page in index:
                u = urllib.request.urlopen(iurl)
                pages = [json.loads(x) for x in u.read().decode('utf-8').strip().split('\n')]
                page = pages[0] # To do: if get multiple pages, find closest match in time

                # Get data from warc file:
                offset, length = int(page['offset']), int(page['length'])
                #print("range: %d - %d" %(offset,length), file=sys.stderr)
                offset_end = offset + length - 1
                url = self.data_url + page['filename']
                request = urllib.request.Request(url)
                rangestr = 'bytes={}-{}'.format(offset, offset_end)
                request.add_header('Range', rangestr)
                u = urllib.request.urlopen(request)
                content = u.read()
                raw_data = BytesIO(content)
                f = gzip.GzipFile(fileobj=raw_data)

                data = f.read()
                enc = chardet.detect(data)
                warc, header, response = data.decode(enc['encoding']).strip().split('\r\n\r\n', 2)
                date = datetime.strptime(page['timestamp'],'%Y%m%d%H%M%S')
                return response, date
                #return response, warc, header
            except urllib.error.HTTPError:
                #traceback.print_exc(file=sys.stderr)
                idx = idx + step
        return None, None

if __name__== "__main__":
    cc = CreativeCommon()
    if len(sys.argv) != 3:
        print("Usage: python %s URL DATE\n\nThe DATE must have the following format: YYYY-MM" % sys.argv[0], file=sys.stderr)
    else:
        url = sys.argv[1]
        month = sys.argv[2]
        html, date = cc.download(url, month)
        if html != None:
            print(html)
            print("<!-- Retrieved on: " + str(date) + " -->")