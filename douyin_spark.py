#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音自动续火花脚本 - GitHub Actions 云端版
基于 Playwright 模拟浏览器操作
"""

import os
import sys
import json
import random
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("错误：请先安装 playwright")
    print("运行: pip install playwright && playwright install chromium")
    sys.exit(1)


# 随机消息列表（如果没指定固定消息，就从这里随机选）
RANDOM_MESSAGES = [
    "早上好呀～",
    "今天也要开心哦",
    "在干嘛呢",
    "记得吃饭",
    "天气变凉了，注意保暖",
    "想你了",
    "今天过得怎么样",
    "晚安好梦",
    "加油呀",
    "嘿嘿",
]


def log(msg):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def random_sleep(min_sec=1, max_sec=3):
    """随机等待，模拟人类操作"""
    time.sleep(random.uniform(min_sec, max_sec))


def parse_cookie_string(cookie_str):
    """
    解析 Cookie 字符串为 Playwright 需要的格式
    """
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".douyin.com",
                "path": "/",
            })
    return cookies


def send_spark(cookie_str, sec_uid, message=None):
    """给指定好友发送消息续火花"""
    if message is None:
        message = random.choice(RANDOM_MESSAGES)
    
    log(f"准备发送消息给 sec_uid={sec_uid}")
    log(f"消息内容: {message}")
    
    cookies = parse_cookie_string(cookie_str)
    log(f"解析到 {len(cookies)} 个 Cookie")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        
        context.add_cookies(cookies)
        log("Cookie 已设置")
        
        page = context.new_page()
        
        # 隐藏 webdriver 特征
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            window.chrome = { runtime: {} };
        """)
        
        try:
            log("正在打开抖音网页版...")
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=30000)
            random_sleep(2, 4)
            
            page_title = page.title()
            log(f"页面标题: {page_title}")
            
            chat_url = f"https://www.douyin.com/user/{sec_uid}"
            log(f"正在打开好友主页: {chat_url}")
            page.goto(chat_url, wait_until="domcontentloaded", timeout=30000)
            random_sleep(3, 5)
            
            log("查找私信按钮...")
            selectors = [
                'text="私信"',
                '[data-e2e="user-info-message"]',
                'button:has-text("私信")',
                '.message-button',
                'a[href*="message"]',
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    elem = page.query_selector(selector)
                    if elem:
                        log(f"找到私信按钮，选择器: {selector}")
                        elem.click()
                        clicked = True
                        break
                except Exception as e:
                    log(f"选择器 {selector} 失败: {e}")
                    continue
            
            if not clicked:
                log("未找到私信按钮，尝试直接进入消息页面...")
                page.goto("https://www.douyin.com/message", wait_until="domcontentloaded", timeout=30000)
                random_sleep(3, 5)
            
            random_sleep(2, 4)
            
            log("查找聊天输入框...")
            input_selectors = [
                'textarea[placeholder*="发送"]',
                'textarea[placeholder*="输入"]',
                'div[contenteditable="true"]',
                '[data-e2e="message-input"]',
                '.chat-input textarea',
            ]
            
            input_elem = None
            for selector in input_selectors:
                try:
                    input_elem = page.query_selector(selector)
                    if input_elem:
                        log(f"找到输入框，选择器: {selector}")
                        break
                except Exception:
                    continue
            
            if not input_elem:
                screenshot_path = os.path.join(os.path.dirname(__file__), "debug_screenshot.png")
                page.screenshot(path=screenshot_path, full_page=True)
                log(f"未找到输入框，已保存截图到: {screenshot_path}")
                raise Exception("未找到聊天输入框，可能页面结构已变化")
            
            input_elem.click()
            random_sleep(0.5, 1.5)
            
            log(f"输入消息: {message}")
            for char in message:
                input_elem.type(char, delay=random.randint(50, 150))
            random_sleep(0.5, 1.5)
            
            log("发送消息...")
            input_elem.press("Enter")
            random_sleep(2, 3)
            
            send_selectors = [
                'button:has-text("发送")',
                '[data-e2e="send-button"]',
                '.send-button',
            ]
            for selector in send_selectors:
                try:
                    send_btn = page.query_selector(selector)
                    if send_btn and send_btn.is_visible():
                        send_btn.click()
                        log(f"点击了发送按钮: {selector}")
                        break
                except Exception:
                    continue
            
            random_sleep(2, 3)
            log("消息发送完成！")
            
            success_path = os.path.join(os.path.dirname(__file__), "success_screenshot.png")
            page.screenshot(path=success_path)
            log(f"成功截图已保存: {success_path}")
            
            return True
            
        except Exception as e:
            log(f"发送失败: {e}")
            try:
                error_path = os.path.join(os.path.dirname(__file__), "error_screenshot.png")
                page.screenshot(path=error_path, full_page=True)
                log(f"错误截图已保存: {error_path}")
            except Exception:
                pass
            raise
        finally:
            browser.close()


def main():
    cookie_str = os.environ.get("DOUYIN_COOKIE", "")
    sec_uid = os.environ.get("FRIEND_SEC_UID", "")
    message = os.environ.get("SEND_MESSAGE", "") or None
    
    if len(sys.argv) >= 3:
        cookie_str = sys.argv[1]
        sec_uid = sys.argv[2]
    if len(sys.argv) >= 4:
        message = sys.argv[3]
    
    if not cookie_str:
        print("错误：未设置 DOUYIN_COOKIE 环境变量")
        sys.exit(1)
    
    if not sec_uid:
        print("错误：未设置 FRIEND_SEC_UID 环境变量")
        sys.exit(1)
    
    log("=== 抖音自动续火花开始 ===")
    log(f"好友 sec_uid: {sec_uid}")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            log(f"第 {attempt}/{max_retries} 次尝试")
            send_spark(cookie_str, sec_uid, message)
            log("=== 续火花成功！===")
            sys.exit(0)
        except Exception as e:
            log(f"第 {attempt} 次失败: {e}")
            if attempt < max_retries:
                wait_time = random.randint(10, 30)
                log(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                log("=== 所有重试均失败 ===")
                sys.exit(1)


if __name__ == "__main__":
    main()
