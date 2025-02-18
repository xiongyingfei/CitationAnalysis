# 论文引用自动分析工具

## 介绍

本项目旨在自动化地下载引文并从引文中提取引用并判断其评价的好坏，目前实现的功能包括：

* 从Google Scholar下载引用页并提取引文下载链接
* 用SemanticScholar补充更多信息
* 适配多个网站自动下载引文
* 提取引文中的引用片段
* 提交引用片段给大模型，判断是否是好评

## 运行环境
Python 3.8以上，安装以下库
    requests
    selenium
    requests_cache
    fuzzywuzzy
    jsonschema
    Levenshtein
    pymupdf
    tools
    beautifulsoup4
    openai

## 使用方法
1. 将config_example.py重命名为config.py，选择合适的大模型配置，修改model变量的赋值，并对应配置中填入自己的API Key。
   * 千问的返回结果有时会不符合格式，DeepSeek效果更好
2. 仿照AAAI20目录，为自己的论文创建目录，并添加info.json文件
   1. ScholarID表示Google Scholar引用页面URL中的数字ID
   2. ApproachName表示论文方法的名字，用于查找引用
3. 修改config.py，将paper_download_id设置成论文目录的名字
4. 执行paper_downloader.py，下载引文
5. 修改config.py，将citation_analysis_id设置成论文目录的名字
6. 执行citation_analysis.py，提取引文文本并分析。分析结果保存在all_snippets.txt中。
