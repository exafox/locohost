import os
import logging
from llama_index import SimpleDirectoryReader, VectorStoreIndex, StorageContext, ServiceContext
from llama_index.vector_stores.simple import SimpleVectorStore
from llama_index.llms import Anthropic
from llama_index.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class Session:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.project_name = None
        self.project_dir = None
        self.context_dir = None
        self._cot_journal_cache = {}
        self.project_files = []
        self.query_engine = None

    def set_project(self, project_name, project_dir):
        self.project_name = project_name
        self.project_dir = os.path.join(project_dir, project_name)
        self.context_dir = os.path.join(self.project_dir, '.context')
        os.makedirs(self.context_dir, exist_ok=True)
        self._scan_project_files()
        self._initialize_query_engine()

    def set_project_dir(self, project_dir):
        if self.project_name:
            self.project_dir = os.path.join(project_dir, self.project_name)
        else:
            self.project_dir = project_dir
        self._scan_project_files()
        self._initialize_query_engine()

    def get_project_name(self):
        return self.project_name

    def get_project_dir(self):
        return self.project_dir

    def _scan_project_files(self):
        if not os.path.exists(self.project_dir):
            logger.warning(f"Project directory does not exist: {self.project_dir}")
            return

        reader = SimpleDirectoryReader(input_dir=self.project_dir, recursive=True)
        documents = reader.load_data()
        self.project_files = [doc.metadata['file_path'] for doc in documents]

    def _initialize_query_engine(self):
        if not self.project_files:
            logger.warning("No project files found. Query engine not initialized.")
            return

        reader = SimpleDirectoryReader(input_files=self.project_files)
        documents = reader.load_data()
        
        # Initialize Anthropic LLM
        llm = Anthropic(model="claude-2")
        
        # Use HuggingFace embeddings instead of OpenAI
        embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create a custom ServiceContext
        service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)
        
        storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            service_context=service_context
        )
        self.query_engine = index.as_query_engine()

    def search(self, query):
        if self.query_engine is None:
            raise ValueError("Query engine not initialized. Set a project first.")
        return self.query_engine.query(query)

    def get_context_dir(self):
        if self.context_dir is None:
            raise ValueError("Context directory not set. Set a project first.")
        return self.context_dir
