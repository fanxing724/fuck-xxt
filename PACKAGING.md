# 打包说明

本项目使用 PyInstaller 打包成本地应用。

## 目标产物

- Windows: `release/FanxingStudyFlow-windows7-win11-x64.zip`
- macOS: `release/FanxingStudyFlow-macos10.13-x64.tar.gz`，内含 `FanxingStudyFlow.app`
- Linux: `release/FanxingStudyFlow-linux-x64.tar.gz`

## 兼容策略

- Windows 7 到 Windows 11 使用 Python 3.8 运行时和 legacy 依赖约束。
- macOS 10.x 使用 Python 3.8、x86_64 架构和 `MACOSX_DEPLOYMENT_TARGET=10.13`。
- PyInstaller 不是跨平台编译器，Windows 包必须在 Windows 构建，macOS 包必须在 macOS 构建。
- 要严格验证 Windows 7，建议在 Windows 7 SP1 x64 或至少 Windows 7 虚拟机中运行产物。
- 要严格验证 macOS 10.13，建议在 macOS 10.13 机器或虚拟机中构建并运行产物。较新的 macOS runner 产物不等于已经验证老系统。

## Windows 本地打包

建议使用 Python 3.8 x64：

```powershell
pwsh scripts/build_windows_app.ps1
```

产物：

```text
release/FanxingStudyFlow-windows7-win11-x64.zip
```

## macOS 本地打包

建议使用 Python 3.8 x64：

```bash
bash scripts/build_macos_app.sh
```

产物：

```text
release/FanxingStudyFlow-macos10.13-x64.tar.gz
```

## Linux 本地打包

建议使用 Python 3.8 x64：

```bash
bash scripts/build_linux_app.sh
```

产物：

```text
release/FanxingStudyFlow-linux-x64.tar.gz
```

## GitHub Actions

推送 `v*` tag 或手动运行 `Build and Release` workflow，会自动构建 Windows、macOS 和 Linux 包。Release 只会在 tag 触发时创建。
