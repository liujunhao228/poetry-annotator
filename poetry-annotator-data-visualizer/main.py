#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
诗词与标注数据可视化分析平台 - Web 应用入口

启动方式:
    streamlit run main.py

或者使用项目脚本:
    poetry-visualizer
"""
from data_visualizer.app.main_app import run_app

if __name__ == "__main__":
    run_app()
