import argparse
import logging
import json
import os
from datetime import datetime
from anthropic import Anthropic
import subprocess
from datetime import datetime
from locohost_cli.session import Session

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the Anthropic client once at the module level
client = Anthropic()
logger.debug(f"Anthropic client initialized: {client}")

# Initialize the Session
session = Session()

def search_project(query):
    try:
        result = session.search(query)
        logger.info(f"Search result for query '{query}': {result}")
        return result
    except ValueError as e:
        logger.error(f"Error searching project: {e}")
        return None

# ========================
# Helper Functions
# ========================

def _get_chain_of_thought_journal():
    context_dir = session.get_context_dir()
    # Check if the journal for this context_dir is already cached
    if context_dir in session._cot_journal_cache:
        logger.debug(f"Using cached journal for context_dir: {context_dir}")
        return session._cot_journal_cache[context_dir]

    # Create a separate logger for Chain of Thought entries
    chain_of_thought_logger = logging.getLogger(f'chain_of_thought_{context_dir}')
    chain_of_thought_logger.setLevel(logging.INFO)
    cot_formatter = logging.Formatter('%(asctime)s - %(message)s')
    

    # Ensure the context directory exists
    os.makedirs(context_dir, exist_ok=True)
    

    commit_position = int(subprocess.run(['git', 'rev-list', '--count', 'HEAD'], capture_output=True, text=True).stdout.strip())
    iso_time = datetime.now().isoformat(timespec='seconds')
    log_file_path = os.path.join(context_dir, f'{commit_position}_{iso_time}_chain_of_thought.log')
    logger.info(f"HELOOOOO Creating Chain of Thought log file: {log_file_path}")
    cot_handler = logging.FileHandler(log_file_path)
    cot_handler.setFormatter(cot_formatter)
    chain_of_thought_logger.addHandler(cot_handler)

    # Create a custom logger that flushes after each write
    class FlushingLogger:
        def __init__(self, logger, handler):
            self.logger = logger
            self.handler = handler

        def info(self, message):
            self.logger.info(message)
            self.handler.flush()

    flushing_logger = FlushingLogger(chain_of_thought_logger, cot_handler)
    
    # Cache the logger
    session._cot_journal_cache[context_dir] = flushing_logger

    return flushing_logger

    
def _journal(content):
    journal = _get_chain_of_thought_journal()
    journal.info(content)
    
def _create_cot(context):
    _journal(context)

def _update_cot(context):
    _journal(context)

import subprocess
import anthropic

def _compress_cot():
    project_name = session.get_project_name()
    context_dir = session.get_context_dir()
    logger.debug(f"Compressing CoT for project: {project_name}")
    snapshot_file = os.path.join(context_dir, 'snapshot.md')
    logger.debug(f"Context directory: {context_dir}")
    logger.debug(f"Snapshot file: {snapshot_file}")

    if not os.path.exists(context_dir):
        logger.error(f"Context directory does not exist: {context_dir}")
        return

    # 1. Read the current snapshot file
    current_snapshot = ""
    if os.path.exists(snapshot_file):
        with open(snapshot_file, 'r') as f:
            current_snapshot = f.read()
        logger.debug(f"Current snapshot length: {len(current_snapshot)} characters")
    else:
        logger.debug("No existing snapshot file found")

    # 2. Read all CoT files
    cot_files = [f for f in os.listdir(context_dir) if f.endswith('chain_of_thought.log')]
    cot_content = ""
    for cot_file in cot_files:
        with open(os.path.join(context_dir, cot_file), 'r') as f:
            cot_content += f.read() + "\n\n"
    logger.debug(f"CoT content length: {len(cot_content)} characters")
    logger.debug(f"CoT files found: {cot_files}")

    # 3. Send data to Anthropic for compression and commit message generation
    prompt = f"""Human: Please compress the following Chain of Thought (CoT) information. 
    Preserve all important information, especially the content of the CoT entries.
    You may reorganize and summarize the information, but do not remove any significant details.
    
    Important: If there are any untrue statements in the CoT content, they should be removed or corrected in the compressed result. Only include factual and correct information in the final snapshot.
    
    Current snapshot:
    {current_snapshot}
    
    CoT content:
    {cot_content}
    
    Provide the compressed result in Markdown format, which should include all CoT entries in a summarized form, excluding any untrue statements.
    
    After compressing the content, please generate a concise and informative commit message that summarizes the key updates or changes made in this compression, including any corrections of untrue statements.
    
    Format your response as follows:
    [COMPRESSED_CONTENT]
    (Your compressed content here, with untrue statements removed or corrected)
    [/COMPRESSED_CONTENT]
    
    [COMMIT_MESSAGE]
    (Your commit message here, mentioning any corrections made)
    [/COMMIT_MESSAGE]

    Assistant:
    """

    logger.info("Sending request to Anthropic API")
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=3000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        logger.debug(f"Received response from Anthropic API")
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        logger.exception("Detailed error information:")
        return

    response_content = response.content[0].text

    # Extract compressed content and commit message from the response
    compressed_content = response_content.split("[COMPRESSED_CONTENT]")[1].split("[/COMPRESSED_CONTENT]")[0].strip()
    commit_message = response_content.split("[COMMIT_MESSAGE]")[1].split("[/COMMIT_MESSAGE]")[0].strip()

    logger.debug(f"Compressed content length: {len(compressed_content)} characters")
    logger.debug(f"Commit message: {commit_message}")

    # 4. Write the response to the new snapshot file
    try:
        with open(snapshot_file, 'w') as f:
            f.write(compressed_content)
        logger.info(f"Written compressed content to {snapshot_file}")
        logger.info(f"Compressed content: {compressed_content}")
    except IOError as e:
        logger.error(f"Error writing to snapshot file: {e}")
        logger.exception("Detailed error information:")
        return

    # 5. Commit the changes to git
    git_add_command = ["git", "add", os.path.basename(snapshot_file)]
    git_commit_command = ["git", "commit", "-m", commit_message]
    
    logger.debug(f"Running git add command: {' '.join(git_add_command)}")
    try:
        subprocess.run(git_add_command, cwd=context_dir, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git add: {e}")
        logger.exception("Detailed error information:")
        return

    logger.debug(f"Running git commit command: {' '.join(git_commit_command)}")
    try:
        subprocess.run(git_commit_command, cwd=context_dir, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git commit: {e}")
        logger.exception("Detailed error information:")
        return

    logger.info(f"CoT snapshot compressed and updated for project: {project_name}")
    logger.info(f"Commit message: {commit_message}")

    return snapshot_file

# ========================
# Entrypoint Functions
# ========================

def create_prd(project_context_file):
    logger.info(f"[NO-OP] Executing create_prd with project_context_file: {project_context_file}")
    pass

def edit_prd(project_name, prd_file):
    logger.info(f"[NO-OP] Executing edit_prd with project_name: {project_name}, prd_file: {prd_file}")
    pass

def start_project(project_name, project_dir):
    logger.info(f"Starting new project: {project_name}")
    
    session.set_project(project_name, project_dir)
    
    os.makedirs(session.get_project_dir(), exist_ok=True)
    logger.info(f"Project directory: {session.get_project_dir()}")
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=session.get_project_dir(), check=True)
    
    # Create .context directory
    os.makedirs(session.get_context_dir(), exist_ok=True)
    
    # Create initial CoT entry
    initial_context = f"Project '{project_name}' initialized on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    _create_cot(initial_context)
    logger.info(f"Initial CoT entry created for project '{session.get_context_dir()}'")
    
    # Create initial snapshot
    snapshot_file = os.path.join(session.get_context_dir(), 'snapshot.md')
    with open(snapshot_file, 'w') as f:
        f.write(f"# {project_name} Snapshot\n\n{initial_context}\n")
    logger.info(f"Initial snapshot created at {snapshot_file}")
    
    # Create basic project structure
    with open(os.path.join(session.get_project_dir(), 'README.md'), 'w') as f:
        f.write(f"# {project_name}\n\nProject description goes here.")
    
    with open(os.path.join(session.get_project_dir(), '.gitignore'), 'w') as f:
        f.write("# Python\n__pycache__/\n*.py[cod]\n\n# Virtual environment\nvenv/\n.env\n")
    
    logger.info(f"Project '{project_name}' initialized successfully in {session.get_project_dir()}")

def git_push(project_name, commit_message):
    logger.info(f"[NO-OP] Executing git_push with project_name: {project_name}, commit_message: {commit_message}")
    pass

def run_tests(project_name):
    logger.info(f"Executing run_tests for project: {project_name}")
    project_dir = os.path.join(os.getcwd(), project_name)
    test_dir = os.path.join(project_dir, 'tests')
    report_dir = os.path.join(project_dir, 'test_reports')
    
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = os.path.join(report_dir, 'test_report.html')
    
    pytest_command = [
        "pytest",
        test_dir,
        f"--html={report_file}",
        "--self-contained-html"
    ]
    
    try:
        subprocess.run(pytest_command, check=True)
        logger.info(f"Tests completed. HTML report generated at: {report_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed with exit code {e.returncode}")
        logger.error(f"HTML report generated at: {report_file}")

def deploy(project_name):
    logger.info(f"[NO-OP] Executing deploy with project_name: {project_name}")
    pass


def generate_new_project_code(project_name, language):
    logger.info(f"[NO-OP] Executing generate_new_project_code with project_name: {project_name}, language: {language}")
    pass

def edit_project_code(file_path):
    logger.info(f"Executing edit_project_code with project_name: {session.get_project_name()}, file_path: {file_path}")
    
    # 1. Run compress_cot and create_prd
    _compress_cot()
    create_prd(os.path.join(session.get_context_dir(), 'project_context.txt'))
    
    # 2. Locate relevant files (stub)
    def locate_relevant_files(file_path):
        # This is a stub function. In a real implementation, this would use
        # project-specific logic to find related files.
        return [file_path]
    
    relevant_files = locate_relevant_files(file_path)
    
    # 3. Use Claude to edit the code
    snapshot_file = os.path.join(session.get_context_dir(), 'snapshot.md')
    
    with open(snapshot_file, 'r') as f:
        snapshot_content = f.read()
    
    for file in relevant_files:
        with open(file, 'r') as f:
            file_content = f.read()
        
        prompt = f"""Human: I need to edit the following code file for the project {session.get_project_name()}. 
        Here's the current project context:
        
        {snapshot_content}
        
        And here's the content of the file to edit:
        
        {file_content}
        
        Please suggest improvements or changes to this code based on the project context and best practices.

        Assistant: Certainly! I'll review the code and suggest improvements based on the project context and best practices. Here are my suggestions:

        [Provide detailed suggestions for improvements or changes]

        Human: Great, please provide the updated code incorporating these changes.

        Assistant: Certainly! Here's the updated code incorporating the suggested changes:

        [UPDATED_CODE]
        {file_content}  # This will be replaced with the actual updated code
        [/UPDATED_CODE]

        Human: Thank you. Now, please provide a brief summary of the changes made and their rationale.

        Assistant: Certainly! Here's a summary of the changes made and their rationale:

        [CHANGE_SUMMARY]
        1. [Change 1]: [Rationale]
        2. [Change 2]: [Rationale]
        ...
        [/CHANGE_SUMMARY]

        Human: Thank you for the summary. Please provide this information in the following format:
        [FILE_TEXT]
        (Updated file content)
        [/FILE_TEXT]
        
        [COMMIT_MESSAGE]
        (A concise commit message summarizing the changes)
        [/COMMIT_MESSAGE]
        
        [CHANGELOG]
        (A more detailed changelog entry)
        [/CHANGELOG]

        Assistant: Certainly! Here's the information in the requested format:

        [FILE_TEXT]
        {file_content}  # This will be replaced with the actual updated code
        [/FILE_TEXT]
        
        [COMMIT_MESSAGE]
        Updated {os.path.basename(file)}: [Brief summary of changes]
        [/COMMIT_MESSAGE]
        
        [CHANGELOG]
        - [Detailed change 1]
        - [Detailed change 2]
        ...
        [/CHANGELOG]
        """
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=3000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_content = response.content[0].text
        
        # Extract updated file content, commit message, and changelog
        updated_content = response_content.split("[FILE_TEXT]")[1].split("[/FILE_TEXT]")[0].strip()
        commit_message = response_content.split("[COMMIT_MESSAGE]")[1].split("[/COMMIT_MESSAGE]")[0].strip()
        changelog = response_content.split("[CHANGELOG]")[1].split("[/CHANGELOG]")[0].strip()
        
        # Write the updated content back to the file
        with open(file, 'w') as f:
            f.write(updated_content)
        
        # Commit the changes
        subprocess.run(["git", "add", file], cwd=os.path.dirname(file), check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=os.path.dirname(file), check=True)
        
        # Update the changelog
        changelog_file = os.path.join(session.get_context_dir(), 'CHANGELOG.md')
        with open(changelog_file, 'a') as f:
            f.write(f"\n\n## {datetime.now().strftime('%Y-%m-%d')}\n{changelog}\n")
    
    logger.info(f"Code editing completed for project: {session.get_project_name()}")

def generate_tests_for_diff(project_name, diff_file):
    logger.info(f"[NO-OP] Executing generate_tests_for_diff with project_name: {project_name}, diff_file: {diff_file}")
    pass

def review_and_refactor(project_name):
    logger.info(f"[NO-OP] Executing review_and_refactor with project_name: {project_name}")
    pass

def generate_performance_tests(project_name):
    logger.info(f"[NO-OP] Executing generate_performance_tests with project_name: {project_name}")
    pass

def upgrade_dependencies(project_name):
    logger.info(f"[NO-OP] Executing upgrade_dependencies with project_name: {project_name}")
    pass

def bootstrap_database_migrations(project_name):
    logger.info(f"[NO-OP] Executing bootstrap_database_migrations with project_name: {project_name}")
    pass

def generate_docs_snapshot(project_name):
    logger.info(f"[NO-OP] Executing generate_docs_snapshot with project_name: {project_name}")
    pass

def generate_or_update_local_deployment(project_name):
    logger.info(f"[NO-OP] Executing generate_or_update_local_deployment with project_name: {project_name}")
    pass

def generate_or_update_production_deployment(project_name):
    logger.info(f"[NO-OP] Executing generate_or_update_production_deployment with project_name: {project_name}")
    pass

def main():
    # Run this code at the beginning of main()
    print("Starting locohost.py")
    logger.info("locohost.py execution started")

    parser = argparse.ArgumentParser(description="AI-assisted project management and development tool for Kubernetes-based applications")
    parser.add_argument("--project-dir", help="Directory of the project", default=os.getcwd())
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # create_prd
    create_prd_parser = subparsers.add_parser("create_prd", help="Create a Product Requirements Document")
    create_prd_parser.add_argument("--project-context-file", required=True, help="Path to the project context file")

    # edit_prd
    edit_prd_parser = subparsers.add_parser("edit_prd", help="Edit an existing Product Requirements Document")
    edit_prd_parser.add_argument("--project-name", required=True, help="Name of the project")
    edit_prd_parser.add_argument("--prd-file", required=True, help="Path to the PRD file to edit")

    # start_project
    start_project_parser = subparsers.add_parser("start_project", help="Initialize a new project with CoT journaling")
    start_project_parser.add_argument("--project-name", required=True, help="Name of the project")

    # git_push
    git_push_parser = subparsers.add_parser("git_push", help="Analyze git status and create a commit message")
    git_push_parser.add_argument("--commit-message", required=True, help="Commit message")

    # run_tests
    subparsers.add_parser("run_tests", help="Analyze test results for the project")

    # deploy
    subparsers.add_parser("deploy", help="Analyze deployment information for the project")

    # generate_new_project_code
    generate_new_project_code_parser = subparsers.add_parser("generate_new_project_code", help="Generate initial code for a new project based on requirements")
    generate_new_project_code_parser.add_argument("--language", required=True, choices=["Python", "Go", "TypeScript"], help="Programming language to use")

    # edit_project_code
    edit_project_code_parser = subparsers.add_parser("edit_project_code", help="Edit existing project code with AI assistance")
    edit_project_code_parser.add_argument("--file-path", required=True, help="Path to the file to edit")

    # generate_tests_for_diff
    generate_tests_for_diff_parser = subparsers.add_parser("generate_tests_for_diff", help="Generate tests for a specific diff using Aider")
    generate_tests_for_diff_parser.add_argument("--diff-file", required=True, help="Path to the diff file")

    # Other parsers remain unchanged...

    args = parser.parse_args()

    # Set the project directory in the session
    session.set_project_dir(args.project_dir)

    if args.action == "create_prd":
        create_prd(args.project_context_file)
    elif args.action == "edit_prd":
        edit_prd(args.project_name, args.prd_file)
    elif args.action == "start_project":
        start_project(args.project_name, args.project_dir)
    elif args.action == "git_push":
        git_push(args.project_name, args.commit_message)
    elif args.action == "run_tests":
        run_tests(session.get_project_name())
        print(f"Test report generated for project: {session.get_project_name()}")
        print("You can find the HTML report in the 'test_reports' directory of your project.")
    elif args.action == "deploy":
        deploy(session.get_project_name())
    elif args.action == "generate_new_project_code":
        generate_new_project_code(session.get_project_name(), args.language)
    elif args.action == "edit_project_code":
        edit_project_code(args.file_path)
    elif args.action == "generate_tests_for_diff":
        generate_tests_for_diff(session.get_project_name(), args.diff_file)
    elif args.action == "review_and_refactor":
        review_and_refactor(session.get_project_name())
    elif args.action == "generate_performance_tests":
        generate_performance_tests(session.get_project_name())
    elif args.action == "upgrade_dependencies":
        upgrade_dependencies(session.get_project_name())
    elif args.action == "bootstrap_database_migrations":
        bootstrap_database_migrations(session.get_project_name())
    elif args.action == "generate_docs_snapshot":
        generate_docs_snapshot(session.get_project_name())
    elif args.action == "generate_or_update_local_deployment":
        generate_or_update_local_deployment(session.get_project_name())
    elif args.action == "generate_or_update_production_deployment":
        generate_or_update_production_deployment(session.get_project_name())

def get_snapshot_data(context: str) -> dict:
    prompt = f"""Human: Generate snapshot data based on this context: {context}
    
    Format your response as follows:
    [FILE_TEXT]
    (Your file text here)
    [/FILE_TEXT]
    
    [COMMIT_MESSAGE]
    (Your commit message here)
    [/COMMIT_MESSAGE]
    
    [CHANGELOG]
    (Your changelog here)
    [/CHANGELOG]

    Assistant: 
    """

    response = client.completions.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens_to_sample=1000,
        prompt=prompt
    )

    response_content = response.completion

    # Extract data from the response
    file_text = response_content.split("[FILE_TEXT]")[1].split("[/FILE_TEXT]")[0].strip()
    commit_message = response_content.split("[COMMIT_MESSAGE]")[1].split("[/COMMIT_MESSAGE]")[0].strip()
    changelog = response_content.split("[CHANGELOG]")[1].split("[/CHANGELOG]")[0].strip()

    return {
        "file_text": file_text,
        "commit_message": commit_message,
        "changelog": changelog
    }

if __name__ == "__main__":
    main()
