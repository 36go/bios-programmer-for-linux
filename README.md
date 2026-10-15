# BIOS Programmer for Linux

[![Language: English](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)](README.md)
[![اللغة: العربية](https://img.shields.io/badge/lang-AR-16a34a?style=flat-square)](README.ar.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-333.svg)](#requirements)

A **native Linux port of [AsProgrammer / NeoProgrammer](https://github.com/nofeletru/UsbAsp-flash)** — a GUI tool to read, write, erase and verify memory chips over **SPI**, **I2C** and **MicroWire**, the same way "CH341A programmer" software works on Windows.

The original project talks to the hardware through Windows DLLs (`CH341DLL.DLL`, `CH347DLL.DLL`, `FTD2XX.DLL`). This port **removes the DLL dependency and re-implements the CH341 backend directly on `libusb`**, so it builds and runs on Linux (including WSL2 with WSLg) with the same GUI and the same `chiplist.xml`/settings model.

<p align="center">
  <img src="images.png" alt="BIOS Programmer for Linux running under WSLg" width="480">
</p>

---

## Table of contents

- [Features](#features)
- [Supported hardware](#supported-hardware)
- [Requirements](#requirements)
- [Build from source](#build-from-source)
- [Running](#running)
- [Project layout](#project-layout)
- [How the Windows DLLs were replaced](#how-the-windows-dlls-were-replaced)
- [Status & known limitations](#status--known-limitations)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

---

## Features

- Full Lazarus/GTK2 **graphical interface** (identical layout to the Windows build).
- Read / Write / Verify / Erase of EEPROM and Flash chips.
- Protocols: **SPI 25**, **SPI 45**, **SPI 95**, **I2C** and **MicroWire**.
- Huge built-in chip database (`chiplist.xml`) with automatic chip detection (JEDEC ID / CFI).
- Hex editor with fill / compare / dump, search, and register editor.
- Lua-like scripting engine (`scripts/`) for custom chip routines.
- Multiple UI translations (`lang/*.po`).

## Supported hardware

| Programmer | Status on Linux | Notes |
|---|---|---|
| **CH341A / CH341** | ✅ **Implemented** | Re-implemented on `libusb` (bulk EP `0x02`/`0x82`). Untested on physical silicon only because no device was available during the port. |
| USBasp | ✅ Expected to work | Uses the `libusb` backend already present upstream. |
| AVRISP-MKII | ✅ Expected to work | Uses the `libusb` backend already present upstream. |
| Arduino (serial) | ✅ Expected to work | Uses the portable serial backend (`synaser`). |
| **CH347** | ⚠️ Not yet | External DLL calls replaced with stubs so the app builds; not implemented. |
| **FT232H** | ⚠️ Not yet | `FTD2XX` calls replaced with stubs; not implemented. |

> If you have CH341 hardware, testing and bug reports are extremely welcome — see [Contributing](#contributing).

## Requirements

- A Linux desktop (X11 or Wayland-with-XWayland) — GTK2 widgetset by default.
- **[Free Pascal Compiler](https://www.freepascal.org/) 3.2+** and **[Lazarus](https://www.lazarus-ide.org/)** (`lazbuild`).
- **`libusb-0.1`** development files (`libusb-dev` / `libusb-0.1-4`).
- GTK2 development files (`libgtk2.0-dev`) *or* Qt5 (`libqt5pas-dev`).
- Lazarus packages: **TurboPowerIPro**, **SynEdit**, **mphexeditor**.

Debian/Ubuntu (including WSL):

```bash
sudo apt update
sudo apt install fpc lazarus libusb-dev libgtk2.0-dev python3
```

## Build from source

```bash
git clone https://github.com/36go/bios-programmer-for-linux.git
cd bios-programmer-for-linux/src

# (first time only) install the three required Lazarus packages, e.g.:
#   lazbuild --add-package-link /usr/lib/lazarus/*/components/synedit/synedit.lpk
#   ... plus TurboPowerIPro and mphexeditor

lazbuild AsProgrammer.lpi
./AsProgrammer
```

The project file (`AsProgrammer.lpi`) is already configured for **Linux / x86_64 / GTK2**, with output in `lang/` and units in `lib/`.

## Running

The application loads `chiplist.xml`, `settings.xml`, `scripts/` and `icons/` from its **current working directory**, so run it from `src/`:

```bash
cd src
./AsProgrammer
```

**CH341 permissions:** on most distros the device node is root-only. Create a udev rule so a normal user can access it (WCH `1a86:5512`):

```bash
sudo tee /etc/udev/rules.d/99-ch341a.rules <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="5512", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="5523", MODE="0666"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

The backend also tries to detach the in-kernel `spi-ch341`/`ch341` driver automatically if it has claimed the device.

## Project layout

```
.
├── src/                 # the application sources (build here)
│   ├── AsProgrammer.lpi # Lazarus project (Linux/x86_64/GTK2)
│   ├── ch341dll.pas     # CH341 API re-implemented on libusb  <-- port
│   ├── ch347dll.pas     # CH347 externals -> stubs             <-- port
│   ├── D2XXUnit.pas     # FTDI D2XX externals -> stubs         <-- port
│   ├── LibUSB01.pas     # libusb-0.1 bindings
│   ├── chiplist.xml     # chip database
│   ├── lang/ icons/ scripts/
│   └── ...
├── tools/               # scripts used to strip/rewrite the DLL bindings
├── docs/PORTING_NOTES.md
├── images.png           # screenshot used in this README
└── LICENSE
```

## How the Windows DLLs were replaced

The upstream code declares every hardware call as an `external '....DLL'` binding, which the Linux linker rejects. This port rewrites the three binding units (see `docs/PORTING_NOTES.md` and `tools/`):

- **`ch341dll.pas`** — all `external` clauses removed. The 10 functions actually used by `ch341hw.pas` are re-implemented in Pascal on top of `LibUSB01` (libusb-0.1): open/close with VID `1a86` / PID `5512` (or `5523`), bulk writes to EP `0x02`, bulk reads from EP `0x82`, the `0xA8` SPI stream framing, `0xAA` stream setup, and the `0xAB` UIO chip-select sequence. The remaining functions are safe stubs.
- **`ch347dll.pas`** — all externals replaced with stubs (backend not implemented yet).
- **`D2XXUnit.pas`** — all externals inlined as stubs (FT232H backend not implemented yet).

Re-apply the shims to a fresh copy of the original source with:

```bash
UPSTREAM=/path/to/AsProgrammer/software ./tools/apply_shims.sh ./src
```

## Status & known limitations

- ✅ **Builds** cleanly with `lazbuild` and **launches** as a GTK2 GUI.
- ✅ CH341 **SPI read/write path** implemented following the Linux kernel `spi-ch341` driver and `ch341prog` framing.
- ⚠️ The port was developed **without a physical programmer**, so the CH341 path is unverified against real hardware.
- ⚠️ I2C (`CH341StreamI2C`), MicroWire (`CH341BitStreamSPI`), `CH341SetOutput` and `CH341GetStatus` are **best-effort** and the most likely to need small corrections on hardware.
- ⚠️ CH347 and FT232H backends are currently stubs.

## Contributing

**This project is open for contribution — pull requests and issues are very welcome!** 🎉

Great places to start:

1. **Test with real hardware.** If you own a CH341A, try read/verify/write on a known chip and report results (chip model, distro, log). This is the single most valuable contribution.
2. **Implement the CH347 backend** (`ch347dll.pas`) — it is already stubbed and waiting for a `libusb` implementation.
3. **Implement the FT232H backend** (`D2XXUnit.pas`) via `libusb`.
4. **Refine the I2C / MicroWire paths** (`CH341StreamI2C`, `CH341BitStreamSPI`, `CH341SetOutput`, `CH341GetStatus`).
5. **Translations** — add or improve `src/lang/*.po`.
6. **Packaging** — AppImage / Flatpak / Debian packages, or a simple `Makefile`.

How to contribute:

```bash
# 1. Fork and clone
git clone https://github.com/<you>/bios-programmer-for-linux.git
# 2. Create a branch
git checkout -b feature/my-fix
# 3. Build & test
cd src && lazbuild AsProgrammer.lpi
# 4. Commit, push, and open a Pull Request
```

Please keep the original code style, and describe any hardware you tested against in your PR.

## Credits

- Original Windows application **AsProgrammer / NeoProgrammer** by **nofeletru** — <https://github.com/nofeletru/UsbAsp-flash>.
- CH341 USB protocol references: Linux kernel `drivers/spi/spi-ch341.c` and the `ch341prog` project.
- Linux port, libusb backend and build fixes: **36go**.

## License

Released under the **MIT License** — see [LICENSE](LICENSE). Original work © 2015 nofeletru; Linux port © 2026 36go.

---

[![Language: English](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)](README.md)
[![اللغة: العربية](https://img.shields.io/badge/lang-AR-16a34a?style=flat-square)](README.ar.md)
