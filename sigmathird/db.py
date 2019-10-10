#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pymongo
import config


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


db_host = config.fetch("database", "host")
db_name = config.fetch("database", "database")
DB = MongoDB(db_host, db_name).get_database()
yinggu_col = DB.yinggu


def save_yinggu(yinggu_task_info):
    yinggu_task_info["status"] = "waiting"
    yinggu_task_info["study_id"] = yinggu_task_info.get("studyInfo").get("studyInstanceUID")
    yinggu_col.insert(yinggu_task_info)


def find_yinggu(query_info):
    res = yinggu_col.find_one(query_info)
    return res


def update_yinggu(query_info, update_info):
    yinggu_col.update(query_info, {"$set": update_info})