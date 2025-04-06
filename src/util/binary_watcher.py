import os
import threading
import time

from PyQt5 import QtCore
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class Worker(QtCore.QObject):
    newBinary = QtCore.pyqtSignal(str, str)
    logWarning = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.known_paths = set()
        self.lock = threading.Lock()
        home = os.path.expanduser("~")
        self.bin_dirs = [
            "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin",
            os.path.join(home, ".local/bin"), os.path.join(home, "bin"),
            os.path.join(home, ".cargo/bin"), os.path.join(home, "go/bin")
        ]
        self.apt_history = "/var/log/apt/history.log"
        self.dpkg_log = "/var/log/dpkg.log"
        self.apt_last_pos = 0
        self.dpkg_last_pos = 0
        self.last_apt_packages = []
        self.last_apt_time = 0
        self.last_dpkg_packages = []
        self.last_dpkg_time = 0

        self.observer = None

    class EventHandler(FileSystemEventHandler):
        def __init__(self, worker):
            super().__init__()
            self.worker = worker

        def on_created(self, event):
            if event.is_directory:
                return
            self.worker.handle_created(event.src_path)

        def on_moved(self, event):
            if event.is_directory:
                return
            dest_path = getattr(event, 'dest_path', None)
            if dest_path:
                self.worker.handle_created(dest_path)

        def on_modified(self, event):
            if event.is_directory:
                return
            self.worker.handle_modified(event.src_path)

    @QtCore.pyqtSlot()
    def start_monitoring(self):
        self.observer = Observer()
        handler = Worker.EventHandler(self)
        warnings = []
        if os.path.exists(self.apt_history):
            try:
                with open(self.apt_history, "rb") as f:
                    f.seek(0, os.SEEK_END)
                    self.apt_last_pos = f.tell()
                self.observer.schedule(handler, os.path.dirname(self.apt_history), recursive=False)
            except PermissionError:
                warnings.append("apt history.log")
        else:
            try:
                self.observer.schedule(handler, "/var/log/apt", recursive=False)
            except PermissionError:
                warnings.append("apt history.log")

        if os.path.exists(self.dpkg_log):
            try:
                with open(self.dpkg_log, "rb") as f:
                    f.seek(0, os.SEEK_END)
                    self.dpkg_last_pos = f.tell()
                self.observer.schedule(handler, os.path.dirname(self.dpkg_log), recursive=False)
            except PermissionError:
                warnings.append("dpkg.log")
        else:
            try:
                self.observer.schedule(handler, "/var/log", recursive=False)
            except PermissionError:
                warnings.append("dpkg.log")

        for d in self.bin_dirs:
            try:
                if os.path.isdir(d):
                    self.observer.schedule(handler, d, recursive=False)
            except PermissionError:
                warnings.append(f"не может отслеживать {d}")
        self.observer.start()
        if warnings:
            warn_text = ", ".join(warnings)
            self.logWarning.emit(f"Нет доступа к {warn_text} (данные об установках из этих источников недоступны)")

    def scan_all_directories(self):
        for d in self.bin_dirs:
            if os.path.isdir(d):
                try:
                    for entry in os.listdir(d):
                        path = os.path.join(d, entry)
                        if (os.path.isfile(path) or os.path.islink(path)) and os.access(path, os.X_OK):
                            with self.lock:
                                if path in self.known_paths:
                                    continue
                                self.known_paths.add(path)
                            source = self.determine_source(path)
                            self.newBinary.emit(path, source)
                except PermissionError:
                    continue

    def handle_created(self, path):
        with self.lock:
            if not os.access(path, os.X_OK):
                return
            if path in self.known_paths:
                return
            self.known_paths.add(path)
        source = self.determine_source(path)
        self.newBinary.emit(path, source)

    def handle_modified(self, path):
        skip_exts = ('.env', '.conf', '.ini', '.txt', '.md', '.html', '.xml', '.json')

        if path.endswith(skip_exts):
            return
        if not os.access(path, os.X_OK):
            return
        if path == self.apt_history:
            try:
                with open(self.apt_history, "r") as f:
                    f.seek(self.apt_last_pos)
                    new_data = f.read()
                    self.apt_last_pos = f.tell()
            except Exception:
                return
            packages = []
            for line in new_data.splitlines():
                line = line.strip()
                if line.startswith("Install:"):
                    items = line[len("Install:"):].split(",")
                    for item in items:
                        pkg = item.strip().split(":")[0]
                        if pkg:
                            packages.append(pkg)
            if packages:
                with self.lock:
                    self.last_apt_packages = packages
                    self.last_apt_time = time.time()
        elif path == self.dpkg_log:
            try:
                with open(self.dpkg_log, "r") as f:
                    f.seek(self.dpkg_last_pos)
                    new_data = f.read()
                    self.dpkg_last_pos = f.tell()
            except Exception:
                return
            packages = []
            for line in new_data.splitlines():
                line = line.strip()
                if " installed " in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "installed" and i + 1 < len(parts):
                            pkg_arch = parts[i + 1]
                            pkg = pkg_arch.split(":")[0]
                            packages.append(pkg)
            if packages:
                with self.lock:
                    self.last_dpkg_packages = packages
                    self.last_dpkg_time = time.time()

    def determine_source(self, path):
        src = ""
        current_time = time.time()
        origin = None
        packages = []
        with self.lock:
            if self.last_apt_time and current_time - self.last_apt_time < 10:
                origin = "APT"
                packages = self.last_apt_packages
            elif self.last_dpkg_time and current_time - self.last_dpkg_time < 10:
                origin = "DPKG"
                packages = self.last_dpkg_packages
        if origin:
            if packages:
                if len(packages) == 1:
                    src = f"{origin} (пакет {packages[0]})"
                else:
                    pkgs_str = ", ".join(packages[:2])
                    if len(packages) > 2:
                        pkgs_str += ", ..."
                    src = f"{origin} (неск. пакетов: {pkgs_str})"
            else:
                src = origin
        else:
            if path.startswith("/snap/"):
                src = "Snap"
            elif "/flatpak/exports/bin" in path:
                src = "Flatpak"
            elif path.startswith("/usr") or path.startswith("/var/lib/flatpak"):
                src = "Система (apt/вручную)"
            elif path.startswith(os.path.expanduser("~")):
                if path.startswith(os.path.join(os.path.expanduser("~"), ".cargo")):
                    src = "Cargo (Rust)"
                elif path.startswith(os.path.join(os.path.expanduser("~"), "go")):
                    src = "Go (GoLang)"
                else:
                    src = "Пользователь"
            else:
                src = "Неизвестно"
        return src

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()


