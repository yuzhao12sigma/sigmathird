# -*- coding=utf-8 -*-

from flask import Flask, request
from flask_api import status
import hashlib
import json
from db import save_yinggu
from logger import logger

app = Flask(__name__)


@app.route('/CloudDiagnosis/Study', methods=['post'])
def yinggu():
    logger.info("start to new a yinggu task")
    request_body = json.loads(request.get_data())
    request_args = request.args.to_dict()
    request_data = dict(request_body[0].items() + request_args.items())

    print("Start YingGu add study, {}".format(request_data))
    content = {"isSuccess": "", "resultCode": "", "resultMsg": ""}
    try:
        # step1: check request_data empty
        required = ["ID", "aiID", "dataInfo", "returnAddr", "dataType", "extention",
                    "studyInfo", "usr", "version", "stamp", "sign"]
        for arg in required:
            if arg not in request_data:
                content["isSuccess"] = False
                content["resultCode"] = "1"
                content["resultMsg"] = "{}参数为空".format(arg)
                logger.warning("new yinggu task failed, because: {}".format(content["resultMsg"]))
                result_content = json.dumps(content)
                return result_content, status.HTTP_400_BAD_REQUEST

        # step2: check sign correct
        remote_sign = request_data.get("sign")
        version = request_data.get("version")
        stamp = request_data.get("stamp")
        usr = request_data.get("usr")
        local_sign = generate_ai_store_token(
            {"version": version, "stamp": stamp, "usr": usr})
        if remote_sign != local_sign:
            content["isSuccess"] = False
            content["resultCode"] = "1102"
            content["resultMsg"] = "签名错误"
            logger.warning("new yinggu task failed, because: {}".format(content["resultMsg"]))
            result_content = json.dumps(content)
            return result_content, status.HTTP_400_BAD_REQUEST

        # step3: check data correct
        correct = True
        result_msg = ""
        series_list = request_data.get("studyInfo").get("seriesInfo")
        if not series_list:
            correct = False
            result_msg = "参数异常:seriesInfo"
        if not correct:
            content["isSuccess"] = False
            content["resultCode"] = "2"
            content["resultMsg"] = result_msg
            logger.warning("new yinggu task failed, because: {}".format(content["resultMsg"]))
            result_content = json.dumps(content)
            return result_content, status.HTTP_400_BAD_REQUEST

        # step4: create waiting task
        save_yinggu(request_data)
        content["isSuccess"] = True
        content["resultCode"] = "0"
        content["resultMsg"] = "success"
        result_content = json.dumps(content)
        logger.info("new yinggu task success!")
        return result_content, status.HTTP_200_OK
    except Exception as e:
        content["isSuccess"] = False
        content["resultCode"] = "3"
        content["resultMsg"] = "系统错误，{}".format(e)
        logger.warning("new yinggu task failed, because: {}".format(content["resultMsg"]))
        result_content = json.dumps(content)
        return result_content, status.HTTP_500_INTERNAL_SERVER_ERROR


def generate_ai_store_token(args_dict):
    # get str
    k_v_list = list()
    for k in sorted(args_dict.keys()):
        k_v_list.append("{}={}".format(k, args_dict[k]))
    temp_str = "{}&{}".format("&".join(k_v_list), "SnxOmNGorsGPiaN")

    # get MD5
    news = str(temp_str).encode()
    m = hashlib.md5(news)
    return m.hexdigest()