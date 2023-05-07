#!/bin/env python3
#-*-coding:utf-8-*-
import datetime
import json
import os
import re
import sys
import time
from getpass import getpass
from random import sample

import pytz
import requests
from icalendar import *

from zfnew import *

base_url = '' #请结合实际情况自行修改

uid_generate = lambda: "-".join(map(lambda l: ''.join(sample("0123456789ABCDEF", l)), [8, 4, 4, 4, 12]))

global debug

debug = 0

def time_it(func):
    def inner():
        start = time.time()
        func()
        end = time.time()
        print('用时:{}秒'.format(end-start))
    return inner

with open('config.json', 'r' , encoding='utf-8') as f:
    config = json.loads(f.read())

def GetCourseInfoFromFile(filename):
    """从文件中导入课表数据"""
    try:
        file = open(filename, mode='r',encoding='utf-8')
    except:
        print("Error: Unable to open file: ", filename)
        exit(1)
    a = file.read()
    b = json.loads(a)
    file.close()
    print("Successfully read file: ", filename)
    return b

# 返回上课的周的区间
def GetCourseTakeWeeks(week_num):
    if '-' in week_num: # A-B周区间内上课
        weekstart = int(week_num[0:week_num.find('-')])
        weekend = int(week_num[week_num.find('-')+1:week_num.find('周')])
    else: # 仅A周上课
        weekstart = weekend = int(week_num[0:week_num.find('周')])
    return weekstart, weekend

def GetCourseDate(year, semester, week, course_in_day_of_week):
    """根据学期和周数返回这节课所在的天数"""
    if semester == 1:
        start = datetime.datetime(year, 8, 30, 0) #2021.8.30.00
    else:
        start = datetime.datetime(year, 2, 13, 0) #2021.3.1.00
    for i in range(7):
        if start.weekday() == 0: # if the start day is monday
            break
        else:
            start = start + datetime.timedelta(days=1)
    time = start + datetime.timedelta(days=(week-1) * 7 + (course_in_day_of_week-1))
    return time

def CreateEventTimePart(event, course_date, course_begin_time, course_end_time, time_zone):
    """创建事件（时间部分）"""
    event.add('dtstart',datetime.datetime(course_date.year,
        course_date.month, course_date.day, course_begin_time.hour, 
        course_begin_time.minute, course_begin_time.second, tzinfo=time_zone))
    event.add('dtend', datetime.datetime(course_date.year,
        course_date.month, course_date.day, course_end_time.hour,
        course_end_time.minute, course_begin_time.second, tzinfo=time_zone))
    event.add('dtstamp', datetime.datetime(course_date.year,
        course_date.month, course_date.day, course_begin_time.hour, 
        course_begin_time.minute, course_begin_time.second, tzinfo=time_zone))
    

def HandleLocation(event, courseRoom, config):
    """创建上课地点位置信息"""
    locations = config['location']
    for location in locations:
        if locations[location]['aka'] in courseRoom:
            event.add('location', locations[location]['name'])
            event.add('X-APPLE-STRUCTURED-LOCATION',locations[location]['location'], 
                parameters={
                    'VALUE': 'URI', 'X-ADDRESS': locations[location]['name'],'X-APPLE-RADIUS':'300',
                    'X-APPLE-REFERENCEFRAME':'2','X-TITLE':locations[location]['name']})
            

def CreateEvent(calendar, year, semester, a):
    """创建事件"""
    time_zone = pytz.timezone('Asia/Shanghai')
    course_in_day_of_week = int(a['courseWeekday']) # 星期几
    course_begin_time = datetime.datetime.strptime(GetInfo.upTime(re.findall(r"(\d+)", a['courseSection'])),'%H:%M') # 上课时间转化为 datetime 对象
    course_end_time = datetime.datetime.strptime(GetInfo.downTime(re.findall(r"(\d+)", a['courseSection'])),'%H:%M')
    course_begin_time_sum = datetime.datetime.strptime(GetInfo.upTime_sum(re.findall(r"(\d+)", a['courseSection'])),'%H:%M')
    course_end_time_sum = datetime.datetime.strptime(GetInfo.downTime_sum(re.findall(r"(\d+)", a['courseSection'])),'%H:%M')    
    #course_begin_time, course_end_time = GetCourseTime(a['courseSection'])

    for week in a['includeWeeks']:
        course_date = GetCourseDate(year, semester, week, course_in_day_of_week)
        event = Event()
        courseRoom = a['courseRoom']
        event.add('summary', a['courseTitle'] +'\n'+courseRoom)

        if (5 <= course_date.month <= 9 ):  #夏季作息时间课表日程生成
            CreateEventTimePart(event, course_date, course_begin_time_sum,
                                course_end_time_sum, time_zone)

        else :  #冬季作息时间课表日程生成
            CreateEventTimePart(event, course_date, course_begin_time,
                                course_end_time, time_zone)

        event.add('description', "({}) 周数: {}, 课程类别: {}, 教师: {}, 教学班: {},学分 {} ,考核方式: {}, 选课备注: {}, 课程学时组成: {}".format(
            a['courseSection'], a['courseWeek'], a['courseCategory'], a['teacher'], a['className'], a['credit'], a['exam'], a['SelectionNotes'], a['hoursComposition']))

        HandleLocation(event, courseRoom, config)
        
        """添加课程上课提醒"""
        alarm = Alarm()
        alarm.add('action', 'display')
        alarm.add('DESCRIPTION', '上课提醒')
        #alert_time = timedelta(minutes=-int(30))
        alarm.add('trigger', '-P0DT0H30M0S', encode=0) #提前30 min
        event.add('UID', uid_generate())
        event.add_component(alarm)
        calendar.add_component(event)
        
    return calendar

def ConvertCalendar(course_dict, semester):
    """创建日历 """
    calendar = Calendar()
    vtimezone= Timezone()
    vtimezone.add('TZID', 'Asia/Shanghai')
    time_zone = pytz.timezone('Asia/Shanghai')
    calendar.add_component(vtimezone)
    calendar.add('prodid', '-//zhengfang-jwgl ics Exporter//syc@nbsyc.com//')
    studentName = course_dict['name']
    yearName = course_dict['yearName']
    calendar.add('X-WR-CALNAME','{} 学年度 第{}学期 {}的课表'.format(yearName, str(semester), studentName))
    calendar.add('X-APPLE-CALENDAR-COLOR','#63da38')
    calendar.add('X-WR-TIMEZONE','Asia/Shanghai')
    calendar.add('version', '2.0')
    calendar.add('CALSCALE','GREGORIAN')
    # year = int(course_dict['xsxx']['XNM'])
    yearname = course_dict['yearName'].split('-')
    if semester == 2:
        year = int(yearname[1])
    else:
        year = int(yearname[0])
    #创建周数显示事件
    for w in range(1, 20):
        week_date = GetCourseDate(year, semester, w, 1)
        event_week = Event()
        event_week.add('summary', '第{}周'.format(w))
        event_week.add('dtstart',datetime.datetime(week_date.year,
            week_date.month, week_date.day, 6, 0, 0, tzinfo=time_zone))
        event_week.add('dtend', datetime.datetime(week_date.year,
            week_date.month, week_date.day, 7, 0, 0, tzinfo=time_zone))
        event_week.add('UID',uid_generate())
        calendar.add_component(event_week)
    for num in course_dict['normalCourse']: # 创建课程事件
        a = num
        week_string_list = a['courseWeek'].split(',') # 
        calendar = CreateEvent(calendar,  year, semester, a)   

    """输出课程表文件"""
    output_file_name = '{}({}-{}).ics'.format(course_dict['studentId'], 
        course_dict['yearName'], course_dict['schoolTerm'])
    output_file0 = calendar.to_ical()
    output_file1 = eval(repr(output_file0).replace('\\\\,', ','))
    output_file2 = eval(repr(output_file1).replace("\\\'",""))
    output_file = open(output_file_name, 'wb')
    output_file.write(output_file2)
    output_file.close()
    print('Successfully write your calendar to', output_file_name)

def ShowHelp():
    print("Usage:\npython3 ./ics_exporter.py [option]")
    print("\nOptions:")
    print("     -f, --file [Directory]\tImport course data from file.")
    print("     -v, --verstion\t\tShow version.")
    print("     -h, --help\t\t\tShow this help.")

def main():
    print('--------------欢迎使用 Zhengfangics导出工具--------------')

    global cookie, filename

    now = datetime.datetime.now()
    
    if now.month >= 1 and now.month <= 6:  # 自动决定当前学期
        year = now.year - 1
        semester = 2
    else:
        year = now.year
        semester = 1

    for i in range(1, len(sys.argv)):
        start = time.time()
        if sys.argv[i] == '-f' or sys.argv[i] == '--file':
            cookies = ''

            if i+1 < len(sys.argv):
                filename = sys.argv[i+1]

            elif filename == "":
                ShowHelp()
                exit(1)

            person = GetInfo(base_url=base_url, cookies=cookies)
            course_dict = GetCourseInfoFromFile(filename)
            course_json = json.dumps(course_dict)
            course_json = person.covert_schedule(course_json)
            ConvertCalendar(course_json,semester)
            print(time.time()-start)
            exit(0)

        elif sys.argv[i] == '-v' or sys.argv[i] == '--version':
            print("Version: 1.1 - 2023.5.1")
            print("by: sdy623")
            exit(0)

        elif sys.argv[i] == '-h' or sys.argv[i] == '--help':
            ShowHelp()
            exit(0)

    if len(sys.argv) == 1:
        stuNumber = input("请输入教务系统用户名: ")
        pswd = getpass("请输入教务系统密码: ")
        start = time.time()
        #long running
        #do something other


        lgn = Login(base_url=base_url)
        lgn.normal_login(stuNumber, pswd) # 一般登录，密码明文传输

        cookies = lgn.cookies  # cookiejar类cookies获取方法
        person = GetInfo(base_url=base_url, cookies=cookies)

        try:
            course_dict = person.get_schedule(year, str(semester))
        except json.decoder.JSONDecodeError :
                    print ('用户名或密码错误') 
                    main()
                    
        os.system("pause")
        exit(0)


    ShowHelp()

if __name__ == '__main__':
    main()
