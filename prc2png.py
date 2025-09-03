
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from io import BytesIO
from PIL import Image
import platform
import subprocess

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ImageExtractorGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("PRC/MOBI Image Extractor")
        self.root.geometry("860x620")
        self.root.minsize(720, 540)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.selected_paths = []
        self.is_directory = False
        self.processing = False

        self.compression_mode = tk.StringVar(value="optimized")
        self.compression_level = tk.IntVar(value=6)
        self.outdir_var = tk.StringVar(value="")
        self.open_when_done = tk.BooleanVar(value=False)
        self.ui_scale = tk.DoubleVar(value=1.0)

        self.cancel_event = threading.Event()
        self.global_total = 0
        self.global_done = 0

        self.setup_ui()
        self.root.bind("<Configure>", self.on_resize)

    def setup_ui(self):
        container = ctk.CTkFrame(self.root, corner_radius=12)
        container.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(container)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        header.grid_columnconfigure(0, weight=1)
        self.header_title = ctk.CTkLabel(header, text="PRC/MOBI Image Extractor", font=ctk.CTkFont(size=18, weight="bold"))
        self.header_title.grid(row=0, column=0, sticky="w")
        self.scale_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.scale_frame.grid(row=0, column=1, sticky="e", padx=(10, 0))
        self.scale_label = ctk.CTkLabel(self.scale_frame, text="UI Scale")
        self.scale_label.pack(side="left", padx=(0,6))
        self.scale_slider = ctk.CTkSlider(self.scale_frame, from_=0.8, to=1.2, number_of_steps=8, command=self.on_scale_change, width=140)
        self.scale_slider.set(self.ui_scale.get())
        self.scale_slider.pack(side="left")
        self.scale_value = ctk.CTkLabel(self.scale_frame, text="100%")
        self.scale_value.pack(side="left", padx=(6,0))

        body = ctk.CTkFrame(container)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        for i in range(12):
            body.grid_rowconfigure(i, weight=0)
        body.grid_rowconfigure(11, weight=1)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        selection = ctk.CTkFrame(body)
        selection.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 10))
        selection.grid_columnconfigure(0, weight=1)
        selection.grid_columnconfigure(1, weight=1)
        self.file_button = ctk.CTkButton(selection, text="Add File(s)", command=self.select_file, height=40, font=ctk.CTkFont(size=14))
        self.file_button.grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=12)
        self.folder_button = ctk.CTkButton(selection, text="Add Folder", command=self.select_folder, height=40, font=ctk.CTkFont(size=14))
        self.folder_button.grid(row=0, column=1, sticky="ew", padx=(6, 10), pady=12)
        self.selection_label = ctk.CTkLabel(selection, text="No file selected", font=ctk.CTkFont(size=12), text_color="gray")
        self.selection_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0,6))
        self.info_label = ctk.CTkLabel(selection, text="", font=ctk.CTkFont(size=12))
        self.info_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0,8))

        out_frame = ctk.CTkFrame(body)
        out_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 10))
        out_frame.grid_columnconfigure(0, weight=1)
        out_frame.grid_columnconfigure(1, weight=0)
        out_title = ctk.CTkLabel(out_frame, text="Output directory", font=ctk.CTkFont(size=14, weight="bold"))
        out_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,6))
        self.outdir_entry = ctk.CTkEntry(out_frame, textvariable=self.outdir_var, placeholder_text="Empty = same path as original file", height=36)
        self.outdir_entry.grid(row=1, column=0, sticky="ew", padx=(10, 6), pady=(0,10))
        browse_btn = ctk.CTkButton(out_frame, text="Browse…", width=110, command=self.select_output_dir)
        browse_btn.grid(row=1, column=1, sticky="e", padx=(6, 10), pady=(0,10))
        self.open_checkbox = ctk.CTkCheckBox(out_frame, text="Open folder when done", variable=self.open_when_done)
        self.open_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10))

        options = ctk.CTkFrame(body)
        options.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,10))
        options.grid_columnconfigure(0, weight=1)
        opt_title = ctk.CTkLabel(options, text="Processing options", font=ctk.CTkFont(size=14, weight="bold"))
        opt_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10,6))

        mode_row = ctk.CTkFrame(options, fg_color="transparent")
        mode_row.grid(row=1, column=0, sticky="w", padx=10, pady=(0,8))
        self.radio_normal = ctk.CTkRadioButton(mode_row, text="No compression (RAW)", variable=self.compression_mode, value="normal")
        self.radio_normal.pack(side="left", padx=(0,16))
        self.radio_optimized = ctk.CTkRadioButton(mode_row, text="With compression (Optimized)", variable=self.compression_mode, value="optimized")
        self.radio_optimized.pack(side="left", padx=(0,16))
        self.radio_both = ctk.CTkRadioButton(mode_row, text="Both (RAW + Optimized)", variable=self.compression_mode, value="both")
        self.radio_both.pack(side="left")

        comp_row = ctk.CTkFrame(options, fg_color="transparent")
        comp_row.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,10))
        comp_row.grid_columnconfigure(1, weight=1)
        comp_label = ctk.CTkLabel(comp_row, text="PNG compression level")
        comp_label.grid(row=0, column=0, sticky="w")
        self.comp_slider = ctk.CTkSlider(comp_row, from_=0, to=9, number_of_steps=9, command=self.on_comp_change)
        self.comp_slider.set(self.compression_level.get())
        self.comp_slider.grid(row=0, column=1, sticky="ew", padx=(10,10))
        self.comp_value = ctk.CTkLabel(comp_row, text="6")
        self.comp_value.grid(row=0, column=2, sticky="e")

        actions = ctk.CTkFrame(body)
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,10))
        actions.grid_columnconfigure(0, weight=1)
        self.start_button = ctk.CTkButton(actions, text="Start", command=self.start_extraction, height=46, font=ctk.CTkFont(size=16, weight="bold"), state="disabled")
        self.start_button.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,10))

        self.progress_button_frame = ctk.CTkFrame(actions, height=46)
        self.button_progress = ctk.CTkProgressBar(self.progress_button_frame)
        self.button_progress.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.button_progress.set(0)
        self.button_progress_label = ctk.CTkLabel(self.progress_button_frame, text="Processing 0%", font=ctk.CTkFont(size=16, weight="bold"))
        self.button_progress_label.place(relx=0.5, rely=0.5, anchor="center")
        self.progress_button_frame.grid_forget()

        self.progress_bar = ctk.CTkProgressBar(body)
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 8))
        self.progress_bar.set(0)

        status_area = ctk.CTkFrame(body)
        status_area.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 10))
        status_area.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(status_area, text="Ready", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=(0,8))

        controls = ctk.CTkFrame(body)
        controls.grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6))
        self.cancel_button = ctk.CTkButton(controls, text="Cancel", command=self.cancel_processing, height=36, state="disabled", width=110)
        self.cancel_button.pack(side="left", padx=(10,6), pady=8)
        self.appearance_mode_switch = ctk.CTkSwitch(controls, text="Dark mode", command=self.change_appearance_mode, onvalue="dark", offvalue="light")
        self.appearance_mode_switch.pack(side="right", padx=(6, 10), pady=8)
        self.appearance_mode_switch.select()
        self.register_shortcuts()

    def register_shortcuts(self):
        r = self.root
        for seq in ("<Return>", "<KP_Enter>", "<Control-Return>"):
            r.bind_all(seq, self.kb_start)
        r.bind_all("<Escape>", self.kb_cancel)
        r.bind_all("<Control-o>", self.kb_add_files)
        r.bind_all("<Control-Shift-O>", self.kb_add_folder)
        r.bind_all("<Control-l>", self.kb_browse_output)
        r.bind_all("<Control-e>", self.kb_open_output)

    def kb_start(self, event=None):
        if (not self.processing) and self.start_button.cget("state") == "normal":
            self.start_extraction()
        return "break"

    def kb_cancel(self, event=None):
        if self.cancel_button.cget("state") == "normal":
            self.cancel_processing()
        return "break"

    def kb_add_files(self, event=None):
        if not self.processing:
            self.select_file()
        return "break"

    def kb_add_folder(self, event=None):
        if not self.processing:
            self.select_folder()
        return "break"

    def kb_browse_output(self, event=None):
        if not self.processing:
            self.select_output_dir()
        return "break"

    def kb_open_output(self, event=None):
        if not self.processing:
            self.open_output_location()
        return "break"

    def on_scale_change(self, value):
        self.ui_scale.set(float(value))
        ctk.set_widget_scaling(self.ui_scale.get())
        self.scale_value.configure(text=f"{int(self.ui_scale.get()*100)}%")

    def on_comp_change(self, value):
        v = int(round(float(value)))
        self.compression_level.set(v)
        self.comp_value.configure(text=str(v))

    def on_resize(self, event):
        if event.width < 820:
            self.header_title.configure(font=ctk.CTkFont(size=16, weight="bold"))
        else:
            self.header_title.configure(font=ctk.CTkFont(size=18, weight="bold"))

    def change_appearance_mode(self):
        mode = self.appearance_mode_switch.get()
        ctk.set_appearance_mode(mode)

    def select_output_dir(self):
        folder = filedialog.askdirectory(title="Select output directory")
        if folder:
            self.outdir_var.set(folder)

    def select_file(self):
        files = filedialog.askopenfilenames(title="Select PRC/MOBI files", filetypes=[("PRC/MOBI files", "*.prc *.mobi"), ("All files", "*.*")])
        if files:
            self.selected_paths = list(files)
            self.is_directory = False
            self.update_selection_display()
            self.start_button.configure(state="normal")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            self.selected_paths = [folder]
            self.is_directory = True
            self.update_selection_display()
            self.start_button.configure(state="normal")

    def update_selection_display(self):
        if self.is_directory:
            folder_name = os.path.basename(self.selected_paths[0])
            self.selection_label.configure(text=f"Selected folder: {folder_name}", text_color="green")
        else:
            count = len(self.selected_paths)
            if count == 1:
                filename = os.path.basename(self.selected_paths[0])
                self.selection_label.configure(text=f"Selected file: {filename}", text_color="green")
            else:
                self.selection_label.configure(text=f"{count} files selected", text_color="green")

    def start_extraction(self):
        if self.processing:
            return
        self.processing = True
        self.cancel_event.clear()
        self.global_done = 0
        self.global_total = 0
        self.start_button.grid_forget()
        self.progress_button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,10))
        self.button_progress.set(0)
        self.button_progress_label.configure(text="Processing 0%")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting...")
        self.info_label.configure(text="")
        self.cancel_button.configure(state="normal")
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def cancel_processing(self):
        self.cancel_event.set()

    def process_files(self):
        try:
            targets = self.gather_targets()
            if not targets:
                self.root.after(0, lambda: self.show_error("No .prc/.mobi files found"))
                return
            mode = self.compression_mode.get()
            passes_per_file = 2 if mode == "both" else 1
            file_counts = {}
            for target in targets:
                try:
                    with open(target, 'rb') as f:
                        data = f.read()
                    imgs = self.extract_images_from_bytes(data)
                    file_counts[target] = len(imgs)
                except Exception:
                    file_counts[target] = 0
            self.global_total = sum(file_counts.get(t, 0) * passes_per_file for t in targets)
            if self.global_total == 0:
                self.root.after(0, lambda: self.show_error("No images detected in the selected files"))
                return
            total_files = len(targets)
            self.root.after(0, lambda: self.info_label.configure(text=f"Files: {total_files} • Images to process: {self.global_total}"))
            for target_file in targets:
                if self.cancel_event.is_set():
                    break
                base_name = os.path.basename(target_file)
                self.root.after(0, lambda f=base_name: self.status_label.configure(text=f"Preparing: {f}"))
                try:
                    n_raw, n_opt = self.process_file(target_file, mode, self.progress_increment)
                    msg = []
                    if n_raw:
                        msg.append(f"{n_raw} RAW")
                    if n_opt:
                        msg.append(f"{n_opt} OPT")
                    if msg:
                        self.root.after(0, lambda t=base_name, m=', '.join(msg): self.info_label.configure(text=f"{t}: {m}"))
                except Exception as e:
                    print(f"Error with {target_file}: {e}")
            if self.cancel_event.is_set():
                self.root.after(0, self.processing_canceled)
            else:
                self.root.after(0, self.processing_completed)
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Error while processing: {str(e)}"))

    def progress_increment(self, filename=None, done_in_file=None, total_in_file=None):
        self.global_done += 1
        overall = self.global_done / max(1, self.global_total)
        pct = int(overall * 100)
        def ui_update():
            self.progress_bar.set(overall)
            self.button_progress.set(overall)
            self.button_progress_label.configure(text=f"Processing {pct}%")
            if filename is not None and done_in_file is not None and total_in_file is not None:
                self.status_label.configure(text=f"Processing {filename} ({done_in_file}/{total_in_file})")
        self.root.after(0, ui_update)

    def processing_completed(self):
        self.processing = False
        self.progress_bar.set(1.0)
        self.button_progress.set(1.0)
        self.button_progress_label.configure(text="Done 100%")
        self.status_label.configure(text="Processing completed")
        self.cancel_button.configure(state="disabled")
        self.progress_button_frame.grid_forget()
        self.start_button.configure(state="normal", text="Start")
        self.start_button.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,10))
        messagebox.showinfo("Completed", "Processing finished successfully.")
        if self.open_when_done.get():
            self.open_output_location()

    def processing_canceled(self):
        self.processing = False
        self.cancel_button.configure(state="disabled")
        self.progress_button_frame.grid_forget()
        self.start_button.configure(state="normal", text="Start")
        self.start_button.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,10))
        self.status_label.configure(text="Processing canceled")
        messagebox.showwarning("Canceled", "Processing was canceled.")

    def show_error(self, message):
        self.processing = False
        self.cancel_button.configure(state="disabled")
        self.progress_button_frame.grid_forget()
        self.start_button.configure(state="normal", text="Start")
        self.start_button.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,10))
        self.status_label.configure(text="Processing error")
        messagebox.showerror("Error", message)

    def gather_targets(self):
        targets = []
        if self.is_directory:
            folder_path = self.selected_paths[0]
            for root_dir, _, files in os.walk(folder_path):
                for filename in files:
                    if filename.lower().endswith(('.prc', '.mobi')):
                        targets.append(os.path.join(root_dir, filename))
        else:
            targets = self.selected_paths
        return targets

    def find_all(self, data, sub):
        start = 0
        while True:
            i = data.find(sub, start)
            if i == -1:
                return
            yield i
            start = i + 1

    def extract_jpeg(self, data, start):
        end = data.find(b'\xff\xd9', start + 2)
        if end == -1:
            return None
        return data[start:end+2], end+2

    def extract_png(self, data, start):
        sig = b'\x89PNG\r\n\x1a\n'
        if not data.startswith(sig, start):
            return None
        i = start + 8
        while i + 12 <= len(data):
            length = int.from_bytes(data[i:i+4], 'big', signed=False)
            if i + 8 + length + 4 > len(data):
                return None
            ctype = data[i+4:i+8]
            i = i + 8 + length + 4
            if ctype == b'IEND':
                return data[start:i], i
        return None

    def extract_gif(self, data, start):
        if not (data.startswith(b'GIF87a', start) or data.startswith(b'GIF89a', start)):
            return None
        end = data.find(b'\x3b', start+6)
        if end == -1:
            return None
        return data[start:end+1], end+1

    def extract_bmp(self, data, start):
        if not data.startswith(b'BM', start):
            return None
        if start + 6 > len(data):
            return None
        size = int.from_bytes(data[start+2:start+6], 'little', signed=False)
        if size <= 0 or start + size > len(data):
            return None
        return data[start:start+size], start+size

    def extract_images_from_bytes(self, data):
        offsets_taken = set()
        results = []
        for sig, extractor in [(b'\xff\xd8\xff', self.extract_jpeg),(b'\x89PNG\r\n\x1a\n', self.extract_png),(b'GIF87a', self.extract_gif),(b'GIF89a', self.extract_gif),(b'BM', self.extract_bmp)]:
            for pos in self.find_all(data, sig):
                if any(p <= pos < p+ln for p, ln in offsets_taken):
                    continue
                out = extractor(data, pos)
                if out is None:
                    continue
                blob, newpos = out
                offsets_taken.add((pos, len(blob)))
                results.append((pos, blob))
        results.sort(key=lambda x: x[0])
        return [b for _, b in results]

    def to_png_bytes(self, blob, optimize=False):
        with Image.open(BytesIO(blob)) as im:
            im = im.convert("RGBA")
            buf = BytesIO()
            if optimize:
                im.save(buf, format="PNG", optimize=True, compress_level=self.compression_level.get())
            else:
                im.save(buf, format="PNG", compress_level=0)
            return buf.getvalue()

    def ensure_dir(self, path):
        os.makedirs(path, exist_ok=True)

    def process_file(self, path, mode, progress_cb):
        with open(path, 'rb') as f:
            data = f.read()
        imgs = self.extract_images_from_bytes(data)
        base = os.path.splitext(os.path.basename(path))[0]
        default_root = os.path.dirname(path)
        out_root = self.outdir_var.get().strip() or default_root
        if not imgs:
            self.root.after(0, lambda f=os.path.basename(path): self.status_label.configure(text=f"No detectable images in: {f}"))
            return 0, 0
        total_imgs = len(imgs)
        n_raw = 0
        n_opt = 0
        def write_folder(dest_dir, optimize_flag):
            nonlocal n_raw, n_opt
            self.ensure_dir(dest_dir)
            for idx, blob in enumerate(imgs, 1):
                if self.cancel_event.is_set():
                    break
                try:
                    png_bytes = self.to_png_bytes(blob, optimize=optimize_flag)
                    out_path = os.path.join(dest_dir, f'{idx:04d}.png')
                    with open(out_path, 'wb') as wf:
                        wf.write(png_bytes)
                    if optimize_flag:
                        n_opt += 1
                    else:
                        n_raw += 1
                except Exception as e:
                    print(f"Image {idx} skipped due to error: {e}")
                progress_cb(filename=os.path.basename(path), done_in_file=idx, total_in_file=total_imgs)
        if mode in ["normal", "both"] and not self.cancel_event.is_set():
            folder_normal = os.path.join(out_root, base + '_raw')
            write_folder(folder_normal, optimize_flag=False)
        if mode in ["optimized", "both"] and not self.cancel_event.is_set():
            folder_opt = os.path.join(out_root, base + '_opt')
            write_folder(folder_opt, optimize_flag=True)
        return n_raw, n_opt

    def open_output_location(self):
        path = self.outdir_var.get().strip()
        if not path:
            if self.is_directory:
                path = os.path.dirname(self.selected_paths[0])
            else:
                path = os.path.dirname(self.selected_paths[0]) if self.selected_paths else os.getcwd()
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            print(f"Could not open folder: {e}")

    def run(self):
        self.root.mainloop()

def main():
    app = ImageExtractorGUI()
    app.run()

if __name__ == '__main__':
    main()
