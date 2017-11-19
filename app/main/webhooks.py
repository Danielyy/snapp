import requests
import json
import urllib.parse

# 客服组（部门）
client_service_small = 'https://oapi.dingtalk.com/robot/send?access_token=2d33cbba037c363dd50fc107b960e1dade33e0838e8a4df86b857325150cb086'

HEADERS = {
    "Content-Type": "application/json; charset=utf-8"
}


def SNSendDing(user_account, activity, series_number):
    textmsg = {
        "msgtype": "text",
        "text": {
            "content": '{0} 用户已成功领取{1}序列号： {2} '.format(user_account, activity, series_number)
        }
    }
    # SendTextMsg = json.dumps(TextMsg)
    requests.post(url=client_service_small, data=json.dumps(textmsg), headers=HEADERS)
    # res = requests.post(url=url, data=SendTextMsg, headers=HEADERS)
    # print(res.text)
    return