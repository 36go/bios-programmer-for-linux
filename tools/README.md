# tools

Scripts used to remove the Windows-DLL dependency from the original AsProgrammer
source and replace the CH341 backend with a native `libusb` implementation.

| File | Purpose |
|---|---|
| `stub_unit.py` | Replace `external '...DLL'` declarations in a unit with no-op stubs. |
| `patch_ch341.py` | Rewrite `ch341dll.pas` with a full Pascal/libusb CH341 implementation. |
| `apply_shims.sh` | Restore the three binding units from a pristine upstream copy and run both scripts. |

## `stub_unit.py`

```
python3 stub_unit.py <inline|impl> <file.pas>
```

- `inline` — for units whose externals live in the **implementation** section
  (`D2XXUnit.pas`): the stub body replaces the `external` clause in place.
- `impl` — for units whose externals live in the **interface** section
  (`ch347dll.pas`): the `external` clause is removed and the stub bodies are
  appended inside the implementation section.

Both modes read/write the file as `latin-1` so non-ASCII (CP1251) source bytes
are preserved.

## `apply_shims.sh`

```
UPSTREAM=/path/to/AsProgrammer/software ./apply_shims.sh /path/to/linux/src
```

`UPSTREAM` must point at the original repository's `software/` directory (the
one that still contains the untouched `ch341dll.pas`, `ch347dll.pas` and
`D2XXUnit.pas`). The script copies those three files into the destination source
tree and applies the shims. It is idempotent because it always starts from the
pristine copies.

> The committed `src/` tree already contains the patched files, so you only need
> these scripts if you want to regenerate them from a fresh upstream checkout.
