import pytest
import os
import logging
from locohost_cli.locohost import _create_cot, _update_cot, _compress_cot

# Configure logging to display messages during test execution
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@pytest.fixture
def project_setup(tmp_path):
    project_name = "test_project"
    project_dir = tmp_path
    context_dir = project_dir / '.context'
    context_dir.mkdir(parents=True, exist_ok=True)
    
    yield project_name, str(project_dir), str(context_dir)
    
    # Clean up is handled automatically by pytest's tmp_path fixture

def test_create_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Initial CoT entry", context_dir=context_dir)
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 1
    
    with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
        content = f.read()
    assert "Initial CoT entry" in content
    assert "# Chain of Thought Entry 1" in content
    assert f"Project: {project_name}" in content

def test_update_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Initial CoT entry", context_dir=context_dir)
    _update_cot(project_name, "Updated CoT entry", context_dir=context_dir)
    
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 1
    
    with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
        content = f.read()
    assert "Initial CoT entry" in content
    assert "Updated CoT entry" in content

def test_compress_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Initial CoT entry", context_dir=context_dir)
    _update_cot(project_name, "Updated CoT entry", context_dir=context_dir)
    _compress_cot(project_name, context_dir=context_dir)
    
    snapshot_file = os.path.join(context_dir, 'snapshot.md')
    assert os.path.exists(snapshot_file)
    
    with open(snapshot_file, 'r') as f:
        content = f.read()
    assert "Initial CoT entry" in content
    assert "Updated CoT entry" in content
