#!/usr/bin/env python  
# -*- coding:utf-8 _*-  
"""
@Time:2022-10-26 20:43
@Author:Veigar
@File: crawler.py
@Github:https://github.com/veigaran
"""
import os
import re
import time
import json
import pandas as pd
import requests
import logging
from lxml import html

logging.basicConfig(level=logging.INFO)
logging.StreamHandler()


class CENEA:
    def __init__(self, index_url, out_folder, xlsx_path, json_path, cached_path):
        self.url = index_url
        self.json_path = json_path
        self.out_folder = out_folder
        self.xlsx_path = xlsx_path
        self.cache_path = cached_path
        if not os.path.exists(self.out_folder):
            os.mkdir(self.out_folder)
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)

    def open_proxy_url(self, url: str):
        """
        request方法,获取目标网页信息
        :param url: 目标url
        :return:
        """
        title = url.replace("/", "-")
        save_path = os.path.join(self.cache_path, title)
        if os.path.exists(save_path):
            logging.info(save_path+"已缓存，直接读取")
            with open(save_path, "r", encoding="utf8") as f:
                return f.read()
        else:
            try:
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
                headers = {'User-Agent': user_agent}
                r = requests.get(url, headers=headers, timeout=20)
                r.raise_for_status()
                r.encoding = r.apparent_encoding
                content = r.text
                self.save_html(save_path, content)
                return (content)
            except:
                time.sleep(20)
                logging.info("请求失败，正在重试")

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
        :param text:
        :param path:
        :return:
        """
        with open(path, 'w', encoding='utf8') as fw:
            fw.write(text)  # 忽略非法字符
        print(path + "已保存！")

    # 爬取导航主页面，获取翻页方式,得到所有目录页的url
    def parse_index(self) -> list:
        """
        获取翻页的列表，这个主要是通过前端html观察测试得到的
        :return: page组成的列表
        """
        page_url_list = []
        # page_length = self.get_max_page()
        for i in range(2007, 2023):
            url = f'https://cenea.org.pl/{i}'
            page_url_list.append(url)
        return page_url_list

    # 获取最大页数
    #
    def get_max_page(self) -> int:
        """
        获取最大页数
        :return:
        """
        max_num = 75
        page_length = 0
        logging.info("开始获取最大页数")
        while True:
            page_url = self.url + "/?page=" + str(max_num)
            html_text = self.open_proxy_url(page_url)
            if "Sorry, nothing to display" in html_text:
                break
            max_num += 5
        for num in range(max_num - 10, max_num):
            page_url = self.url + "/?page=" + str(num)
            html_text = self.open_proxy_url(page_url)
            if "Sorry, nothing to display" in html_text:
                page_length = num - 1
                break
            time.sleep(1)
        logging.info("最大页数为：{}".format(page_length))
        return page_length

    # 遍历每一页，提取url，保存基本字段，包括标题、url地址信息
    def extract_url(self, page_list: list) -> None:
        """
        遍历每一页，提取url，保存基本字段，包括url地址、摘要信息
        :param page_list: 目录页列表
        :return: 保存待抓取的网页url、摘要到本地文件
        """
        url_list = []
        url_json = {}
        for page_url in page_list:
            try:
                page_html = self.open_proxy_url(page_url)
                tree = html.fromstring(page_html)
                # 用于匹配每一个page下的详情页url
                urls = tree.xpath("//header[@class='article-header']/h2/a/@href")
                # 用于匹配每一个page下的详情页标题
                titles = tree.xpath("//header[@class='article-header']/h2/a/text()")
                for index in range(len(urls)):
                    # 此处匹配得到的url为完整的url，无需补充
                    title = re.sub(r"\W", "-", titles[index])
                    url = urls[index]
                    url_list.append(title + "\t" + url)
                    url_dict = {"title": title,
                                "url": url,
                                "resource": "https://cenea.org.pl/",
                                }
                    url_json[title] = url_dict
                time.sleep(1)
            except Exception as e:
                logging.info(e)
                continue
        json.dump(url_json, open(self.json_path, "w", encoding="utf8"), indent=4, separators=(',', ': '))

    # 保存具体html，提取信息
    def get_html_detail(self):
        # 1.先读取txt，得到所有的url，同时与文件夹进行判重，确保不会重复抓取
        url_dict = self.remove_existed()
        logging.info("还剩" + str(len(url_dict)) + "未爬取")
        # 2.对未爬取的网页进行抓取及保存
        try:
            for name, url_info in url_dict.items():
                temp = {}
                path = self.out_folder + "/" + "".join(name) + '.json'
                html_text = self.open_proxy_url(url_info["url"])
                temp["title"] = name.replace("-", " ")
                temp["url"] = url_info["url"]
                temp["resource"] = url_info["resource"]
                temp["html"] = html_text
                json.dump(temp, open(path, "w", encoding="utf8"), indent=4, separators=(',', ': '))
                logging.info("已保存" + name)
        except Exception as e:
            logging.info(e)

    def remove_existed(self):
        """
        读取url.txt获取所有url，同时和保存html目录下的文件进行对比，若存在已爬取的网页，则跳过，从而避免重复抓取
        :return:
        """
        # url_dict = {}
        with open(self.json_path, "r", encoding="utf8") as f:
            url_dict = json.load(f)
        for i in os.listdir(self.out_folder):
            name = i.split('.')[0]
            if name in url_dict:
                del url_dict[name]
        return url_dict

    # 解析下载的html文本
    def parse_html(self):
        """
        解析html，提取信息
        :return:
        """
        logging.info("开始解析html")
        result_list = []
        for file in os.listdir(self.out_folder):
            try:
                file_path = self.out_folder + "/" + file
                with open(file_path, "r", encoding="utf8") as f:
                    html_dict = json.load(f)
                content_str = ""
                # html_text = f.read()
                tree = html.fromstring(html_dict["html"])
                title = tree.xpath("//h1[@class='single-post-title']")[0].text
                date = tree.xpath("//p[@class='single-post-byline']")[0].text
                content = tree.xpath("//section[@class='single-post-content entry-content']/p")
                # if tree.xpath("//div[@class='l2 experts']/a"):
                #     author = tree.xpath("//div[@class='l2 experts']/a")[0].text
                # else:
                #     author = ""
                for item in content:
                    if item.text is not None:
                        content_str += item.text
                result_list.append(
                    [title, html_dict["url"], content_str, " ", "", date, html_dict["resource"], " "])
            except Exception as e:
                logging.info(e)
                logging.info(file + "解析失败")
                continue
        df = pd.DataFrame(result_list,
                          columns=['title', 'url', 'content', 'summary', 'author', 'time', 'resource', 'pdf'])
        df.to_csv(self.xlsx_path)
        logging.info("html解析成功")

    def main(self):
        # 1.获取所有page页列表
        # page_url_list = self.parse_index()
        # # 2.遍历每一页page，获取所有的详情页url和标题，保存至txt
        # self.extract_url(page_url_list)
        # time.sleep(1)
        # # 3.根据url.txt内容，提取所有未爬取的url，保存至本地
        self.get_html_detail()
        # 4.解析下载的html，保存至xlsx
        self.parse_html()


if __name__ == '__main__':
    test_url = "https://cenea.org.pl/category/publication/"
    handler = CENEA(test_url,  "cenea", "cenea.csv", "cenea.json", "cache")
    handler.main()
