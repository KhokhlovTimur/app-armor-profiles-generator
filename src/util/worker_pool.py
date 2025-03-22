from concurrent.futures import ThreadPoolExecutor


class AppArmorWorker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppArmorWorker, cls).__new__(cls)
            cls._instance.executor = ThreadPoolExecutor(max_workers=4)
        return cls._instance

    def exec_async(self, executable):
        return self.executor.submit(executable)
