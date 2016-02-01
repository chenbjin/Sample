# -*- encoding: utf-8 -*-
'''
Created on 2016/1/30
@author:chenbjin
'''

import re
import os
import time
import cookielib
import urllib2
import requests
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class Spider(object):
	"""
		Spider for papers on Web of Science. 
	"""
	def __init__(self,url):
		super(Spider, self).__init__()
		self.SID = None
		self.cookie = None
		self.headers = None
		self.opener = None
		self.urls = []
		self._init_header()
		self._init_cookie(url)
		self._get_cookie()

	def _init_header(self):
		user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/47.0.2526.73 Chrome/47.0.2526.73 Safari/537.36'
		self.headers = { 'User-Agent': user_agent }
	
	def _init_cookie(self, url):
		logging.info("Init cookie with:"+url)
		filename = 'cookie.txt'
		cookie = cookielib.MozillaCookieJar(filename)
		handler = urllib2.HTTPCookieProcessor(cookie)
		self.opener = urllib2.build_opener(handler)
		response = self.opener.open(url)
		cookie.save(ignore_discard=True, ignore_expires=True)
	
	def _get_cookie(self):
		#cookie handler
		self.cookie = cookielib.MozillaCookieJar()
		self.cookie.load('cookie.txt',ignore_discard=True, ignore_expires=True)
		for x in self.cookie:
			if x.name == 'SID':
				self.SID = x.value
				break
		handler = urllib2.HTTPCookieProcessor(self.cookie)
		self.opener = urllib2.build_opener(handler)

	def get_sid(self):
		return self.SID.strip('"')

	def get_url_with_cookie(self, url):
		logging.info("getting url:"+url)
		request = urllib2.Request(url, headers=self.headers)
		html = None
		try:
			html = self.opener.open(request).read()
		except Exception, e:
			print e
			ep = open('exception14.txt', 'a')
			ep.write(url+'\n')
			ep.close() 
		return html

	#get url without cookie
	def get_url(self, url):
		logging.info("getting url:"+url)
		request = urllib2.Request(url, headers=self.headers)
		html = None
		try:
			html = urllib2.urlopen(request, timeout=20).read()
		except Exception, e:
			print e
			html = urllib2.urlopen(request).read()
		return html

	# find all papers link in a page
	def get_all_pages(self, html):
		self.urls = re.findall(r'<a class="smallV110" href="(.*?)"',html)

def query_search(SpiderHandle, SID, query_input, editions, startYear, endYear):
	'''
	    SpiderHandle: Spider instance
		SID: the session ID
		query_input: query set
		editions: indexs. eg. SCI/SSCI/AHCI
		startYear: start year
		endYear: end year
		(records_num): return the num of records for query.
	'''
	base_url = 'http://apps.webofknowledge.com/'
	query_url = 'summary.do?product=WOS&parentProduct=WOS&search_mode=AdvancedSearch&qid=1&SID='
	query_acts = '&page=1&action=changePageSize&pageSize=50'
	datas = {
		'product': 'WOS', 
		'search_mode': 'AdvancedSearch',
		'SID': SID,
		'action': 'search',
		'goToPageLoc': 'SearchHistoryTableBanner',
		'value(input1)': query_input,
		'value(searchOp)': 'search', 
		'x': '85', 
		'y': '442',
		'value(select2)': 'LA', 
		'value(select3)': 'DT', 
		'value(limitCount)':14,
		'limitStatus': 'expanded',
		'ss_lemmatization': 'On',
		'ss_spellchecking': 'Suggest',
		'period':'Year Range',
		'startYear': startYear,
		'endYear': endYear,
		'range': 'ALL',  
		'editions': editions,
		'update_back2search_link_param':'yes',
		'rs_sort_by': 'PY.A;LD.A;SO.A;VL.A;PG.A;AU.A'  #oldest-newest
		#'rs_sort_by': 'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A' #newest-oldest
	}
	res = requests.post("http://apps.webofknowledge.com/WOS_AdvancedSearch.do", data=datas)
	html = res.text.encode('utf-8')
	records_num = re.findall('<a href="/summary.do?(.*?)" title="Click to view the results">(.*?)</a>', html)[0][1]
	print records_num
	f = open('search_result.html','w')
	f.write(html)
	f.close()
	curl = base_url + query_url + SID + query_acts #change pagesize to 50
	html = SpiderHandle.get_url(curl)
	return records_num.replace(',','')

def main():
	base_url = 'http://apps.webofknowledge.com/'
	query_input = 'FO=National And CU=China'
	editions = 'AHCI'
	startYear = 1986
	endYear = 2016
	
	SpiderHandle = Spider(base_url)
	SID = SpiderHandle.get_sid()
	records_num = query_search(SpiderHandle, SID, query_input, editions, startYear, endYear)
	SpiderHandle.cookie.save('cookie.txt',ignore_discard=True, ignore_expires=True)

	if int(records_num)%50 == 0 :
		pages_num = int(records_num) / 50
	else:
		pages_num = int(records_num) / 50 +1
	
	base_url = 'http://apps.webofknowledge.com'
	query_str = '/summary.do?product=WOS&parentProduct=WOS&search_mode=AdvancedSearch&parentQid=&qid=1&SID='
	base_dir = './Source/'+ editions + '/'
	doc_dir = base_dir + str(endYear)
	if os.path.exists(doc_dir) == False:
		os.makedirs(doc_dir)

	for page in range(1, pages_num+1):
		SpiderHandle._get_cookie()
		logging.info("dealing with page "+str(page))
	
		url = base_url + query_str + SpiderHandle.get_sid() + '&&update_back2search_link_param=yes&page=' + str(page)
		html = SpiderHandle.get_url_with_cookie(url)
			
		SpiderHandle.get_all_pages(html)
		SpiderHandle.headers['Referer'] = url

		for curl in SpiderHandle.urls:
			curl = base_url + curl.replace('&amp;','&')
			docid = curl[curl.find('doc=')+4:]
			if docid.find('&') != -1:
				docid = docid[:docid.find('&')]
			logging.info("docid: "+docid)

			html = SpiderHandle.get_url_with_cookie(curl)
			if html == None:
				continue
			f = open(doc_dir+'/'+docid.zfill(5)+'.html','w+')
			f.write(html)
			f.close()
			#time.sleep(1)
		#To avoid Session expired, every 5 pages request for a new session
		if page%5 == 0:
			SpiderHandle = Spider(base_url)
			SID = SpiderHandle.get_sid()
			records_num = query_search(SpiderHandle, SID, query_input, editions, startYear, endYear)
			SpiderHandle.cookie.save('cookie.txt',ignore_discard=True, ignore_expires=True)
	time.sleep(1)

if __name__ == '__main__':
	main()
