#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地网页控制台。

不依赖 Tkinter，用 Python 标准库启动 127.0.0.1 上的配置页，并在后台运行 main.py。
"""
import argparse
import configparser
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = APP_DIR.parent
CONFIG_PATH = BASE_DIR / "config.ini"
STATIC_DIR = APP_DIR / "static"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clamp_float(value, default, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return min(maximum, max(minimum, number))


def clamp_int(value, default, minimum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, number)


def form_bool(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def first_value(fields, key, default=""):
    value = fields.get(key, default)
    if isinstance(value, list):
        return value[0] if value else default
    return value


def load_default_config():
    data = {
        "username": "",
        "password": "",
        "course_list": "",
        "speed": "2.0",
        "verbose": False,
        "save_config": True,
        "save_password": True,
        "ai_enabled": False,
        "submit": False,
        "endpoint": "https://api.openai.com/v1",
        "key": "",
        "model": "gpt-4o-mini",
        "proxy": "",
        "min_interval_seconds": "3",
        "cover_rate": "0.8",
    }
    if not CONFIG_PATH.exists():
        return data

    config = configparser.ConfigParser(interpolation=None)
    config.read(CONFIG_PATH, encoding="utf8")
    if config.has_section("common"):
        common = config["common"]
        data.update(
            {
                "username": common.get("username", ""),
                "password": common.get("password", ""),
                "course_list": common.get("course_list", ""),
                "speed": common.get("speed", "2.0"),
            }
        )
    if config.has_section("tiku"):
        tiku = config["tiku"]
        ai_enabled = tiku.get("provider", "").strip() == "AI"
        data.update(
            {
                "ai_enabled": ai_enabled,
                "submit": tiku.get("submit", "false").strip().lower() == "true",
                "endpoint": tiku.get(
                    "endpoint",
                    tiku.get(
                        "openai_api_base",
                        tiku.get("siliconflow_endpoint", "https://api.openai.com/v1"),
                    ),
                ),
                "key": tiku.get("key", tiku.get("openai_api_key", tiku.get("siliconflow_key", ""))),
                "model": tiku.get("model", tiku.get("openai_model", tiku.get("siliconflow_model", "gpt-4o-mini"))),
                "proxy": tiku.get("http_proxy", tiku.get("proxy", "")),
                "min_interval_seconds": tiku.get("min_interval_seconds", "3"),
                "cover_rate": tiku.get("cover_rate", "0.8"),
            }
        )
    return data


def normalize_config(fields, password_for_file=None):
    ai_enabled = form_bool(fields.get("ai_enabled"))
    provider = "AI" if ai_enabled else ""
    endpoint = first_value(fields, "endpoint").strip()
    key = first_value(fields, "key").strip()
    model = first_value(fields, "model").strip()
    proxy = first_value(fields, "proxy").strip()
    course_list = ",".join(
        item.strip()
        for item in first_value(fields, "course_list").split(",")
        if item.strip()
    )
    speed = clamp_float(first_value(fields, "speed"), 2.0, 1.0, 2.0)
    cover_rate = clamp_float(first_value(fields, "cover_rate"), 0.8, 0.0, 1.0)
    interval = clamp_int(first_value(fields, "min_interval_seconds"), 3, 0)

    ai_endpoint = endpoint or "https://api.openai.com/v1"
    ai_model = model or "gpt-4o-mini"

    config = configparser.ConfigParser(interpolation=None)
    config["common"] = {
        "username": first_value(fields, "username").strip(),
        "password": password_for_file if password_for_file is not None else first_value(fields, "password"),
        "course_list": course_list,
        "auto_select_all": "true" if not course_list else "false",
        "speed": f"{speed:.1f}",
        "notopen_action": "continue",
    }
    config["tiku"] = {
        "provider": provider,
        "submit": "true" if form_bool(fields.get("submit")) else "false",
        "endpoint": ai_endpoint,
        "key": key,
        "model": ai_model,
        "http_proxy": proxy,
        "min_interval_seconds": str(interval),
        "cover_rate": f"{cover_rate:.2f}",
        "true_list": "正确,对,√,是",
        "false_list": "错误,错,×,否,不对,不正确",
    }
    config["notification"] = {
        "provider": "",
        "token": "",
    }
    return config


def write_config(path, fields, password_for_file=None):
    config = normalize_config(fields, password_for_file=password_for_file)
    with open(path, "w", encoding="utf8") as file:
        config.write(file)


def models_endpoint(endpoint):
    base = (endpoint or "https://api.openai.com/v1").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    return f"{base}/models"


def fetch_models(fields):
    key = first_value(fields, "key").strip()
    endpoint = first_value(fields, "endpoint", "https://api.openai.com/v1").strip()
    url = models_endpoint(endpoint)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Referer": endpoint or "https://api.openai.com/v1",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf8", errors="replace")
        if exc.code == 403 and ("Cloudflare" in detail or "1010" in detail):
            raise RuntimeError(
                "模型列表获取失败: 接口被 Cloudflare 拦截。可以直接手动输入模型名后继续运行。"
            ) from exc
        raise RuntimeError(f"模型列表获取失败: HTTP {exc.code} {detail[:200]}") from exc
    except Exception as exc:
        raise RuntimeError(f"模型列表获取失败: {exc}") from exc

    model_ids = []
    for item in payload.get("data", []):
        model_id = item.get("id") if isinstance(item, dict) else None
        if model_id:
            model_ids.append(model_id)
    return sorted(set(model_ids))


class Runner:
    def __init__(self):
        self.lock = threading.Lock()
        self.process = None
        self.temp_config = None
        self.logs = []
        self.status = "就绪"
        self.exit_code = None
        self.started_at = None

    def add_log(self, text):
        clean = ANSI_RE.sub("", text)
        with self.lock:
            self.logs.append(clean)

    def snapshot(self, since):
        with self.lock:
            running = self.process is not None and self.process.poll() is None
            return {
                "status": self.status,
                "running": running,
                "exit_code": self.exit_code,
                "started_at": self.started_at,
                "logs": self.logs[since:],
                "next": len(self.logs),
            }

    def validate(self, fields):
        username = first_value(fields, "username").strip()
        password = first_value(fields, "password")
        if not username:
            return "请填写手机号"
        if not password:
            return "请填写密码"
        if form_bool(fields.get("ai_enabled")) and not first_value(fields, "key").strip():
            return "启用 AI 答题时需要填写 API Key"
        return ""

    def start(self, fields):
        error = self.validate(fields)
        if error:
            return False, error

        with self.lock:
            if self.process is not None and self.process.poll() is None:
                return False, "任务正在运行"
            self.logs = []
            self.status = "准备启动"
            self.exit_code = None
            self.started_at = time.strftime("%Y-%m-%d %H:%M:%S")

        temp = tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False, encoding="utf8")
        temp.close()
        self.temp_config = Path(temp.name)
        write_config(self.temp_config, fields)

        if form_bool(fields.get("save_config")):
            password = first_value(fields, "password") if form_bool(fields.get("save_password")) else ""
            write_config(CONFIG_PATH, fields, password_for_file=password)

        thread = threading.Thread(target=self._run, args=(form_bool(fields.get("verbose")),), daemon=True)
        thread.start()
        return True, "已启动"

    def stop(self):
        with self.lock:
            process = self.process
        if process is None or process.poll() is not None:
            return False, "没有正在运行的任务"
        self.status = "正在停止"
        process.terminate()
        return True, "已发送停止信号"

    def _run(self, verbose):
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--cli", "-c", str(self.temp_config)]
        else:
            cmd = [sys.executable, "-u", "main.py", "-c", str(self.temp_config)]
        if verbose:
            cmd.append("-v")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        self.add_log(f"$ {' '.join(cmd)}\n")

        try:
            process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR if getattr(sys, "frozen", False) else APP_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf8",
                errors="replace",
                env=env,
            )
            with self.lock:
                self.process = process
                self.status = "运行中"
            assert process.stdout is not None
            for line in process.stdout:
                self.add_log(line)
            code = process.wait()
            with self.lock:
                self.exit_code = code
                self.status = "已完成" if code == 0 else f"已退出，状态码 {code}"
        except Exception as exc:
            self.add_log(f"启动失败: {type(exc).__name__}: {exc}\n")
            with self.lock:
                self.exit_code = 1
                self.status = "启动失败"
        finally:
            if self.temp_config and self.temp_config.exists():
                try:
                    self.temp_config.unlink()
                except OSError:
                    pass
            with self.lock:
                self.process = None
                self.temp_config = None


class Handler(BaseHTTPRequestHandler):
    server_version = "SuperStarWeb/1.0"

    def log_message(self, fmt, *args):
        return

    @property
    def runner(self):
        return self.server.runner

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_fields(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf8")
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return json.loads(raw or "{}")
        return urllib.parse.parse_qs(raw, keep_blank_values=True)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self.send_html()
        elif parsed.path.startswith("/static/"):
            self.send_static(parsed.path)
        elif parsed.path == "/api/config":
            self.send_json(load_default_config())
        elif parsed.path == "/api/status":
            params = urllib.parse.parse_qs(parsed.query)
            since = clamp_int(first_value(params, "since", "0"), 0, 0)
            self.send_json(self.runner.snapshot(since))
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        fields = self.read_fields()
        if parsed.path == "/api/start":
            ok, message = self.runner.start(fields)
            self.send_json({"ok": ok, "message": message}, 200 if ok else 400)
        elif parsed.path == "/api/stop":
            ok, message = self.runner.stop()
            self.send_json({"ok": ok, "message": message}, 200 if ok else 400)
        elif parsed.path == "/api/models":
            try:
                models = fetch_models(fields)
                self.send_json({"ok": True, "models": models})
            except RuntimeError as exc:
                self.send_json({"ok": False, "message": str(exc)}, 400)
        elif parsed.path == "/api/save":
            password = first_value(fields, "password") if form_bool(fields.get("save_password")) else ""
            write_config(CONFIG_PATH, fields, password_for_file=password)
            self.send_json({"ok": True, "message": "已保存配置"})
        else:
            self.send_error(404)

    def send_html(self):
        initial = json.dumps(load_default_config(), ensure_ascii=False).replace("</", "<\\/")
        body = HTML.replace("__INITIAL_CONFIG__", initial).encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path):
        relative = request_path.removeprefix("/static/").lstrip("/")
        path = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in path.parents and path != STATIC_DIR.resolve():
            self.send_error(403)
            return
        if not path.is_file():
            self.send_error(404)
            return
        content_type = "application/octet-stream"
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        elif path.suffix.lower() == ".png":
            content_type = "image/png"
        elif path.suffix.lower() == ".webp":
            content_type = "image/webp"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SuperStar 网页控制台</title>
<style>
:root {
  color-scheme: light;
  --surface: rgba(255, 255, 255, 0.86);
  --surface-strong: rgba(255, 255, 255, 0.94);
  --line: rgba(255, 255, 255, 0.38);
  --text: #241f2b;
  --muted: #5f566b;
  --accent: #8a4de8;
  --accent-strong: #6b32c4;
  --accent-soft: rgba(246, 239, 255, 0.9);
  --danger: #b42318;
  --warn: #9a5a00;
  --log-bg: rgba(18, 15, 28, 0.88);
  --log-text: #f5f0ff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background:
    linear-gradient(90deg, rgba(17, 13, 24, 0.86), rgba(17, 13, 24, 0.28) 46%, rgba(17, 13, 24, 0.78)),
    url("/static/background.jpeg") center / cover fixed no-repeat;
  color: var(--text);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
}
.app {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 22px;
  background: rgba(255, 255, 255, 0.34);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(10px);
}
h1 {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0;
  color: #fff;
  text-shadow: 0 1px 10px rgba(20, 12, 35, 0.35);
}
.status {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.74);
  color: #3a2d4b;
  border-radius: 6px;
  white-space: nowrap;
}
main {
  display: grid;
  grid-template-columns: minmax(360px, 460px) minmax(0, 1fr);
  gap: 16px;
  padding: 16px;
}
section {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 18px 50px rgba(24, 16, 38, 0.28);
  backdrop-filter: blur(16px);
}
.form-section {
  height: calc(100vh - 82px);
  overflow: auto;
}
.log-section {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: calc(100vh - 82px);
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.46);
}
h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}
form {
  padding: 14px;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
label {
  display: grid;
  gap: 5px;
  color: var(--muted);
  font-size: 13px;
}
label.full { grid-column: 1 / -1; }
input, select {
  width: 100%;
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface-strong);
  color: var(--text);
  padding: 7px 9px;
  font: inherit;
}
input:focus, select:focus {
  outline: 2px solid rgba(15, 118, 110, 0.18);
  border-color: var(--accent);
}
.ai-panel {
  display: grid;
  gap: 12px;
  margin: 14px 0;
  padding: 12px;
  border: 1px solid rgba(138, 77, 232, 0.22);
  border-radius: 8px;
  background: var(--accent-soft);
}
.ai-panel.off .ai-fields {
  display: none;
}
.inline {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 8px;
}
.checks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
  margin: 12px 0;
}
.check {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  color: var(--text);
}
.check input {
  width: 16px;
  min-height: 16px;
}
.toolbar {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}
button {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--text);
  padding: 0 13px;
  font: inherit;
  cursor: pointer;
}
button.primary {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}
button.primary:hover { background: var(--accent-strong); }
button.secondary {
  border-color: rgba(138, 77, 232, 0.34);
  background: #ffffff;
  color: var(--accent-strong);
}
button.danger {
  border-color: #fecdca;
  color: var(--danger);
}
button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.message {
  min-height: 20px;
  margin-top: 10px;
  color: var(--warn);
}
pre {
  margin: 0;
  padding: 14px;
  background: var(--log-bg);
  color: var(--log-text);
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font: 12px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (max-width: 900px) {
  main { grid-template-columns: 1fr; }
  .form-section, .log-section { height: auto; min-height: auto; }
}
@media (max-width: 560px) {
  header { align-items: flex-start; flex-direction: column; }
  main { padding: 10px; }
  .grid, .checks { grid-template-columns: 1fr; }
  .toolbar { flex-wrap: wrap; }
  button { flex: 1 1 auto; }
}
</style>
</head>
<body>
<div class="app">
  <header>
    <h1>SuperStar 控制台</h1>
    <div class="status" id="status">就绪</div>
  </header>
  <main>
    <section class="form-section">
      <div class="section-head"><h2>运行配置</h2></div>
      <form id="configForm">
        <div class="grid">
          <label>手机号
            <input name="username" autocomplete="username">
          </label>
          <label>密码
            <input name="password" type="password" autocomplete="current-password">
          </label>
          <label class="full">课程ID
            <input name="course_list" placeholder="留空学习全部，多个用逗号分隔">
          </label>
          <label>播放倍速
            <select name="speed">
              <option value="1.0">1.0x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2.0">2.0x</option>
            </select>
          </label>
        </div>
        <div class="ai-panel off" id="aiPanel">
          <label class="check"><input name="ai_enabled" id="aiEnabled" type="checkbox">启用 AI 答题</label>
          <div class="ai-fields grid">
            <label class="full">Endpoint
              <input name="endpoint" placeholder="https://api.openai.com/v1">
            </label>
            <label>API Key
              <input name="key" type="password">
            </label>
            <label>请求间隔
              <input name="min_interval_seconds" type="number" min="0" step="1">
            </label>
            <div class="inline full">
              <label>模型
                <input name="model" list="modelList" placeholder="先填写 Endpoint 和 Key，再刷新模型">
                <datalist id="modelList"></datalist>
              </label>
              <button type="button" id="modelsBtn" class="secondary">刷新模型</button>
            </div>
            <label>Proxy
              <input name="proxy">
            </label>
            <label>覆盖率
              <input name="cover_rate" type="number" min="0" max="1" step="0.05">
            </label>
            <label class="check"><input name="submit" type="checkbox">直接提交答案</label>
          </div>
        </div>
        <div class="checks">
          <label class="check"><input name="verbose" type="checkbox">详细日志</label>
          <label class="check"><input name="save_config" type="checkbox">保存配置</label>
          <label class="check"><input name="save_password" type="checkbox">保存密码</label>
        </div>
        <div class="toolbar">
          <button type="button" id="saveBtn">保存配置</button>
          <button type="button" id="stopBtn" class="danger" disabled>停止</button>
          <button type="submit" id="startBtn" class="primary">开始运行</button>
        </div>
        <div class="message" id="message"></div>
      </form>
    </section>
    <section class="log-section">
      <div class="section-head">
        <h2>运行日志</h2>
        <button type="button" id="clearBtn">清空</button>
      </div>
      <pre id="log"></pre>
    </section>
  </main>
</div>
<script>
const initialConfig = __INITIAL_CONFIG__;
const form = document.getElementById("configForm");
const statusEl = document.getElementById("status");
const messageEl = document.getElementById("message");
const logEl = document.getElementById("log");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const aiEnabled = document.getElementById("aiEnabled");
const aiPanel = document.getElementById("aiPanel");
const modelsBtn = document.getElementById("modelsBtn");
const modelList = document.getElementById("modelList");
let logIndex = 0;

function setMessage(text, isError = false) {
  messageEl.textContent = text || "";
  messageEl.style.color = isError ? "#b42318" : "#b54708";
}

function fillForm(data) {
  for (const [key, value] of Object.entries(data)) {
    const field = form.elements[key];
    if (!field) continue;
    if (field.type === "checkbox") field.checked = Boolean(value);
    else field.value = value == null ? "" : String(value);
  }
}

function collectForm() {
  const fd = new FormData(form);
  for (const name of ["ai_enabled", "verbose", "submit", "save_config", "save_password"]) {
    if (!fd.has(name)) fd.set(name, "false");
    else fd.set(name, "true");
  }
  return new URLSearchParams(fd);
}

async function post(path) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
    body: collectForm()
  });
  const data = await response.json();
  if (!response.ok || !data.ok) throw new Error(data.message || "请求失败");
  return data;
}

function syncAiPanel() {
  aiPanel.classList.toggle("off", !aiEnabled.checked);
}

function canFetchModels() {
  return aiEnabled.checked && form.elements.endpoint.value.trim() && form.elements.key.value.trim();
}

async function refreshModels() {
  if (!canFetchModels()) {
    setMessage("填写 Endpoint 和 API Key 后会获取模型列表");
    return;
  }
  setMessage("正在获取模型列表...");
  modelsBtn.disabled = true;
  try {
    const response = await fetch("/api/models", {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
      body: collectForm()
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.message || "模型列表获取失败");
    modelList.innerHTML = "";
    for (const model of data.models) {
      const option = document.createElement("option");
      option.value = model;
      modelList.appendChild(option);
    }
    setMessage(data.models.length ? `已获取 ${data.models.length} 个模型` : "接口未返回模型");
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    modelsBtn.disabled = false;
  }
}

async function poll() {
  try {
    const response = await fetch(`/api/status?since=${logIndex}`);
    const data = await response.json();
    statusEl.textContent = data.status;
    startBtn.disabled = data.running;
    stopBtn.disabled = !data.running;
    if (data.logs.length) {
      logEl.textContent += data.logs.join("");
      logEl.scrollTop = logEl.scrollHeight;
      logIndex = data.next;
    }
  } catch (error) {
    statusEl.textContent = "连接中断";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("");
  logEl.textContent = "";
  logIndex = 0;
  try {
    const data = await post("/api/start");
    setMessage(data.message);
    poll();
  } catch (error) {
    setMessage(error.message, true);
  }
});

document.getElementById("saveBtn").addEventListener("click", async () => {
  try {
    const data = await post("/api/save");
    setMessage(data.message);
  } catch (error) {
    setMessage(error.message, true);
  }
});

stopBtn.addEventListener("click", async () => {
  try {
    const data = await post("/api/stop");
    setMessage(data.message);
    poll();
  } catch (error) {
    setMessage(error.message, true);
  }
});

document.getElementById("clearBtn").addEventListener("click", () => {
  logEl.textContent = "";
});

aiEnabled.addEventListener("change", () => {
  syncAiPanel();
  if (canFetchModels()) refreshModels();
});
form.elements.endpoint.addEventListener("change", () => {
  if (canFetchModels()) refreshModels();
});
form.elements.key.addEventListener("change", () => {
  if (canFetchModels()) refreshModels();
});
modelsBtn.addEventListener("click", refreshModels);

fillForm(initialConfig);
syncAiPanel();
if (canFetchModels()) refreshModels();
setInterval(poll, 1000);
poll();
</script>
</body>
</html>
"""


def build_server(host, port, runner):
    last_error = None
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer((host, candidate), Handler)
            server.runner = runner
            return server, candidate
        except OSError as exc:
            last_error = exc
    raise RuntimeError(f"无法绑定端口 {port}-{port + 19}: {last_error}")


def main():
    parser = argparse.ArgumentParser(description="SuperStar 本地网页控制台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    runner = Runner()
    server, port = build_server(args.host, args.port, runner)
    url = f"http://{args.host}:{port}/"
    print(f"SuperStar 网页控制台已启动: {url}", flush=True)
    print("按 Ctrl+C 停止服务", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
    finally:
        runner.stop()
        server.server_close()


if __name__ == "__main__":
    main()
