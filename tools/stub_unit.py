#!/usr/bin/env python3
# Replace Windows DLL `external` declarations with in-Pascal stubs.
# Usage: stub_unit.py <mode> <file.pas>
#   mode=inline : function bodies inserted where the external clause was
#                 (for functions declared in the implementation section, e.g. D2XXUnit)
#   mode=impl   : external clause removed from interface decls, stub bodies
#                 appended inside the implementation section (e.g. ch347dll)
import re
import sys

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


def result_value(ret):
    return RET_LITERAL.get(ret.lower(), 'Default(%s)' % ret)


def build_snippet(header, kind):
    stripped = clean(header).rstrip()
    if kind == 'procedure':
        return 'begin\nend;\n'
    rp = stripped.rfind(')')
    ret = 'integer'
    if rp != -1:
        m = re.search(r':\s*([A-Za-z_][A-Za-z0-9_\.]*)', stripped[rp:])
        if m:
            ret = m.group(1)
    return 'begin\n  Result := ' + result_value(ret) + ';\nend;\n'


def build_body(header, kind, with_header):
    snippet = build_snippet(header, kind)
    if not with_header:
        return snippet
    return clean(header).rstrip() + '\n' + snippet


def main():
    if len(sys.argv) != 3:
        sys.stderr.write('usage: stub_unit.py <inline|impl> <file>\n')
        return 2
    mode, path = sys.argv[1], sys.argv[2]
    with open(path, 'r', encoding='latin-1') as f:
        text = f.read()

    matches = list(EXT_RE.finditer(text))
    bodies = []
    for m in matches:
        pre = text[:m.start()]
        km = None
        for f2 in FUNC_RE.finditer(pre):
            km = f2
        if km is None:
            sys.stderr.write('warning: no function header before %r\n' % m.group(0))
            bodies.append('')
            continue
        bodies.append(build_body(pre[km.start():m.start()], km.group(1).lower(),
                                 mode == 'impl'))

    if mode == 'inline':
        out = []
        last = 0
        for i, m in enumerate(matches):
            out.append(text[last:m.start()])
            out.append(bodies[i])
            last = m.end()
        out.append(text[last:])
        newtext = ''.join(out)
    elif mode == 'impl':
        newtext = EXT_RE.sub('', text)
        idx = newtext.rfind('end.')
        if idx == -1:
            sys.stderr.write('error: no final "end."\n')
            return 1
        newtext = newtext[:idx] + '\n' + '\n'.join(bodies) + '\n' + newtext[idx:]
    else:
        sys.stderr.write('unknown mode %s\n' % mode)
        return 2

    with open(path, 'w', encoding='latin-1') as f:
        f.write(newtext)
    print('%s [%s]: %d external declarations stubbed' % (path, mode, len(matches)))
    return 0


sys.exit(main())
