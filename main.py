import requests
import urllib.parse
import csv


def push_message(server_bot_key, title, content):
    push_url = f"http://sctapi.ftqq.com/{server_bot_key}.send/"
    params = {"title": title, "desp": content.encode("utf-8")}
    res = requests.post(url=push_url, params=params)
    status_code = res.status_code
    if status_code != 200:
        print(res.text)
        raise Exception("push message error: status code != 200")
    # "data": {
    #     "pushid": "58656802",
    #     "readkey": "SCTPFTOWwwItUyM",
    #     "error": "SUCCESS",
    #     "errno": 0
    #   }
    push_id = res.json()["data"]["pushid"]
    return push_id


class Account:
    def __init__(self, nickname, username, region="com", key=""):
        self.nickname = nickname
        self.username = username
        self.region = region
        self.key = key
        self.homepage = f"https://leetcode.com/{username}" if region == "com" else f"https://leetcode-cn.com/u/{username}/"
        self.stat = {"All": 0}

    def count_cn(self):
        query_url = "https://leetcode-cn.com/graphql/"
        payload = {"query":"\n    query userQuestionProgress($userSlug: String!) {\n  userProfileUserQuestionProgress(userSlug: $userSlug) {\n    numAcceptedQuestions {\n      difficulty\n      count\n    }\n    numFailedQuestions {\n      difficulty\n      count\n    }\n    numUntouchedQuestions {\n      difficulty\n      count\n    }\n  }\n}\n    ","variables":{"userSlug": f"{self.username}"}}
        res = requests.post(url=query_url, json=payload)
        if res.status_code != 200:
            print(res.text)
            raise Exception("count error: status code != 200")
        data = res.json()["data"]["userProfileUserQuestionProgress"]["numAcceptedQuestions"]
        total = 0
        for item in data:
            level = item["difficulty"]
            num = item["count"]
            total += num
            self.stat[level] = num
        self.stat["All"] = total
        # print(self.stat)

    def count(self):
        if self.region == "cn":
            self.count_cn()
            return
        query_url = "https://leetcode.com/graphql/"
        payload = {
            "query": "\n    query userProblemsSolved($username: String!) {\n  allQuestionsCount {\n    difficulty\n    count\n  }\n  matchedUser(username: $username) {\n    problemsSolvedBeatsStats {\n      difficulty\n      percentage\n    }\n    submitStatsGlobal {\n      acSubmissionNum {\n        difficulty\n        count\n      }\n    }\n  }\n}\n    ",
            "variables": {"username": f"{self.username}"}}
        # print(payload)
        res = requests.post(url=query_url, json=payload)
        if res.status_code != 200:
            print(res.text)
            raise Exception("count error: status code != 200")
        data = res.json()["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
        for item in data:
            level = item["difficulty"]
            num = item["count"]
            self.stat[level] = num


users = []

with open('accounts.csv', newline='\n') as csv_file:
    account_reader = csv.reader(csv_file, delimiter=',')
    for row in account_reader:
        nickname = row[0]
        region = row[1]
        username = row[2]
        user = Account(nickname, username, region)
        users.append(user)

# update
for u in users:
    u.count()

users.sort(key=lambda x: x.stat["All"], reverse=True)

# send message
title = f"@所有人 扪心自问，今天刷题了吗？追上{users[0].nickname}了吗？没有的话还不去刷？？？\r\r"
msg = f"全群以{users[0].nickname}为目标!!!\r\r"


for u in users:
    msg += f"{u.nickname} ({u.stat['All']}) {u.homepage}\r\r"

print(title)
print(msg)
push_message("SCT143349TuFttN15c2QWOBLvpjdHkYWVw", title, msg)

