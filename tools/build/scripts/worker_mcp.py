import json
import os
import re
import shlex
import subprocess
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

WSL_DISTRO = os.environ.get("WSL_DISTRO", "Ubuntu-26.04")
WSL_PREFIX = rf"\\wsl.localhost\{WSL_DISTRO}"
WSL_REPO = os.environ.get("WSL_REPO", "/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline")
WSL_REPO_WIN = Path(WSL_PREFIX + WSL_REPO.replace("/", "\\"))
WIN_WORKDIR = Path(os.environ.get("WIN_WORKDIR", r"C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion"))

DEVICE_SSH = os.environ.get("DEVICE_SSH", "").strip()
DEVICE_UART_PORT = os.environ.get("DEVICE_UART_PORT", "").strip()
DEVICE_UART_BAUD = int(os.environ.get("DEVICE_UART_BAUD", "115200"))

API_KEY = os.environ.get("WORKER_API_KEY", "local-no-key")
BASE_URL = os.environ.get("WORKER_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
MODEL = os.environ.get("WORKER_MODEL", "qwen2.5-coder-7b")
MAX_CHARS = 20_000  # Tuned for Q8+FA with -c 12288

mcp = MCPServer("kernel-offload-worker")
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_PATCH_RE = re.compile(
    r"<<<<<<< SEARCH\r?\n(.*?)\r?\n=======\r?\n(.*?)>>>>>>> REPLACE",
    re.DOTALL,
)


def _trim(text: str, limit: int = 8000) -> str:
    if len(text) <= limit:
        return text
    head = limit // 3
    tail = limit - head
    return text[:head] + f"\n...[TRUNCATED {len(text) - limit} CHARS]...\n" + text[-tail:]


def _load_json(rel_path: str) -> dict:
    p = WIN_WORKDIR / rel_path
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _resolve_path(raw_path: str) -> Path:
    p = raw_path.strip()
    if p.startswith("/"):
        return Path(WSL_PREFIX + p.replace("/", "\\"))
    cand = Path(p)
    if cand.is_absolute():
        return cand
    win_p = WIN_WORKDIR / cand
    if win_p.exists():
        return win_p
    wsl_p = WSL_REPO_WIN / cand
    return wsl_p if wsl_p.exists() else win_p


def _to_wsl_posix(raw_path: str) -> str:
    p = raw_path.strip().replace("\\", "/")
    unc_prefix = f"//wsl.localhost/{WSL_DISTRO}".lower()
    if p.lower().startswith(unc_prefix + "/"):
        return p[len(unc_prefix) :]
    if p.startswith("/"):
        return p
    rel = re.sub(r"^(?:\./)+", "", p).lstrip("/")
    return f"{WSL_REPO}/{rel}"


def _resolve_target(raw_path: str) -> tuple[Path, str | None]:
    p = raw_path.strip()
    p_posix = p.replace("\\", "/")
    unc_repo = f"//wsl.localhost/{WSL_DISTRO}{WSL_REPO}".lower()
    if p_posix.lower().startswith(unc_repo + "/"):
        rel = p_posix[len(unc_repo) + 1 :]
        return WSL_REPO_WIN / rel, rel
    if p_posix.startswith(WSL_REPO + "/"):
        rel = p_posix[len(WSL_REPO) + 1 :]
        return WSL_REPO_WIN / rel, rel
    if p.startswith("/"):
        return Path(WSL_PREFIX + p.replace("/", "\\")), None
    rel = re.sub(r"^(?:\./)+", "", p_posix).lstrip("/")
    wsl_cand = WSL_REPO_WIN / rel
    if wsl_cand.exists():
        return wsl_cand, rel
    return WIN_WORKDIR / rel, None


def _wsl_stdin(script: str, cwd: str = "", timeout: int = 60) -> subprocess.CompletedProcess:
    full = f"cd {shlex.quote(cwd)} || exit 1\n{script}\n" if cwd else f"{script}\n"
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "bash", "-s"],
        input=full,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )


def _ssh_stdin(script: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "wsl",
            "-d",
            WSL_DISTRO,
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=6",
            "-o",
            "StrictHostKeyChecking=accept-new",
            DEVICE_SSH,
            "bash -s",
        ],
        input=f"{script}\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )


def _uart_exec(cmd: str, timeout: int = 10) -> str:
    if not DEVICE_UART_PORT:
        return "[UART_ERROR] DEVICE_UART_PORT is not configured."
    try:
        import serial  # type: ignore
    except ImportError:
        return "[UART_ERROR] pyserial not installed. Run: pip install pyserial"
    try:
        with serial.Serial(DEVICE_UART_PORT, DEVICE_UART_BAUD, timeout=0.5) as ser:
            ser.reset_input_buffer()
            if cmd.strip():
                ser.write((cmd.strip() + "\n").encode("utf-8"))
            deadline = time.time() + timeout
            chunks: list[bytes] = []
            while time.time() < deadline:
                data = ser.read(4096)
                if data:
                    chunks.append(data)
                elif chunks:
                    time.sleep(0.2)
                    more = ser.read(4096)
                    if more:
                        chunks.append(more)
                    else:
                        break
            return b"".join(chunks).decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[UART_ERROR] {type(e).__name__}: {e}"


def _wsl_dirty_map() -> dict[str, str]:
    res = _wsl_stdin("git status --porcelain", cwd=WSL_REPO, timeout=20)
    dirty: dict[str, str] = {}
    for line in res.stdout.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip().strip('"')
        dirty[path] = code
    return dirty


def _wsl_diff_stats(paths: list[str]) -> tuple[int, int]:
    if not paths:
        return 0, 0
    quoted = " ".join(shlex.quote(p) for p in paths)
    res = _wsl_stdin(f"git diff --shortstat -- {quoted}", cwd=WSL_REPO, timeout=20)
    out = res.stdout.strip()
    if not out:
        return 0, 0
    files, lines = 0, 0
    for part in out.split(","):
        tokens = part.strip().split()
        if not tokens or not tokens[0].isdigit():
            continue
        num = int(tokens[0])
        if "file" in part:
            files = num
        elif "insertion" in part or "deletion" in part:
            lines += num
    return files, lines


def _read_slice(file_path: str, start_line: int = 1, end_line: int = 0) -> tuple[str, str]:
    all_lines = _resolve_path(file_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    total = len(all_lines)
    if total == 0:
        return "", "[empty file: 0 lines]"
    s = max(1, start_line)
    e = total if end_line <= 0 else min(total, max(s, end_line))
    selected = [f"{idx}: {all_lines[idx - 1]}" for idx in range(s, e + 1)]
    text = "\n".join(selected)
    truncated = False
    if len(text) > MAX_CHARS:
        if start_line == 1 and end_line <= 0:
            head = MAX_CHARS // 3
            tail = MAX_CHARS - head
            text = text[:head] + "\n...[TRUNCATED]...\n" + text[-tail:]
        else:
            text = text[:MAX_CHARS] + "\n...[SLICE TRUNCATED]..."
        truncated = True
    meta = f"[total={total} lines | slice={s}-{e}{' | truncated' if truncated else ''}]"
    return text, meta


def _ask(system_prompt: str, content: str, max_tokens: int = 1536) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    try:
        with _opener.open(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (data["choices"][0]["message"].get("content") or "").strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")[:300]
        return f"[LOCAL_WORKER_ERROR] HTTP {e.code}: {detail}"
    except Exception as e:
        return f"[LOCAL_WORKER_ERROR] {type(e).__name__}: {e}"


def _apply_patches(original_text: str, model_output: str) -> tuple[str, int, list[str]]:
    patches = _PATCH_RE.findall(model_output)
    if not patches:
        return original_text, 0, ["no valid SEARCH/REPLACE blocks"]
    updated = original_text
    applied = 0
    errors: list[str] = []
    for idx, (search_blk, replace_blk) in enumerate(patches, 1):
        if replace_blk.endswith("\r\n"):
            replace_blk = replace_blk[:-2]
        elif replace_blk.endswith("\n"):
            replace_blk = replace_blk[:-1]
        if search_blk not in updated:
            errors.append(f"patch #{idx} search block not found")
            continue
        updated = updated.replace(search_blk, replace_blk, 1)
        applied += 1
    return updated, applied, errors


def _parse_ver(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v))


@mcp.tool()
def digest_kernel_log(
    file_path: str,
    focus: str = "panic,oops,timeout,probe,error",
    custom_prompt: str = "",
    start_line: int = 1,
    end_line: int = 0,
) -> str:
    """Summarize logs or configs via local LLM (12K ctx). Supports line slicing and custom_prompt."""
    text, meta = _read_slice(file_path, start_line, end_line)
    if not text:
        return meta
    sys_prompt = (
        custom_prompt.strip()
        if custom_prompt.strip()
        else f"Linux kernel log assistant. Extract exact timestamps, error lines, call traces, and 10 lines before first fault matching [{focus}]. Be terse, never invent."
    )
    return f"{meta}\n{_ask(sys_prompt, text)}"


@mcp.tool()
def scan_vendor_driver(
    file_path: str,
    target_kernel: str = "Linux 7.1",
    start_line: int = 1,
    end_line: int = 0,
) -> str:
    """Scan vendor driver slice via local LLM for structs, locks, hw deps, and deprecated APIs."""
    code, meta = _read_slice(file_path, start_line, end_line)
    if not code:
        return meta
    sys_prompt = (
        f"Analyze numbered vendor kernel C slice. Output concise bullet list only: "
        f"1) key structs & locks; 2) clk/regulator/genpd/reset/irq deps; "
        f"3) deprecated APIs for {target_kernel} with exact line numbers."
    )
    return f"{meta}\n{_ask(sys_prompt, code)}"


@mcp.tool()
def delegate_local_agent(
    task: str,
    target_files: str,
    max_files: int = 2,
    max_lines: int = 150,
    allow_dirty: bool = False,
    verify_target: str = "",
) -> str:
    """Apply localized SEARCH/REPLACE edits to target_files via local LLM with rollback guard."""
    try:
        raw_list = [f.strip() for f in target_files.split(",") if f.strip()]
        if not raw_list:
            return "[BLOCKED] target_files is required."
        if len(raw_list) > max_files:
            return f"[BLOCKED] file count ({len(raw_list)}) > max_files={max_files}."

        resolved = [_resolve_target(f) for f in raw_list]
        wsl_targets = [rel for _, rel in resolved if rel]
        if wsl_targets and not allow_dirty:
            dirty_map = _wsl_dirty_map()
            dirty_hits = [rel for rel in wsl_targets if rel in dirty_map]
            if dirty_hits:
                return f"[BLOCKED] dirty target files: {', '.join(dirty_hits)}. Commit/stash or set allow_dirty=True."

        sys_prompt = (
            "Output exact SEARCH/REPLACE blocks only, no prose:\n"
            "<<<<<<< SEARCH\nexact original lines\n=======\nreplacement lines\n>>>>>>> REPLACE\n"
            "Preserve indentation/tabs. Reply NO_CHANGES if nothing to edit."
        )
        backups: list[tuple[Path, str, bool]] = []
        reports: list[str] = []
        total_changed_lines = 0

        for path_obj, wsl_rel in resolved:
            if not path_obj.exists():
                return f"[ERROR] file not found: {path_obj}"
            orig = path_obj.read_text(encoding="utf-8", errors="ignore")
            if len(orig) > MAX_CHARS:
                return f"[BLOCKED] {path_obj.name} too large ({len(orig)} > {MAX_CHARS} chars)."
            reply = _ask(sys_prompt, f"File: {wsl_rel or path_obj.name}\nTask: {task}\n\n```\n{orig}\n```")
            if reply.startswith("[LOCAL_WORKER_ERROR]"):
                return reply
            if "NO_CHANGES" in reply and "<<<<<<< SEARCH" not in reply:
                reports.append(f"- {wsl_rel or path_obj.name}: NO_CHANGES")
                continue
            updated, applied, errs = _apply_patches(orig, reply)
            if applied == 0:
                reports.append(f"- {wsl_rel or path_obj.name}: patch failed ({'; '.join(errs)})\n{reply[:350]}")
                continue
            diff_lines = abs(len(updated.splitlines()) - len(orig.splitlines())) + sum(
                1 for a, b in zip(orig.splitlines(), updated.splitlines()) if a != b
            )
            total_changed_lines += diff_lines
            backups.append((path_obj, orig, bool(wsl_rel)))
            path_obj.write_text(updated, encoding="utf-8", newline="\n" if wsl_rel else None)
            warn = f" (partial: {'; '.join(errs)})" if errs else ""
            reports.append(f"- {wsl_rel or path_obj.name}: applied {applied} patch(es){warn}")

        check_lines = max(_wsl_diff_stats(wsl_targets)[1], total_changed_lines) if wsl_targets else total_changed_lines
        if check_lines > max_lines:
            for path_obj, orig, is_wsl in backups:
                path_obj.write_text(orig, encoding="utf-8", newline="\n" if is_wsl else None)
            return f"[ROLLBACK] changed lines ({check_lines}) > max_lines={max_lines}. Restored."

        gate_out = ""
        if verify_target.strip():
            gate = subprocess.run(
                ["powershell", "-File", str(WIN_WORKDIR / "scripts" / "run-gate.ps1"), verify_target.strip()],
                cwd=str(WIN_WORKDIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=90,
            )
            gate_out = f"\n--- run-gate ({verify_target}) ---\n{(gate.stdout + gate.stderr)[-2000:]}"

        return f"[OK: files={len(resolved)}, lines~{check_lines}]\n" + "\n".join(reports) + gate_out
    except Exception as e:
        return f"[EXCEPTION] {type(e).__name__}: {e}\n{traceback.format_exc()[-1200:]}"


@mcp.tool()
def wsl_exec(cmd: str, cwd: str = "", timeout: int = 60, max_output: int = 8000) -> str:
    """Run raw bash script in WSL via stdin (bypasses PowerShell escaping). Returns exit code and output."""
    try:
        res = _wsl_stdin(cmd, cwd=cwd or WSL_REPO, timeout=min(timeout, 150))
        combined = (res.stdout or "") + (f"\n[STDERR]\n{res.stderr}" if res.stderr else "")
        return f"[wsl exit={res.returncode}]\n{_trim(combined.strip(), max_output)}"
    except subprocess.TimeoutExpired:
        return f"[WSL_TIMEOUT] exceeded {timeout}s"
    except Exception as e:
        return f"[WSL_ERROR] {type(e).__name__}: {e}"


@mcp.tool()
def build_project(profile: str, extra_args: str = "") -> str:
    """Run preset WSL build profile (from .ai/build_profiles.json) with filtered errors/warnings and artifact list."""
    profiles = _load_json(".ai/build_profiles.json")
    if not profiles:
        return "[ERROR] Missing or empty .ai/build_profiles.json"
    if profile not in profiles:
        return f"[ERROR] Unknown profile '{profile}'. Available: {', '.join(profiles.keys())}"

    p = profiles[profile]
    cwd = p.get("cwd", WSL_REPO)
    cmd = p["cmd"] + (f" {extra_args.strip()}" if extra_args.strip() else "")
    timeout = min(int(p.get("timeout", 140)), 155)
    artifacts = p.get("artifacts", [])

    t0 = time.time()
    try:
        res = _wsl_stdin(f"set -o pipefail\n{cmd} 2>&1", cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"[BUILD_TIMEOUT] profile={profile} exceeded {timeout}s"

    elapsed = time.time() - t0
    lines = (res.stdout or "").splitlines()
    diags = [
        ln for ln in lines
        if re.search(r"(?:error:|warning:|Error \d+|FAILED:|ninja: build stopped|undefined reference|No such file)", ln, re.I)
    ]
    diag_block = "\n".join(diags[:45]) if diags else ("\n".join(lines[-25:]) if res.returncode != 0 else "(clean, 0 warnings/errors)")

    art_block = ""
    if res.returncode == 0 and artifacts:
        find_cmds = " ".join(f'ls -1d {a} 2>/dev/null;' for a in artifacts)
        stat_res = _wsl_stdin(
            f"({find_cmds}) | sort -u | xargs -r stat -c '%Y|%y|%s|%n' | sort -rn | head -n 10",
            cwd=cwd,
            timeout=15,
        )
        rows = []
        for row in stat_res.stdout.splitlines():
            parts = row.split("|", 3)
            if len(parts) == 4:
                rows.append(f"- {parts[3]} ({int(parts[2]) // 1024} KB, mtime={parts[1].split('.')[0]})")
        art_block = "\nARTIFACTS (newest first):\n" + ("\n".join(rows) if rows else "- (none matched)")

    status = "PASS" if res.returncode == 0 else f"FAIL(exit={res.returncode})"
    return f"[BUILD {status}] profile={profile} time={elapsed:.1f}s\nDIAGNOSTICS:\n{_trim(diag_block, 4000)}{art_block}"


@mcp.tool()
def device_exec(cmd: str, transport: str = "auto", timeout: int = 30, max_output: int = 8000) -> str:
    """Run bash command on target device via SSH stdin with optional UART fallback (transport: auto|ssh|uart)."""
    mode = transport.strip().lower()
    if mode in ("auto", "ssh"):
        if not DEVICE_SSH:
            if mode == "ssh":
                return "[ERROR] DEVICE_SSH not set in .agents/mcp_config.json."
        else:
            try:
                res = _ssh_stdin(cmd, timeout=min(timeout, 120))
                if res.returncode != 255:
                    combined = (res.stdout or "") + (f"\n[STDERR]\n{res.stderr}" if res.stderr else "")
                    return f"[ssh exit={res.returncode}]\n{_trim(combined.strip(), max_output)}"
                if mode == "ssh":
                    return f"[SSH_UNREACHABLE] {res.stderr.strip()}"
            except subprocess.TimeoutExpired:
                if mode == "ssh":
                    return f"[SSH_TIMEOUT] exceeded {timeout}s"
    if mode in ("auto", "uart"):
        return f"[uart]\n{_trim(_uart_exec(cmd, timeout=min(timeout, 30)).strip(), max_output)}"
    return "[ERROR] Both SSH and UART unavailable."


@mcp.tool()
def check_target_abi(elf_path: str, max_glibc: str = "") -> str:
    """Pre-check ARM64 ELF (.so/.ko/bin) in WSL against .ai/device_profiles.json ABI baseline."""
    cfg = _load_json(".ai/device_profiles.json").get("abi", {})
    arch = cfg.get("arch", "AArch64")
    ceiling = max_glibc.strip() or cfg.get("max_glibc", "2.39")
    forbidden = cfg.get("forbidden_symbols", ["wl_fixes_interface", "wl_display_create_queue_with_name"])

    wsl_path = _to_wsl_posix(elf_path)
    script = f"""
f={shlex.quote(wsl_path)}
[ -f "$f" ] || {{ echo "MISSING_FILE"; exit 2; }}
echo "===HDR==="
readelf -h "$f" 2>/dev/null | grep -E "Class:|Machine:"
echo "===NEEDED==="
readelf -d "$f" 2>/dev/null | grep NEEDED
echo "===SYMS==="
(aarch64-linux-gnu-objdump -T "$f" 2>/dev/null || objdump -T "$f" 2>/dev/null) || true
"""
    out = _wsl_stdin(script, timeout=20).stdout
    if "MISSING_FILE" in out:
        return f"[ERROR] File not found in WSL: {wsl_path}"

    issues: list[str] = []
    hdr = out.split("===NEEDED===")[0]
    if arch not in hdr:
        issues.append(f"ARCH_MISMATCH: expected {arch}, got: {hdr.replace('===HDR===', '').strip()}")

    needed_sec = out.split("===NEEDED===")[1].split("===SYMS===")[0] if "===NEEDED===" in out else ""
    syms_sec = out.split("===SYMS===")[1] if "===SYMS===" in out else ""

    max_tuple = _parse_ver(ceiling)
    bad_glibc: set[str] = set()
    for m in re.finditer(r"GLIBC_(\d+\.\d+(?:\.\d+)?)", syms_sec):
        if _parse_ver(m.group(1)) > max_tuple:
            bad_glibc.add(f"GLIBC_{m.group(1)}")
    if bad_glibc:
        bad_lines = [ln.strip() for ln in syms_sec.splitlines() if any(g in ln for g in bad_glibc)][:10]
        issues.append(f"GLIBC_EXCEEDED (>{ceiling}): {', '.join(sorted(bad_glibc))}\n  " + "\n  ".join(bad_lines))

    for sym in forbidden:
        if sym in syms_sec:
            issues.append(f"FORBIDDEN_SYMBOL: {sym}")

    needed_libs = re.findall(r"\[([^\]]+)\]", needed_sec)
    status = "PASS" if not issues else "FAIL"
    report = [f"[ABI {status}] {wsl_path} (glibc<={ceiling})", f"NEEDED: {', '.join(needed_libs) or 'none'}"]
    if issues:
        report.append("ISSUES:\n- " + "\n- ".join(issues))
    return "\n".join(report)


@mcp.tool()
def device_deploy(
    local_path: str,
    remote_path: str,
    kind: str = "auto",
    reboot: bool = False,
    wait_sec: int = 90,
) -> str:
    """Verify ABI/md5, strip temp copy (.ko=--strip-debug, .so=--strip-unneeded), backup .orig, push, optionally reboot & collect dmesg."""
    if not DEVICE_SSH:
        return "[ERROR] DEVICE_SSH not set in .agents/mcp_config.json."
    wsl_src = _to_wsl_posix(local_path)
    k = kind.strip().lower()
    if k == "auto":
        k = "ko" if wsl_src.endswith(".ko") else ("so" if ".so" in Path(wsl_src).name else "bin")

    if k in ("so", "bin"):
        abi = check_target_abi(wsl_src)
        if abi.startswith("[ABI FAIL]") or abi.startswith("[ERROR]"):
            return f"[DEPLOY_BLOCKED]\n{abi}"

    strip_flag = "--strip-debug" if k == "ko" else "--strip-unneeded"
    stage_script = f"""
set -e
src={shlex.quote(wsl_src)}
[ -f "$src" ] || {{ echo "ERR: missing $src"; exit 2; }}
STAGE="/tmp/mcp_deploy_$(basename "$src")"
cp "$src" "$STAGE"
STRIP=$(command -v aarch64-linux-gnu-strip || command -v llvm-strip || command -v strip)
"$STRIP" {strip_flag} "$STAGE"
echo "META: mtime=$(stat -c '%y' "$src" | cut -d. -f1) orig_sz=$(stat -c '%s' "$src") strip_sz=$(stat -c '%s' "$STAGE") md5=$(md5sum "$STAGE" | awk '{{print $1}}')"
scp -o BatchMode=yes -o ConnectTimeout=8 "$STAGE" {shlex.quote(DEVICE_SSH)}:/tmp/_mcp_incoming
rm -f "$STAGE"
"""
    res = _wsl_stdin(stage_script, timeout=45)
    if res.returncode != 0:
        return f"[DEPLOY_STAGE_FAILED]\n{res.stdout}\n{res.stderr}"

    depmod_cmd = "&& $SUDO depmod -a" if (k == "ko" and "/lib/modules/" in remote_path) else ""
    install_script = f"""
set -e
[ "$(id -u)" -eq 0 ] && SUDO="" || SUDO="sudo"
DST={shlex.quote(remote_path)}
if [ -f "$DST" ] && [ ! -f "$DST.orig" ]; then $SUDO cp "$DST" "$DST.orig"; fi
$SUDO install -m 0644 /tmp/_mcp_incoming "$DST"
rm -f /tmp/_mcp_incoming
sync {depmod_cmd}
echo "INSTALLED: $(md5sum "$DST" | awk '{{print $1}}') -> $DST"
"""
    inst = _ssh_stdin(install_script, timeout=30)
    if inst.returncode != 0:
        return f"[DEPLOY_INSTALL_FAILED]\n{inst.stdout}\n{inst.stderr}"

    out = [res.stdout.strip(), inst.stdout.strip()]
    if not reboot:
        return "[DEPLOY_OK]\n" + "\n".join(out)

    _ssh_stdin('[ "$(id -u)" -eq 0 ] && reboot || sudo reboot', timeout=10)
    time.sleep(10)
    deadline = time.time() + max(20, wait_sec)
    while time.time() < deadline:
        chk = _ssh_stdin(
            "uname -r; echo '---MODS---'; lsmod | grep -iE 'pvr|mtk|snd' | head -n 15; "
            "echo '---DMESG_ERR---'; dmesg -l err,crit,alert,emerg | tail -n 25",
            timeout=10,
        )
        if chk.returncode == 0 and chk.stdout.strip():
            out.append("---POST_REBOOT---\n" + chk.stdout.strip())
            return "[DEPLOY_REBOOT_OK]\n" + "\n".join(out)
        time.sleep(4)

    uart_tail = _uart_exec("", timeout=5) if DEVICE_UART_PORT else "(UART not configured)"
    return f"[REBOOT_TIMEOUT] SSH not back within {wait_sec}s.\nUART tail:\n{_trim(uart_tail, 2000)}"


@mcp.tool()
def device_run_profile(profile: str, arg: str = "") -> str:
    """Run preset on-device snapshot or regression suite from .ai/device_profiles.json (optional ARG filter)."""
    suites = _load_json(".ai/device_profiles.json").get("suites", {})
    if not suites:
        return "[ERROR] Missing or empty suites in .ai/device_profiles.json"
    if profile not in suites:
        return f"[ERROR] Unknown suite '{profile}'. Available: {', '.join(suites.keys())}"

    s = suites[profile]
    cmd = f"ARG={shlex.quote(arg.strip())}\n{s['cmd']}"
    return device_exec(cmd=cmd, transport="ssh", timeout=int(s.get("timeout", 45)), max_output=6000)


if __name__ == "__main__":
    mcp.run()
