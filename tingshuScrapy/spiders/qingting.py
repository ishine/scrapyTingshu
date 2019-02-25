# -*- coding: utf-8 -*-
# @desc:
#   蜻蜓FM爬虫、爬取专辑信息
# @date:
#   2019-02-25
# @author:
#   https://github.com/LuYongwang
from copy import deepcopy

import json
import scrapy


class QingtingSpider(scrapy.Spider):
    name = 'qingting'
    allowed_domains = ['qingting.fm']
    # 蜻蜓FM分类页
    start_urls = ['https://www.qingting.fm/categories/']

    # 蜻蜓FM 专辑列表页接口
    album_list = "https://i.qingting.fm/capi/neo-channel-filter?category={}&attrs={}&curpage={}"

    def parse(self, response):
        # 一级分类
        category_list = response.xpath("//*[@id='app']/div/div[2]/div/div/div[1]/ul/li")
        for category in category_list:
            item = dict()
            item['album_platform'] = "qingting"
            item['category_name'] = category.xpath("./a/text()").extract_first()
            category_url = category.xpath("./a/@href").extract_first()

            if category_url is not None:
                item['category_id'] = str(category_url).replace("/categories/", "").replace("/0/1", "")
                # 获取二级分类
                yield scrapy.Request(
                    "https://www.qingting.fm" + category_url,
                    callback=self.parse_classify
                    , meta={"item": item}
                    # , dont_filter=False
                )

    # 获取二级分类
    def parse_classify(self, response):
        item = response.meta['item']
        classify_list = response.xpath("//*[@id='app']/div/div[2]/div/div/div[2]/div[1]/div[1]/div[3]/a")
        for classify in classify_list:
            item['classify_name'] = classify.xpath("./div/text()").extract_first()
            if item['classify_name'] == '全部':
                continue
            # /categories/3617/3305/1
            category_url = classify.xpath("./@href").extract_first()
            if category_url is not None:
                item['classify_id'] = str(category_url).replace("/categories/" + str(item['category_id']) + "/",
                                                                "").replace("/1", "")
                # https://www.qingting.fm/categories/3617/3305/1
                yield scrapy.Request(
                    self.album_list.format(item['category_id'], item['classify_id'], 1)
                    , callback=self.parse_album_list
                    , meta={"item": deepcopy(item)})

    # 分类对应专辑列表
    def parse_album_list(self, response):
        item = deepcopy(response.meta['item'])
        response_json = json.loads(response.text)
        if response_json['errorno'] != 0:
            return
        # 获取专辑ID
        for album in response_json['data']['channels']:
            item['album_id'] = album['id']
            item['album_name'] = album['title']
            item['update_time'] = album['update_time']
            item['album_img'] = album['cover']

            # 获取专辑信息
            # https://i.qingting.fm/wapi/channels/231968
            album_detail_url = str("https://i.qingting.fm/wapi/channels/" + str(item['album_id']))
            yield scrapy.Request(
                album_detail_url
                , callback=self.parse_album_detail
                , meta={"item": deepcopy(item)})

        # 判断分页
        total = response_json['total']
        page = response_json['curpage']
        if total / 12.00 > page:
            yield scrapy.Request(
                self.album_list.format(item['category_id'], item['classify_id'], page + 1)
                , callback=self.parse_album_list
                , meta={"item": deepcopy(response.meta['item'])})

    # 专辑详情页面管理
    def parse_album_detail(self, response):
        item = deepcopy(response.meta['item'])
        response_json = json.loads(response.text)
        if response_json['code'] != 0:
            return
        album_info = response_json['data']
        item['album_desc'] = album_info['desc']
        item['album_song_total'] = album_info['program_count']
        item['playcount'] = album_info['playcount']
        item['artist'] = album_info['podcasters'][0]['name']
        item['artist_img'] = album_info['podcasters'][0]['img_url']

        yield item
