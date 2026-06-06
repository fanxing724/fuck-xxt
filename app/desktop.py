# -*- coding: utf-8 -*-
"""
超星学习通自动刷课脚本 - 桌面版

桌面层只负责收集配置、启动/停止 main.py，并实时展示日志。
核心学习逻辑仍在 main.py 和 api/ 中，避免 GUI 与业务流程耦合。
"""
import configparser
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = APP_DIR.parent
CONFIG_PATH = BASE_DIR / "config.ini"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class SuperStarDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SuperStar 桌面版")
        self.geometry("1080x840")
        self.minsize(920, 700)

        self.process = None
        self.worker = None
        self.temp_config = None
        self.log_queue = queue.Queue()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.course_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=2.0)
        self.verbose_var = tk.BooleanVar(value=False)
        self.save_password_var = tk.BooleanVar(value=True)
        self.tiku_provider_var = tk.StringVar(value="")
        self.tiku_submit_var = tk.BooleanVar(value=False)
        self.tiku_tokens_var = tk.StringVar(value="")
        self.tiku_endpoint_var = tk.StringVar(value="https://api.openai.com/v1")
        self.tiku_key_var = tk.StringVar(value="")
        self.tiku_model_var = tk.StringVar(value="gpt-4o-mini")
        self.tiku_proxy_var = tk.StringVar(value="")
        self.tiku_interval_var = tk.IntVar(value=3)
        self.tiku_cover_rate_var = tk.DoubleVar(value=0.8)
        self.tiku_provider_var.trace_add("write", lambda *_: self._apply_tiku_provider_defaults())
        self.status_var = tk.StringVar(value="就绪")

        self._build_ui()
        self._load_default_config()
        self.after(100, self._drain_logs)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(8, weight=1)

        title = ttk.Label(root, text="SuperStar 桌面版", font=("Helvetica", 20, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(root, text="手机号").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.username_var).grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(root, text="密码").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.password_var, show="*").grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(root, text="课程ID").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.course_var).grid(row=3, column=1, sticky="ew", pady=6)
        ttk.Label(root, text="留空学习全部，多个用逗号分隔").grid(row=3, column=2, sticky="w", padx=(10, 0))

        ttk.Label(root, text="播放倍速").grid(row=4, column=0, sticky="w", pady=6)
        speed_frame = ttk.Frame(root)
        speed_frame.grid(row=4, column=1, columnspan=2, sticky="ew", pady=6)
        speed_frame.columnconfigure(0, weight=1)
        ttk.Scale(speed_frame, from_=1.0, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL).grid(
            row=0, column=0, sticky="ew"
        )
        self.speed_label = ttk.Label(speed_frame, width=6)
        self.speed_label.grid(row=0, column=1, padx=(10, 0))
        self.speed_var.trace_add("write", lambda *_: self._update_speed_label())
        self._update_speed_label()

        options = ttk.Frame(root)
        options.grid(row=5, column=1, columnspan=2, sticky="w", pady=6)
        ttk.Checkbutton(options, text="详细日志", variable=self.verbose_var).pack(side=tk.LEFT)
        ttk.Checkbutton(options, text="保存密码到 config.ini", variable=self.save_password_var).pack(side=tk.LEFT, padx=(18, 0))

        tiku_frame = ttk.LabelFrame(root, text="题库 / AI")
        tiku_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(10, 8))
        tiku_frame.columnconfigure(1, weight=1)
        tiku_frame.columnconfigure(4, weight=1)

        ttk.Label(tiku_frame, text="提供商").grid(row=0, column=0, sticky="w", pady=4, padx=(10, 6))
        provider_combo = ttk.Combobox(
            tiku_frame,
            textvariable=self.tiku_provider_var,
            values=["", "TikuYanxi", "AI", "SiliconFlow"],
            state="readonly",
            width=18,
        )
        provider_combo.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Checkbutton(tiku_frame, text="直接提交", variable=self.tiku_submit_var).grid(
            row=0, column=2, sticky="w", padx=(12, 0)
        )
        ttk.Label(tiku_frame, text="覆盖率").grid(row=0, column=3, sticky="w", padx=(12, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_cover_rate_var, width=8).grid(
            row=0, column=4, sticky="w", pady=4
        )

        ttk.Label(tiku_frame, text="Tokens").grid(row=1, column=0, sticky="w", pady=4, padx=(10, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_tokens_var).grid(
            row=1, column=1, columnspan=4, sticky="ew", pady=4
        )

        ttk.Label(tiku_frame, text="Endpoint").grid(row=2, column=0, sticky="w", pady=4, padx=(10, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_endpoint_var).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=4
        )
        ttk.Label(tiku_frame, text="API Key").grid(row=2, column=3, sticky="w", padx=(12, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_key_var, show="*").grid(
            row=2, column=4, sticky="ew", pady=4
        )

        ttk.Label(tiku_frame, text="Model").grid(row=3, column=0, sticky="w", pady=4, padx=(10, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_model_var).grid(
            row=3, column=1, sticky="ew", pady=4
        )
        ttk.Label(tiku_frame, text="Proxy").grid(row=3, column=2, sticky="w", padx=(12, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_proxy_var).grid(
            row=3, column=3, sticky="ew", pady=4
        )
        ttk.Label(tiku_frame, text="Interval").grid(row=3, column=4, sticky="w", padx=(12, 6))
        ttk.Entry(tiku_frame, textvariable=self.tiku_interval_var, width=8).grid(
            row=3, column=5, sticky="w", pady=4, padx=(0, 10)
        )

        buttons = ttk.Frame(root)
        buttons.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(12, 10))
        ttk.Button(buttons, text="导入配置", command=self._pick_config).pack(side=tk.LEFT)
        ttk.Button(buttons, text="保存配置", command=self._save_default_config).pack(side=tk.LEFT, padx=(8, 0))
        self.start_button = ttk.Button(buttons, text="开始运行", command=self._start)
        self.start_button.pack(side=tk.RIGHT)
        self.stop_button = ttk.Button(buttons, text="停止", command=self._stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=(0, 8))

        log_frame = ttk.Frame(root)
        log_frame.grid(row=8, column=0, columnspan=3, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=18, padx=10, pady=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        status = ttk.Label(root, textvariable=self.status_var, anchor="w")
        status.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(8, 0))

    def _update_speed_label(self):
        self.speed_label.configure(text=f"{self.speed_var.get():.1f}x")

    def _apply_tiku_provider_defaults(self):
        provider = self.tiku_provider_var.get().strip()
        endpoint = self.tiku_endpoint_var.get().strip()
        model = self.tiku_model_var.get().strip()

        if provider == "AI":
            if not endpoint or "siliconflow.cn" in endpoint:
                self.tiku_endpoint_var.set("https://api.openai.com/v1")
            if not model or model == "deepseek-ai/DeepSeek-V3":
                self.tiku_model_var.set("gpt-4o-mini")
        elif provider == "SiliconFlow":
            if not endpoint or endpoint == "https://api.openai.com/v1":
                self.tiku_endpoint_var.set("https://api.siliconflow.cn/v1/chat/completions")
            if not model or model == "gpt-4o-mini":
                self.tiku_model_var.set("deepseek-ai/DeepSeek-V3")

    def _load_default_config(self):
        if CONFIG_PATH.exists():
            self._load_config(CONFIG_PATH)

    def _pick_config(self):
        path = filedialog.askopenfilename(
            title="选择配置文件",
            initialdir=APP_DIR,
            filetypes=[("INI 配置", "*.ini"), ("所有文件", "*.*")],
        )
        if path:
            self._load_config(Path(path))

    def _load_config(self, path):
        config = configparser.ConfigParser(interpolation=None)
        config.read(path, encoding="utf8")
        if not config.has_section("common"):
            messagebox.showerror("配置错误", "配置文件缺少 [common] 节")
            return

        common = config["common"]
        self.username_var.set(common.get("username", ""))
        self.password_var.set(common.get("password", ""))
        self.course_var.set(common.get("course_list", ""))
        try:
            self.speed_var.set(float(common.get("speed", 2.0)))
        except ValueError:
            self.speed_var.set(2.0)

        if config.has_section("tiku"):
            tiku = config["tiku"]
            self.tiku_provider_var.set(tiku.get("provider", ""))
            self.tiku_submit_var.set(tiku.get("submit", "false").strip().lower() == "true")
            self.tiku_tokens_var.set(tiku.get("tokens", ""))
            self.tiku_endpoint_var.set(
                tiku.get("endpoint", tiku.get("openai_api_base", tiku.get("siliconflow_endpoint", "https://api.openai.com/v1")))
            )
            self.tiku_key_var.set(
                tiku.get("key", tiku.get("openai_api_key", tiku.get("siliconflow_key", "")))
            )
            self.tiku_model_var.set(
                tiku.get("model", tiku.get("openai_model", tiku.get("siliconflow_model", "gpt-4o-mini")))
            )
            self.tiku_proxy_var.set(tiku.get("http_proxy", tiku.get("proxy", "")))
            try:
                self.tiku_interval_var.set(int(tiku.get("min_interval_seconds", 3)))
            except ValueError:
                self.tiku_interval_var.set(3)
            try:
                self.tiku_cover_rate_var.set(float(tiku.get("cover_rate", 0.8)))
            except ValueError:
                self.tiku_cover_rate_var.set(0.8)
        self._append_log(f"已导入配置: {path}\n")

    def _save_default_config(self):
        username = self.username_var.get().strip()
        password = self.password_var.get() if self.save_password_var.get() else ""
        self._write_config(CONFIG_PATH, username, password)
        self._append_log(f"已保存配置: {CONFIG_PATH}\n")

    def _write_config(self, path, username, password):
        courses = ",".join(item.strip() for item in self.course_var.get().split(",") if item.strip())
        provider = self.tiku_provider_var.get().strip()
        endpoint = self.tiku_endpoint_var.get().strip()
        key = self.tiku_key_var.get().strip()
        model = self.tiku_model_var.get().strip()
        proxy = self.tiku_proxy_var.get().strip()
        ai_endpoint = endpoint or "https://api.openai.com/v1"
        ai_model = model or "gpt-4o-mini"
        siliconflow_endpoint = (
            endpoint
            if endpoint and endpoint != "https://api.openai.com/v1"
            else "https://api.siliconflow.cn/v1/chat/completions"
        )
        siliconflow_model = (
            model
            if model and model != "gpt-4o-mini"
            else "deepseek-ai/DeepSeek-V3"
        )

        try:
            cover_rate = min(1.0, max(0.0, float(self.tiku_cover_rate_var.get())))
        except (tk.TclError, ValueError):
            cover_rate = 0.8
        try:
            min_interval = max(0, int(self.tiku_interval_var.get()))
        except (tk.TclError, ValueError):
            min_interval = 3

        config = configparser.ConfigParser(interpolation=None)
        config["common"] = {
            "username": username,
            "password": password,
            "course_list": courses,
            "auto_select_all": "true" if not courses else "false",
            "speed": f"{min(2.0, max(1.0, self.speed_var.get())):.1f}",
            "notopen_action": "continue",
        }
        config["tiku"] = {
            "provider": provider,
            "submit": "true" if self.tiku_submit_var.get() else "false",
            "tokens": self.tiku_tokens_var.get().strip(),
            "endpoint": ai_endpoint,
            "key": key,
            "model": ai_model,
            "http_proxy": proxy,
            "min_interval_seconds": str(min_interval),
            "cover_rate": f"{cover_rate:.2f}",
            "true_list": "正确,对,√,是",
            "false_list": "错误,错,×,否,不对,不正确",
            "siliconflow_endpoint": siliconflow_endpoint,
            "siliconflow_key": key,
            "siliconflow_model": siliconflow_model,
        }
        config["notification"] = {
            "provider": "",
            "token": "",
        }
        with open(path, "w", encoding="utf8") as file:
            config.write(file)

    def _start(self):
        if self.process and self.process.poll() is None:
            return

        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("缺少账号", "请先填写手机号和密码")
            return
        if not self._validate_tiku_settings():
            return

        temp = tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False, encoding="utf8")
        temp.close()
        self.temp_config = Path(temp.name)
        self._write_config(self.temp_config, username, password)

        self.log_text.delete("1.0", tk.END)
        self.status_var.set("运行中")
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)

        self.worker = threading.Thread(target=self._run_process, daemon=True)
        self.worker.start()

    def _validate_tiku_settings(self):
        provider = self.tiku_provider_var.get().strip()
        if not provider:
            return True
        if provider == "TikuYanxi" and not self.tiku_tokens_var.get().strip():
            messagebox.showerror("题库配置缺失", "TikuYanxi 需要填写 Tokens")
            return False
        if provider in {"AI", "SiliconFlow"} and not self.tiku_key_var.get().strip():
            messagebox.showerror("题库配置缺失", f"{provider} 需要填写 API Key")
            return False
        return True

    def _run_process(self):
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--cli", "-c", str(self.temp_config)]
        else:
            cmd = [sys.executable, "-u", "main.py", "-c", str(self.temp_config)]
        if self.verbose_var.get():
            cmd.append("-v")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            self.log_queue.put(f"$ {' '.join(cmd)}\n")
            self.process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR if getattr(sys, "frozen", False) else APP_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf8",
                errors="replace",
                env=env,
            )
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.log_queue.put(ANSI_RE.sub("", line))
            code = self.process.wait()
            self.log_queue.put(("__DONE__", code))
        except Exception as exc:
            self.log_queue.put(f"启动失败: {type(exc).__name__}: {exc}\n")
            self.log_queue.put(("__DONE__", 1))

    def _stop(self):
        if self.process and self.process.poll() is None:
            self.status_var.set("正在停止")
            self.process.terminate()

    def _drain_logs(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "__DONE__":
                    self._on_process_done(item[1])
                else:
                    self._append_log(item)
        except queue.Empty:
            pass
        self.after(100, self._drain_logs)

    def _append_log(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def _on_process_done(self, code):
        if self.temp_config and self.temp_config.exists():
            try:
                self.temp_config.unlink()
            except OSError:
                pass
        self.process = None
        self.temp_config = None
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("已完成" if code == 0 else f"已退出，状态码 {code}")

    def _on_close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno("确认退出", "任务仍在运行，确定要停止并退出吗？"):
                return
            self._stop()
        self.destroy()


def main():
    app = SuperStarDesktop()
    app.mainloop()


if __name__ == "__main__":
    main()
