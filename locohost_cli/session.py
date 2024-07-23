import os
import logging
from llama_index import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.simple import SimpleVectorStore

logger = logging.getLogger(__name__)

class Session:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
            cls._instance.project_name = None
            cls._instance.project_dir = None
            cls._instance.context_dir = None
            cls._instance._cot_journal_cache = {}
            cls._instance.project_files = []
            cls._instance.query_engine = None
        return cls._instance

    def set_project(self, project_name, project_dir):
        self.project_name = project_name
        self.project_dir = os.path.join(project_dir, project_name)
        self.context_dir = os.path.join(self.project_dir, '.context')
        self._scan_project_files()
        self._initialize_query_engine()

    def _scan_project_files(self):
        reader = SimpleDirectoryReader(input_dir=self.project_dir, recursive=True)
        documents = reader.load_data()
        self.project_files = [doc.metadata['file_path'] for doc in documents]

    def _initialize_query_engine(self):
        reader = SimpleDirectoryReader(input_dir=self.project_dir, recursive=True)
        documents = reader.load_data()
        storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        self.query_engine = index.as_query_engine()

    def search(self, query):
        if self.query_engine is None:
            raise ValueError("Query engine not initialized. Set a project first.")
        return self.query_engine.query(query)
