import os

class Session:
    _instance = None
    _project_dir = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
            cls._instance.project_name = None
            cls._instance.project_dir = None
            cls._instance.context_dir = None
            cls._instance._cot_journal_cache = {}
            cls._instance.project_files = []
        return cls._instance

    def set_project(self, project_name, project_dir):
        self.project_name = project_name
        self.project_dir = os.path.join(project_dir, project_name)
        self.context_dir = os.path.join(self.project_dir, '.context')
        self.scan_project_files()

    def get_project_dir(self):
        return self.project_dir

    def get_context_dir(self):
        return self.context_dir

    def get_project_name(self):
        return self.project_name

    def set_project_dir(self, project_dir):
        self._project_dir = project_dir
        self.scan_project_files()

    def get_project_dir(self):
        return self._project_dir

    def scan_project_files(self):
        self.project_files = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                self.project_files.append(os.path.join(root, file))

    def get_project_files(self):
        return self.project_files
