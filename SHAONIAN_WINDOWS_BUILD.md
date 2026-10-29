# ShaoNian Windows 客户端 —— 从官方源码到成品安装包的完整流程

本文档描述如何从 **RustDesk 官方 1.5.0 源码** 出发，做出一份「少年远程 / ShaoNianDesk」品牌的
Windows x64 安装包。按章节顺序执行即可，无需依赖任何已有改动。

- 目标平台：Windows x64（`x86_64-pc-windows-msvc`）
- 构建方式：GitHub Actions，`.github/workflows/build-windows-x64.yml`
- 成品：`ShaoNianDesk-1.5.0-x86_64.exe`（便携版）、`ShaoNianDesk-1.5.0-x86_64.msi`（安装包）

---

## 0. 起点

```bash
git clone --depth 1 https://github.com/rustdesk/rustdesk
cd rustdesk
git checkout 1.5.0        # 或任意同结构版本
git submodule update --init --recursive --depth 1
```

以下所有章节都是在此源码上做的改动。改完推到一个**自己的仓库**的 `shaonian-build` 分支即可触发编译。

---

## 1. 改名 RustDesk → ShaoNian

改名不是全局替换。`RustDesk` 在源码里同时承担「产品名」和「协议/路径常量」两种角色，
只改下面这些位置，其余保持原样（否则会破坏 FFI、协议与子模块）。

### 1.1 产品名（核心）

| 文件 | 行 | 改为 |
| --- | --- | --- |
| `libs/hbb_common/src/config.rs` | `APP_NAME` 初始化 | `RwLock::new("ShaoNian".to_owned())` |
| `build.py` | `hbb_name = 'RustDesk' + ('.exe' if windows else '')` | `'ShaoNian'` |
| `build.py` | `--portable` 段中的 `rustdesk.exe` / `rustdesk_portable.exe` / `rustdesk-{version}-install.exe` | 依次改为 `ShaoNian.exe` / `ShaoNian_portable.exe` / `ShaoNian-{version}-install.exe` |
| `build.py` | `generate.py ... -e ../../<dir>/rustdesk.exe` | `ShaoNian.exe` |
| `flutter/windows/CMakeLists.txt` | `set(BINARY_NAME "rustdesk")` | `"ShaoNian"` |
| `flutter/windows/runner/main.cpp` | `std::wstring app_name = L"RustDesk";` | `L"ShaoNian"` |
| `flutter/windows/runner/Runner.rc` | `CompanyName` / `InternalName` / `OriginalFilename` / `ProductName` / `FileDescription` | 见第 4 节 |
| `libs/portable/generate.py` | `options.executable = 'rustdesk.exe'` 及 `--startup` 默认值说明 | `ShaoNian.exe` |

`APP_NAME` 改完后，以下内容自动跟随，无需单独改：

- 服务名、`%ProgramFiles%\ShaoNian`、`%APPDATA%\ShaoNian`
- IPC 管道 `\\.\pipe\ShaoNian\query...`
- 窗口标题、托盘提示

### 1.2 隐私模式辅助进程

`RuntimeBroker_rustdesk.exe` → `RuntimeBroker_shaonian.exe`，共 3 处：

| 文件 | 说明 |
| --- | --- |
| `libs/portable/src/main.rs` | 常量 `WIN_TOPMOST_INJECTED_PROCESS_EXE`，以及 `taskkill /IM` 参数 |
| `src/privacy_mode/win_topmost_window.rs` | 同名常量 |
| `res/msi/CustomActions/CustomActions.cpp` | `DeleteRuntimeGeneratedFile(installFolder, L"...")` |
| `res/msi/Package/Components/RustDesk.wxs` | `TerminateBrokers.SetParam` 的 `Value` 属性 |

### 1.3 其他带品牌名的字符串

| 文件 | 原值 | 改为 |
| --- | --- | --- |
| `src/auth_2fa.rs` | `const ISSUER: &str = "RustDesk"` | `"ShaoNian"` |
| `src/whiteboard/windows.rs` | `.with_title("RustDesk whiteboard")` | `"ShaoNian whiteboard"` |
| `res/msi/CustomActions/RemotePrinter.cpp` | `RD_DEFAULT_APP_NAME = L"RustDesk"` | `L"ShaoNian"` |
| `src/platform/windows.rs` | `shaonian-sciter` 暂存目录、`ShaoNian.exe` 目标名、`ShaoNian Output` 对话框标题 | 已按此命名 |

> **不要改**：`librustdesk`（Rust cdylib 名，Flutter FFI 依赖它）、`rustdesk` crate 名、
> `rustdesk-org/*` 依赖、`com.carriez.*`（仅 Flutter 旧包名注释）。

---

## 2. 内置默认服务器与 API

全新安装（无 `custom-rendezvous-server`、无 `CONFIG2` 缓存）时使用下列编译期常量。

### 2.1 `libs/hbb_common/src/config.rs`

```rust
pub const RENDEZVOUS_SERVERS: &[&str] = &["rustdesk.vzzw.com"];
pub const RS_PUB_KEY: &str = "bh4JvONOwgQ+AWOR1vKbEiFcCpaJTz1CnjBKLtPusPw=";
// 原值分别为 "rs-ny.rustdesk.com" 和 "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw="
pub const API_SERVER: &str = "https://rustdesk.vzzw.com:21114";   // 新增
```

`API_SERVER` 必须单独定义，不能用 `RENDEZVOUS_SERVERS` 推导：后者推导出来的 scheme 是
`http://`，而这里需要 `https://`。

### 2.2 `src/common.rs` —— 让内置 API 生效

`get_api_server_()` 末尾原本硬编码回退到官方控制台：

```rust
// 改前
"https://admin.rustdesk.com".to_owned()
// 改后
config::API_SERVER.to_owned()
```

### 2.3 `src/common.rs` —— 保留 API 的 `:21114` 端口

`get_api_server()` 有一段逻辑：URL 以 `https` 开头且以 `:21114` 结尾、但
`allow-https-21114` 不为 `Y` 时，会**把端口去掉**。若不处理，上面的
`https://rustdesk.vzzw.com:21114` 会退化成 `https://rustdesk.vzzw.com`。

在 `get_builtin_option()` 里加内置默认值（`custom.txt` 仍然优先，因为它先填 `BUILTIN_SETTINGS`）：

```rust
#[inline]
pub fn get_builtin_option(key: &str) -> String {
    let v = config::BUILTIN_SETTINGS
        .read().unwrap().get(key).cloned().unwrap_or_default();
    if v.is_empty() {
        match key {
            "hide-powered-by-me" | "hide-network-settings" | "allow-https-21114" => {
                return "Y".to_owned()
            }
            _ => {}
        }
    }
    v
}
```

### 2.4 `src/common.rs` —— 隐藏「自建服务器」提示

上游 `using_public_server()` 只判断用户是否填了自定义服务器。由于我们把内置服务器换成了
自己的域名，它仍会误判为「公共服务器」，导致首页显示「如果需要更快连接速度，你可以选择自建服务器」，
并且连接时的画质弹窗会隐藏 FPS/画质选项。

```rust
#[inline]
pub fn using_public_server() -> bool {
    if !crate::get_custom_rendezvous_server(get_option("custom-rendezvous-server")).is_empty() {
        return false;
    }
    // 内置服务器不是 rustdesk.com 时，视为非公共服务器
    let builtin = config::RENDEZVOUS_SERVERS;
    builtin.is_empty() || builtin.iter().any(|s| s.to_lowercase().ends_with("rustdesk.com"))
}
```

### 2.5 端口推导规则（无需额外配置）

- ID 服务器 `rustdesk.vzzw.com:21116`
- 中继服务器 = ID 端口 +1 → `rustdesk.vzzw.com:21117`
  （`src/rendezvous_mediator.rs` 的 `get_relay_server` 调 `increase_port(host, 1)`）
- API 服务器 `https://rustdesk.vzzw.com:21114`（ID 端口 −2，但 scheme 为 https，故需常量）

---

## 3. 去除官方痕迹

### 3.1 统一到一个常量文件

新增 `flutter/lib/consts.dart` 常量，所有界面链接只引用这里，后续换域名只改一处：

```dart
const String kBrandWebsiteUrl = 'https://rustdesk.vzzw.com';
const String kBrandWebsiteLabel = 'rustdesk.vzzw.com';
const String kBrandPrivacyUrl = 'https://rustdesk.vzzw.com/privacy.html';
const String kBrandCopyright = '少年远程';
```

### 3.2 Flutter 界面替换

| 文件 | 原内容 | 改为 |
| --- | --- | --- |
| `desktop/pages/desktop_setting_page.dart` | 隐私声明 `https://rustdesk.com/privacy.html` | `kBrandPrivacyUrl` |
| `desktop/pages/desktop_setting_page.dart` | 网站 `https://rustdesk.com` | `kBrandWebsiteUrl` |
| `desktop/pages/desktop_setting_page.dart` | 版权行 `Purslane Tech Pte. Ltd.` | `$kBrandCopyright` |
| `desktop/pages/install_page.dart` | 许可协议链接与 Tooltip `rustdesk.com/privacy.html` | `kBrandPrivacyUrl`（并补 `consts.dart` 导入） |
| `desktop/pages/connection_page.dart` | `https://rustdesk.com/pricing` | `kBrandWebsiteUrl` |
| `desktop/pages/desktop_home_page.dart` | 更新按钮 `rustdesk.com/download`、Changelog GitHub 链接、3 处 Linux 帮助链接 | 均改为 `kBrandWebsiteUrl` |
| `mobile/pages/settings_page.dart` | 顶部 `const url`、隐私声明、关于弹窗链接文字 | `kBrand*` 常量 |
| `mobile/pages/connection_page.dart` | 更新按钮 `rustdesk.com/download` | `kBrandWebsiteUrl` |
| `common.dart` | `loadPowered()` 里的 `rustdesk.com` | `kBrandWebsiteUrl` |

### 3.3 Rust 侧帮助链接

| 文件 | 原值 |
| --- | --- |
| `libs/hbb_common/src/config.rs` | `LINK_DOCS_HOME`、`LINK_DOCS_X11_REQUIRED` → `https://rustdesk.vzzw.com/` |
| `src/client.rs` | `SCRAP_X11_REF_URL`、Wayland 登录错误框 `link` → `https://rustdesk.vzzw.com/` |
| `src/lang/en.rs` | `doc_mac_permission`、`doc_fix_wayland` → `https://rustdesk.vzzw.com/` |

### 3.4 Sciter 界面（仅 32 位回退用，但建议一并改）

`src/ui/index.tis`、`src/ui/install.tis` 中所有 `handler.open_url(...)` / `view.open_url(...)`
的 `rustdesk.com` 改为 `rustdesk.vzzw.com`，版权行的 `Purslane Tech Pte. Ltd.` 改为 `少年远程`。

### 3.5 保留项（重要）

- `src/common.rs` 的 `is_public()` 里的 `rustdesk.com` 判断**不要改**。它只用于识别
  「官方公共服务」来决定是否上报审计、是否开放 UDP/WebRTC 打洞，不展示给用户。
- 自动检查更新不必改：`check_software_update()` 首行是
  `if is_custom_client() { return; }`，`APP_NAME != "RustDesk"` 时直接返回，
  因此不会请求 `api.rustdesk.com`。

---

## 4. 版本信息与安装包元数据

### 4.1 可执行文件

| 文件 | 字段 | 值 |
| --- | --- | --- |
| `Cargo.toml` | `authors` | `["ShaoNian"]` |
| `Cargo.toml` | `[package.metadata.winres] LegalCopyright` | `Copyright (C) 2026 ShaoNian. All rights reserved.` |
| `Cargo.toml` | `[package.metadata.bundle] identifier` | `com.shaonian.remotedesk` |
| `libs/portable/Cargo.toml` | `LegalCopyright` | 同上 |
| `libs/base/Cargo.toml` | `authors` | `["ShaoNian"]` |
| `flutter/windows/runner/Runner.rc` | `CompanyName` / `LegalCopyright` | `ShaoNian` / 同上 |

> **必须用 ASCII**：版权与公司名字段保持 `ShaoNian`，不要写中文。`Runner.rc` 由 `rc.exe` 编译、
> `winres` 生成的资源脚本也没有可靠的多字节处理，中文会导致编译失败或乱码。

### 4.2 MSI

| 文件 | 改动 |
| --- | --- |
| `res/msi/preprocess.py` | `g_arpsystemcomponent` 的 `Contact`/`HelpLink`/`ReadMe` → `https://rustdesk.vzzw.com` |
| `res/msi/preprocess.py` | `--manufacturer` 默认值 `Purslane Tech Pte. Ltd.` → `ShaoNian` |
| `res/msi/preprocess.py` | `update_license_file()` 增加 `rustdesk.com` → `rustdesk.vzzw.com` 的两条 replace |
| `res/msi/Package/License.rtf` | 文本中的 `rustdesk.com` / `RustDesk` / `Purslane Tech Pte. Ltd.` 全部替换 |

> **MSI 厂商名与许可证必须用 ASCII**：`res/msi/Package/Language/Package.en-us.wxl` 是
> `Codepage="1252"`，中文会让 WiX 编译报错。中文品牌只出现在运行时界面与图标里。

改完 `License.rtf` 后建议校验 RTF 结构（花括号必须配对）：

```powershell
$t = [System.IO.File]::ReadAllText('res\msi\Package\License.rtf')
([regex]::Matches($t,'\{')).Count -eq ([regex]::Matches($t,'\}')).Count
```

### 4.3 RPM（可选，仅 Linux 打包）

`res/rpm.spec`、`res/rpm-flutter.spec`、`res/rpm-flutter-suse.spec` 的 `URL:` 与 `Vendor:`。

---

## 5. 图标与 Logo

### 5.1 需要替换的文件

| 文件 | 用途 |
| --- | --- |
| `res/icon.ico` | exe / dll 主图标（`build.rs` 通过 `winres::set_icon` 写入 PE 资源） |
| `res/tray-icon.ico` | 托盘图标（`src/tray.rs` 的 `include_bytes!`），保持单张 32×32 |
| `flutter/windows/runner/resources/app_icon.ico` | 窗口 / 任务栏 / 资源管理器 |
| `res/32x32.png`、`64x64.png`、`128x128.png`、`128x128@2x.png`、`icon.png`、`mac-icon.png` | 各平台打包 |
| `flutter/assets/logo_light.png`、`logo_dark.png`、`logo.png` | 首页顶部字标（亮色 / 暗色 / 兜底） |

### 5.2 用脚本生成

仓库内 `tools/gen_brand_icons.py` 会一次性生成以上全部文件（蓝底白色「少年」图标 +
「少年远程」横向字标）。依赖 Pillow：

```powershell
python -m pip install pillow
python tools/gen_brand_icons.py
```

手动制作时的要求：

- `res/icon.ico` 至少包含 16/32/48/64/128/256 六种尺寸
- `res/tray-icon.ico` 只放 32×32（多尺寸会让托盘图标变大）
- `flutter/assets/logo*.png` 高度 64px 左右，透明背景；暗色版文字需接近白色，
  否则在深色主题下不可见

### 5.3 `.gitignore` 例外（关键）

`.gitignore` 有 `*png` 规则，会把新生成的 logo 一起忽略，导致 Flutter 打包时缺文件。
必须加例外：

```gitignore
!flutter/assets/logo*.png
```

验证：

```bash
git check-ignore -v flutter/assets/logo.png   # 应输出 !flutter/assets/logo*.png
```

---

## 6. GitHub Actions 编译

### 6.1 工作流改动

| 位置 | 改动 |
| --- | --- |
| `on:` | 增加 `push: branches: [shaonian-build]`，向该分支推送即自动编译 |
| 便携 exe 输出 | `SignOutput/rustdesk-<ver>-<arch>.exe` → `ShaoNianDesk-<ver>-<arch>.exe` |
| MSI 输出 | `SignOutput/rustdesk-<ver>-<arch>.msi` → `ShaoNianDesk-<ver>-<arch>.msi` |
| `sha256sum` | 同步改为 `ShaoNianDesk-*.msi` |
| 签名 EXE / MSI 上传 `path` | 同步改名 |
| Release `files` | `ShaoNianDesk-*.msi`、`ShaoNianDesk-*.exe` |

只改**打包产物名**，`ShaoNian.exe` 与 `librustdesk.dll` 的磁盘名保持不变。

### 6.2 关键环境变量（已在工作流中）

```yaml
FLUTTER_VERSION: "3.24.5"
RUST_VERSION: "1.75"
VCPKG_COMMIT_ID: "9e593bb18ea69cc5095e012465dcd675a822ed0d"
VERSION: "1.5.0"
UPLOAD_ARTIFACT: "true"
PUBLISH_UPDATE_METADATA: "false"
SIGN_BASE_URL: "-2"      # 跳过签名，产出未签名包
```

构建命令：`python3 build.py --portable --flutter --skip-portable-pack --hwcodec --vram`

### 6.3 产物

| 位置 | 名称 |
| --- | --- |
| Actions artifact `rustdesk-unsigned-windows-x86_64` | 绿色版目录（含 `ShaoNian.exe`、`librustdesk.dll`、`data/`、`drivers/`） |
| Release 附件 | `ShaoNianDesk-1.5.0-x86_64.exe` |
| Release 附件 | `ShaoNianDesk-1.5.0-x86_64.msi` |

---

## 7. 验证清单

编译完成后按下表核对，全部通过才算成功。

### 7.1 二进制内容

从 MSI 解出 `librustdesk.dll` 后检查字符串：

```powershell
# 应包含
#   rustdesk.vzzw.com
#   bh4JvONOwgQ+AWOR1vKbEiFcCpaJTz1CnjBKLtPusPw=
# 不应包含
#   rustdesk.shaonian.cc      （旧域名）
#   rs-ny.rustdesk.com        （官方默认服务器）
#   OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=   （官方公钥）
#   admin.rustdesk.com        （官方 API 回退）
```

### 7.2 运行时行为

| 检查项 | 期望 |
| --- | --- |
| 全新安装后设置页「网络」 | 整页不出现（`hide-network-settings=Y`） |
| 首页页脚 | 无「由 RustDesk 提供支持」 |
| 首页连接提示 | 无「如需更快连接速度，可选择自建服务器」 |
| 连接后画质弹窗 | 显示 FPS / 画质选项（未被隐藏） |
| 设置 → 关于 | 显示「少年远程」版权，链接指向 `rustdesk.vzzw.com` |
| 任务管理器 / 托盘 / 开始菜单 | 均为新的「少年」图标 |
| 控制面板卸载项 | 发布者为 `ShaoNian`，支持链接指向 `rustdesk.vzzw.com` |

### 7.3 已知需要自行补的内容

`https://rustdesk.vzzw.com/privacy.html` 目前尚未部署，点击会 404，需要自行放页面。
若暂时不想外链，可把 `kBrandPrivacyUrl` 改成本地资源，或直接删除该入口。

---

## 8. 常见问题

**Q：改了 `APP_NAME` 后个别文案仍显示 RustDesk？**
`src/lang.rs` 的 `translate_locale()` 会在 `APP_NAME != "RustDesk"` 时把译文里的
`RustDesk` 批量替换成新名字，但 `powered_by_me` 和 `upgrade_rustdesk_server_pro_*`
是显式排除的。前者靠 `hide-powered-by-me=Y` 隐藏，后者只在连接 Server Pro 时出现。

**Q：MSI 编译报 codepage 错误？**
厂商名、许可证文本、`Runner.rc` 里的公司/版权字段都是 ASCII `ShaoNian`。
把中文写进去就会触发这个错误。

**Q：`git status` 看不到新 logo？**
被 `.gitignore` 的 `*png` 忽略了，见 5.3。

**Q：改完 ID 服务器后中继连不上？**
中继默认取 ID 端口 +1。如果服务器实际中继不在 21117，需要用
`relay-server` 选项显式指定，否则会连错端口。

**Q：`github.com:443` 无法访问怎么推送？**
可用 `api.github.com` 的 Git Data API（blobs → trees → commits → PATCH `refs/heads/<branch>`）
绕过对 `github.com` 的直接连接。
