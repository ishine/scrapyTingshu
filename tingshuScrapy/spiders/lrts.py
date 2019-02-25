# -*- coding: utf-8 -*-
# @desc:
#   懒人听书爬虫、爬取专辑信息
# @date:
#   2019-02-25
# @author:
#   https://github.com/LuYongwang
import re
from copy import deepcopy

import scrapy


class LrtsSpider(scrapy.Spider):
    name = 'lrts'
    allowed_domains = ['www.lrts.me']
    start_urls = ['http://www.lrts.me/book/category']

    def parse(self, response):
        # 大分类分组
        category_list = response.xpath("//div[@class='sns-category']/ol/li")
        for category in category_list:
            item = dict()
            item['album_platform'] = "lrts"
            item['category_name'] = category.xpath("./a/text()").extract_first()
            category_url = category.xpath("./a/@href").extract_first()

            if category_url is not None:
                item['category_id'] = str(category_url).replace("/book/category/", "")
                # 获取小分类分组
                yield scrapy.Request(
                    "http://www.lrts.me" + category_url,
                    callback=self.parse_classify
                    , meta={"item": item}
                )

    # 获取二级分类
    def parse_classify(self, response):
        item = response.meta['item']
        classify_list = response.xpath("//section[@class='category-filter']/div/a")
        for classify in classify_list:
            item['classify_name'] = classify.xpath("./text()").extract_first()
            if item['classify_name'] == '全部':
                continue
            item['classify_id'] = classify.xpath("./@href").extract_first()
            if item['classify_id'] is not None:
                item['classify_id'] = str(item['classify_id']).replace("/book/category/", "")
                # http://www.lrts.me/book/category/63/recommend/1/20
                yield scrapy.Request(
                    "http://www.lrts.me/book/category/" + item['classify_id'] + "/recommend/1/20"
                    , callback=self.parse_album_list
                    , meta={"item": deepcopy(item)}
                )

    # 分析专辑列表
    def parse_album_list(self, response):
        item_info = deepcopy(response.meta['item'])
        item_list = response.xpath('//div[@class="category-book"]/ul/li')
        for item in item_list:
            # 专辑名
            item_info['album_name'] = item.xpath(
                "./div[@class='book-item-r']/a[@class='book-item-name']/text()").extract_first()
            url = item.xpath("./div[@class='book-item-r']/a[@class='book-item-name']/@href").extract_first()
            item_info['album_id'] = str(url).replace("/book/", '')
            yield scrapy.Request(
                "http://www.lrts.me" + url
                , callback=self.parse_album_detail
                , meta={"item": deepcopy(item_info)}
            )
        # 分页
        url = response.xpath("//a[@class='next']/@href").extract_first()
        if url is not None:
            yield scrapy.Request(
                "http://www.lrts.me" + url
                , callback=self.parse_album_list
                , meta={"item": deepcopy(response.meta['item'])}
            )

    # 分析专辑详情
    def parse_album_detail(self, response):
        item = response.meta['item']
        # 专辑图
        item['album_img'] = response.xpath("//div[@class='d-cover d-book-cover']/img/@src").extract_first()
        # 跟新状态
        item['album_finished'] = response.xpath("//h1[@class='nowrap']/i[@class='d-status']/text()").extract_first()
        # 作者
        item['album_author'] = response.xpath(
            "//ul[@class='d-grid nowrap']/li[1]/a[@class='author']/text()").extract_first()
        # 主播
        item['album_artist'] = response.xpath(
            "//ul[@class='d-grid nowrap']/li[2]/a[@class='g-user']/text()").extract_first()

        # 主播图
        artist_photo = response.xpath("//img[@class='round photo-s50']/@src").extract_first()
        if artist_photo is not None:
            artist_photo = artist_photo.split("?")[0]
        item['album_artist_img'] = artist_photo
        # 描述
        item['album_desc'] = response.xpath("//div[@class='d-desc f14']/p/text()").extract_first()
        # 播放量
        play_cnt = response.xpath("//div[@class='d-o d-book-o']/a/span/em/text()").extract_first()
        if play_cnt is not None:
            item['play_cnt'] = str(play_cnt).strip()
        # 歌曲数
        item['song_num'] = response.xpath("//div[@class='d-o d-book-o']/a/input/@value").extract_first()

        # 评分
        rate = response.xpath("//div[@class='d-star']/i[@class='icon-star-s']").extract_first()
        if rate is None:
            rate = []
        item['album_rate'] = len(rate)

        # Time
        item['album_time'] = response.xpath(
            "//section[@class='d-info d-book-info clearfix']/div[@class='d-r']/ul[3]/li[3]/text()").extract_first()
        #
        # # 文件大小
        item['album_file_size'] = response.xpath(
            "//section[@class='d-info d-book-info clearfix']/div[@class='d-r']/ul[3]/li[2]/text()").extract_first()
        #
        # # 更新日期
        response.xpath(
            "//section[@class='d-info d-book-info clearfix']/div[@class='d-r']/ul[3]/li[4]/text()").extract_first()

        # 评论数
        item['album_comments_num'] = re.findall("我来发表第(.*?)条评论", response.body.decode())
        item['album_comments_num'] = item['album_comments_num'][0] if len(item['album_comments_num']) > 0 else None

        yield item
