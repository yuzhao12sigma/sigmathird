# !/usr/bin/env python
# -*- coding=utf-8 -*-

from __future__ import absolute_import

import os
import time
import shutil
import requests
import json
import config
from logger import logger
from db import find_yinggu, update_yinggu
from utils import get_file_md5_digest, path_split, get_temp_store_dir, SigmaAuth


server_addr = config.fetch("server_addr")
yinggu_key = config.fetch("auth", "yinggu", "key")
yinggu_secret = config.fetch("auth", "yinggu", "secret")
conn = requests.session()


def yinggu_download_one(local, remote):
    if os.path.exists(local):
        os.remove(local)
    for i in range(5):
        try:
            response = conn.get(remote, timeout=5)
            with open(local, "wb") as w:
                w.write(response.content)
        except Exception as e:
            if i >= 4:
                logger.info("e")
            else:
                time.sleep(1)
        else:
            time.sleep(0.1)
            break


def upload_multi(account, groupname, pathname, dirname, quantity, key, secret):
    upload_id = upload_multi_init(account, groupname, dirname, quantity, key, secret)
    for root, dirs, files in os.walk(pathname):
        for name in files:
            filename = root + "/" + name
            ret = upload_multi_part(account, upload_id, filename, key, secret)
            if 'store_id' in ret.keys():
                return ret


def upload_multi_init(account, groupname, dirname, quantity, key, secret):
    contents = {"dirname": dirname, "quantity": quantity, "overwrite": 1, "converted": 1}
    url = "{}/accounts/{}/store/uploads/{}/".format(server_addr, account, groupname)
    response = conn.post(url, data=json.dumps(contents), auth=SigmaAuth(key, secret))
    jsondata = json.loads(response.text)
    return jsondata["data"]["upload_id"]


def upload_multi_part(account, upload_id, filename, key, secret):
    _dirname, _filename = path_split(filename)
    url = "{}/accounts/{}/store/uploads/{}/?upload_id={}".format(server_addr, account, _filename, upload_id)
    headers = {
        "Content-Length": str(os.path.getsize(filename)),
        "Content-MD5": get_file_md5_digest(filename)
    }
    with open(filename, "rb") as f:
        response = conn.put(url, data=f.read(), headers=headers, auth=SigmaAuth(key, secret))
        return json.loads(response.text)


def new_job(account, user, study_id, series_id, notify_url, notify_info, key, secret):
    request_data = {
        'account_name': account,
        'user_name': user,
        'study_id': study_id,
        'series_id': series_id,
        'patient_id': '',
        'format': 'nii',
        'filename': series_id + ".nii",
        'job_type': 'lung_nodule_detection',
        'priority': '2',
        'type': 'file',
        'notify': "1",
        'notify_url': notify_url,
        'notify_info': notify_info
        }
    request_url = "{}/accounts/{}/jobs/".format(server_addr, account)
    conn.post(url=request_url, data=json.dumps(request_data), auth=SigmaAuth(key, secret))


def run_yinggu(account, user, task_info):
    uid = task_info.get("ID")
    usr = task_info.get("usr")
    ai_id = task_info.get("aiID")
    data_info = task_info.get("dataInfo")
    return_addr = task_info.get("returnAddr")
    version = task_info.get("version")
    study_info = task_info.get("studyInfo")
    study_id = study_info.get("studyInstanceUID")
    series_list = study_info.get("seriesInfo")
    # filter
    series_instance_uid_list = list()
    series_files_dict = dict()
    for series in series_list:
        if int(series.get("imageCount")) < 20:
            continue
        img_list = list()
        for img in series.get("imageFileList").split(","):
            series_path = series.get("seriesPath")
            series_path = series_path if series_path.endswith("/") else series_path + "/"
            img_list.append((img, "{}{}".format(series_path, img)))
        series_files_dict[series.get("seriesInstanceUID")] = {"img_list": img_list, "img_count": len(img_list)}
        series_instance_uid_list.append(series.get("seriesInstanceUID"))

    notify_info = {
        "uid": uid, "usr": usr, "ai_id": ai_id, "study_id": study_id, "data_info": data_info,
        "version": version, "series_instance_uid_list": series_instance_uid_list}

    yinggu_dir = get_temp_store_dir()
    try:
        # 1.先获取dcm数据
        for series_uid in series_files_dict:
            logger.info("start to download dcms, study_id:{}, series_id:{}".format(study_id, series_uid))
            # 每个序列创建一个文件夹
            series_dir = os.path.join(yinggu_dir, series_uid)
            if not os.path.exists(series_dir):
                os.makedirs(series_dir)
            for dcm_tuple in series_files_dict[series_uid]["img_list"]:
                local_path = os.path.join(series_dir, dcm_tuple[0])
                remote_path = dcm_tuple[1]
                yinggu_download_one(local_path, remote_path)

        # 2.dcm图都下载好了之后，开始上传dcm，并且创建Job
        for each_series in os.listdir(yinggu_dir):
            each_series_path = os.path.join(yinggu_dir, each_series)
            logger.info("start to upload dcms, series_id:{}".format(each_series))
            upload_multi(account, each_series, each_series_path, "/",
                         series_files_dict[each_series]["img_count"], yinggu_key, yinggu_secret)
            logger.info("start to create job, series_id:{}".format(each_series))
            new_job(account, user, study_id, each_series, return_addr, notify_info,yinggu_key, yinggu_secret)
    except Exception as e:
        raise Exception("yinggu upload data or create job error!!!!: info:{}".format(e))
    finally:
        if os.path.exists(yinggu_dir):
            shutil.rmtree(yinggu_dir)


def worker():
    try:
        waiting_task_info = find_yinggu({"status": "waiting"})
        if waiting_task_info:
            study_id = waiting_task_info.get("study_id")
            try:
                update_yinggu({"study_id": study_id, "status": "waiting"}, {"status": "running"})
                run_yinggu("yinggu", "yinggu", waiting_task_info)
                update_yinggu({"study_id": study_id}, {"status": "finished"})
            except Exception as e:
                logger.warning("run yinggu error: {}".format(e))
                update_yinggu({"study_id": study_id}, {"status": "failed", "error": str(e)})
                raise
    except Exception as e:
        logger.warning("worker error: {}".format(e))


def main():
    while True:
        worker()


if __name__ == "__main__":
    main()
