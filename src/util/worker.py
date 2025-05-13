from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtCore import pyqtSignal, QObject, QTimer


class AppArmorWorker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppArmorWorker, cls).__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=4)
        return cls._instance

    def run_async(self, func, *args, **kwargs):
        return self.executor.submit(func, *args, **kwargs)


class TaskWatcher(QObject):
    finished = pyqtSignal(object)

    def __init__(self, future):
        super().__init__()
        self.future = future
        self._check()

    def _check(self):
        print("[TaskWatcher] Checking...")
        if self.future.done():
            try:
                result = self.future.result()
                print("[TaskWatcher] Future completed:", result)
                self.finished.emit(result)
            except Exception as e:
                print(f"[TaskWatcher] Exception while resolving future: {e}")
                self.finished.emit(["Ошибка выполнения"])
        else:
            QTimer.singleShot(100, self._check)
