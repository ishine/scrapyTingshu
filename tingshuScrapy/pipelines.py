# -*- coding: utf-8 -*-
#
# 将数据存入Mysql中、这里可以随意修改
#
from tingshuScrapy import settings
import pymysql


class TingshuscrapyPipeline(object):

    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            db=settings.MYSQL_DBNAME,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASSWD,
            charset='utf8', port=settings.MYSQL_PORT,
            use_unicode=True,
        )

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        try:
            # 插入数据
            self.cursor.execute(
                """INSERT INTO `payment`.`other_album`(`album_id`, `platfrom`, `album_name`, `album_subtitle`, 
                `album_img`, `artist`, `author`, `artist_img`, `album_pay`, `album_price`, `album_song_num`,
                 `playcnt`, `update_date`) VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, '2019-02-24 13:44:27')""",
                (item['album_id'],
                 item['album_platform'],
                 item['album_name'],
                 item['album_name'],
                 item['album_img'],
                 item['album_artist'],
                 item['album_artist'],
                 item['artist_photo'],
                 item['pay_type'],
                 item['pay_price'],
                 item['song_num'],
                 item['play_cnt']
                 ))

            # 提交sql语句
            self.connect.commit()
        except Exception as error:
            # 出现错误时打印错误日志
            print(error)
        return item
