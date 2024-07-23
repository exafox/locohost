import pytest
import os
import logging
import sys
import time
from tempfile import TemporaryDirectory
from locohost_cli.locohost import Session, search_project
from llama_index import SimpleDirectoryReader, VectorStoreIndex, StorageContext

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

@pytest.fixture
def temp_project_setup():
    with TemporaryDirectory() as temp_dir:
        project_name = "test_performance_project"
        project_dir = os.path.join(temp_dir, project_name)
        os.makedirs(project_dir)
        
        # Create some sample files
        for i in range(100):
            with open(os.path.join(project_dir, f"file_{i}.txt"), "w") as f:
                f.write(f"This is test file {i} with some content for searching.")
        
        session = Session()
        session.set_project(project_name, temp_dir)
        
        yield project_name, project_dir, session

def test_file_loading_performance(temp_project_setup):
    _, project_dir, _ = temp_project_setup
    
    logger.info("Starting file loading performance test")
    start_time = time.time()
    
    reader = SimpleDirectoryReader(input_dir=project_dir, recursive=True)
    documents = reader.load_data()
    
    end_time = time.time()
    load_time = end_time - start_time
    
    logger.info(f"File loading completed in {load_time:.2f} seconds")
    logger.info(f"Number of documents loaded: {len(documents)}")
    
    assert len(documents) == 100, f"Expected 100 documents, but loaded {len(documents)}"
    assert load_time < 5, f"File loading took {load_time:.2f} seconds, which is longer than expected"

def test_search_performance(temp_project_setup):
    project_name, _, session = temp_project_setup
    
    logger.info("Starting search performance test")
    
    # First, ensure the query engine is initialized
    start_time = time.time()
    session._initialize_query_engine()
    end_time = time.time()
    index_time = end_time - start_time
    
    logger.info(f"Query engine initialization completed in {index_time:.2f} seconds")
    
    # Perform a search
    query = "test file content"
    start_time = time.time()
    result = search_project(query)
    end_time = time.time()
    search_time = end_time - start_time
    
    logger.info(f"Search completed in {search_time:.2f} seconds")
    logger.info(f"Search result: {result}")
    
    assert result is not None, "Search result should not be None"
    assert search_time < 2, f"Search took {search_time:.2f} seconds, which is longer than expected"

def test_large_file_performance(temp_project_setup):
    _, project_dir, session = temp_project_setup
    
    logger.info("Starting large file performance test")
    
    # Create a large file
    large_file_path = os.path.join(project_dir, "large_file.txt")
    with open(large_file_path, "w") as f:
        f.write("Large file content\n" * 100000)  # Approximately 1.9 MB file
    
    start_time = time.time()
    session._scan_project_files()
    session._initialize_query_engine()
    end_time = time.time()
    process_time = end_time - start_time
    
    logger.info(f"Large file processing completed in {process_time:.2f} seconds")
    
    assert os.path.basename(large_file_path) in session.project_files, "Large file should be in project files"
    assert process_time < 10, f"Large file processing took {process_time:.2f} seconds, which is longer than expected"
