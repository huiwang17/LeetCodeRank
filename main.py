import json
import os
from datetime import datetime, time, timedelta

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
    def __init__(self, nickname, username, region="com", key="", last_solved=0, last_submissions=0):
        self.nickname = nickname
        self.username = username
        self.region = region
        self.key = key
        self.last_solve = last_solved
        self.last_submissions = last_submissions
        self.homepage = f"https://leetcode.com/{username}" if region == "com" else f"https://leetcode-cn.com/u/{username}/"
        self.stat = {"All": 0, "totalSubmissions": 0}
        self.solved_increase = 0
        self.submissions_increase = 0

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
        self.submissions_increase = total - self.last_solve
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
        self.solved_increase = self.stat["All"] - self.last_solve

    def calendar_submission(self):
        payload = {
            "query": "\n    query userProfileCalendar($username: String!, $year: Int) {\n  matchedUser(username: $username) {\n    userCalendar(year: $year) {\n      activeYears\n      streak\n      totalActiveDays\n      dccBadges {\n        timestamp\n        badge {\n          name\n          icon\n        }\n      }\n      submissionCalendar\n    }\n  }\n}\n    ",
            "variables": {
                "username": f"{self.username}",
            },
            "operationName": "userProfileCalendar"
        }
        query_url = "https://leetcode.com/graphql/"
        res = requests.post(url=query_url, json=payload)
        if res.status_code != 200:
            print(res.text)
            raise Exception("count error: status code != 200")
        try:
            data_str = res.json()["data"]["matchedUser"]["userCalendar"]["submissionCalendar"]
            data_js = json.loads(data_str)
        except TypeError as e:
            print(res.text)
            raise "error getting calendar submissions: " + e
        total = 0
        for k, v in data_js.items():
            total += v
        self.stat["totalSubmissions"] = total
        self.submissions_increase = total - self.last_submissions

    def to_json(self):
        return {
            "nickname": self.nickname,
            "username": self.username,
            "region": self.region,
            "key": self.key,
            "stat": self.stat,
            "last_fetch": self.last_fetch
        }


users = []

with open('accounts.csv', newline='\n') as csv_file:
    account_reader = csv.reader(csv_file, delimiter=',')
    for row in account_reader:
        nickname = row[0]
        region = row[1]
        username = row[2]
        solved = int(row[3])
        submissions = int(row[4])

        user = Account(nickname, username, region, "", solved, submissions)
        users.append(user)

# update
for u in users:
    print(u.nickname)
    u.count()
    u.calendar_submission()


users.sort(key=lambda x: x.stat["totalSubmissions"], reverse=True)

# send message
title = f"@所有人 扪心自问，今天刷题了吗？追上{users[0].nickname}了吗？没有的话还不去刷？？？\r\r"
msg = f"全群以{users[0].nickname}为目标!!!\r\r"
for u in users:
    msg += f"{u.nickname} submitted:{u.stat['totalSubmissions']}(+{u.submissions_increase})| solved: {u.stat['All']}(+{u.submissions_increase}) {u.homepage}\r\r "


print(title)
print(msg)
push_message("SCT143349TuFttN15c2QWOBLvpjdHkYWVw", title, msg)




# 获取文件上次修改时间
modified_time = datetime.fromtimestamp(os.path.getmtime('accounts.csv'))
print("Last modified: %s" % modified_time)

# 获取当前时间
now = datetime.now()

# 计算上次修改时间到现在的时间差
time_diff = now - modified_time

# 如果时间差大于7天，则删除文件
if time_diff > timedelta(days=7):
    print("Updating file: accounts.csv")

    # dump the data to the csv file
    with open('accounts_2.csv', 'w', newline='\n') as csv_file:
        account_writer = csv.writer(csv_file, delimiter=',')
        for u in users:
            account_writer.writerow([u.nickname, u.region, u.username, u.stat["All"], u.stat["totalSubmissions"]])
    os.rename('accounts_2.csv', 'accounts.csv')



