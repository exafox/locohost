import pytest
import os
import shutil
from locohost_cli.locohost import _create_cot, _update_cot, _compress_cot

@pytest.fixture
def project_setup():
    project_name = "test_project"
    project_dir = os.path.join(os.getcwd(), project_name)
    context_dir = os.path.join(project_dir, '.context')
    
    # Create project directory
    os.makedirs(context_dir, exist_ok=True)
    
    yield project_name, project_dir, context_dir
    
    # Clean up: remove the test project directory
    shutil.rmtree(project_dir)

def test_create_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Initial CoT entry")
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 1
    
    with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
        content = f.read()
    assert "Initial CoT entry" in content

def test_update_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Initial CoT entry")
    _update_cot(project_name, "Updated CoT entry")
    
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 1
    
    with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
        content = f.read()
    assert "Initial CoT entry" in content
    assert "Updated CoT entry" in content

def test_compress_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Initial CoT entry")
    _update_cot(project_name, "Updated CoT entry")
    _compress_cot(project_name)
    
    snapshot_file = os.path.join(context_dir, 'snapshot.md')
    assert os.path.exists(snapshot_file)
    
    with open(snapshot_file, 'r') as f:
        content = f.read()
    assert "Initial CoT entry" in content
    assert "Updated CoT entry" in content
