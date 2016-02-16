# -*- encoding: utf-8 -*-
'''
Created on 2016/1/20 chenbjin
@author:chenbjin
'''

import re
import os
import csv
import json
import time
import logging
from lxml import etree

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class Parser(object):
	"""docstring for Parser"""
	def __init__(self):
		super(Parser, self).__init__()
		self.papers = []
		self.urls = []
		self.postfix = "0ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		self.authors = []  #[ ("Wu, N", "Wu, Na", 1)]
		self.orgnizations = [] #[[Sun Yet-sen University],[Sun Yet-sen University, Jiangnan University]]

	def detail_parse(self, html, i=0):
		'''
		Get Detail information followed:

		'''
		self.papers[i]["Abstract"] = "NA"
		self.papers[i]["Keywords"] = "NA"
		self.papers[i]["Impact_Factor"] = "NA"
		self.papers[i]["Impact_Factor_5Year"] = "NA"
		self.papers[i]["Publisher"] = "NA"
		self.papers[i]["Published"] = "NA"
		self.papers[i]["PubMed_ID"] = "NA"
		self.papers[i]["Research_Area"] = "NA"
		self.papers[i]["ISSN"] = "NA"
		self.papers[i]["eISSN"] = "NA"
		self.papers[i]["Authors_Emails"] = "NA"
		self.papers[i]["Authors_Other"] = "NA"
		self.papers[i]["Authors_Other_Orgs"] = "NA"
		self.papers[i]["Author_Reprint"] = "NA"
		self.papers[i]["Agents_Names"] = "NA"
		self.papers[i]["Agents_Grant_Nums"] = "NA"
		self.papers[i]["JCR_Types"] = "NA"
		self.papers[i]["JCR_Ranks"] = "NA"
		self.papers[i]["JCR_Quantiles"] = "NA"
		html_tree = etree.HTML(html.decode('utf-8','ignore'))

		title_content = html_tree.xpath(u'//div[@class="title"]/value/text()')
		if len(title_content) == 0:
			logging.info("Error: No title ,index :"+str(i))
			return False
		self.papers[i]["Title"] = title_content[0].strip().replace('&amp;','&')

		blocks = html_tree.xpath(u'//div[@class="block-record-info"]')
		for block in blocks:
			area = block.findtext('div')
			if area == None:
				self._get_authors(block, i)
			elif area.strip() == "Abstract":
				self._get_abstract(block, i)
			elif area.strip() == "Keywords":
				self._get_keywords(block, i)
			elif area.strip() == "Author Information":
				self._get_author_info(block, i)
			elif area.strip() == "Funding":
				self._get_funding(block, i)
			elif area.strip() == "Publisher":
				self._get_publisher(block, i)
			elif area.strip() == "Categories / Classification":
				self._get_research_area(block, i)
			elif area.strip() == "Document Information":
				self._get_document_info(block, i)
			elif area.strip() == "Other Information":
				self._get_other_info(block, i)
			elif area.strip() == "Journal Information":
				self._get_journal_info(html, i)
		block = html_tree.xpath(u'//div[@class="block-record-info block-record-info-source"]')[0]
		self._get_paper_source(block, i)
		return True

	def _get_authors(self, block, i):
		'''
		Get Author's Name and orgnization num
		'''
		#print etree.tostring(block.find('p'))
		block = etree.tostring(block.find('p'))
		keys = re.sub('<.*?>','',block).replace('\t','').replace('\n','').strip()
		keys = keys.replace('By:','').replace('  ','').replace(' ]',']').replace('[ ','[')
		keys = keys.replace('...More','').replace('...Less','')
		#print keys
		self.authors = []
		start = 0
		idx = keys.find('[')
		if idx != -1:
			while idx != -1 and start < len(keys):  # author, org_num
				end = keys.find(']',idx,len(keys))
				authors = keys[start:idx].split(';')
				org_num = keys[idx+1:end].split(',')

				for author in authors:
					if author != '':
						#print author
						item = re.findall(r'(.*?)\((.*?)\)', author)
						if len(item) == 0:
							continue
						item = re.findall(r'(.*?)\((.*?)\)', author)[0]
						# check pattern "By:Gaerrang (Gaerrang (Kabzung))[1]"
						sim_name = item[0].strip()
						tot_name = item[1].strip()
						if tot_name.find('(') != -1 and tot_name.find(')') == -1 :
							tot_name += ')'
						#print (sim_name, tot_name, org_num)
						self.authors.append((sim_name, tot_name, org_num))
				start = end+1
				idx = keys.find('[', idx+1, len(keys))
			# the last authors: just author no org_num
			if start < len(keys):  
				authors = keys[start:len(keys)].split(';')
				for author in authors:
					if author != '':
						item = re.findall(r'(.*?)\((.*?)\)', author)[0]
						# check pattern "By:Gaerrang (Gaerrang (Kabzung))[1]"
						sim_name = item[0].strip()
						tot_name = item[1].strip()
						if tot_name.find('(') != -1 and tot_name.find(')') == -1 :
							tot_name += ')'
						self.authors.append((sim_name, tot_name, "NA"))
						#print (sim_name, tot_name, org_num)
		# only authors no org_num
		elif idx == -1: 
			authors = keys.split(';')
			#print authors
			for author in authors:
				if author != '':
					item = re.findall(r'(.*?)\((.*?)\)', author)[0]
					# check pattern "By:Gaerrang (Gaerrang (Kabzung))[1]"
					sim_name = item[0].strip()
					tot_name = item[1].strip()
					if tot_name.find('(') != -1 and tot_name.find(')') == -1 :
						tot_name += ')'
					self.authors.append((sim_name, tot_name, ['1']))
					#print (sim_name, tot_name, org_num)
		self.papers[i]["Authors_Num"] = len(self.authors)
		#print len(self.authors)

	def _get_abstract(self, block, i):
		'''
		Get Abstract for the paper
		'''
		#self.papers[i]["Abstract"] = block.findtext('p')
		abstract = etree.tostring(block.xpath('p')[0])
		abstract = abstract.replace('<br/>','').replace('</br>','').replace('<br>','').replace('\n','').strip() #maybe have <br/>
		abstract = re.search('<p .*?>(.*?)</p>', abstract).group(1)
		abstract = abstract.replace('&amp;','&')
		low_abstract = abstract.lower()
		
		''' remove pattern: Copyright (C) '''
		start = low_abstract.rfind('copyright (c)')
		flag = False
		if start != -1:
			nstart = low_abstract.rfind('.', 0, start)
			#print abstract[:nstart+1]
			self.papers[i]["Abstract"] = abstract[:nstart+1]
			flag = True
		
		''' remove pattern: (C) ... All rights reserved '''
		if flag == False:	
			start = low_abstract.rfind('all rights reserved')
			if start != -1:
				nstart = low_abstract.rfind('(c)', 0, start)
				if nstart != -1:
					pstart = low_abstract.rfind('.', 0, nstart)
					self.papers[i]["Abstract"] = abstract[:pstart+1]
					flag = True
				else:
					self.papers[i]["Abstract"] = abstract[:nstart]
					flag = True

		''' remove other pattern: (c)... '''
		if flag == False:
			start = low_abstract.rfind('. (c)')
			if start != -1:
				#print abstract[:start+1]
				self.papers[i]["Abstract"] = abstract[:start+1]
				flag = True

		''' source abstract '''
		if flag == False:
			self.papers[i]["Abstract"] = abstract

	def _get_keywords(self, block, i):
		'''
		Get Kewords but not Kewords_Plus
		'''
		#self.papers[i]["Keywords"] = []
		keword_tags = block.xpath('p[@class="FR_field"]')
		for keword in keword_tags:
			text = keword.findtext('span').strip()
			if text == "Author Keywords:":
				keword = etree.tostring(keword)
				kewords = re.findall('<a .*?>(.*?)</a>',keword)
				if len(kewords) != 0:
					self.papers[i]["Keywords"] = ';'.join(kewords)

	def _get_author_info(self, block, i):
		address_tags = block.xpath('p[@class="FR_field"]')
		reprint_author_flag = False
		for address in address_tags:
			text = address.findtext('span').strip()
			#print text
			if text == "Reprint Address:":
				address = etree.tostring(address)
				reprint_author_content = re.search('</span>(.*?)</p>',address)
				if reprint_author_content == None:
					reprint_author = "NA"
				else:
					reprint_author = re.search('</span>(.*?)</p>',address).group(1).replace('(reprint author)','').strip()
				#print '2.reprint author:',self.authors[reprint_author][0]
				flag = True
				for man in self.authors:
					if man[0] == reprint_author:
						self.papers[i]["Author_Reprint"] = man[1]
						flag = False
						break
				if flag:
					self.papers[i]["Author_Reprint"] = reprint_author
				reprint_author_flag = True
			elif text == "Addresses:":
				orgs = block.xpath('//td[@class="fr_address_row2"]')
				if reprint_author_flag:#no reprint_author
					orgs = orgs[1:len(orgs)]
				self.orgnizations = []
				for org in orgs:
					communicate_address = re.findall(u'<a name="address(.*?)" id="address(.*?)">(.*?)</a>',etree.tostring(org))[0][2]
					communicate_address = communicate_address.replace('<span class="hitHilite">','').replace('</span>','')
					start = communicate_address.find(']')
					communicate_address = communicate_address[start+1:].strip()
					#print communicate_address
					org_list = []
					for org_name in org.iter('preferred_org'):
						org_list.append(org_name.text)
					if len(org_list) > 0:
						self.orgnizations.append(org_list)
					elif communicate_address.find('Univ') != -1:
						start = communicate_address.find(']') 
						sim_org = communicate_address.split(',')[0]
						org_list.append(sim_org.strip())
						self.orgnizations.append(org_list)
					else:
						org_list.append(communicate_address)
						self.orgnizations.append(org_list)
				# map self.authors with self.orgnizations
				if len(self.authors) > 1:
					self.papers[i]["Authors_Other"] = []
					self.papers[i]["Authors_Other_Orgs"] = []

					for x,author in enumerate(self.authors):
						if x >= 5:
							break
						if x == 0:
							self.papers[i]["Author_First"] = author[1]
							org_list = []
							if author[2] != "NA":
								#print author[2]
								for org_index in author[2]:
									for org in self.orgnizations[int(org_index)-1]:
										org = org.replace("&amp;","&")
										if org not in org_list:
											org_list.append(org)
							if len(org_list) != 0:
								self.papers[i]["Author_First_Org"] = ';'.join(org_list)
							else:
								self.papers[i]["Author_First_Org"] = "NA"
						else:
							self.papers[i]["Authors_Other"].append(author[1])
							org_list = []
							if author[2] != "NA":
								#print author[2]
								for org_index in author[2]:
									if org_index > len(self.orgnizations):
										org_index = len(self.orgnizations)
									for org in self.orgnizations[int(org_index)-1]:
										org = org.replace("&amp;","&")
										if org not in org_list:
											org_list.append(org)
							if len(org_list) != 0:
								self.papers[i]["Authors_Other_Orgs"].append('|'.join(org_list))
							else:
								self.papers[i]["Authors_Other_Orgs"].append("NA")
					self.papers[i]["Authors_Other"] = ';'.join(self.papers[i]["Authors_Other"])
					self.papers[i]["Authors_Other_Orgs"] = ';'.join(self.papers[i]["Authors_Other_Orgs"])

			elif text == "E-mail Addresses:":
				emails = etree.tostring(address)
				author_emails = re.findall('<a href=.*?>(.*?)</a>', emails)
				if len(author_emails) != 0:
					self.papers[i]["Authors_Emails"] = ';'.join(author_emails)

	def _get_funding(self, block, i):
		cnt = 1
		self.papers[i]["Agents_Names"] = []
		self.papers[i]["Agents_Grant_Nums"] = []
		for item in block.iter('tr'):
			item = etree.tostring(item)
			item = item.replace('<span class="hitHilite">','').replace('</span>','').replace('&#160;','').strip()
			#print item
			funds = re.findall('<td>(.*?)</td>',item)
			if len(funds) != 0:
				ag_name = funds[0].replace("&amp;","&").strip()
				ag_name = re.sub('<.*?>','', ag_name)
				ag_num = re.findall('<div>(.*?)</div>',item)
				
				if ag_name != "":
					self.papers[i]["Agents_Names"].append(ag_name)
				else:
					self.papers[i]["Agents_Names"].append("NA")
				if len(ag_num) != 0:
					self.papers[i]["Agents_Grant_Nums"].append('|'.join(ag_num) )
				else:
					self.papers[i]["Agents_Grant_Nums"].append("NA")
				cnt += 1
		self.papers[i]["Agents_Names"] = ';'.join(self.papers[i]["Agents_Names"])
		self.papers[i]["Agents_Grant_Nums"] = ';'.join(self.papers[i]["Agents_Grant_Nums"])

	def _get_publisher(self, block, i):
		block = etree.tostring(block)
		#print re.search('<value>(.*?)</value>', block).group(1)
		self.papers[i]["Publisher"] = re.search('<value>(.*?)</value>', block).group(1).replace("&amp;","&").strip()

	def _get_research_area(self, block, i):
		block = etree.tostring(block)
		#print re.search('<span class="FR_label">Research Areas:</span>(.*?)</p>',block).group(1).replace("&amp;","&").split(';')
		researchs = re.search('<span class="FR_label">Research Areas:</span>(.*?)</p>',block).group(1).replace("&amp;","&").split(';')
		if len(researchs) != 0:
			self.papers[i]["Research_Area"] = []
			for area in researchs:
				self.papers[i]["Research_Area"].append(area.strip())
		self.papers[i]["Research_Area"] = ';'.join(self.papers[i]["Research_Area"])

	def _get_document_info(self, block, i):
		#print etree.tostring(block)
		block_s = etree.tostring(block)
		self.papers[i]["Document_Type"] = re.search('<span class="FR_label">Document Type:</span>(.*?)</p>', block_s).group(1).strip()
		self.papers[i]["Language"] = re.search('<span class="FR_label">Language:</span>(.*?)</p>', block_s).group(1).strip()
		for item in block.iter('p'):
			if item.findtext('span') != None:
				text = item.findtext('span').strip()
				if text == "Accession Number:":
					self.papers[i]["Accession_Num"] = item.findtext('value')
				elif text == "PubMed ID:":
					self.papers[i]["PubMed_ID"] = item.findtext('value')
				elif text == "ISSN:":
					self.papers[i]["ISSN"] = item.findtext('value')
				elif text == "eISSN:":
					self.papers[i]["eISSN"] = item.findtext('value')

	def _get_other_info(self, block, i):
		block = etree.tostring(block)
		#print re.search('<value>(.*?)</value>',block).group(1).strip()
		self.papers[i]["IDS_Num"] = re.search('<value>(.*?)</value>',block).group(1).strip()
		cite = re.findall('<b>(.*?)</b>', block)
		self.papers[i]["Cited_Refference"] = int(cite[0].replace(',',''))
		self.papers[i]["Cited_Num"] = int(cite[1].replace(',',''))

	def _get_journal_info(self, html, i):
		'''
		Get Impact_Factor and JCR Info
		'''
		index = html.find('Impact Factor')
		journal_info = html[index+1:index+2000].strip().replace('\n','').replace('\t','')
		journal_info = re.findall('<td(.*?)>(.*?)</td>',journal_info)
		
		if len(journal_info) > 0:
			if journal_info[0][1].strip() != "":
				self.papers[i]["Impact_Factor"] = float(journal_info[0][1].strip())
			if journal_info[1][1].strip() != "":
				self.papers[i]["Impact_Factor_5Year"] = float(journal_info[1][1].strip())
		
		pos = 2
		cnt = 1
		self.papers[i]["JCR_Types"] = []
		self.papers[i]["JCR_Ranks"] = []
		self.papers[i]["JCR_Quantiles"] = []
		while pos < len(journal_info):
			jcr_type = journal_info[pos][1].strip().replace('&amp;','&')
			jcr_type = re.sub(' <.*?>','', jcr_type).strip()
			#print jcr_type
			self.papers[i]["JCR_Types"].append(jcr_type)
			pos += 1
			self.papers[i]["JCR_Ranks"].append(journal_info[pos][1].strip().replace('&amp;','&').replace(' of ','/') )
			pos += 1
			self.papers[i]["JCR_Quantiles"].append(journal_info[pos][1].strip().replace('&amp;','&') )
			pos += 1
			cnt += 1
		self.papers[i]["JCR_Types"] = ';'.join(self.papers[i]["JCR_Types"])
		self.papers[i]["JCR_Ranks"] = ';'.join(self.papers[i]["JCR_Ranks"])
		self.papers[i]["JCR_Quantiles"] = ';'.join(self.papers[i]["JCR_Quantiles"])

	def _get_paper_source(self, block, i):
		paper_source = {}
		self.papers[i]["Journal"] = block.findtext('p/value').strip().replace('&amp;','&')
		for label in block.iter('p'):
			if label.findtext('span') != None:
				text = label.findtext('span').strip()
				if text == "Volume:":
					paper_source["Volume"] = label.findtext('value')
				elif text == "Issue:":
					paper_source["Issue"] = label.findtext('value')
				elif text == "Pages:":
					paper_source["Pages"] = label.findtext('value')
				elif text == "Part:":
					paper_source["Part"] = label.findtext('value')
				elif text == "DOI:":
					paper_source["DOI"] = label.findtext('value')
				elif text == "Published:":
					self.papers[i]["Published"] = label.findtext('value')
		if len(paper_source) == 0:
			self.papers[i]["Paper_Source"] = "NA"
		else:
			self.papers[i]["Paper_Source"] = paper_source

	def save_json(self, filename):
		with open(filename, 'wb') as fp:
			json.dump(self.papers , fp,  sort_keys=True, indent=4, separators=(',', ': '))

	def save_csv(self, filename):
		with open(filename, 'wb') as csvfile:
			fieldnames = self.papers[0].keys()
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			writer.writerows(self.papers)

def main():
	base_dir = './Source/SCI/2012'
	ParserHandle = Parser()
	files = os.listdir(base_dir)
	files.sort()
	for i,filename in enumerate(files):
		#logging.info('parse '+filename)
		html = open(base_dir + '/' + filename).read()
		ParserHandle.papers.append({})
		flag = ParserHandle.detail_parse(html,i)
		if flag == False: #error record
			print filename
	print len(ParserHandle.papers)
	ParserHandle.save_json('papers_SCI_2012.txt')

if __name__ == '__main__':
	main()
