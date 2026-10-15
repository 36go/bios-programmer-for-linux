# Porting notes — AsProgrammer / NeoProgrammer to Linux

This document records everything that was changed to make the project build and
run on Linux without the Windows DLLs.

## 1. Why it did not build

The upstream project binds every hardware operation to a Windows DLL with
`external '....DLL'` declarations, for example:

```pascal
function CH341OpenDevice(iIndex: ULONG): Longint; stdcall;
  external CH341_DLL_Name name 'CH341OpenDevice';
```

On Linux the linker cannot resolve these, so the build fails with unresolved
external symbols. The three offending units are:

| Unit | DLL | Used by |
|---|---|---|
| `ch341dll.pas` | `CH341DLL.DLL` | `ch341hw.pas` |
| `ch347dll.pas` | `CH347DLL.DLL` | `ch347hw.pas` |
| `D2XXUnit.pas` | `FTD2XX.DLL` | `ft232hhw.pas` |

## 2. Changes per unit

### `ch341dll.pas` — real libusb implementation

- Every `external` clause is removed.
- `uses LibUSB01;` is injected into the implementation section.
- **10 functions used by `ch341hw.pas` are re-implemented in Pascal on
  libusb-0.1** (`LibUSB01`):

  `CH341OpenDevice`, `CH341CloseDevice`, `CH341SetStream`, `CH341Set_D5_D0`,
  `CH341SetOutput`, `CH341StreamSPI4`, `CH341StreamI2C`, `CH341WriteData`,
  `CH341GetStatus`, `CH341BitStreamSPI`.

- All remaining functions become safe no-op stubs.

Device constants: VID `0x1A86`; PID `0x5512` (and clone `0x5523`); bulk OUT
endpoint `0x02`; bulk IN endpoint `0x82`.

Protocol framing follows the Linux kernel `drivers/spi/spi-ch341.c` driver and
the `ch341prog` project:

- SPI stream command `0xA8`, payload up to 31 bytes: send `[0xA8, data...]`
  (n+1 bytes), read back `n` bytes (MSB-first; no byte swapping).
- Stream setup `CH341SetStream` → `[0xAA, 0x60 | (mode & 7), 0x00]`.
- UIO stream `0xAB` used for chip-select: `OUT`/`DIR`/`END` sub-commands to
  drive the CS line on D0/D1/D2.
- `CH341Set_D5_D0` → `[0xAB, OUT|data, DIR|dir, END]`.
- `CH341SetOutput` (I2C line control) → `[0xA1, data>>8, dir>>8, data, dir, data>>16]`.

### `ch347dll.pas` and `D2XXUnit.pas` — stubs

These backends are **not implemented** on Linux yet. Their externals are
replaced with stubs so the application compiles and the rest of the tool is
usable:

- `ch347dll.pas`: externals removed from the interface declarations, stub bodies
  appended inside the implementation.
- `D2XXUnit.pas`: externals are declared in the *implementation* section, so the
  stub bodies are inlined in place of each `external` clause.

## 3. Other Linux fixes

- `LibUSB.pas` renamed to `LibUSB01.pas` (`unit LibUSB01;`) to avoid clashing
  with other units in the tree; `uses` updated in `avrisphw.pas`,
  `usbasphw.pas`, `usbhid.pas`.
- `pascalc.pas` / `synautil.pas` contain x86 assembler that does not compile on
  FPC 3.2 / x86_64 (`UpCaseR`, an `Alpha` set literal). Minimal, encoding-safe
  edits were applied. **These files are CP1251/ISO-8859 encoded — patch them
  with byte-preserving tools, never with a UTF-8 re-encoding editor.**
- `AsProgrammer.lpi` configured for Linux/x86_64/GTK2 (`PathDelim`, `OutDir=lang`,
  `UnitOutputDirectory=lib/$(TargetCPU)-$(TargetOS)`, `TargetOS=linux`,
  `TargetCPU=x86_64`).

## 4. Tooling

The scripts in `../tools/` reproduce the DLL stripping/rewriting:

- `stub_unit.py <inline|impl> <file>` — replace `external` clauses with stubs.
- `patch_ch341.py <file>` — full libusb CH341 implementation.
- `apply_shims.sh` — restores the three units from a pristine upstream copy and
  applies both scripts.

## 5. Unverified / best-effort

Developed without physical hardware, so these paths are unverified and are the
most likely to need correction on a real device:

- real SPI read/write on a chip;
- `CH341StreamI2C` (I2C EEPROM);
- `CH341BitStreamSPI` (MicroWire);
- `CH341SetOutput` / `CH341GetStatus` (I2C bit-bang line readback).

If you can test on hardware, please open an issue/PR with logs.
