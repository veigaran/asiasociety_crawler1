#!/usr/bin/env python  
# -*- coding:utf-8 _*-  
"""
@Time:2022-10-19 12:12
@Author:Veigar
@File: crawler.py
@Github:https://github.com/veigaran/asiasociety_crawler1
"""
import os
import re
import time

import requests
import logging
from lxml import html

logging.basicConfig(level=logging.INFO)
logging.StreamHandler()


class AsiaSocietyCrawler:
    def __init__(self, index_url, url_txt, out_folder,page_length):
        self.url = index_url
        self.url_txt = url_txt
        self.out_folder = out_folder
        self.page_length = page_length

    @staticmethod
    def open_proxy_url(url: str):
        """
        request方法,获取目标网页信息
        :param url: 目标url
        :return:
        """
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
        headers = {'User-Agent': user_agent}
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return (r.text)

    # 爬取导航主页面，获取翻页方式,得到所有目录页的url
    def parse_index(self, page_length) -> list:
        """
        获取翻页的列表，这个主要是通过前端html观察测试得到的
        :return: page组成的列表
        """
        page_url_list = []
        for i in range(page_length):
            page_url_list.append(self.url + "?page=" + str(i))
        return page_url_list

    # 遍历每一页，提取url，保存基本字段url地址
    def extract_url(self, page_list: list) -> None:
        """
        遍历每一页，提取url，保存基本字段，包括url地址、摘要信息
        :param page_list: 目录页列表
        :return: 保存待抓取的网页url、摘要到本地文件
        """
        url_list = []
        for page_url in page_list:
            page_html = self.open_proxy_url(page_url)
            tree = html.fromstring(page_html)
            urls = tree.xpath("//h4[@class='card-title']/a/@href")
            abstracts = tree.xpath("//div[@class='teaser-text']/div")
            for index in range(len(urls)):
                # url, abs = "https://asiasociety.org/" + urls[index], abstracts[index].text
                url = "https://asiasociety.org/" + urls[index]
                url_list.append(url)
            time.sleep(1)
        self.write2txt(url_list, self.url_txt)

    # 保存具体html，提取信息
    def get_html_detail(self):
        # 1.先读取txt，得到所有的url及摘要，同时与文件夹进行判重，确保不会重复抓取
        url_list = self.remove_existed()
        logging.info("还剩" + str(len(url_list)) + "未爬取")
        # 2.对未爬取的网页进行抓取及保存
        try:
            for url in url_list:
                name = "".join(re.findall(r'policy-institute/(.*)', url)).replace("/","")
                path = self.out_folder + "/" + "".join(name) + '.html'
                html_text = self.open_proxy_url(url)
                self.save_html(path, html_text)
                time.sleep(1)
        except Exception as e:
            logging.info(e)


    def remove_existed(self):
        """
        读取url.txt获取所有url，同时和保存html目录下的文件进行对比，若存在已爬取的网页，则跳过
        :return:
        """
        url_dict = {}
        with open(self.url_txt, 'r', encoding='utf') as f:
            for line in f.readlines():
                name = "".join(re.findall(r'policy-institute/(.*)', line))
                url_dict[name] = line.strip()
        for i in os.listdir(self.out_folder):
            name = i.split('.')[0]
            if name in url_dict:
                del url_dict[name]
        return list(url_dict.values())

    @staticmethod
    def write2txt(url_list: list, path: str):
        with open(path, 'w', encoding='utf') as f:
            for info in url_list:
                f.write(info)
                f.write('\n')
        logging.info("文件写入成功")

    @staticmethod
    def save_html(path, text):
        """
        保存网页至本地
        :param name:
        :return:
        """
        with open(path, 'w', encoding='utf8') as fw:
            fw.write(text)  # 忽略非法字符
        print(path + "已保存！")

    def main(self):
        if not os.path.exists(self.url_txt):
            logging.info("第一次爬取，获取所有的url，保存至txt")
            page_url_list = self.parse_index(self.page_length)
            self.extract_url(page_url_list)
            time.sleep(1)
        else:
            logging.info("已存在url文件，直接开始获取详情页")
        self.get_html_detail()


if __name__ == '__main__':
    test_url = "https://asiasociety.org/policy-institute/publications"
    handler = AsiaSocietyCrawler(test_url, "url.txt", "html/",53)
    handler.main()
