# -*- coding: utf-8 -*-
#@author: chenbjin
#@time:  2015-08-13

import urllib2, logging, time
from lxml import etree
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def time_cost(fn):
	def _wrapper(*args, **kwargs):
		start = time.clock()
		fn(*args, **kwargs)
		logging.info("%s() cost %s seconds"%(fn.__name__, time.clock() - start))
	return _wrapper

class CVParser(object):
	"""docstring for CVParser"""
	def __init__(self):
		super(CVParser, self).__init__()
		self.urls = []

	def get_html(self, url, getid=False):
		if getid: 
			cv_id = url.split('/')[4]
		user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
		headers = { 'User-Agent' : user_agent }
		request = urllib2.Request(url, headers=headers)
		try:
			html = urllib2.urlopen(request, timeout=10).read()
		except Exception, e:
			if getid: return False, False
			return False
		else:
			if getid: return cv_id, html
			return html

	def get_url(self, html):
		'''
			get cv url from html page.
		'''
		page = etree.HTML(html.lower().decode('utf-8','ignore'))
		hrefs = page.xpath(u"//a[@class='fl']")
		if len(hrefs) == 0: return False
		else:
			for href in hrefs:
				if href.attrib['href'].startswith('http://jianli.58.com/'):
					self.urls.append(href.attrib['href'])
			return True

	def is_good_cv(self, html):
		'''
			true: have job experiment and projects.
		'''
		page = etree.HTML(html.lower().decode('utf-8','ignore'))
		expes = page.xpath(u"//div[@class='addcont addexpe']")
		projs = page.xpath(u"//div[@class='addcont addproj']")
		if expes and projs: return True
		else: return False

	def save_cv(self, cv_id, html, cnt):
		filename = './58cv/wuhang/'+cv_id+'.html'
		logging.info('line:'+str(cnt)+' saving html to '+filename)
		f = open(filename,'w+')
		f.write(html)
		f.close()

@time_cost
def main():
	base_url = 'http://wh.58.com/'
	ff = open('58job_types.txt').readlines()
	job_types = [job.strip() for job in ff]
	#print job_types
	cv_filter = 'pve_5593_5/'
	
	for job_type in job_types:
		cv = CVParser()
		logging.info('Dealing with '+job_type)
		for page in xrange(1,50):
			url = base_url+job_type+'pn'+str(page)+'/'+cv_filter
			logging.info('getting html :'+url)
			html = cv.get_html(url)
			if page % 15==0:
				time.sleep(2)
			if html: 
				goon = cv.get_url(html)
				if goon == False:
					break
		logging.info('Total urls:'+str(len(cv.urls)))
		cnt = 0
		for url in cv.urls:
			logging.info('deal with '+ url)
			time.sleep(1)
			cv_id, html = cv.get_html(url, getid=True)
			if html and cv.is_good_cv(html):
				cv.save_cv(cv_id, html, cnt)
			cnt += 1
		logging.info('waiting for another type ...')
		time.sleep(8)

if __name__ == '__main__':
	main()
