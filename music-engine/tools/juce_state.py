"""Decode/encode JUCE plugin state blobs (MemoryBlock base64 + VST3 'VC2!' XML wrapper)."""
import re, zlib
CH = ".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+"
def jb64_decode(s):
    n, data = s.split(".", 1)
    n = int(n); out = bytearray(n); pos = 0
    for c in data:
        v = CH.index(c)
        for b in range(6):
            if (v >> b) & 1 and (pos + b) // 8 < n: out[(pos + b) // 8] |= 1 << ((pos + b) % 8)
        pos += 6
    return bytes(out)
def jb64_encode(b):
    bits = len(b) * 8; out = []
    for pos in range(0, bits, 6):
        v = 0
        for k in range(6):
            p = pos + k
            if p < bits and (b[p // 8] >> (p % 8)) & 1: v |= 1 << k
        out.append(CH[v])
    return f"{len(b)}." + "".join(out)
def vst3_inner(state_bytes):
    m = re.search(rb"<IComponent>(.*?)</IComponent>", state_bytes, re.S)
    return jb64_decode(m.group(1).decode())


def splice_state(template_vst3_state, plugin_xml):
    """Return a DawDreamer/VST3 state with plugin_xml (Splice INSTRUMENT processor XML) inside."""
    import struct
    raw = template_vst3_state
    inner = bytearray(vst3_inner(raw))
    off = 16 + 8 + 20 + 128                     # VstW header + CcnK/size + FBCh fields + future[128]
    csize = struct.unpack(">I", inner[off:off + 4])[0]
    chunk = bytes(inner[off + 4: off + 4 + csize])
    assert chunk[:4] == b"VC2!"
    xlen = struct.unpack("<I", chunk[4:8])[0]
    rest = chunk[8 + xlen + 1:]                 # JUCEPrivateData etc. after xml + null
    x = plugin_xml.encode()
    newchunk = b"VC2!" + struct.pack("<I", len(x)) + x + b"\0" + rest
    delta = len(newchunk) - csize
    inner[20:24] = struct.pack(">I", struct.unpack(">I", inner[20:24])[0] + delta)   # CcnK byteSize
    inner = inner[:off] + struct.pack(">I", len(newchunk)) + newchunk + inner[off + 4 + csize:]
    import re
    oxml_start = raw.index(b"<?xml"); oxml = raw[oxml_start:].rstrip(b"\0")
    oxml = re.sub(rb"<IComponent>.*?</IComponent>", b"<IComponent>" + jb64_encode(bytes(inner)).encode() + b"</IComponent>", oxml, flags=re.S)
    return b"VC2!" + struct.pack("<I", len(oxml)) + oxml + b"\0"


def patched_xml(base_xml, family, name, patch):
    import re
    x = re.sub(r'<META family="[^"]*" name="[^"]*"', f'<META family="{family}" name="{name}"', base_xml)
    x = re.sub(r'(<SETTING id="a_name" value=")[^"]*', r'\g<1>' + patch, x)
    return x
