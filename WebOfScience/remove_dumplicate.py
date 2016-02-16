# -*- encoding: utf-8 -*-
'''
Created on 2016/2/3 chenbjin
@author:chenbjin
'''
import json

def main():
	#remove dumplicate
	records = json.loads(open('papers_SCI_2012.txt','r').read())
	papers = []
	for record in records:
		if record not in papers:
			papers.append(record)
	print len(papers)
	with open('papers_SCI_2012_r.txt', 'wb') as fp:
		json.dump(papers , fp,  sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == '__main__':
	main()