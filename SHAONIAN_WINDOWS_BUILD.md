# ShaoNian Windows 客户端编译说明

本源码由 RustDesk 改名而来。Windows 进程名、服务名、IPC 管道、配置目录、安装包产品名均已改为 `ShaoNian`。

编译统一在 GitHub Actions 上完成，见 `.github/workflows/build-windows-x64.yml`。

## 改名后生效的内容

| 项目 | 值 |
| --- | --- |
| 任务管理器进程 | `ShaoNian.exe` |
| Windows 服务名 | `ShaoNian` |
| 安装路径 | `%ProgramFiles%\ShaoNian\ShaoNian.exe` |
| 配置目录 | `%APPDATA%\ShaoNian` |
| IPC 管道 | `\\.\pipe\ShaoNian\query...` |
| 隐私模式辅助进程 | `RuntimeBroker_shaonian.exe` |
| 应用图标 / 托盘图标 / 窗口图标 | 蓝底白色「少年」 |
| 首页 Logo | 「少年远程」横向字标（`flutter/assets/logo*.png`） |

## 编译（GitHub Actions）

工作流：`.github/workflows/build-windows-x64.yml`

- 触发：向 `shaonian-build` 分支推送任意改动；也支持 `workflow_dispatch`（需有 Actions 写权限的 token）
- 矩阵：仅 Windows x64（`x86_64-pc-windows-msvc`），Flutter 3.24.5 + 自定义 engine
- 构建参数：`build.py --portable --flutter --skip-portable-pack --hwcodec --vram`
- 签名：`SIGN_BASE_URL=-2`，跳过签名步骤，产物为未签名包

产物：

| 位置 | 名称 | 内容 |
| --- | --- | --- |
| Actions artifact | `rustdesk-unsigned-windows-x86_64` | 绿色版目录：`ShaoNian.exe`、`librustdesk.dll`、`data/`、`drivers/` 等 |
| Release 附件 | `ShaoNianDesk-1.5.0-x86_64.exe` | 便携单文件版 |
| Release 附件 | `ShaoNianDesk-1.5.0-x86_64.msi` | MSI 安装包 |
| Actions artifact | `rustdesk-unsigned-msi-template-x86_64` | MSI 模板 |

## 品牌信息（已去除官方痕迹）

客户端不再把用户引向 RustDesk 官方页面，所有可点击链接集中定义在 `flutter/lib/consts.dart`：

| 常量 | 值 | 使用位置 |
| --- | --- | --- |
| `kBrandWebsiteUrl` | `https://rustdesk.vzzw.com` | 桌面/移动端「关于」、更新按钮、自建服务器引导、Linux 帮助链接、页脚 |
| `kBrandWebsiteLabel` | `rustdesk.vzzw.com` | 「关于」与设置页显示的链接文字 |
| `kBrandPrivacyUrl` | `https://rustdesk.vzzw.com/privacy.html` | 隐私声明、安装页最终用户协议 |
| `kBrandCopyright` | `少年远程` | 桌面「关于」页版权行 |

其他已替换项：

- 应用图标：`res/icon.ico`（16–256 全尺寸）、`res/tray-icon.ico`、`flutter/windows/runner/resources/app_icon.ico`；PNG 同步更新 `res/32x32.png`、`res/64x64.png`、`res/128x128.png`、`res/128x128@2x.png`、`res/icon.png`、`res/mac-icon.png`。图标由 `tools/gen_brand_icons.py` 生成，可直接重跑（依赖 Pillow）。
- 安装包元数据：`res/msi/preprocess.py` 的 ARP 联系/帮助/自述链接改为 `https://rustdesk.vzzw.com`，厂商默认值改为 `ShaoNian`；`res/msi/Package/License.rtf` 中的 `rustdesk.com`、`RustDesk`、`Purslane Tech` 已清除。
- 可执行文件版本信息：`Cargo.toml`、`libs/portable/Cargo.toml`、`flutter/windows/runner/Runner.rc` 的公司名与版权改为 `ShaoNian`。
- Rust 侧帮助链接：`libs/hbb_common/src/config.rs` 的 `LINK_DOCS_*`、`src/client.rs` 的 `SCRAP_X11_REF_URL`、`src/lang/en.rs` 的两条文档链接均指向 `https://rustdesk.vzzw.com`。
- Sciter 界面（仅 32 位回退用）：`src/ui/index.tis`、`src/ui/install.tis` 的链接与版权同样已替换。

注意：

- `is_public()`（`src/common.rs`）保留 `rustdesk.com` 域名判断，仅用于识别「官方公共服务」以关闭审计上报与打洞选项，不属于展示内容，不要改。
- 自动检查更新沿用上游逻辑：`check_software_update()` 在 `APP_NAME != "RustDesk"` 时直接返回，因此不会请求 `api.rustdesk.com`。
- MSI 的语言文件使用 Codepage 1252，厂商名与许可证文本保持 ASCII（`ShaoNian`），避免 WiX 编译失败；带中文的品牌名只出现在运行时界面与图标中。
- `https://rustdesk.vzzw.com/privacy.html` 尚未在该服务器上部署，点击会 404，需要自行放页面。

## 内置默认值（编译进二进制）

以下为全新安装（无缓存配置、无 `custom.txt`）时使用的编译期默认值。它们打包在二进制内，需修改源码后重新编译才能生效。

| 项目 | 值 | 源码位置 |
| --- | --- | --- |
| ID 服务器 | `rustdesk.vzzw.com:21116` | `libs/hbb_common/src/config.rs` 的 `RENDEZVOUS_SERVERS` |
| 中继服务器 | `rustdesk.vzzw.com:21117` | 由 ID 服务器端口 +1 推导（`src/rendezvous_mediator.rs` 的 `get_relay_server`），无需单独配置 |
| API 服务器 | `https://rustdesk.vzzw.com:21114` | `libs/hbb_common/src/config.rs` 的 `API_SERVER`，并由 `get_builtin_option` 对 `allow-https-21114` 返回 `Y`，否则 `:21114` 会被去掉 |
| 公钥 | `bh4JvONOwgQ+AWOR1vKbEiFcCpaJTz1CnjBKLtPusPw=` | `libs/hbb_common/src/config.rs` 的 `RS_PUB_KEY` |
| 关闭网络配置 | 开启 | `src/common.rs` 的 `get_builtin_option`，对 `hide-network-settings` 返回 `Y` |
| 关闭「提供支持」页脚 | 开启 | `src/common.rs` 的 `get_builtin_option`，对 `hide-powered-by-me` 返回 `Y` |
| 隐藏「自建服务器」提示 | 开启 | `src/common.rs` 的 `using_public_server`，内置服务器不是 `rustdesk.com` 时判定为非公共服务 |

生效条件与效果：

- 服务器地址仅在 `custom-rendezvous-server` 选项与 `CONFIG2` 缓存均为空时生效（见 `config.rs` 的 `get_rendezvous_server`）。已保存过服务器地址的机器保留原值。
- 公钥仅在 `key` 选项为空时生效（见 `src/common.rs` 的 `get_key`）。
- API 服务器仅在 `api-server` 选项为空、且 `custom-rendezvous-server` 也为空时使用内置值（`src/common.rs` 的 `get_api_server_`）；若只填了 ID 服务器，API 地址按 `http://<ID服务器>:21114-2` 推导。
- `hide-network-settings=Y` 会移除桌面设置的整个「网络」标签页（`flutter/lib/desktop/pages/desktop_setting_page.dart`），并隐藏移动端设置中的网络相关项。
- `hide-powered-by-me=Y` 会让 `loadPowered()`（`flutter/lib/common.dart`）返回空组件，「由 ShaoNian 提供支持」链接将从桌面首页页脚与移动端设置页消失。
- `using_public_server()` 会同时参考内置的 `RENDEZVOUS_SERVERS`：内置域名不是 `rustdesk.com` 即视为非公共服务器，首页不再显示「如果需要更快连接速度，你可以选择自建服务器」，连接画质弹窗也不再隐藏 FPS/画质选项。

以上各项均可在运行时通过放在 exe 同级的签名 `custom.txt` 覆盖（使用 `app-name`、`default-settings`、`override-settings`、`hide-*` 等键）。

## 注意事项

- 编译后不要重命名 `ShaoNian.exe`。服务名、IPC、安装路径均来自 `APP_NAME`。
- `librustdesk.dll` 保持 Rust cdylib 名称不变，改名会破坏 Flutter FFI。
- 打包产物（便携 exe 与 msi）以 `ShaoNianDesk-<version>-<arch>` 命名，由工作流在 `SignOutput/` 中生成，与内部 exe 名无关。
- 由于 `APP_NAME` 已不再是 `RustDesk`，界面中包含 `RustDesk` 的文案会在运行时被替换。
