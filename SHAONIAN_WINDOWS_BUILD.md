# ShaoNian Windows 客户端编译说明

本源码由 RustDesk 改名而来。Windows 进程名、服务名、IPC 管道、配置目录、安装包产品名均已改为 `ShaoNian`。

当前环境为 Linux，无法直接产出 Windows 安装包，请在 Windows 机器或 GitHub Actions 上编译。

## 改名后生效的内容

| 项目 | 值 |
| --- | --- |
| 任务管理器进程 | `ShaoNian.exe` |
| Windows 服务名 | `ShaoNian` |
| 安装路径 | `%ProgramFiles%\ShaoNian\ShaoNian.exe` |
| 配置目录 | `%APPDATA%\ShaoNian` |
| IPC 管道 | `\\.\pipe\ShaoNian\query...` |
| 隐私模式辅助进程 | `RuntimeBroker_shaonian.exe` |

## 编译机要求

使用 Windows 10/11 x64，并安装：

- Visual Studio 2022（Desktop development with C++）
- Rust stable（`rustup` 默认工具链）
- Flutter 3.24.5（x64，与 `.github/workflows/flutter-build.yml` 保持一致）
- Python 3
- Git
- [vcpkg](https://github.com/microsoft/vcpkg)
- LLVM / clang-cl 已加入 PATH（Flutter Windows 编译需要）

## 一次性环境准备

```bat
git clone --depth 1 https://github.com/microsoft/vcpkg C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
setx VCPKG_ROOT C:\vcpkg
```

重启终端后执行：

```bat
vcpkg install libvpx:x64-windows-static libyuv:x64-windows-static opus:x64-windows-static aom:x64-windows-static
```

克隆本源码（已完成改名）并初始化子模块：

```bat
git submodule update --init --recursive --depth 1
```

## 编译 Flutter Windows 包

在仓库根目录执行：

```bat
python3 build.py --portable --flutter --hwcodec
```

产物：

- 未打包的 Flutter 应用：`flutter\build\windows\x64\runner\Release\ShaoNian.exe`
- 便携版安装包：`ShaoNian-<version>-install.exe`

只保留 Release 目录、不打包安装程序：

```bat
python3 build.py --portable --flutter --skip-portable-pack --hwcodec
```

## MSI 安装包

Flutter 编译完成后，复制 Release 目录并用新名称运行 WiX 预处理：

```bat
python res\msi\preprocess.py --arp -d ..\..\path\to\Release --app-name ShaoNian
```

`Release` 目录内必须包含 `ShaoNian.exe`。随后用 MSBuild 编译 `res\msi\msi.sln`（Release / x64）。

## GitHub Actions

`.github/workflows/flutter-build.yml` 中的 Windows 任务已指向 `ShaoNian.exe`，在 Windows runner 上运行该工作流即可获得构建产物。

## 内置默认值（编译进二进制）

以下为全新安装（无缓存配置、无 `custom.txt`）时使用的编译期默认值。它们打包在二进制内，需修改源码后重新编译才能生效。

| 项目 | 值 | 源码位置 |
| --- | --- | --- |
| 默认 ID/中继服务器 | `rustdesk.shaonian.cc` | `libs/hbb_common/src/config.rs` 的 `RENDEZVOUS_SERVERS` |
| 默认公钥 | `nB34zYNbMyT5pxlXNh2jVrLmcSd3Kf8Pvlr8RWNVyOQ=` | `libs/hbb_common/src/config.rs` 的 `RS_PUB_KEY` |
| 关闭网络配置 | 开启 | `src/common.rs` 的 `get_builtin_option`，对 `hide-network-settings` 返回 `Y` |
| 关闭「提供支持」页脚 | 开启 | `src/common.rs` 的 `get_builtin_option`，对 `hide-powered-by-me` 返回 `Y` |

生效条件与效果：

- 服务器地址仅在 `custom-rendezvous-server` 选项与 `CONFIG2` 缓存均为空时生效（见 `config.rs` 的 `get_rendezvous_server`）。已保存过服务器地址的机器保留原值。
- 公钥仅在 `key` 选项为空时生效（见 `src/common.rs` 的 `get_key`）。
- `hide-network-settings=Y` 会移除桌面设置的整个「网络」标签页（`flutter/lib/desktop/pages/desktop_setting_page.dart`），并隐藏移动端设置中的网络相关项。
- `hide-powered-by-me=Y` 会让 `loadPowered()`（`flutter/lib/common.dart`）返回空组件，「由 ShaoNian 提供支持」链接将从桌面首页页脚与移动端设置页消失。

以上四项均可在运行时通过放在 exe 同级的签名 `custom.txt` 覆盖（使用 `app-name`、`default-settings`、`override-settings`、`hide-*` 等键）。

## 注意事项

- 编译后不要重命名 `ShaoNian.exe`。服务名、IPC、安装路径均来自 `APP_NAME`。
- `librustdesk.dll` 保持 Rust cdylib 名称不变，改名会破坏 Flutter FFI。
- 由于 `APP_NAME` 已不再是 `RustDesk`，界面中包含 `RustDesk` 的文案会在运行时被替换。
