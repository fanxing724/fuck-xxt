# -*- coding: utf-8 -*-
"""
超星学习通自动刷课脚本 - 小白友好版
功能：自动完成视频、文档、阅读任务，章节测验需手动完成
"""
import argparse
import configparser
import random
import time
import sys
import os
import traceback
from urllib3 import disable_warnings, exceptions

from api.logger import logger
from api.base import Chaoxing, Account
from api.exceptions import LoginError, InputFormatError, MaxRollBackExceeded
from api.answer import Tiku
from api.notification import Notification

# 关闭SSL警告
disable_warnings(exceptions.InsecureRequestWarning)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="超星学习通自动刷课脚本",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-c", "--config", type=str, default="config.ini", 
        help="配置文件路径（默认config.ini）"
    )
    parser.add_argument("-u", "--username", type=str, default=None, help="手机号账号")
    parser.add_argument("-p", "--password", type=str, default=None, help="登录密码")
    parser.add_argument(
        "-l", "--list", type=str, default=None, 
        help="要学习的课程ID，多个用逗号分隔，如：123456,789012"
    )
    parser.add_argument(
        "-s", "--speed", type=float, default=2.0, 
        help="视频播放倍速（默认2倍速，最大2）"
    )
    parser.add_argument(
        "-v", "--verbose", "--debug", action="store_true",
        help="显示详细调试信息"
    )

    if len(sys.argv) == 2 and sys.argv[1] in {"-h", "--help"}:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()


def load_config(config_path):
    """从配置文件加载配置"""
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf8")
    
    common_config = {}
    tiku_config = {"DISABLE": True}  # 默认关闭题库功能
    notification_config = {}
    
    # 读取common节
    if config.has_section("common"):
        common_config = dict(config.items("common"))
        if "course_list" in common_config and common_config["course_list"]:
            common_config["course_list"] = common_config["course_list"].split(",")
        if "speed" in common_config:
            common_config["speed"] = float(common_config["speed"])
        # 默认跳过未开放章节，不重试
        if "notopen_action" not in common_config:
            common_config["notopen_action"] = "continue"
    
    # 读取tiku节（默认禁用）
    if config.has_section("tiku"):
        tiku_config = dict(config.items("tiku"))
        tiku_config["DISABLE"] = True  # 强制关闭自动答题
    
    # 读取notification节
    if config.has_section("notification"):
        notification_config = dict(config.items("notification"))
    
    return common_config, tiku_config, notification_config


def get_user_input():
    """获取用户输入"""
    print("\n" + "=" * 50)
    print("欢迎使用超星学习通自动刷课脚本")
    print("=" * 50)
    print("\n功能说明：")
    print("  ✓ 自动完成视频任务（支持2倍速）")
    print("  ✓ 自动完成文档任务")
    print("  ✓ 自动完成阅读任务")
    print("  ✗ 章节测验需要手动完成（安全起见）")
    print("\n" + "=" * 50)
    
    username = input("\n请输入你的手机号: ").strip()
    if not username:
        print("错误：手机号不能为空")
        sys.exit(1)
    
    password = input("请输入你的密码: ").strip()
    if not password:
        print("错误：密码不能为空")
        sys.exit(1)
    
    return username, password


class RollBackManager:
    """课程回滚管理器"""
    def __init__(self):
        self.rollback_times = 0
        self.rollback_id = ""

    def add_times(self, id: str):
        """增加回滚次数"""
        if id == self.rollback_id and self.rollback_times >= 3:
            raise MaxRollBackExceeded("回滚次数已达3次，请手动检查任务点完成情况")
        else:
            self.rollback_times += 1

    def new_job(self, id: str):
        """设置新任务，重置回滚次数"""
        if id != self.rollback_id:
            self.rollback_id = id
            self.rollback_times = 0


def init_chaoxing(username, password):
    """初始化超星实例"""
    account = Account(username, password)
    
    # 创建禁用的题库实例（不启用自动答题）
    tiku = Tiku()
    tiku.DISABLE = True
    
    chaoxing = Chaoxing(account=account, tiku=tiku)
    return chaoxing


def process_job(chaoxing, course, job, job_info, speed):
    """处理单个任务点"""
    if job["type"] == "video":
        logger.info(f"[视频] {course['title']} - {job.get('name', '未知视频')}")
        # 先尝试视频
        result = chaoxing.study_video(course, job, job_info, _speed=speed, _type="Video")
        if chaoxing.StudyResult.is_failure(result):
            logger.info("不是视频任务，尝试音频任务...")
            result = chaoxing.study_video(course, job, job_info, _speed=speed, _type="Audio")
        if chaoxing.StudyResult.is_failure(result):
            logger.warning(f"任务异常，已跳过: {job['jobid']}")
            
    elif job["type"] == "document":
        logger.info(f"[文档] {course['title']} - {job.get('name', '未知文档')}")
        chaoxing.study_document(course, job)
        
    elif job["type"] == "workid":
        logger.info(f"[测验] {course['title']} - 需要手动完成")
        logger.info("  ⚠️  章节测验需手动完成，已跳过")
        
    elif job["type"] == "read":
        logger.info(f"[阅读] {course['title']} - {job.get('name', '未知阅读')}")
        chaoxing.strdy_read(course, job, job_info)


def process_chapter(chaoxing, course, point, RB, speed):
    """处理单个章节"""
    logger.info(f"\n{'='*50}")
    logger.info(f"当前章节: {point['title']}")
    logger.info(f"{'='*50}")
    
    if point["has_finished"]:
        logger.info("该章节已完成，跳过")
        return 1
    
    # 随机等待1-3秒，避免请求过快
    sleep_time = random.uniform(1, 3)
    logger.debug(f"等待 {sleep_time:.1f} 秒...")
    time.sleep(sleep_time)
    
    # 获取章节任务列表
    jobs, job_info = chaoxing.get_job_list(
        course["clazzId"], course["courseId"], course["cpi"], point["id"]
    )
    
    # 处理未开放章节
    if job_info.get("notOpen", False):
        logger.info(f"章节未开放，跳过: {point['title']}")
        return 1
    
    RB.new_job(point["id"])
    chaoxing.rollback_times = RB.rollback_times
    
    # 空章节处理
    if not jobs:
        if RB.rollback_times > 0:
            chaoxing.study_emptypage(course, point)
        return 1
    
    # 处理所有任务点
    for job in jobs:
        process_job(chaoxing, course, job, job_info, speed)
    
    return 1


def process_course(chaoxing, course, speed):
    """处理单个课程"""
    logger.info(f"\n{'#'*60}")
    logger.info(f"开始学习: {course['title']}")
    logger.info(f"{'#'*60}")
    
    point_list = chaoxing.get_course_point(
        course["courseId"], course["clazzId"], course["cpi"]
    )
    
    index = 0
    RB = RollBackManager()
    
    while index < len(point_list["points"]):
        point = point_list["points"][index]
        result = process_chapter(chaoxing, course, point, RB, speed)
        
        if result == -1:  # 出错退出
            break
        index += 1


def select_courses(all_courses, course_ids=None):
    """选择要学习的课程"""
    if not course_ids:
        print("\n" + "*" * 50)
        print("你的课程列表：")
        print("*" * 50)
        for i, course in enumerate(all_courses, 1):
            print(f"  {i}. ID: {course['courseId']}  课程: {course['title']}")
        print("*" * 50)
        
        choice = input("\n请输入要学习的课程编号（多个用逗号分隔，留空学习全部）: ").strip()
        if not choice:
            return all_courses
        
        try:
            selected_indices = [int(x.strip()) - 1 for x in choice.split(",")]
            return [all_courses[i] for i in selected_indices if 0 <= i < len(all_courses)]
        except Exception as e:
            logger.error(f"输入格式错误: {e}")
            return all_courses
    
    # 根据ID筛选
    return [c for c in all_courses if c["courseId"] in course_ids]


def main():
    """主程序"""
    try:
        # 解析参数
        args = parse_args()
        
        # 加载配置
        config_file = args.config if os.path.exists(args.config) else None
        if config_file:
            common_config, tiku_config, notification_config = load_config(config_file)
            username = common_config.get("username", "")
            password = common_config.get("password", "")
            course_list = common_config.get("course_list")
            speed = common_config.get("speed", args.speed)
        else:
            username, password = get_user_input()
            course_list = args.list.split(",") if args.list else None
            speed = args.speed
        
        # 规范化速度
        speed = min(2.0, max(1.0, speed))
        
        # 初始化
        chaoxing = init_chaoxing(username, password)
        
        # 登录
        logger.info("正在登录...")
        login_result = chaoxing.login()
        if not login_result["status"]:
            logger.error(f"登录失败: {login_result['msg']}")
            sys.exit(1)
        logger.info("登录成功！")
        
        # 获取课程列表
        all_courses = chaoxing.get_course_list()
        logger.info(f"共找到 {len(all_courses)} 门课程")
        
        # 选择课程
        courses = select_courses(all_courses, course_list)
        logger.info(f"本次将学习 {len(courses)} 门课程")
        
        # 开始学习
        for course in courses:
            process_course(chaoxing, course, speed)
        
        logger.info("\n" + "=" * 50)
        logger.info("所有课程学习任务已完成！")
        logger.info("=" * 50)
        
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
    except Exception as e:
        logger.error(f"错误: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
