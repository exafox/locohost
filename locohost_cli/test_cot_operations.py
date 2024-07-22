import pytest
import os
import logging
import sys
import subprocess
from locohost_cli.locohost import _create_cot, _update_cot, _compress_cot, start_project

# Configure logging to display messages during test execution
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
logger.addHandler(ch)

@pytest.fixture
def project_setup(tmp_path):
    project_name = "test_project"
    project_dir = tmp_path
    
    # Use start_project to initialize the project
    start_project(project_name, str(project_dir))
    
    context_dir = project_dir / project_name / '.context'
    
    yield project_name, str(project_dir / project_name), str(context_dir)
    
    # Clean up is handled automatically by pytest's tmp_path fixture

def test_start_project(tmp_path):
    project_name = "new_test_project"
    project_dir = tmp_path
    
    start_project(project_name, str(project_dir))
    
    # Check if project directory is created
    assert os.path.exists(os.path.join(project_dir, project_name))
    
    # Check if .context directory is created
    context_dir = os.path.join(project_dir, project_name, '.context')
    assert os.path.exists(context_dir)
    
    # Check if initial CoT file is created
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 1
    
    # Check if README.md is created
    assert os.path.exists(os.path.join(project_dir, project_name, 'README.md'))
    
    # Check if .gitignore is created
    assert os.path.exists(os.path.join(project_dir, project_name, '.gitignore'))
    
    # Check if git repository is initialized
    assert os.path.exists(os.path.join(project_dir, project_name, '.git'))

def test_create_cot(project_setup):
    project_name, _, context_dir = project_setup
    _create_cot(project_name, "Additional CoT entry", context_dir=context_dir)
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 2  # One from start_project, one from this test
    
    with open(os.path.join(context_dir, cot_files[-1]), 'r') as f:
        content = f.read()
    assert "Additional CoT entry" in content
    assert "# Chain of Thought Entry 2" in content
    assert f"Project: {project_name}" in content

def test_update_cot(project_setup):
    project_name, _, context_dir = project_setup
    _update_cot(project_name, "Updated CoT entry", context_dir=context_dir)
    
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    assert len(cot_files) == 1
    
    with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
        content = f.read()
    assert "Project initialized" in content, f"Content: {content}"  # From start_project
    assert "Updated CoT entry" in content, f"Content: {content}"
    assert "Update:" in content, f"Content: {content}"  # Check for the update section

def test_compress_cot(project_setup):
    project_name, _, context_dir = project_setup
    _update_cot(project_name, "Additional CoT entry", context_dir=context_dir)
    snapshot_file = _compress_cot(project_name, context_dir=context_dir)
    
    assert os.path.exists(snapshot_file)
    
    with open(snapshot_file, 'r') as f:
        content = f.read()
    assert "Chain of Thought Entry" in content  # Check for the title
    assert "Project initialized" in content  # From start_project
    assert "Additional CoT entry" in content
