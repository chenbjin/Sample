# -*- coding: utf-8 -*-
#@author: chenbjin
#@time:  2015-08-14

from bs4 import BeautifulSoup
from datetime import date
from math import ceil
import re, json, os, logging, csv
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class CVAnalyser(object):
	"""docstring for CVAnalyser"""
	def __init__(self):
		super(CVAnalyser, self).__init__()
		self.cvs = []
		self.comps = None
		self.comps_dict = {}
		self.compsname = []
		self.score = {}

	#对原始简历网页进行分析，提取关键属性信息
	def analyse(self, html_file, base_path):
		cv = {}
		html = open(base_path+'/'+html_file).read()
		soup = BeautifulSoup(html)
		
		#简历基本条目
		cv['cv_id'] = html_file.split('.')[0]
		cv['job_goal'] = soup.find('span',class_="jobGoal").text.encode('utf-8') if soup.find('span',class_="jobGoal") else ''
		#教育经历
		cv['educations'] = []
		if soup.find('div',class_="addcont addeduc"):
			educations = soup.find('div',class_="addcont addeduc").find_all('div', class_=re.compile("^infoview"))
			for edu in educations:
				record = {}
				lis = edu.find_all('li')
				record['time'] = lis[0].text.encode('utf-8')
				record['school'] = lis[1].text.encode('utf-8')
				record['major'] = lis[2].text.encode('utf-8')
				cv['educations'].append(record)

		#工作经历
		cv['experiences'] = []
		experiences = soup.find('div',class_="addcont addexpe").find_all('div', class_=re.compile("^infoview"))
		for exp in experiences:
			record = {}
			record['company'] = exp.find('h4').text.encode('utf-8')
			#print record['company']
			std = exp.find_all('span', class_='std')
			record['time'] = std[0].text.encode('utf-8').split(' ')[0]
			record['salary'] = std[1].text.encode('utf-8').strip()
			record['position'] = std[2].text.encode('utf-8').strip()
			record['responsibility'] = std[3].text.encode('utf-8').strip()
			cv['experiences'].append(record)

		#项目经历
		cv['projects'] = []
		projects = soup.find('div',class_="addcont addproj").find_all('div', class_=re.compile("^infoview"))
		for proj in projects:
			record = {}
			record['project'] = proj.find('h4').text.encode('utf-8')
			#print record['company']
			std = proj.find_all('span', class_='std')
			record['time'] = std[0].text.encode('utf-8').strip()
			record['description'] = std[1].text.encode('utf-8').strip()
			record['responsibility'] = std[2].text.encode('utf-8').strip()
			cv['projects'].append(record)
		
		self.cvs.append(json.dumps(cv, ensure_ascii=False,sort_keys=True))
		print cv['cv_id'], cv['job_goal']

	#对所有原始网页进行处理，保存为allcv.txt
	def fit(self, path, result='allcv.txt'):
		walk = os.walk(path)
		cv_ids = []
		for root, dirs, files in walk:
			for name in files:
				if name in cv_ids:
					continue
				else:
					print 'Deal with ',str(root+'/'+name)
					self.analyse(name,base_path=root)
					cv_ids.append(name)
		f = open(result, 'w+')
		for cv in self.cvs:
			f.write(cv+'\n')
		f.close()

	def get_companys(self, companyfile='allcompany.csv'):
		reader = csv.DictReader(open(companyfile,'rb'))
		self.comps = [ line for line in reader]
		for comp in self.comps:
			self.comps_dict[comp['companyName']] = comp
			self.comps_dict[comp['companyShortName']] = comp
		logging.info('Get companys done!')

	def get_cvs(self, cvfile='allcv_w.txt'):
		reader = open(cvfile).readlines()
		self.cvs = [ json.loads(line, encoding='utf-8') for line in reader]
		ff = open('score.txt').readlines()
		for line in ff:
			line = line.strip().split(': ')
			item = line[0]
			score = line[1]
			self.score[item] = score

	def calssify(self):
		self.get_companys()
		self.get_cvs()
		self.compsname = self.comps_dict.keys()

		cnt = 0
		total = 0
		zero_num = 0
		edu_cnt = 0
		for cv in self.cvs:
			total += len(cv['projects'])
			for proj in cv['projects']:
				score = self._proj_score(proj, cv['experiences'])
				if score == 0:
					flag=False
					for edu in cv['educations']:
						if self._time_cmp(proj['time'], edu['time'], approximate=True):
							#print edu['time'].encode('utf-8'), edu['school'].encode('utf-8'), edu['major'].encode('utf-8')
							score=1.0
							flag=True
							edu_cnt += 1
							#print proj['project'].encode('utf-8'), score
							break
					if flag==False:
						zero_num += 1
						print proj['project'].encode('utf-8'), score
				else:
					cnt += 1
					#print proj['project'].encode('utf-8'), score
		print 'total:',total
		print 'edu:', edu_cnt
		print 'zero_num:', zero_num
		print 'nonzero:', cnt

	#proj score = 65%salary + 25%scale + 10%time
	def _proj_score(self, proj, expes):
		proj_time = proj['time']
		score = self._proj_time_score(proj_time) / 10.0
		flag = False
		#print "proj_time: ", proj_time.encode('utf-8'), self._time_pass(proj_time)
		for expe in expes:
			if self._time_cmp(proj_time, expe['time']):
				flag = True
				cur_comp = expe['company'].encode('utf-8').replace('(','（').replace(')','）')
				score += float(self.score[expe['salary'].encode('utf-8')])*13/20.0
				if cur_comp in self.compsname:
					#找到公司				
					if self.comps_dict[cur_comp]['financeStage'] in self.score.keys():
						score += float(self.score[self.comps_dict[cur_comp]['financeStage']]) / 4.0
					else :
						score += float(self.score[self.comps_dict[cur_comp]['companySize']]) / 4.0
					return score
				else: 
					#找不到公司 scale=5
					score += 5.0/4.0
					return score
					#print 'can`t find :', expe['company'].encode('utf-8') 
				break
		return 0

	def _proj_time_score(self, proj_time):
		score = 0
		if proj_time > 18: score = 10
		elif proj_time > 16 and proj_time <= 18: score = 9
		elif proj_time > 14 and proj_time <= 16: score = 8
		elif proj_time > 12 and proj_time <= 14: score = 7
		elif proj_time > 10 and proj_time <= 12: score = 6
		elif proj_time > 8 and proj_time <= 10: score = 5
		elif proj_time > 6 and proj_time <= 8: score = 4
		elif proj_time > 4 and proj_time <= 6: score = 3
		elif proj_time > 2 and proj_time <= 4: score = 2
		else: score = 1
		return score

	#时间比较，time1项目时间，time2公司时间
	def _time_cmp(self, time1, time2, approximate=False):
		time1 = self._time_cast(time1)
		time2 = self._time_cast(time2)
		if approximate:		
			if time1[0] >= time2[0] or time1[1] <= time2[1]:
				#print 'Bingo',time1, time2
				return True
			else: return False
		else:
			if time1[0] >= time2[0] and time1[1] <= time2[1]:
				#print 'Bingo',time1, time2
				return True
			else: return False

	#将时间串转化为date数据格式
	def _time_cast(self, str_time):
		time = re.findall(r'(\d+)年(\d+)月', str_time.encode('utf-8'), re.S)
		if time:
			if len(time)==1: start_time=date(int(time[0][0]),int(time[0][1]), 1); end_time=date.today()
			elif len(time)==2: start_time=date(int(time[0][0]),int(time[0][1]), 1); end_time=date(int(time[1][0]), int(time[1][1]), 1)
			#print "end_time > start_time:",end_time>start_time
			return (start_time, end_time)
		else:
			print 'Error: check the format of time...'

	#计算时间date跨度(return num_of_month)
	def _time_pass(self, str_time):
		start, end = self._time_cast(str_time)
		return int( ceil((end-start).days/31.0) )

def main():
	cv = CVAnalyser()
	#cv.fit('./58cv/')
	cv.calssify()
	#cv._time_cast(u'2014年4月-2014年4月')
	

if __name__ == '__main__':
	main()
		