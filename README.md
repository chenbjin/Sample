# Sample
数据抓取的一些case

1. WebOfScience
  
  spider.py: 获取Web of Science的文献记录页面,保存为html.

  parse.py: 解析提取文献记录信息,保存为json格式.
  
  remove_dumplicate.py: 去重.

2. 58CV

  cv_getfrom58.py: 从58简历库中抓取简历
  
  cv_analyse.py: 简历信息提取评分
  
  58job_types.txt: 抓取的简历应聘职位

3. BaiduIndex
  
  抓取百度指数
  调用浏览器打开网页，登录查询，截图识别
  sudo pip install pytesseract
  sudo apt-get install tesseract-ocr
