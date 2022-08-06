#!/usr/bin/env python3
#########################################################################
# 本脚本用于FileCoin日常巡检，及时告警通知到企业微信。
# FilGuard致力于提供开箱即用的Fil挖矿技术解决方案
# 原作者「mje」：# WeChat：Mjy_Dream
# 企业微信接口作者：abelzhu, abelzhu@tencent.com
# 修改 esonbest
#########################################################################
import logging
from logging.handlers import RotatingFileHandler
import time
import traceback
import subprocess as sp
from weworkapi.Message import we_work_api


# Server酱SendKey
# 本fork 版本不再使用server 酱，直接使用文企业微信接口，需要sever酱的看原版本
# 脚本运行所在的机器类型
# lotus（一）、Seal-Miner（二）、Wining-Miner（三）、WindowPost-Miner（四）
# 现做出约定，直接填写一、二、三、四来表示对应的机器类型，可写入多个类型
check_machine = "二"
# 存储挂载路径「选填，在Seal-Miner、Wining-Miner、WindowPost-Miner上运行时需要填写，多个挂载目录使用'|'进行分隔」
# nfs 使用show mount 检测
# WindowPost—Miner日志路径「选填，在WindowPost-Miner上运行时需要填写」
wdpost_log_path = "/log/minerf01xxx.log"
# WiningPost-Miner日志路径「选填，在Wining-Miner上运行时需要填写」
winingpost_log_path = "/log/minerf01xxx.log"
# 节点号「选填」
fil_account = "f01843"
# 最长时间任务告警，如设置10，那么sealing jobs中最长的时间超过10小时就会告警「选填」
job_time_alert = 10
# mpool stuck alert
max_mpool_nonce = 3
# wallet_addr 需要检查余额的钱包地址
wallet_addr = "f3v4ar6bnjtbhxxxx"
# Default钱包余额告警阈值「选填，默认100」
default_wallet_balance = 100
# 巡检周期300秒，不建议设置太小。
check_interval = 300


# 日志配置，默认最大文件50M，数量2个，文件名alert.log 初始化的时候可以设置
# 日志已配置错误处理，无需捕捉具体错误原因，和写入详细错误内容。
# lotus和lotus-miner 如果不能正常运行，注意检查环境变量，或者在脚本中带环境变量运行

class MyLogger:
    def __init__(self, log_path="alert.log", max_size=50, back_count=2):
        self.log_path = log_path
        self.max_size = max_size
        self.back_count = max_size
        self.app_log = None
        self.config_logging()

    def config_logging(self):
        _log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        _my_handler = RotatingFileHandler(self.log_path, mode='a', maxBytes=self.max_size * 1024 * 1024,
                                          backupCount=self.back_count, encoding=None, delay=0)
        _my_handler.setFormatter(_log_formatter)
        _my_handler.setLevel(logging.INFO)
        self.app_log = logging.getLogger('root')
        self.app_log.setLevel(logging.INFO)
        self.app_log.addHandler(_my_handler)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def server_post(content='默认正文'):
    try:
        we_work_api.send_wework_message(content)
    except:
        app_log.error(str(traceback.format_exc()))


# 高度同步检查
def chain_check():
    try:
        out = sp.getoutput("timeout 36s lotus sync wait")
        app_log.info('chain_check:')
        app_log.info(out)
        if out.endswith('Done!'):
            app_log.info("chain check ok.")
            return True
        else:
            _err_message = "节点同步出错", "请及时排查！"
            app_log.warn(_err_message)
            server_post(_err_message)
            return False
    except Exception as e:
        app_log.error(str(traceback.format_exc()))
        return False


# 显卡驱动检查
def nvidia_check(check_type=''):
    out = sp.getoutput("timeout 15s echo $(nvidia-smi | grep GeForce)")
    app_log.info('nvidia_check:')
    app_log.info(out)
    if out.find("GeForce") >= 0:
        app_log.info("GPU check ok.")
    else:
        _err_message = "显卡故障，请及时排查！"
        app_log.warn(_err_message)
        server_post(_err_message)


# miner进程检查
def miner_process_check(check_type=''):
    out = sp.getoutput("timeout 30s echo $(pidof lotus-miner)")
    app_log.info('miner_process_check:')
    app_log.info(out)
    if out.strip():
        app_log.info("miner process check ok.")
    else:
        _err_message = "Miner进程丢失，请及时排查！"
        app_log.warn(_err_message)
        server_post(_err_message)


# lotus进程检查
def lotus_process_check():
    out = sp.getoutput("timeout 30s echo $(pidof lotus)")
    app_log.info('start lotus process_check:')
    app_log.info(out)
    if out.strip():
        app_log.info("lotus process check ok.")
    else:
        _err_message = "Lotus进程丢失，请及时排查！"
        app_log.warn(_err_message)
        server_post(_err_message)


# 消息堵塞检查
def mpool_check():
    out = sp.getoutput("lotus mpool pending --local |grep Nonce | wc -l")
    app_log.info('start mpool check:')
    app_log.info(out)
    if is_number(out):
        if int(out) < max_mpool_nonce:
            app_log.info("true")
        else:
            _err_message = "{}消息堵塞，请及时清理！".format(fil_account)
            app_log.warn(_err_message)
            server_post(_err_message)


# 存储文件挂载检查根据情况修改自己IP段和IP地址
def fm_check(check_type=''):
    storage_ip_list = ['204', '206', '207', '221', '222', '223', '224']
    for ip in storage_ip_list:
        ip = "192.168.1.{0}".format(ip)
        cmd = "timeout 5s showmount -e {0}".format(ip)
        out = sp.getoutput(cmd)
        app_log.info('存储检查: {0}'.format(ip))
        app_log.info(out)
        if "018xx" not in out.strip():
            _err_message = "{0}存储故障，请及时排查！".format(ip)
            app_log.warn(_err_message)
            server_post(_err_message)


# WindowPost—Miner日志报错检查
def wdpost_log_check():
    out = sp.getoutput("cat " + wdpost_log_path + "| grep 'running window post failed'")
    app_log.info('wdpost_log_check:')
    app_log.info(out)
    if not out.strip():
        app_log.info("wdpost check ok.")
    else:
        _err_message = "Wdpost报错，请及时处理！"
        app_log.warn(_err_message)
        server_post(_err_message)


# 在lotus中对Miner爆块进行检查,这里填上你自己要检测的账号,可以填写多个
def mined_block_check():
    account_list = [fil_account]
    chain_txt = sp.getoutput("lotus chain list --count {0}".format(int(check_interval/30)))
    for account in account_list:
        block_count = chain_txt.count(account)
        _message = '大吉大利，{},爆块{}个:'.format(account, block_count)
        app_log.info(_message)
        if int(block_count) > 0:
            server_post(_message)


# 任务超时检查
def overtime_check():
    global job_time_alert
    out = sp.getoutput("lotus-miner sealing jobs | awk '{ print $7}' | head -n 2 | tail -n 1")
    app_log.info('overtime_check:')
    app_log.info(out)
    if (out.find("Time") >= 0) or (not out.find('h') >= 0):
        app_log.info("sealing jobs overtime check ok")
        return True
    if out.strip() and int(out[0:out.find('h')]) <= job_time_alert:
        app_log.info(out[0:out.find("h")])
        app_log.info("sealing jobs overtime check ok.")
    else:
        _err_message = "封装任务超时，请及时处理！"
        app_log.warn(_err_message)
        server_post(_err_message)


# Default钱包余额预警
def balance_check():
    global default_wallet_balance
    out = sp.getoutput("lotus wallet balance {0}".format(wallet_addr))
    app_log.info('start balance check:')
    app_log.info(out)
    balance = out.split(' ')
    if is_number(balance[0]):
        if float(balance[0]) < default_wallet_balance:
            _err_message = "{}，钱包余额不足，请及时充值！".format(wallet_addr)
            app_log.warn(_err_message)
            server_post(_err_message)


def loop():
    while True:
        try:
            global check_machine
            global fil_account
            if not check_machine.strip():
                app_log.info("请填写巡检的机器类型！")
                break
            if check_machine.find('一') >= 0:
                lotus_process_check()
                if chain_check():
                    mined_block_check()
                    balance_check()
                    mpool_check()
            if check_machine.find('二') >= 0:
                miner_process_check("SealMiner")
                fm_check("SealMiner")
                overtime_check()
            if check_machine.find('三') >= 0:
                nvidia_check("WiningMiner")
                miner_process_check("WiningMiner")
                fm_check("WiningMiner")
            if check_machine.find('四') >= 0:
                nvidia_check("WindowPostMiner")
                miner_process_check("WindowPostMiner")
                fm_check("WindowPostMiner")
                wdpost_log_check()
            # sleep
            app_log.info("sleep 300 seconds\n")
            time.sleep(check_interval)
        except KeyboardInterrupt:
            exit(0)
        except:
            app_log.error(str(traceback.format_exc()))
            time.sleep(check_interval)


def main():
    loop()


if __name__ == "__main__":
    app_log = MyLogger().app_log
    main()
