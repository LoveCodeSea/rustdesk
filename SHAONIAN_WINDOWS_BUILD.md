# ShaoNian Windows Client Build

This tree is rebranded from RustDesk. The Windows process, service, IPC pipe, config directory, and installer product name are `ShaoNian`.

This environment is Linux. Produce the Windows package on a Windows machine or GitHub Actions.

## What changes after this rebrand

| Item | Value |
| --- | --- |
| Task Manager process | `ShaoNian.exe` |
| Windows service name | `ShaoNian` |
| Install path | `%ProgramFiles%\ShaoNian\ShaoNian.exe` |
| Config directory | `%APPDATA%\ShaoNian` |
| IPC pipe | `\\.\pipe\ShaoNian\query...` |
| Privacy helper process | `RuntimeBroker_shaonian.exe` |

## Build machine

Use Windows 10/11 x64 with:

- Visual Studio 2022 (Desktop development with C++)
- Rust stable (`rustup` default toolchain)
- Flutter 3.24.5 (x64; match `.github/workflows/flutter-build.yml`)
- Python 3
- Git
- [vcpkg](https://github.com/microsoft/vcpkg)
- LLVM / clang-cl on PATH (Flutter Windows build)

## One-time setup

```bat
git clone --depth 1 https://github.com/microsoft/vcpkg C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
setx VCPKG_ROOT C:\vcpkg
```

Restart the terminal, then:

```bat
vcpkg install libvpx:x64-windows-static libyuv:x64-windows-static opus:x64-windows-static aom:x64-windows-static
```

Clone this source (already rebranded) and init the submodule:

```bat
git submodule update --init --recursive --depth 1
```

## Flutter Windows package

From the repo root:

```bat
python3 build.py --portable --flutter --hwcodec
```

Outputs:

- Unpacked Flutter app: `flutter\build\windows\x64\runner\Release\ShaoNian.exe`
- Portable installer: `ShaoNian-<version>-install.exe`

Skip packing and keep the Release folder only:

```bat
python3 build.py --portable --flutter --skip-portable-pack --hwcodec
```

## MSI installer

After a Flutter build, copy the Release folder and run WiX preprocess with the new name:

```bat
python res\msi\preprocess.py --arp -d ..\..\path\to\Release --app-name ShaoNian
```

`Release` must contain `ShaoNian.exe`. Then build `res\msi\msi.sln` with MSBuild (Release / x64).

## GitHub Actions

The Windows job in `.github/workflows/flutter-build.yml` already points at `ShaoNian.exe`. Run that workflow on a Windows runner to get signed/unsigned artifacts.

## Notes

- Do not rename `ShaoNian.exe` after compile. Service name, IPC, and install path come from `APP_NAME`.
- `librustdesk.dll` stays as the Rust cdylib name. Changing it would break Flutter FFI.
- UI strings that contain `RustDesk` are rewritten at runtime because `APP_NAME` is no longer `RustDesk`.
