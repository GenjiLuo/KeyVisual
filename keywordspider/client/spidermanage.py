# -*- coding: utf-8 -*-
# @Author: SHLLL
# @Email: shlll7347@gmail.com
# @Date:   2018-05-10 19:54:19
# @Last Modified by:   SHLLL
# @Last Modified time: 2018-05-28 16:36:50
# @License: MIT LICENSE

import queue
import logging
from multiprocessing import Queue, Process
import threading
from . import spider
from .mykeyword import Keyword
from . import assorules


class _RunsoiderOption(object):

    def __init__(self, option):
        # 设置log的记录格式
        logging.basicConfig(level=logging.INFO,
                            format="%(filename)s[line:%(lineno)d]"
                            " - %(levelname)s: %(message)s")

        # 设置爬虫爬取的条目数
        self.max_count = int(option['spiderNum'])
        # 设置最小支持度和置信度
        self.min_support = float(option['minSupp'])
        self.min_confidence = float(option['minConf'])
        # 设置运行对应的模块

        def func(x):
            return x == 'true'
        self.run_server = func(option['runSpider'])
        self.run_keyword = func(option['runKeyword'])
        self.run_assorule = func(option['runAssoword'])
        self.option = option

    def run(self):
        self._queue.put("running", 1)
        if self.run_server:
            if self.option['saveMethod'] == 'csv':
                spider_writer = spider.CsvWriter(
                    "data/csv/ifeng.csv",
                    ["url", "title", "datee", "news"])
            else:
                spider_writer = spider.MysqlWriter("client_content")
            myspider = spider.Spider(
                self.max_count, datawriter=spider_writer, msg_queue=self._queue)
            myspider.start_working()
        if self.run_keyword:
            if self.option['saveMethod'] == 'csv':
                keyword_writer = spider.CsvWriter(
                    "data/csv/ifeng_key.csv", ["url", "title", "keywords"])
                keyword_reader = spider.CsvReader("data/csv/ifeng.csv")
            else:
                keyword_writer = spider.MysqlWriter("client_keyword")
                keyword_reader = spider.MysqlReader("client_content")
            mykeyword = Keyword(keyword_writer,
                                keyword_reader, msg_queue=self._queue)
            mykeyword.working()
        if self.run_assorule:
            if self.option['saveMethod'] == 'csv':
                asso_fre_writer = spider.PandasCsvWriter(
                    "data/csv/ifeng_frequent.csv")
                asso_con_writer = spider.PandasCsvWriter(
                    "data/csv/ifeng_confidence.csv")
                asso_reader = spider.PandasCsvReader("data/csv/ifeng_key.csv")
            else:
                asso_fre_writer = spider.PandasMysqlWriter("client_frequent")
                asso_con_writer = spider.PandasMysqlWriter("client_confidence")
                asso_reader = spider.PandasMysqlReader("client_keyword")
            myassorules = assorules.Assokeyword(
                asso_reader, asso_fre_writer, asso_con_writer, msg_queue=self._queue)
            myassorules.working(
                min_support=self.min_support,
                min_confidence=self.min_confidence,
                find_rules=True, max_len=4)
        self._queue.put("running", 2)


class SpiderQueueInThread(object):

    def __init__(self):
        self.data = {"running": 0, "spider": 0, "keyword": 0, "assoword": 0}

    def put(self, key, value):
        if key in self.data.keys():
            if isinstance(value, float):
                value = round(value, 2)
            self.data[key] = value

    def get(self):
        return self.data

    def emptyData(self):
        for item in self.data:
            self.data[item] = 0

    def setData(self, item, num):
        self.data[item] = num

    def getQueue(self):
        return self


class RunSpiderInThread(_RunsoiderOption, threading.Thread):

    def __init__(self, option, queue):
        # 调用_RunsoiderOption类初始化方法
        super().__init__(option)
        # 调用Thread类初始化方法
        super(_RunsoiderOption, self).__init__()

        self._queue = queue

    def run(self):
        super().run()


class RunSpiderInProcess(_RunsoiderOption, Process):

    def __init__(self, option, queue):
        # 调用_RunsoiderOption类初始化方法
        super().__init__(option)
        # 调用Process类的初始化方法
        super(_RunsoiderOption, self).__init__()

        self._queue = QueuePutterInProcess(queue)

    def run(self):
        super().run()


class QueuePutterInProcess(object):

    def __init__(self, queue):
        self._queue = queue
        self._data = {"running": 0, "spider": 0, "keyword": 0, "assoword": 0}

    def put(self, key, value):
        try:
            self._queue.get_nowait()
        except queue.Empty:
            pass
        if key in self._data.keys():
            if isinstance(value, float):
                value = round(value, 2)
            self._data[key] = value
        try:
            self._queue.put_nowait(self._data)
        except queue.Full:
            pass


class QueueGetterInProcess(object):

    def __init__(self):
        self.queue = Queue(1)
        self.data = {"running": 0, "spider": 0, "keyword": 0, "assoword": 0}

    def emptyData(self):
        for item in self.data:
            self.data[item] = 0

    def setData(self, item, num):
        self.data[item] = num

    def get(self):
        try:
            self.data = self.queue.get_nowait()
        except queue.Empty:
            pass
        return self.data

    def getQueue(self):
        return self.queue
