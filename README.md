# Zhengfang-ics
这是一个将正方教务系统课表导出为 ics 日历格式的python小工具，通过模拟登录正方教务系统抓取课表网页转换的方式实现。
利用开源的zfnew包的代码并进行修改，在此感谢zfenw的开发者。

## 工具特性
- [x] 自动根据课程表信息生成ics  
- [x] ics中有授课老师课程时间地点考核方式等信息  
- [x] 适配apple 日历的精确地址  
- [x] 夏季冬季作息时间表自适应
## TODO
- [ ] 多样化的命令行选项
- [ ] 更加好用的异常处理


## 使用方法
1. python3 安装依赖
```bash
pip install -r requitement.txt
```
2. 配置

    2.1 把 `config.json` 和 `ics_exporter.py` 中的 `base_url` 修改为你所在学校教务系统的地址。

    2.2.  结合你所在学校的作息时间表 修改 `config.json` 中的 `TimesUp, TimesDown, TimesUp_sum, TimesDown_sum`。

    * 其中 `TimesUp` 为冬季作息的上课时间 ； `TimesDown` 为冬季作息的下课时间
    * 其中 `TimesUp_sum` 为夏季作息的上课时间 ； `TimesDown_sum` 为夏季作息的下课时间
    
    若作息时间表不分夏冬季 则两个时间都须设置为同一时间

    2.3. （可选）修改`config.json` 中的 `location` 可以按照此格式添加，若不添加则会不启用苹果设备内的位置提醒，若有位置提醒苹果会根据路程所需时间自动提醒通知。
    ```json
        "area1":{ 
            "aka" : "课程表内简称 area1",
            "name": "地址全称 area1",
            "location":"geo:31.567305,112.423548",
            "mapkit":""
        },
    ```
    2.4 执行 `python ./ics_exporter.py` 按指令操作，成功后会输出ics文件到文件夹下。