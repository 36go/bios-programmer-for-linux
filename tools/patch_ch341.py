#!/usr/bin/env python3
# Rewrite ch341dll.pas so that the CH341 API is backed by libusb (Linux).
# - strips all `external 'CH341DLL.DLL'` clauses
# - injects `uses LibUSB01;` into the implementation section
# - provides real libusb implementations for the 10 functions used by ch341hw.pas
# - stubs every remaining function
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'ch341dll.pas'

CUSTOM_NAMES = {
    'ch341opendevice', 'ch341closedevice', 'ch341setstream', 'ch341set_d5_d0',
    'ch341setoutput', 'ch341streamspi4', 'ch341streami2c', 'ch341writedata',
    'ch341getstatus', 'ch341bitstreamspi',
}

CUSTOM_IMPL = r'''
function usb_detach_kernel_driver_np(dev: pusb_dev_handle; iinterface: longword): longword; cdecl; external LIBUSB_DLL_NAME name 'usb_detach_kernel_driver_np';

var
  GHandles: array[0..mCH341_MAX_NUMBER-1] of pusb_dev_handle;
  GHighOut: array[0..mCH341_MAX_NUMBER-1] of cardinal;
  GLibusbInit: boolean = False;

function CH341_Handle(iIndex: cardinal): pusb_dev_handle;
begin
  Result := nil;
  if iIndex < cardinal(mCH341_MAX_NUMBER) then
    Result := GHandles[iIndex];
end;

function CH341_BulkOut(h: pusb_dev_handle; buf: pointer; len: cardinal): integer;
begin
  Result := usb_bulk_write(h, mCH341_ENDP_DATA_DOWN, pbyte(buf)^, len, 5000);
end;

function CH341_BulkIn(h: pusb_dev_handle; buf: pointer; len: cardinal): integer;
begin
  Result := usb_bulk_read(h, mCH341_ENDP_DATA_UP, pbyte(buf)^, len, 5000);
end;

procedure CH341_UIO_CS(h: pusb_dev_handle; csPin: cardinal; assertcs: boolean);
var
  pkt: array[0..3] of byte;
  selbit, outb: byte;
begin
  selbit := 1 shl (csPin and 3);
  if assertcs then
    outb := $36 and (not selbit)
  else
    outb := $36 or selbit;
  pkt[0] := mCH341A_CMD_UIO_STREAM;
  pkt[1] := mCH341A_CMD_UIO_STM_OUT or (outb and $3F);
  pkt[2] := mCH341A_CMD_UIO_STM_DIR or $3F;
  pkt[3] := mCH341A_CMD_UIO_STM_END;
  CH341_BulkOut(h, @pkt[0], 4);
end;

function CH341OpenDevice(iIndex: cardinal): integer; stdcall;
var
  bus: pusb_bus;
  dev: pusb_device;
  h: pusb_dev_handle;
  count: cardinal;
begin
  Result := -1;
  if iIndex >= cardinal(mCH341_MAX_NUMBER) then Exit;
  if GHandles[iIndex] <> nil then
  begin
    Result := integer(iIndex);
    Exit;
  end;
  if not GLibusbInit then
  begin
    usb_init;
    GLibusbInit := True;
  end;
  usb_find_busses;
  usb_find_devices;
  count := 0;
  bus := usb_get_busses;
  while bus <> nil do
  begin
    dev := bus^.devices;
    while dev <> nil do
    begin
      if (dev^.descriptor.idVendor = $1A86) and
         ((dev^.descriptor.idProduct = $5512) or (dev^.descriptor.idProduct = $5523)) then
      begin
        if count = iIndex then
        begin
          h := usb_open(dev);
          if h <> nil then
          begin
            usb_set_configuration(h, 1);
            if integer(usb_claim_interface(h, 0)) < 0 then
            begin
              usb_detach_kernel_driver_np(h, 0);
              usb_claim_interface(h, 0);
            end;
            GHandles[iIndex] := h;
            GHighOut[iIndex] := 0;
            Result := integer(iIndex);
            Exit;
          end;
        end;
        Inc(count);
      end;
      dev := dev^.next;
    end;
    bus := bus^.next;
  end;
end;

procedure CH341CloseDevice(iIndex: cardinal); stdcall;
var
  h: pusb_dev_handle;
begin
  h := CH341_Handle(iIndex);
  if h <> nil then
  begin
    usb_release_interface(h, 0);
    usb_close(h);
    GHandles[iIndex] := nil;
  end;
end;

function CH341SetStream(iIndex: cardinal; iMode: cardinal): boolean; stdcall;
var
  pkt: array[0..2] of byte;
  h: pusb_dev_handle;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  pkt[0] := mCH341A_CMD_I2C_STREAM;
  pkt[1] := mCH341A_CMD_I2C_STM_SET or (byte(iMode) and $07);
  pkt[2] := mCH341A_CMD_I2C_STM_END;
  Result := CH341_BulkOut(h, @pkt[0], 3) >= 0;
end;

function CH341Set_D5_D0(iIndex: cardinal; iSetDirOut: cardinal; iSetDataOut: cardinal): boolean; stdcall;
var
  pkt: array[0..3] of byte;
  h: pusb_dev_handle;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  pkt[0] := mCH341A_CMD_UIO_STREAM;
  pkt[1] := mCH341A_CMD_UIO_STM_OUT or (byte(iSetDataOut) and $3F);
  pkt[2] := mCH341A_CMD_UIO_STM_DIR or (byte(iSetDirOut) and $3F);
  pkt[3] := mCH341A_CMD_UIO_STM_END;
  Result := CH341_BulkOut(h, @pkt[0], 4) >= 0;
end;

function CH341SetOutput(iIndex: cardinal; iEnable: cardinal; iSetDirOut: cardinal; iSetDataOut: cardinal): boolean; stdcall;
var
  pkt: array[0..5] of byte;
  h: pusb_dev_handle;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  pkt[0] := mCH341A_CMD_SET_OUTPUT;
  pkt[1] := byte(iSetDataOut shr 8);
  pkt[2] := byte(iSetDirOut shr 8);
  pkt[3] := byte(iSetDataOut);
  pkt[4] := byte(iSetDirOut);
  pkt[5] := byte(iSetDataOut shr 16);
  if (iEnable and $10) <> 0 then
    GHighOut[iIndex] := (iSetDataOut shr 16) and $FF;
  Result := CH341_BulkOut(h, @pkt[0], 6) >= 0;
end;

function CH341StreamSPI4(iIndex: cardinal; iChipSelect: cardinal; iLength: cardinal; ioBuffer: PVOID): boolean; stdcall;
var
  h: pusb_dev_handle;
  p: pbyte;
  remaining, chunk, n: integer;
  pkt: array[0..31] of byte;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  p := pbyte(ioBuffer);
  remaining := integer(iLength);
  if (iChipSelect and $80) <> 0 then
    CH341_UIO_CS(h, iChipSelect and 3, True);
  while remaining > 0 do
  begin
    chunk := remaining;
    if chunk > 31 then chunk := 31;
    FillChar(pkt, 32, 0);
    pkt[0] := mCH341A_CMD_SPI_STREAM;
    Move(p^, pkt[1], chunk);
    if CH341_BulkOut(h, @pkt[0], cardinal(chunk + 1)) < 0 then
    begin
      if (iChipSelect and $80) <> 0 then CH341_UIO_CS(h, iChipSelect and 3, False);
      Exit;
    end;
    n := CH341_BulkIn(h, @pkt[0], cardinal(chunk));
    if n < 0 then
    begin
      if (iChipSelect and $80) <> 0 then CH341_UIO_CS(h, iChipSelect and 3, False);
      Exit;
    end;
    Move(pkt[0], p^, chunk);
    Inc(p, chunk);
    Dec(remaining, chunk);
  end;
  if (iChipSelect and $80) <> 0 then
    CH341_UIO_CS(h, iChipSelect and 3, False);
  Result := True;
end;

function CH341WriteData(iIndex: cardinal; iBuffer: PVOID; ioLength: PULONG): boolean; stdcall;
var
  h: pusb_dev_handle;
  n: integer;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  n := CH341_BulkOut(h, iBuffer, ioLength^);
  if n >= 0 then
  begin
    ioLength^ := cardinal(n);
    Result := True;
  end;
end;

function CH341StreamI2C(iIndex: cardinal; iWriteLength: cardinal; iWriteBuffer: pvoid; iReadLength: cardinal; oReadBuffer: pvoid): boolean; stdcall;
var
  h: pusb_dev_handle;
  wp, rp: pbyte;
  cmd: array of byte;
  idx: integer;
  n: integer;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  wp := pbyte(iWriteBuffer);
  rp := pbyte(oReadBuffer);
  SetLength(cmd, 4 + integer(iWriteLength) + 4);
  idx := 0;
  cmd[idx] := mCH341A_CMD_I2C_STREAM; Inc(idx);
  cmd[idx] := mCH341A_CMD_I2C_STM_STA; Inc(idx);
  if iWriteLength > 0 then
  begin
    cmd[idx] := mCH341A_CMD_I2C_STM_OUT or (byte(iWriteLength) and $3F); Inc(idx);
    Move(wp^, cmd[idx], iWriteLength);
    Inc(idx, integer(iWriteLength));
  end;
  if iReadLength > 0 then
  begin
    cmd[idx] := mCH341A_CMD_I2C_STM_STA; Inc(idx);
    cmd[idx] := mCH341A_CMD_I2C_STM_IN or (byte(iReadLength) and $3F); Inc(idx);
  end;
  cmd[idx] := mCH341A_CMD_I2C_STM_STO; Inc(idx);
  cmd[idx] := mCH341A_CMD_I2C_STM_END; Inc(idx);
  if CH341_BulkOut(h, @cmd[0], cardinal(idx)) < 0 then Exit;
  if iReadLength > 0 then
  begin
    n := CH341_BulkIn(h, rp, iReadLength);
    if n < 0 then Exit;
  end;
  Result := True;
end;

function CH341GetStatus(iIndex: cardinal; iStatus: PULONG): boolean; stdcall;
var
  h: pusb_dev_handle;
  pkt: array[0..2] of byte;
  rd: array[0..7] of byte;
  n: integer;
  st: cardinal;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  pkt[0] := mCH341A_CMD_UIO_STREAM;
  pkt[1] := mCH341A_CMD_UIO_STM_IN;
  pkt[2] := mCH341A_CMD_UIO_STM_END;
  st := 0;
  if CH341_BulkOut(h, @pkt[0], 3) >= 0 then
  begin
    n := CH341_BulkIn(h, @rd[0], 4);
    if n > 0 then
      st := rd[0];
  end;
  if (GHighOut[iIndex] and $08) <> 0 then
    st := st or $00800000;
  iStatus^ := st;
  Result := True;
end;

function CH341BitStreamSPI(iIndex: cardinal; iLength: cardinal; ioBuffer: PVOID): boolean; stdcall;
var
  h: pusb_dev_handle;
  p: pbyte;
  bits, i, n: integer;
  pkt: array[0..5] of byte;
  rb: byte;
  sig: byte;
begin
  Result := False;
  h := CH341_Handle(iIndex);
  if h = nil then Exit;
  p := pbyte(ioBuffer);
  bits := integer(iLength);
  if bits <= 0 then
  begin
    Result := True;
    Exit;
  end;
  for i := 0 to bits - 1 do
  begin
    sig := p[i] and $37;
    pkt[0] := mCH341A_CMD_UIO_STREAM;
    pkt[1] := mCH341A_CMD_UIO_STM_OUT or (sig and $3F);
    pkt[2] := mCH341A_CMD_UIO_STM_OUT or ((sig or $08) and $3F);
    pkt[3] := mCH341A_CMD_UIO_STM_OUT or (sig and $3F);
    pkt[4] := mCH341A_CMD_UIO_STM_IN;
    pkt[5] := mCH341A_CMD_UIO_STM_END;
    if CH341_BulkOut(h, @pkt[0], 6) < 0 then Exit;
    n := CH341_BulkIn(h, @rb, 1);
    if n < 0 then Exit;
    if (rb and $80) <> 0 then p[i] := p[i] or $80 else p[i] := p[i] and $7F;
    if (rb and $40) <> 0 then p[i] := p[i] or $40 else p[i] := p[i] and $BF;
  end;
  Result := True;
end;
'''

EXT_RE = re.compile(r'[Ee]xternal\s+[^;\n]*;')
FUNC_RE = re.compile(r'\b(function|procedure)\b', re.IGNORECASE)

RET_LITERAL = {
    'boolean': 'False',
    'byte': '0', 'word': '0', 'smallint': '0',
    'integer': '0', 'longint': '0', 'cardinal': '0', 'longword': '0',
    'dword': '0', 'ft_result': '0', 'qword': '0', 'int64': '0',
    'pointer': 'nil', 'pvoid': 'nil', 'pchar': 'nil', 'pbyte': 'nil',
    'pbytearray': 'nil', 'pulong': 'nil', 'pcardinal': 'nil',
}


def clean(header):
    header = re.sub(r'//[^\n]*', '', header)
    header = re.sub(r'\{[^}]*\}', '', header, flags=re.S)
    return header


def build_stub(header, kind):
    stripped = clean(header).rstrip()
    if kind == 'procedure':
        return stripped + '\nbegin\nend;\n'
    rp = stripped.rfind(')')
    ret = 'integer'
    if rp != -1:
        m = re.search(r':\s*([A-Za-z_][A-Za-z0-9_\.]*)', stripped[rp:])
        if m:
            ret = m.group(1)
    return stripped + '\nbegin\n  Result := ' + RET_LITERAL.get(ret.lower(), 'Default(%s)' % ret) + ';\nend;\n'


def main():
    with open(PATH, 'r', encoding='latin-1') as f:
        text = f.read()

    matches = list(EXT_RE.finditer(text))
    stubs = []
    name_re = re.compile(r'\b(function|procedure)\s+([A-Za-z_]\w*)', re.IGNORECASE)
    skipped = 0
    for m in matches:
        pre = text[:m.start()]
        km = None
        for f2 in FUNC_RE.finditer(pre):
            km = f2
        if km is None:
            continue
        header = pre[km.start():m.start()]
        nm = name_re.search(clean(header))
        fname = nm.group(2).lower() if nm else ''
        if fname in CUSTOM_NAMES:
            skipped += 1
            continue
        stubs.append(build_stub(header, km.group(1).lower()))

    # remove all external clauses
    newtext = EXT_RE.sub('', text)

    # inject uses into implementation
    newtext = re.sub(r'(?m)^implementation\b', 'implementation\nuses LibUSB01;\n', newtext, count=1)

    idx = newtext.rfind('end.')
    if idx == -1:
        sys.stderr.write('error: no final end.\n')
        return 1
    inserted = '\n' + CUSTOM_IMPL + '\n' + '\n'.join(stubs) + '\n'
    newtext = newtext[:idx] + inserted + newtext[idx:]

    with open(PATH, 'w', encoding='latin-1') as f:
        f.write(newtext)
    print('%s: %d externals, %d custom impls, %d stubs' % (PATH, len(matches), skipped, len(stubs)))
    return 0


sys.exit(main())
