### 本脚本用于FileCoin日常巡检，及时告警通知到企业微信。
### FilGuard致力于提供开箱即用的Fil挖矿技术解决方案
### 脚本原作者「mje」：WeChat：Mjy_Dream
### 此版本根据需要由 WeChat: esonbest进行修改，增加Logger功能，企业微信官方接口功能。
企业微信接口作者：abelzhu, abelzhu@tencent.com
注意，企业微信配置ApiConf.py 文件中有说明
另外注意在企业微信中授权服务器IP。
默认消息接收人是应用的所有人，可以根据自己需要修改 Message.py
也可以新建一个config.py 进行个性化配置。
测试的时候可以打开debug开关。
AbstractApi.py 中 设置 debug = True.
