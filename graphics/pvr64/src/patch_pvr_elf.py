#!/usr/bin/env python3
import os
import struct
import shutil

BASE_IN = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/dist/vendor-pvr64/lib64"
BASE_OUT = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/dist/vendor-pvr64/patched/lib64"

PVR_LIBS = [
    "libsrv_um.so",
    "libIMGegl.so",
    "libusc.so",
    "libglslcompiler.so",
    "libPVRMtkutils.so",
    "libgralloc_extra.so",
    "libmpvr.so",
    "egl/libEGL_mtk.so",
    "egl/libGLESv2_mtk.so",
    "egl/libGLESv1_CM_mtk.so",
    "hw/gralloc.rogue.so",
]

KEEP_NEEDED = {
    "libsrv_um.so",
    "libIMGegl.so",
    "libusc.so",
    "libglslcompiler.so",
    "libPVRMtkutils.so",
    "libgralloc_extra.so",
    "libmpvr.so",
    "libEGL_mtk.so",
    "libGLESv2_mtk.so",
    "libGLESv1_CM_mtk.so",
    "gralloc.rogue.so",
}

RENAME_SYMS = {
    "pthread_mutex_init": "b_mutex_init",
    "pthread_mutex_lock": "b_mutex_lock",
    "pthread_mutex_trylock": "b_mutex_trylock",
    "pthread_mutex_unlock": "b_mutex_unlock",
    "pthread_mutex_destroy": "b_mutex_destroy",
    "pthread_mutexattr_init": "b_mutexattr_init",
    "pthread_mutexattr_settype": "b_mutexattr_settype",
    "pthread_mutexattr_destroy": "b_mutexattr_destroy",
    "pthread_cond_init": "b_cond_init",
    "pthread_cond_wait": "b_cond_wait",
    "pthread_cond_timedwait": "b_cond_timedwait",
    "pthread_cond_signal": "b_cond_signal",
    "pthread_cond_broadcast": "b_cond_broadcast",
    "pthread_cond_destroy": "b_cond_destroy",
    "setjmp": "bsetjm",
    "longjmp": "blongjm",
    "dlopen": "bdlopn",
    "sysconf": "bsyscon",
    "memset": "bmemst",
    "__memset_chk": "b_memset_chk",
    "memcpy": "bmemcp",
    "__memcpy_chk": "b_memcpy_chk",
}

DT_NEEDED = 1
DT_NULL = 0
ANDROID_RELR_MAP = {
    0x6FFFE000: 36,  # DT_ANDROID_RELR -> DT_RELR
    0x6FFFE001: 35,  # DT_ANDROID_RELRSZ -> DT_RELRSZ
    0x6FFFE003: 37,  # DT_ANDROID_RELRENT -> DT_RELRENT
}
VERSION_TAGS = {
    0x6FFFFFF0,  # DT_VERSYM
    0x6FFFFFFC,  # DT_VERDEF
    0x6FFFFFFD,  # DT_VERDEFNUM
    0x6FFFFFFE,  # DT_VERNEED
    0x6FFFFFFF,  # DT_VERNEEDNUM
}

def read_cstring(data, offset):
    end = data.find(b"\x00", offset)
    return data[offset:end].decode("ascii", errors="replace")

def patch_elf(in_path, out_path):
    with open(in_path, "rb") as f:
        data = bytearray(f.read())

    assert data[:4] == b"\x7fELF" and data[4] == 2, f"Not ELF64: {in_path}"
    e_shoff, = struct.unpack_from("<Q", data, 40)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 58)

    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = (
            struct.unpack_from("<IIQQQQIIQQ", data, off)
        )
        sections.append({
            "idx": i,
            "sh_name": sh_name,
            "sh_type": sh_type,
            "sh_offset": sh_offset,
            "sh_size": sh_size,
            "sh_entsize": sh_entsize,
        })

    shstr_off = sections[e_shstrndx]["sh_offset"]
    sec_by_name = {}
    for s in sections:
        name = read_cstring(data, shstr_off + s["sh_name"])
        s["name"] = name
        sec_by_name[name] = s

    dyn_sec = sec_by_name[".dynamic"]
    dynsym_sec = sec_by_name[".dynsym"]
    dynstr_sec = sec_by_name[".dynstr"]
    dynstr_off = dynstr_sec["sh_offset"]

    # 1. Zero out .gnu.version if present
    if ".gnu.version" in sec_by_name:
        gv = sec_by_name[".gnu.version"]
        for i in range(gv["sh_offset"], gv["sh_offset"] + gv["sh_size"]):
            data[i] = 0

    # 2. Rename undefined ABI-divergent symbols in .dynsym / .dynstr
    num_syms = dynsym_sec["sh_size"] // 24
    for i in range(num_syms):
        soff = dynsym_sec["sh_offset"] + i * 24
        st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack_from("<IBBHQQ", data, soff)
        if st_shndx == 0 and st_name != 0:
            sname = read_cstring(data, dynstr_off + st_name)
            if sname in RENAME_SYMS:
                new_name = RENAME_SYMS[sname].encode("ascii") + b"\x00"
                assert len(new_name) <= len(sname) + 1
                data[dynstr_off + st_name : dynstr_off + st_name + len(new_name)] = new_name

    # 3. Filter .dynamic: strip VERSION_TAGS, replace libc.so with libb.so, drop Android system libs
    num_dyn = dyn_sec["sh_size"] // 16
    new_dyn = []
    libb_added = False
    for i in range(num_dyn):
        doff = dyn_sec["sh_offset"] + i * 16
        d_tag, d_val = struct.unpack_from("<QQ", data, doff)
        if d_tag == DT_NULL:
            break
        if d_tag in VERSION_TAGS:
            continue
        if d_tag in ANDROID_RELR_MAP:
            print(f"  Converted 0x{d_tag:x} -> {ANDROID_RELR_MAP[d_tag]} in {os.path.basename(in_path)}")
            new_dyn.append((ANDROID_RELR_MAP[d_tag], d_val))
            continue
        if d_tag == DT_NEEDED:
            libname = read_cstring(data, dynstr_off + d_val)
            if libname in KEEP_NEEDED:
                new_dyn.append((d_tag, d_val))
            elif libname == "libc.so" and not libb_added:
                # Overwrite "libc.so\0" with "libb.so\0" in .dynstr
                data[dynstr_off + d_val : dynstr_off + d_val + 8] = b"libb.so\x00"
                new_dyn.append((d_tag, d_val))
                libb_added = True
            else:
                # Drop liblog.so, libged.so, libsync.so, libm.so, libdl.so, etc. (provided by libb.so)
                continue
        else:
            new_dyn.append((d_tag, d_val))

    assert libb_added, f"libc.so not found in DT_NEEDED of {in_path}"
    while len(new_dyn) < num_dyn:
        new_dyn.append((DT_NULL, 0))

    for i, (d_tag, d_val) in enumerate(new_dyn):
        doff = dyn_sec["sh_offset"] + i * 16
        struct.pack_into("<QQ", data, doff, d_tag, d_val)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Patched: {os.path.relpath(out_path, BASE_OUT)}")

def main():
    for rel in PVR_LIBS:
        in_p = os.path.join(BASE_IN, rel)
        out_p = os.path.join(BASE_OUT, rel)
        patch_elf(in_p, out_p)

if __name__ == "__main__":
    main()
