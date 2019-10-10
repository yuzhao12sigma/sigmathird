#!/usr/bin/env python
# -*- coding:utf-8 -*-

import hashlib
import logging
import time
import hmac
import base64
import requests
import uuid
import os
import config


SELF_DEFINE_HEADER_PREFIX = "x-sigma-"
SELF_DEFINE_AUTH_PREFIX = "12Sigma"
work_path = config.fetch("work_path")


def get_temp_store_dir():
    workspace = work_path
    uid = uuid.uuid1().hex
    upload_dir = os.path.join(os.path.join(workspace, "upload"), uid)
    return upload_dir


def get_file_md5_digest(pathname, block=64 * 1024):
    """Calculate md5 hexdigest of content."""
    with open(pathname, "rb") as stream:
        md5 = hashlib.md5()
        while True:
            data = stream.read(block)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def path_split(filename):
    """Split filename and get dirname and basename."""
    _filename = "/" + filename if filename[0] != "/" else filename
    items = _filename.split("/")
    dirname = "/"
    if len(items[:-1]) != 1:
        dirname = "/".join(items[:-1])
    basename = items[-1]
    return dirname, basename


def convert_utf8(input_string):
    if isinstance(input_string, unicode):
        input_string = input_string.encode('utf-8')
    return input_string


def extract_resource_from_url(url):
    if url.lower().startswith("http://"):
        idx = url.find('/', 7, -1)
        return url[idx:].strip()
    elif url.lower().startswith("https://"):
        idx = url.find('/', 8, -1)
        return url[idx:].strip()
    else:
        return url.strip()


def format_header(headers=None):
    """
    format the headers that self define
    convert the self define headers to lower.
    """
    if not headers:
        headers = {}
    tmp_headers = {}

    for k in headers.keys():
        tmp_str = headers[k]
        if isinstance(tmp_str, unicode):
            tmp_str = convert_utf8(tmp_str)

        if k.lower().startswith(SELF_DEFINE_HEADER_PREFIX):
            k_lower = k.lower().strip()
            tmp_headers[k_lower] = tmp_str
        else:
            tmp_headers[k.strip()] = tmp_str
    return tmp_headers


def canonicalize_resource(resource):
    res_list = resource.split("?")
    if len(res_list) <= 1 or len(res_list) > 2:
        return resource
    res = res_list[0]
    param = res_list[1]
    params = param.split("&")
    params = sorted(params)
    param = '&'.join(params)
    return res + '?' + param


class SigmaAuth(requests.auth.AuthBase):
    def __init__(self, access_key_id, access_key_secret, verbose=True):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.verbose = verbose
        if verbose:
            self.logger = logging.getLogger("auth")
            self.logger.debug("Initialize SigmaAuth, access key id: " + access_key_id +
                              ", access key secret: " + access_key_secret)

    def __call__(self, r):
        method = r.method
        content_type = r.headers.get('Content-Type', '')
        content_md5 = r.headers.get('Content-MD5', '')
        canonicalized_gd_headers = ""
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        resource = extract_resource_from_url(r.url)

        tmp_headers = format_header(r.headers)
        if len(tmp_headers) > 0:
            x_header_list = tmp_headers.keys()
            x_header_list.sort()
            for k in x_header_list:
                if k.startswith(SELF_DEFINE_HEADER_PREFIX):
                    canonicalized_gd_headers += "%s:%s\n" % (k, tmp_headers[k])

        canonicalized_resource = canonicalize_resource(resource)
        if self.verbose:
            self.logger.debug("Canonicalized resource: " + canonicalized_resource)

        string_to_sign = method + "\n" + content_md5 + "\n" + content_type + "\n" + date + "\n" + canonicalized_gd_headers + canonicalized_resource
        if self.verbose:
            self.logger.debug("String to Sign: " + string_to_sign)

        h = hmac.new(self.access_key_secret.encode('utf-8'), string_to_sign, hashlib.sha256)
        signature = base64.encodestring(h.digest()).strip()

        r.headers["Date"] = date
        r.headers["Authorization"] = SELF_DEFINE_AUTH_PREFIX + " " + self.access_key_id + ":" + signature
        if self.verbose:
            self.logger.info("Authorization header: " + r.headers["Authorization"])

        return r
