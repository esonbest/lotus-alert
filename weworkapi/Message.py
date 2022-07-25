#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
# Copyright (C) 2018 All rights reserved.
#   
# @File UserTest.py
# @Brief 
# @Author abelzhu, abelzhu@tencent.com
# @Version 1.0
# @Date 2018-02-24
#
#

import sys

sys.path.append("./weworkapi/")
import random
from CorpApi import *
from ApiConf import *


class WeWorkApi(object):
    def __init__(self):
        self.api = CorpApi(ApiConf['CORP_ID'], ApiConf['APP_SECRET'])

    def send_wework_message(self, _message):

        try:
            ##
            response = self.api.httpCall(
                CORP_API_TYPE['MESSAGE_SEND'],
                {
                    "touser": "@all",
                    "agentid": ApiConf["APP_ID"],
                    'msgtype': 'text',
                    'climsgid': 'climsgidclimsgid_%f' % (random.random()),
                    'text': {
                        'content': '{0}'.format(_message),
                    },
                    'safe': 0,
                })
        except ApiException as e:
            print(e.errCode, e.errMsg)


we_work_api = WeWorkApi()
