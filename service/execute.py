# !/usr/bin/env python
# -*- coding=utf-8 -*-

from __future__ import absolute_import

import os
import shutil
import threading
import pymongo


class MongoDB(object):
    def __init__(self, endpoint, db_name):
        endpoint = endpoint if endpoint.find("mongodb://") else "mongodb://" + endpoint
        self.connection = pymongo.MongoClient(endpoint)
        self.db_name = db_name

    def get_db_connection(self):
        """Return mongodb connect instance."""
        return self.connection

    def get_database(self):
        """Return database instance."""
        return self.connection[self.db_name]


DB = MongoDB("127.0.0.1:27017", "sigmathird").get_database()
DB_TASKS = DB.tasks


def get_one_waiting_task():
    pass


def run_task():
    pass


def clean(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


def worker():
    """每个线程执行任务定义"""
    # 发现waiting的task, 设置成running
    get_one_waiting_task()
    # 执行后设置成success/failed
    run_task()
    # 清理临时文件
    clean()


def scanning():
    """多线程扫描waiting状态的任务"""
    processies = list()
    process = threading.Thread(target=worker)
    processies.append(process)
    process.start()


def main():
    while True:
        scanning()


if __name__ == "__main__":
    main()
