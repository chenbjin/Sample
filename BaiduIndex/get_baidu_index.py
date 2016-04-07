#-*- coding: UTF-8 -*-

from selenium import webdriver
from PIL import Image, ImageFilter
import pytesseract
import time, logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def getDigit(text):
    '''get digit of text'''
    ans = ""
    for i in text:
        if i.isdigit():
            ans += i
    return ans

def recognize(img_path):
    # crop img
    box = (365,  325,  480,  380)  #(115*55)
    img = Image.open(img_path) #打开截图
    crop_img = img.crop(box)  #使用Image的crop函数，截取需要的区域
    crop_img.save('./fuck.tiff')
    # 
    img = Image.open('./fuck.tiff')
    img = img.resize((230,110),Image.BILINEAR) 
    img = img.filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(img).strip()
    return getDigit(text)

def baidu_index(keyword):
    logging.info("Opening Firefox...")
    browser = webdriver.Firefox()
    browser.get('http://index.baidu.com/')
    time.sleep(1)
    
    # login
    logging.info("Login in Baidu Index...")
    browser.find_element_by_link_text('登录').click()
    time.sleep(1)
    browser.find_element_by_name('userName').send_keys('your_username')
    browser.find_element_by_name('password').send_keys('your_password')
    browser.find_element_by_id('TANGRAM_12__submit').click()
    time.sleep(5)
    
    # query search and screenshot
    logging.info("Query keyword: " + keyword)
    browser.find_element_by_id('schword').send_keys(keyword)
    browser.find_element_by_id('searchWords').click()
    time.sleep(5)
    browser.get_screenshot_as_file("./NM.png")

    # recognize digit
    logging.info("Recognizing with OCR...")
    text = recognize("./NM.png")
    print 'baidu index of', keyword, 'is', text

    browser.quit()

def main():
    keyword = raw_input("Please input keyword: ")
    baidu_index(keyword.decode('utf-8'))

if __name__ == '__main__':
    main()
