# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import re
import wave
import contextlib

TIME_RE = re.compile(r'(?P<h>\d{2,}):(?P<m>\d{2}):(?P<s>\d{2})[,.](?P<ms>\d{1,3})')
TIMING_LINE = re.compile(r'^(?P<pre>\s*)(?P<a>\d{2,}:\d{2}:\d{2}[,.]\d{1,3})(?P<arrow>\s*-->\s*)(?P<b>\d{2,}:\d{2}:\d{2}[,.]\d{1,3})(?P<tail>.*)$')

def parse_time(s):
    m = TIME_RE.search(s)
    if not m:
        raise ValueError("无法识别时间戳：" + s)
    ms = (m.group('ms') + '000')[:3]
    return int(m.group('h'))*3600 + int(m.group('m'))*60 + int(m.group('s')) + int(ms)/1000

def fmt_time(seconds, comma=True):
    total_ms = max(0, int(round(seconds * 1000)))
    h, rem = divmod(total_ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{',' if comma else '.'}{ms:03d}"

def read_srt(path):
    # Handle common UTF-8 and Chinese Windows encodings.
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    raise ValueError("无法识别 SRT 编码，请尝试将文件另存为 UTF-8。")

def transform_srt(content, ratio):
    out, changed = [], 0
    for line in content.splitlines(keepends=True):
        raw = line.rstrip('\r\n')
        ending = line[len(raw):]
        m = TIMING_LINE.match(raw)
        if m:
            a = parse_time(m.group('a')) * ratio
            b = parse_time(m.group('b')) * ratio
            new = (m.group('pre') + fmt_time(a, ',' in m.group('a')) +
                   m.group('arrow') + fmt_time(b, ',' in m.group('b')) + m.group('tail'))
            out.append(new + ending)
            changed += 1
        else:
            out.append(line)
    if changed == 0:
        raise ValueError("没有找到标准 SRT 时间轴，请确认文件格式正确。")
    return ''.join(out), changed

def audio_duration(path):
    """Read common audio duration. WAV uses Python built-in; other formats use Mutagen."""
    path = Path(path)
    if path.suffix.lower() == ".wav":
        with contextlib.closing(wave.open(str(path), 'rb')) as w:
            frames, rate = w.getnframes(), w.getframerate()
            if rate <= 0:
                raise ValueError("无法读取 WAV 时长。")
            return frames / float(rate)
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(str(path))
        if audio is None or not getattr(audio, "info", None) or not audio.info.length:
            raise ValueError("音频文件没有可读取的时长信息。")
        return float(audio.info.length)
    except ImportError:
        raise ValueError("此版本缺少音频读取组件。请使用打包后的正式 EXE。")
    except Exception as e:
        raise ValueError(f"无法自动读取该音频时长：{e}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SRT Sync 歌词时间戳调整器")
        self.geometry("790x640")
        self.minsize(730, 600)
        self.srt = tk.StringVar()
        self.original_audio = tk.StringVar()
        self.processed_audio = tk.StringVar()
        self.original_seconds = tk.StringVar()
        self.processed_seconds = tk.StringVar()
        self.stretch = tk.StringVar(value="105")
        self.mode = tk.StringVar(value="duration")
        self.status = tk.StringVar(value="请选择 SRT，并选择一种换算方式。")
        self._ui()

    def _ui(self):
        outer = ttk.Frame(self, padding=16); outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="SRT Sync", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w")
        ttk.Label(outer, text="本地歌词时间戳调整器 · Windows 11", font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(0, 12))
        box = ttk.LabelFrame(outer, text="1. 原始歌词", padding=10); box.pack(fill="x", pady=6)
        row = ttk.Frame(box); row.pack(fill="x")
        ttk.Entry(row, textvariable=self.srt).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="选择 SRT", command=self.pick_srt).pack(side="left")

        box = ttk.LabelFrame(outer, text="2. 选择换算方式", padding=10); box.pack(fill="x", pady=6)
        ttk.Radiobutton(box, text="按歌曲实际时长比例（推荐）", variable=self.mode, value="duration", command=self.mode_changed).pack(anchor="w")
        ttk.Radiobutton(box, text="按 AU 伸缩百分比（先验证 AU 参数方向）", variable=self.mode, value="stretch", command=self.mode_changed).pack(anchor="w")
        self.duration_frame = ttk.Frame(box); self.duration_frame.pack(fill="x", pady=(8, 0))
        r1 = ttk.Frame(self.duration_frame); r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="原曲音频：", width=12).pack(side="left")
        ttk.Entry(r1, textvariable=self.original_audio).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(r1, text="选择音频", command=lambda: self.pick_audio("original")).pack(side="left")
        r2 = ttk.Frame(self.duration_frame); r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="处理后音频：", width=12).pack(side="left")
        ttk.Entry(r2, textvariable=self.processed_audio).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(r2, text="选择音频", command=lambda: self.pick_audio("processed")).pack(side="left")
        r3 = ttk.Frame(self.duration_frame); r3.pack(fill="x", pady=3)
        ttk.Label(r3, text="原曲时长（秒）：", width=15).pack(side="left")
        ttk.Entry(r3, textvariable=self.original_seconds, width=14).pack(side="left", padx=5)
        ttk.Label(r3, text="处理后时长（秒）：").pack(side="left", padx=(12, 0))
        ttk.Entry(r3, textvariable=self.processed_seconds, width=14).pack(side="left", padx=5)
        ttk.Label(self.duration_frame, text="提示：选择 WAV / MP3 / M4A / FLAC / AAC 后会尝试自动读取时长；若读取失败可手动修改秒数。").pack(anchor="w", pady=(3, 0))
        self.stretch_frame = ttk.Frame(box); self.stretch_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(self.stretch_frame, text="AU 伸缩百分比：").pack(side="left")
        ttk.Entry(self.stretch_frame, textvariable=self.stretch, width=12).pack(side="left", padx=6)
        ttk.Label(self.stretch_frame, text="例如 105").pack(side="left")

        info = ttk.LabelFrame(outer, text="换算说明", padding=10); info.pack(fill="x", pady=6)
        ttk.Label(info, text=(
            "实际时长模式：新时间戳 = 原时间戳 × 处理后时长 ÷ 原曲时长。\n"
            "伸缩模式：暂按时间比例 = 100 ÷ 伸缩百分比计算，必须先用实际导出时长验证。\n"
            "适用于整首歌统一伸缩且未剪切/拼接的情况；输出文件不会覆盖原始 SRT。"
        ), justify="left", wraplength=730).pack(anchor="w")
        actions = ttk.Frame(outer); actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="计算并导出新 SRT", command=self.export).pack(side="left")
        ttk.Button(actions, text="清空", command=self.clear).pack(side="left", padx=8)
        ttk.Label(outer, textvariable=self.status, wraplength=730).pack(anchor="w", pady=(12, 0))

    def mode_changed(self):
        state = "normal" if self.mode.get() == "duration" else "disabled"
        for child in self.duration_frame.winfo_children():
            self._set_state(child, state)
        for child in self.stretch_frame.winfo_children():
            self._set_state(child, "normal" if self.mode.get() == "stretch" else "disabled")

    def _set_state(self, widget, state):
        try: widget.configure(state=state)
        except tk.TclError: pass
        for child in widget.winfo_children():
            self._set_state(child, state)

    def pick_srt(self):
        p = filedialog.askopenfilename(filetypes=[("SRT 字幕", "*.srt"), ("所有文件", "*.*")])
        if p: self.srt.set(p)

    def pick_audio(self, which):
        p = filedialog.askopenfilename(filetypes=[("音频文件", "*.wav *.mp3 *.m4a *.flac *.aac"), ("所有文件", "*.*")])
        if not p: return
        if which == "original":
            self.original_audio.set(p)
            target = "original_seconds"
        else:
            self.processed_audio.set(p)
            target = "processed_seconds"
        try:
            var = self.original_seconds if which == "original" else self.processed_seconds
            var.set(f"{audio_duration(p):.3f}")
        except Exception as e:
            messagebox.showwarning("读取时长失败", f"{e}\n\n你仍然可以手动填写时长（秒）。")

    def export(self):
        try:
            if not Path(self.srt.get()).is_file(): raise ValueError("请先选择有效的 SRT 文件。")
            if self.mode.get() == "duration":
                a, b = float(self.original_seconds.get()), float(self.processed_seconds.get())
                if a <= 0 or b <= 0: raise ValueError("请填写大于 0 的歌曲时长。")
                ratio = b / a
                detail = f"实际时长比例={ratio:.8f}"
            else:
                x = float(self.stretch.get())
                if x <= 0: raise ValueError("伸缩百分比必须大于 0。")
                ratio = 100.0 / x
                detail = f"伸缩参数={x:g}%，换算比例={ratio:.8f}"
            content = read_srt(self.srt.get())
            result, n = transform_srt(content, ratio)
            src = Path(self.srt.get())
            dest = filedialog.asksaveasfilename(
                title="保存新 SRT", initialdir=str(src.parent),
                initialfile=src.stem + "_调整后.srt", defaultextension=".srt",
                filetypes=[("SRT 字幕", "*.srt")])
            if not dest: return
            Path(dest).write_text(result, encoding="utf-8-sig", newline="")
            messagebox.showinfo("完成", f"已调整 {n} 条时间轴。\n{detail}\n\n已保存：\n{dest}")
            self.status.set(f"导出成功：{dest}")
        except Exception as e:
            messagebox.showerror("处理失败", str(e))
            self.status.set("处理失败，请检查文件和输入值。")

    def clear(self):
        for v in (self.srt, self.original_audio, self.processed_audio, self.original_seconds, self.processed_seconds):
            v.set("")
        self.stretch.set("105")
        self.status.set("已清空。")

if __name__ == "__main__":
    App().mainloop()
