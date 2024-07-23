import os
from llama_index.core import SimpleDirectoryReader

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
        if self.project_name != project_name or self.project_dir != os.path.join(project_dir, project_name):
            self.project_name = project_name
            self.project_dir = os.path.join(project_dir, project_name)
            self.context_dir = os.path.join(self.project_dir, '.context')
            self._scan_project_files()

    def get_project_dir(self):
        return self.project_dir

    def get_context_dir(self):
        return self.context_dir

    def get_project_name(self):
        return self.project_name

    def set_project_dir(self, project_dir):
        if self._project_dir != project_dir:
            self._project_dir = project_dir
            self._scan_project_files()

    def get_project_dir(self):
        return self._project_dir

    def _scan_project_files(self):
        reader = SimpleDirectoryReader(input_dir=self.project_dir, recursive=True)
        documents = reader.load_data()
        self.project_files = [doc.metadata['file_path'] for doc in documents]

    def get_project_files(self):
        if not self.project_files:
            self._scan_project_files()
        return self.project_files
