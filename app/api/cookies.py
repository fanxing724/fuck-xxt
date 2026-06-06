# -*- coding: utf-8 -*-
import os.path
import pickle
from api.config import GlobalConst as gc


def save_cookies(_session):
    """保存Cookies"""
    with open(gc.COOKIES_PATH, "wb") as f:
        pickle.dump(_session.cookies, f)


def use_cookies():
    """使用Cookies，如果文件不存在返回空字典"""
    if os.path.exists(gc.COOKIES_PATH):
        try:
            with open(gc.COOKIES_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            return {}
    return {}
