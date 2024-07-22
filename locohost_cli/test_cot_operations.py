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
    
    # Test with three untrue statements
    untrue_statements = [
        "The Earth is flat and supported by four elephants standing on a giant turtle.",
        "Chocolate is a vegetable that grows underground like potatoes.",
        "All cats are actually tiny aliens in disguise, monitoring human behavior."
    ]
    
    for i, statement in enumerate(untrue_statements, start=1):
        _create_cot(project_name, statement, context_dir=context_dir)
        cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
        assert len(cot_files) == i + 1  # One from start_project, plus the new ones
        
        with open(os.path.join(context_dir, cot_files[-1]), 'r') as f:
            content = f.read()
        assert statement in content
        assert f"# Chain of Thought Entry {i + 1}" in content
        assert f"Project: {project_name}" in content

def test_update_cot(project_setup):
    project_name, _, context_dir = project_setup
    
    # Test with three true statements that refute the untrue statements
    true_statements = [
        "The Earth is an oblate spheroid, orbiting the Sun in our solar system.",
        "Chocolate is derived from cacao beans, which grow on trees in tropical regions.",
        "Cats are domesticated mammals of the species Felis catus, not extraterrestrial beings."
    ]
    
    for i, statement in enumerate(true_statements, start=1):
        _update_cot(project_name, statement, context_dir=context_dir)
        
        cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
        assert len(cot_files) == 1
        
        with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
            content = f.read()
        assert "Project initialized" in content, f"Content: {content}"  # From start_project
        assert statement in content, f"Content: {content}"
        assert f"Update:" in content, f"Content: {content}"  # Check for the update section
        assert content.count("Update:") == i, f"Expected {i} updates, found {content.count('Update:')}"

def test_compress_cot(project_setup):
    project_name, _, context_dir = project_setup
    
    # Add true and untrue statements
    _update_cot(project_name, "True statement: The Earth is an oblate spheroid.", context_dir=context_dir)
    _update_cot(project_name, "Untrue statement: The Earth is flat.", context_dir=context_dir)
    _update_cot(project_name, "True statement: Water is composed of hydrogen and oxygen.", context_dir=context_dir)
    _update_cot(project_name, "Untrue statement: Water is a element.", context_dir=context_dir)
    
    snapshot_file = _compress_cot(project_name, context_dir=context_dir)
    
    assert os.path.exists(snapshot_file)
    
    with open(snapshot_file, 'r') as f:
        content = f.read()
    
    # Check for the title and initial entry
    assert "Chain of Thought Entry" in content
    assert "Project initialized" in content
    
    # Check that true statements are included
    assert "The Earth is an oblate spheroid" in content
    assert "Water is composed of hydrogen and oxygen" in content
    
    # Check that untrue statements are excluded
    assert "The Earth is flat" not in content
    assert "Water is a element" not in content
