# -*- coding: utf-8 -*-
# @desc:
#   喜马拉雅爬虫、爬取专辑信息
# @date:
#   2019-02-25
# @author:
#   https://github.com/LuYongwang
import json

import scrapy
from copy import deepcopy
from bs4 import BeautifulSoup


class XmlySpider(scrapy.Spider):
    name = 'xmly'
    allowed_domains = ['www.ximalaya.com']
    start_urls = ['https://www.ximalaya.com/category/']

    classify_album_list_url = "https://www.ximalaya.com/revision/category/queryCategoryPageAlbums?" \
                              "category={}&subcategory={}&meta=&sort=0&page={}&perPage=200"

    def parse(self, response):
        # 一级分类、 喜马拉雅分为三级
        category_list = []
        # 这里从JS变量获取方便
        resp = response.text
        soup = BeautifulSoup(resp, 'lxml')
        script_list = soup.select('script')

        for script in script_list:
            if str(script).find("window.__INITIAL_STATE__ = {") >= 0:
                json_data = str(script.string).replace("window.__INITIAL_STATE__ = ", "").replace("};", "}")
                category_list = json.loads(json_data)['CategoryPage']['allCategoryInfo']
                # print(category_list)
                break

        # 一二级 合并输出
        for category in category_list:
            item = dict()
            item['album_platform'] = "xmly"
            item['category_name'] = category['name']
            item['category_id'] = category['id']
            for category_level_two in category['categories']:
                item['category_name'] = category['name'] + "-" + category_level_two['displayName']
                item['category_id'] = str(category['id']) + "-" + str(category_level_two['id'])
                # self.parse_classify(item=item, classify_list=category_level_two['subcategories'],
                #      code=category_level_two['pinyin'])
                for classify in category_level_two['subcategories']:
                    item['classify_name'] = classify['displayValue']
                    item['classify_id'] = classify['id']
                    if item['classify_id'] is not None:
                        item['classify_id'] = str(item['classify_id']).replace("/book/category/", "")
                        item['category_pinyin'] = category_level_two['pinyin']
                        item['classify_pinyin'] = classify['code']
                        album_list_url = self.classify_album_list_url.format(item['category_pinyin'],
                                                                             item['classify_pinyin'], 1)
                        # 一次最多200条 否则数据有问题
                        yield scrapy.Request(url=album_list_url, callback=self.parse_album_list,
                                             meta={"item": deepcopy(item)}, dont_filter=False)

    # 分析专辑列表
    def parse_album_list(self, response):
        # print(response.text)
        item_info = deepcopy(response.meta['item'])
        response_json = json.loads(response.text)
        if response_json['ret'] != 200:
            return
        for album_base_info in response_json['data']['albums']:
            # item_info = dict(item_info, **album_base_info)
            # https://www.ximalaya.com/revision/album?albumId=21390161

            album_detail_url = "https://www.ximalaya.com/revision/album?albumId=" + str(
                str(album_base_info['link']).split("/")[2])
            # print(album_detail_url)
            yield scrapy.Request(album_detail_url, callback=self.parse_album_detail, meta={"item": deepcopy(item_info)})

        current_page = response_json['data']['page']
        total = response_json['data']['total']
        page_size = response_json['data']['pageSize']

        # 分页获取数据
        if (total / page_size) > current_page:
            album_list_url = self.classify_album_list_url.format(item_info['category_pinyin'],
                                                                 item_info['classify_pinyin'], current_page + 1)
            yield scrapy.Request(url=album_list_url, callback=self.parse_album_list,
                                 meta={"item": deepcopy(response.meta['item'])}, dont_filter=False)

    # 分析专辑详情
    def parse_album_detail(self, response):
        item = response.meta['item']
        response_json = json.loads(response.text)
        if response_json['ret'] != 200:
            return
        item['album_id'] = response_json['data']['albumId']
        item['album_name'] = response_json['data']['mainInfo']['albumTitle']
        # 专辑图
        item['album_img'] = response_json['data']['mainInfo']['cover']
        # 跟新状态
        item['album_finished'] = response_json['data']['mainInfo']['isFinished']
        # 作者 喜马拉雅没有作者信息
        item['album_artist'] = ""
        # 主播
        item['album_artist'] = response_json['data']['anchorInfo']['anchorName']
        # 主播图
        item['artist_photo'] = response_json['data']['anchorInfo']['anchorCover']
        # 描述
        item['album_desc'] = response_json['data']['mainInfo']['detailRichIntro']
        # 播放量
        item['play_cnt'] = response_json['data']['mainInfo']['playCount']
        # 歌曲数
        item['song_num'] = response_json['data']['tracksInfo']['trackTotalCount']
        # 是否付费类型
        if response_json['data']['mainInfo']['isPaid']:
            pay_info = response_json['data']['mainInfo']['priceOp']
            item['pay_type'] = pay_info['priceType']
            item['pay_price'] = pay_info['albumPrice']
        else:
            item['pay_type'] = 0
            item['pay_price'] = 0
            # 评分
        item['album_rate'] = ''

        # Time
        item['album_time'] = ''
        #
        # # 文件大小
        item['album_file_size'] = ''
        # # 更新日期
        item['update_date'] = response_json['data']['mainInfo']['updateDate']

        yield item
