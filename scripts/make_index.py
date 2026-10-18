#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 debs/ 目录，为每个 .deb 生成 APT 索引（Packages）。

用法：
    python make_index.py            # 扫描本目录下的 debs/，重写 Packages
    python make_index.py debs       # 指定目录

原理：deb 是 ar 归档，取出其中的 control.tar.*，读里面的 control 字段，
再补上 Filename / Size / SHA256 / Installed-Size，就是 APT 要的索引条目。
纯标准库，不需要 dpkg-deb，Windows 上也能跑。
"""
import sys, os, io, gzip, lzma, bz2, hashlib, tarfile, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "scripts" else HERE

# 索引里要出现在前面的字段顺序（其余字段按 control 原顺序追加）
PRIORITY = [
    "Package", "Name", "Version", "Architecture", "Section",
    "Priority", "Depends", "Pre-Depends", "Conflicts", "Replaces",
    "Provides", "Installed-Size", "Author", "Maintainer",
    "Filename", "Size", "SHA256", "Description",
]


def read_ar(path):
    """最小 ar 解析器，返回 [(name, bytes), ...]"""
    data = open(path, "rb").read()
    if not data.startswith(b"!<arch>\n"):
        raise ValueError("不是 deb（ar 头不对）")
    off, out = 8, []
    while off + 60 <= len(data):
        hdr = data[off:off + 60]
        name = hdr[0:16].decode("ascii", "replace").strip().rstrip("/")
        try:
            size = int(hdr[48:58].decode("ascii").strip())
        except ValueError:
            break
        body = data[off + 60: off + 60 + size]
        out.append((name, body))
        off += 60 + size + (size % 2)
    return out


def control_of(path):
    """从 deb 里取出 control 文本"""
    for name, body in read_ar(path):
        if not name.startswith("control.tar"):
            continue
        if name.endswith(".gz"):
            raw = gzip.decompress(body)
        elif name.endswith(".xz") or name.endswith(".lzma"):
            raw = lzma.decompress(body)
        elif name.endswith(".bz2"):
            raw = bz2.decompress(body)
        else:
            raw = body
        with tarfile.open(fileobj=io.BytesIO(raw)) as t:
            for m in t.getmembers():
                base = os.path.basename(m.name)
                if base == "control":
                    return t.extractfile(m).read().decode("utf-8", "replace")
    raise ValueError("deb 里没有 control")


def parse_control(text):
    """control 文本 -> 有序 dict（支持续行）"""
    fields, key = {}, None
    for line in text.replace("\r\n", "\n").split("\n"):
        if not line.strip():
            continue
        if line[0] in " \t" and key:
            fields[key] += "\n" + line
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        fields[key] = val.strip()
    return fields


def stanza(fields, filename, size, sha256):
    merged = dict(fields)
    merged["Filename"] = filename
    merged["Size"] = str(size)
    merged["SHA256"] = sha256

    order = [f for f in PRIORITY if f in merged]
    order += [k for k in merged if k not in order]

    lines = []
    for k in order:
        v = merged[k]
        if k == "Description" and "\n" in v:
            first, rest = v.split("\n", 1)
            lines.append(f"{k}: {first}")
            lines.append(rest)
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def main():
    debdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "debs")
    if not os.path.isdir(debdir):
        sys.exit(f"目录不存在：{debdir}")

    debs = sorted(f for f in os.listdir(debdir) if f.lower().endswith(".deb"))
    if not debs:
        sys.exit(f"{debdir} 里没有 .deb")

    entries = []
    for fn in debs:
        full = os.path.join(debdir, fn)
        raw = open(full, "rb").read()
        fields = parse_control(control_of(full))
        rel = "debs/" + fn
        entries.append((fields, rel, len(raw), hashlib.sha256(raw).hexdigest()))
        print(f"  + {fields.get('Package','?'):32s} {fields.get('Version','?'):10s} "
              f"{len(raw):>7d} B  {fn}")

    # 同一个包多个版本时，新版本排前面
    def vkey(e):
        v = e[0].get("Version", "0")
        nums = [int(x) for x in re.findall(r"\d+", v)[:4]]
        return (e[0].get("Package", ""), [-n for n in nums])
    entries.sort(key=vkey)

    body = "\n\n".join(stanza(f, r, s, h) for f, r, s, h in entries) + "\n"
    out = os.path.join(ROOT, "Packages")
    with open(out, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(body)
    print(f"\n✅ 已生成 {out}（{len(entries)} 个包，{len(body)} 字节）")


if __name__ == "__main__":
    main()
