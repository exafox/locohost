import pytest
import os
import logging
import sys
import subprocess
from locohost_cli.locohost import _create_cot, _update_cot, _compress_cot, start_project

# Configure logging to display messages during test execution
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

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
    
    logger.info(f"Setting up project: {project_name}")
    logger.info(f"Project directory: {project_dir}")
    
    # Use start_project to initialize the project
    start_project(project_name, str(project_dir))
    
    context_dir = project_dir / project_name / '.context'
    logger.info(f"Context directory: {context_dir}")
    
    yield project_name, str(project_dir / project_name), str(context_dir)
    
    logger.info(f"Tearing down project: {project_name}")
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
        cot_files = [f for f in os.listdir(context_dir) if f.endswith('chain_of_thought.log')]
        logger.info(f"CoT files after create {i}: {cot_files}")
        assert len(cot_files) == 1  # One from start_project, plus the new ones
        
        with open(os.path.join(context_dir, cot_files[-1]), 'r') as f:
            content = f.read()
        assert statement in content


def test_update_cot(project_setup):
    project_name, _, context_dir = project_setup
    
    # Test with three true statements that refute the untrue statements
    true_statements = [
        "The Earth is an oblate spheroid, orbiting the Sun in our solar system.",
        "Chocolate is derived from cacao beans, which grow on trees in tropical regions.",
        "Cats are domesticated mammals of the species Felis catus, not extraterrestrial beings."
    ]
    
    for i, statement in enumerate(true_statements, start=1):
        _update_cot(project_name, 'Update: ' + statement, context_dir=context_dir)
        
        cot_files = [f for f in os.listdir(context_dir) if f.endswith('chain_of_thought.log')]
        logger.info(f"CoT files after update {i}: {cot_files}")
        
        with open(os.path.join(context_dir, cot_files[0]), 'r') as f:
            content = f.read()
        assert statement in content
        assert content.count("Update:") == i, f"Expected {i} updates, found {content.count('Update:')}"

def test_compress_cot(project_setup):
    project_name, _, context_dir = project_setup
    
    # Add untrue statements
    untrue_statements = [
        "The Earth is flat.",
        "The Sun revolves around the Earth.",
        "Humans only use 10% of their brains."
    ]
    for statement in untrue_statements:
        _update_cot(project_name, f"Untrue: {statement}", context_dir=context_dir)
    
    # Add true counterfactuals
    true_statements = [
        "The Earth is an oblate spheroid.",
        "The Earth revolves around the Sun.",
        "Humans use their entire brain, though not all at once."
    ]
    for statement in true_statements:
        _update_cot(project_name, f"True: {statement}", context_dir=context_dir)
    
    snapshot_file = _compress_cot(project_name, context_dir=context_dir)
    
    assert os.path.exists(snapshot_file)
    logger.info(f"Snapshot file created: {snapshot_file}")
    
    with open(snapshot_file, 'r') as f:
        content = f.read()
    
    # Check that true statements are included
    for statement in true_statements:
        assert statement in content
    
    # Check that untrue statements are excluded
    for statement in untrue_statements:
        assert statement not in content
