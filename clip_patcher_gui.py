#!/usr/bin/env python3
"""
FiveM Clip Patcher - Modern GUI Application
A beautiful desktop application for patching binary ASCII patterns in clip files.
"""

import customtkinter as ctk
import os
import sys
import threading
import datetime
import shutil
import mmap
import fnmatch
import re
from pathlib import Path
from tkinter import filedialog, messagebox

# ============================================================================
# APPEARANCE SETTINGS
# ============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================================
# PATCHER CORE FUNCTIONS (from clip_patcher.py)
# ============================================================================

def get_default_gta_clips_path():
    """Get the default GTA V clips directory path."""
    localappdata = os.environ.get("LOCALAPPDATA")
    if not localappdata:
        return None
    path = Path(localappdata) / "Rockstar Games" / "GTA V" / "videos" / "clips"
    return path if path.exists() else None


def backup_file(src: Path, backup_dir: Path):
    """Create backup copy of source file in backup directory."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    dst = backup_dir / src.name
    shutil.copy2(src, dst)
    return dst


def find_wildcard_matches(data: bytes, pattern: str, case_insensitive: bool = False):
    """Find all wildcard pattern matches in binary data."""
    matches = []
    regex_pattern = fnmatch.translate(pattern)
    flags = re.IGNORECASE if case_insensitive else 0

    try:
        ascii_strings = []
        current_string = ""
        current_start = 0

        for i, byte in enumerate(data):
            if 32 <= byte <= 126:
                if not current_string:
                    current_start = i
                current_string += chr(byte)
            else:
                if current_string:
                    ascii_strings.append((current_start, current_string))
                    current_string = ""

        if current_string:
            ascii_strings.append((current_start, current_string))

        pattern_regex = re.compile(regex_pattern, flags)
        for start_pos, ascii_str in ascii_strings:
            if pattern_regex.match(ascii_str):
                matched_bytes = ascii_str.encode("ascii")
                matches.append((start_pos, ascii_str, matched_bytes))

    except re.error:
        return []

    return matches


def find_exact_matches(data: bytes, pattern: str, case_insensitive: bool = False):
    """Find all exact pattern matches in binary data."""
    matches = []
    pattern_bytes = pattern.encode("ascii", errors="ignore")

    if case_insensitive:
        pattern_lower = pattern.lower()
        pattern_upper = pattern.upper()
        candidates = [
            pattern_bytes,
            pattern_lower.encode("ascii", errors="ignore"),
            pattern_upper.encode("ascii", errors="ignore"),
        ]

        for candidate in set(candidates):
            start = 0
            while True:
                idx = data.find(candidate, start)
                if idx == -1:
                    break
                matched_str = candidate.decode("ascii", errors="ignore")
                matches.append((idx, matched_str, candidate))
                start = idx + 1
    else:
        start = 0
        while True:
            idx = data.find(pattern_bytes, start)
            if idx == -1:
                break
            matches.append((idx, pattern, pattern_bytes))
            start = idx + 1

    return matches


def patch_file(file_path: Path, patterns, mode="null", placeholder="REMOVED",
               backup_dir: Path = None, case_insensitive=False):
    """Patch patterns in a single file after backing it up."""
    if backup_dir:
        backup_file(file_path, backup_dir)

    total_patches = 0
    log_entries = []

    with open(file_path, "r+b") as f:
        data = f.read()
        all_matches = []

        for pattern in patterns:
            if "*" in pattern or "?" in pattern:
                matches = find_wildcard_matches(data, pattern, case_insensitive)
            else:
                matches = find_exact_matches(data, pattern, case_insensitive)

            all_matches.extend([(m[0], m[1], m[2], pattern) for m in matches])

        all_matches.sort(key=lambda x: x[0], reverse=True)

        if all_matches:
            f.seek(0)
            mm = mmap.mmap(f.fileno(), 0)

            for start_idx, matched_str, matched_bytes, original_pattern in all_matches:
                if mode == "null":
                    repl = b"\x00" * len(matched_bytes)
                elif mode == "placeholder":
                    ph = (placeholder * ((len(matched_bytes) // len(placeholder)) + 1))[
                        : len(matched_bytes)
                    ]
                    repl = ph.encode("ascii", errors="ignore")
                    if len(repl) < len(matched_bytes):
                        repl += b"\x00" * (len(matched_bytes) - len(repl))
                    repl = repl[: len(matched_bytes)]
                else:
                    raise ValueError(f"Unknown mode: {mode}")

                mm[start_idx : start_idx + len(matched_bytes)] = repl
                total_patches += 1
                log_entries.append(
                    f"  → '{matched_str}' (pattern: '{original_pattern}') at offset {start_idx}"
                )

            mm.flush()
            mm.close()

    return total_patches, log_entries


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class ClipPatcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🎬 FiveM Clip Patcher")
        self.geometry("700x750")
        self.minsize(600, 650)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)
        
        self._create_widgets()
        self._auto_detect_path()
    
    def _create_widgets(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text="🎬 FiveM Clip Patcher",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        subtitle = ctk.CTkLabel(
            self,
            text="Binary ASCII Pattern Patcher for GTA V Clips",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Folder Selection Frame
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(folder_frame, text="📁 Clips Folder:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=15, pady=15, sticky="w"
        )
        
        self.folder_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select GTA V clips folder...")
        self.folder_entry.grid(row=0, column=1, padx=5, pady=15, sticky="ew")
        
        browse_btn = ctk.CTkButton(folder_frame, text="Browse", width=80, command=self._browse_folder)
        browse_btn.grid(row=0, column=2, padx=15, pady=15)
        
        # Patterns Frame
        patterns_frame = ctk.CTkFrame(self)
        patterns_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        patterns_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(patterns_frame, text="📝 Patterns (one per line):", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=15, pady=(15, 5), sticky="w"
        )
        
        ctk.CTkLabel(
            patterns_frame, 
            text="Supports wildcards: * (any chars), ? (single char)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="e")
        
        self.patterns_text = ctk.CTkTextbox(patterns_frame, height=100)
        self.patterns_text.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="ew")
        
        # Options Frame
        options_frame = ctk.CTkFrame(self)
        options_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        options_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Mode Selection
        mode_label = ctk.CTkLabel(options_frame, text="⚙️ Mode:", font=ctk.CTkFont(weight="bold"))
        mode_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.mode_var = ctk.StringVar(value="null")
        
        null_radio = ctk.CTkRadioButton(options_frame, text="Null Bytes", variable=self.mode_var, value="null")
        null_radio.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
        placeholder_radio = ctk.CTkRadioButton(options_frame, text="Placeholder", variable=self.mode_var, value="placeholder")
        placeholder_radio.grid(row=0, column=2, padx=10, pady=15, sticky="w")
        
        # Case Insensitive
        self.case_var = ctk.BooleanVar(value=False)
        case_check = ctk.CTkCheckBox(options_frame, text="Case Insensitive", variable=self.case_var)
        case_check.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")
        
        # Placeholder Entry
        ctk.CTkLabel(options_frame, text="Placeholder:").grid(row=1, column=1, padx=10, pady=(0, 15), sticky="w")
        self.placeholder_entry = ctk.CTkEntry(options_frame, placeholder_text="REMOVED", width=120)
        self.placeholder_entry.grid(row=1, column=2, padx=10, pady=(0, 15), sticky="w")
        self.placeholder_entry.insert(0, "REMOVED")
        
        # Start Button
        self.start_btn = ctk.CTkButton(
            self,
            text="🚀 Start Patching",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self._start_patching
        )
        self.start_btn.grid(row=5, column=0, padx=20, pady=15, sticky="ew")
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress.set(0)
        
        # Log Frame
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(log_frame, text="📋 Log:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=15, pady=(15, 5), sticky="w"
        )
        
        self.log_text = ctk.CTkTextbox(log_frame, height=150)
        self.log_text.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        
        self.grid_rowconfigure(7, weight=1)
    
    def _auto_detect_path(self):
        """Auto-detect GTA V clips folder."""
        default_path = get_default_gta_clips_path()
        if default_path:
            self.folder_entry.insert(0, str(default_path))
            self._log("✓ Auto-detected GTA V clips folder")
        else:
            self._log("⚠ GTA V clips folder not found. Please select manually.")
    
    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select Clips Folder")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
    
    def _log(self, message):
        """Add message to log."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
    
    def _start_patching(self):
        """Start the patching process in a separate thread."""
        # Validate inputs
        folder = self.folder_entry.get().strip()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "Please select a valid clips folder.")
            return
        
        patterns = [p.strip() for p in self.patterns_text.get("1.0", "end").strip().split("\n") if p.strip()]
        if not patterns:
            messagebox.showerror("Error", "Please enter at least one pattern.")
            return
        
        # Disable button during processing
        self.start_btn.configure(state="disabled", text="⏳ Processing...")
        self.progress.set(0)
        
        # Run in thread
        thread = threading.Thread(target=self._run_patching, args=(folder, patterns))
        thread.daemon = True
        thread.start()
    
    def _run_patching(self, folder, patterns):
        """Run the patching process."""
        try:
            folder_path = Path(folder)
            mode = self.mode_var.get()
            placeholder = self.placeholder_entry.get() or "REMOVED"
            case_insensitive = self.case_var.get()
            
            # Find clip files
            files = list(folder_path.glob("*.clip"))
            
            if not files:
                self.after(0, lambda: self._log("⚠ No .clip files found in folder."))
                self.after(0, self._reset_button)
                return
            
            self.after(0, lambda: self._log(f"Found {len(files)} clip file(s)"))
            self.after(0, lambda: self._log(f"Patterns: {patterns}"))
            self.after(0, lambda: self._log(f"Mode: {mode}"))
            self.after(0, lambda: self._log("-" * 40))
            
            # Create backup directory
            run_ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_dir = Path(__file__).parent / "clip_patcher_files_backups_logs" / f"run_{run_ts}"
            
            total_files_patched = 0
            total_patterns_patched = 0
            
            for i, file_path in enumerate(files):
                progress = (i + 1) / len(files)
                self.after(0, lambda p=progress: self.progress.set(p))
                
                patches_count, log_entries = patch_file(
                    file_path,
                    patterns=patterns,
                    mode=mode,
                    placeholder=placeholder,
                    backup_dir=backup_dir,
                    case_insensitive=case_insensitive
                )
                
                if patches_count > 0:
                    total_files_patched += 1
                    total_patterns_patched += patches_count
                    self.after(0, lambda f=file_path.name, c=patches_count: self._log(f"✓ {f}: {c} pattern(s) patched"))
                    for entry in log_entries:
                        self.after(0, lambda e=entry: self._log(e))
                else:
                    self.after(0, lambda f=file_path.name: self._log(f"○ {f}: no matches"))
            
            # Summary
            self.after(0, lambda: self._log("-" * 40))
            self.after(0, lambda: self._log(f"✅ Done! Files patched: {total_files_patched}/{len(files)}"))
            self.after(0, lambda: self._log(f"   Total patterns patched: {total_patterns_patched}"))
            self.after(0, lambda: self._log(f"   Backups saved to: {backup_dir}"))
            
            self.after(0, lambda: messagebox.showinfo(
                "Complete",
                f"Patching complete!\n\n"
                f"Files patched: {total_files_patched}/{len(files)}\n"
                f"Patterns patched: {total_patterns_patched}\n"
                f"Backups saved to:\n{backup_dir}"
            ))
            
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ Error: {str(e)}"))
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, self._reset_button)
    
    def _reset_button(self):
        """Reset the start button."""
        self.start_btn.configure(state="normal", text="🚀 Start Patching")


if __name__ == "__main__":
    app = ClipPatcherApp()
    app.mainloop()
