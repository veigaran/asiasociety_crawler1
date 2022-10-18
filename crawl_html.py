from request import request_fingerprint
from redis_pool import get_redis
import time
import datetime
import requests
from bs4 import BeautifulSoup
import lxml
import re
# from scrapy_redis.spiders import RedisCrawlSpider
import scrapy
from redis import Redis
import settings
from scrapy.utils.project import get_project_settings
import redis
import logging
name = "detail"
redis_key = 'detail:start_urls'
redis_error_key = 'detail:error_urls'
redis_df_key = 'detail:dupefilter'
handle_httpstatus_list = [
    404,
    503,
    504,
]

log = logging.getLogger("detail")
settings = get_project_settings()
def get_redis():
    redis_args = dict(
        host=settings['REDIS_HOST'],
        port=settings['REDIS_PORT'],
        username=settings["REDIS_PARAMS"]["username"],
        password=settings["REDIS_PARAMS"]["password"],
        db=settings["REDIS_PARAMS"]["db"],
    )
    pool = redis.ConnectionPool(**redis_args)
    return redis.Redis(connection_pool=pool)

redis_server = get_redis()
def parse_and (response):
        try:
            if response.status in handle_httpstatus_list:
                log_str = '%d url %s' %(response.status, response.url)
                log.error(log_str)
                redis_server.rpush(redis_error_key, response.url)
            else:
                if response.status == 200:
                    with open('htmls/'+response.meta['title'].replace(' ','_')+'.html','w+',encoding='utf8') as f:
                        f.write(response.text)
                    fp = request_fingerprint(response.request)
                    redis_server.sadd(redis_df_key, fp)
                else:
                    redis_server.lpush(redis_error_key, response.url)
        except Exception as err:
            log.error(str(err))
            log.error(response.url)
            log.error(response.body)
            redis_server.lpush(redis_error_key, response.url)
