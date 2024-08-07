import argparse
import logging
import json
import os
from datetime import datetime
from anthropic import Anthropic

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the Anthropic client once at the module level
client = Anthropic()
logger.debug(f"Anthropic client initialized: {client}")

# ========================
# Helper Functions
# ========================

def _create_cot(project_name, context, format='md', context_dir=None):
    logger.debug(f"Creating CoT for project: {project_name}, format: {format}")
    context_dir = _get_context_dir(project_name, context_dir)
    logger.debug(f"Context directory: {context_dir}")

    os.makedirs(context_dir, exist_ok=True)
    logger.debug(f"Created context directory: {context_dir}")

    # Get the next available number for the CoT file
    existing_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith(f'.{format}')]
    next_number = len(existing_files) + 1
    logger.debug(f"Next CoT number: {next_number}")

    # Create the new CoT file
    new_cot_file = os.path.join(context_dir, f'cot_{next_number:04d}.{format}')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.debug(f"New CoT file: {new_cot_file}")
    
    try:
        if format == 'md':
            content = f"# Chain of Thought Entry {next_number}\n\n"
            content += f"Created: {timestamp}\n\n"
            content += f"Project: {project_name}\n\n"
            content += "## Entry\n\n"
            content += context
        elif format == 'json':
            content = json.dumps({
                "entry_number": next_number,
                "created": timestamp,
                "project": project_name,
                "content": context
            }, indent=2)
        else:
            logger.error(f"Unsupported format: {format}")
            return

        with open(new_cot_file, 'w') as f:
            f.write(content)
        logger.info(f"Created new CoT file: {new_cot_file}")
        logger.info(f"CoT content: {content}")  # Log full content
    except IOError as e:
        logger.error(f"Error creating CoT file: {e}")
        logger.exception("Detailed error information:")

def _update_cot(project_name, context, format='md', context_dir=None):
    logger.debug(f"Updating CoT for project: {project_name}, format: {format}")
    context_dir = _get_context_dir(project_name, context_dir)
    logger.debug(f"Context directory: {context_dir}")

    if not os.path.exists(context_dir):
        logger.error(f"Context directory does not exist: {context_dir}")
        _create_cot(project_name, context, format, context_dir)
        return

    existing_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith(f'.{format}')]
    logger.debug(f"Existing CoT files: {existing_files}")
    if not existing_files:
        logger.error(f"No existing CoT files found for project: {project_name}")
        return

    latest_file = max(existing_files)
    cot_file = os.path.join(context_dir, latest_file)
    logger.debug(f"Latest CoT file: {cot_file}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if format == 'md':
            with open(cot_file, 'a') as f:
                update_content = f"\n\n## Update: {timestamp}\n\n{context}"
                f.write(update_content)
            logger.info(f"Updated MD file with new content: {update_content}")
        elif format == 'json':
            with open(cot_file, 'r+') as f:
                data = json.load(f)
                update = {
                    "timestamp": timestamp,
                    "content": context
                }
                data['updates'] = data.get('updates', []) + [update]
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            logger.info(f"Updated JSON file with new content: {update}")
        else:
            logger.error(f"Unsupported format: {format}")
            return

        logger.info(f"Updated CoT file: {cot_file}")
    except IOError as e:
        logger.error(f"Error updating CoT file: {e}")
        logger.exception("Detailed error information:")

import subprocess
import anthropic

def _compress_cot(project_name, context_dir=None):
    logger.debug(f"Compressing CoT for project: {project_name}")
    context_dir = _get_context_dir(project_name, context_dir)
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
    cot_files = [f for f in os.listdir(context_dir) if f.startswith('cot_') and f.endswith('.md')]
    cot_content = ""
    for cot_file in cot_files:
        with open(os.path.join(context_dir, cot_file), 'r') as f:
            cot_content += f.read() + "\n\n"
    logger.debug(f"CoT content length: {len(cot_content)} characters")

    # 3. Send data to Anthropic for compression and commit message generation
    prompt = f"""Human: Please compress the following Chain of Thought (CoT) information. 
    Preserve all important information, especially the content of the CoT entries.
    You may reorganize and summarize the information, but do not remove any significant details.
    
    Current snapshot:
    {current_snapshot}
    
    CoT content:
    {cot_content}
    
    Provide the compressed result in Markdown format, which should include all CoT entries in a summarized form.
    
    After compressing the content, please generate a concise and informative commit message that summarizes the key updates or changes made in this compression.
    
    Format your response as follows:
    [COMPRESSED_CONTENT]
    (Your compressed content here)
    [/COMPRESSED_CONTENT]
    
    [COMMIT_MESSAGE]
    (Your commit message here)
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

def start_project(project_name):
    logger.info(f"[NO-OP] Executing start_project with project_name: {project_name}")
    pass

def git_push(project_name, commit_message):
    logger.info(f"[NO-OP] Executing git_push with project_name: {project_name}, commit_message: {commit_message}")
    pass

def run_tests(project_name):
    logger.info(f"[NO-OP] Executing run_tests with project_name: {project_name}")
    pass

def deploy(project_name):
    logger.info(f"[NO-OP] Executing deploy with project_name: {project_name}")
    pass


def generate_new_project_code(project_name, language):
    logger.info(f"[NO-OP] Executing generate_new_project_code with project_name: {project_name}, language: {language}")
    pass

def edit_project_code(project_name, file_path):
    logger.info(f"[NO-OP] Executing edit_project_code with project_name: {project_name}, file_path: {file_path}")
    pass

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
    parser = argparse.ArgumentParser(description="AI-assisted project management and development tool for Kubernetes-based applications")
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
    git_push_parser.add_argument("--project-name", required=True, help="Name of the project")
    git_push_parser.add_argument("--commit-message", required=True, help="Commit message")

    # run_tests
    run_tests_parser = subparsers.add_parser("run_tests", help="Analyze test results for the project")
    run_tests_parser.add_argument("--project-name", required=True, help="Name of the project")

    # deploy
    deploy_parser = subparsers.add_parser("deploy", help="Analyze deployment information for the project")
    deploy_parser.add_argument("--project-name", required=True, help="Name of the project")

    # generate_new_project_code
    generate_new_project_code_parser = subparsers.add_parser("generate_new_project_code", help="Generate initial code for a new project based on requirements")
    generate_new_project_code_parser.add_argument("--project-name", required=True, help="Name of the project")
    generate_new_project_code_parser.add_argument("--language", required=True, choices=["Python", "Go", "TypeScript"], help="Programming language to use")

    # edit_project_code
    edit_project_code_parser = subparsers.add_parser("edit_project_code", help="Edit existing project code with AI assistance")
    edit_project_code_parser.add_argument("--project-name", required=True, help="Name of the project")
    edit_project_code_parser.add_argument("--file-path", required=True, help="Path to the file to edit")

    # generate_tests_for_diff
    generate_tests_for_diff_parser = subparsers.add_parser("generate_tests_for_diff", help="Generate tests for a specific diff using Aider")
    generate_tests_for_diff_parser.add_argument("--project-name", required=True, help="Name of the project")
    generate_tests_for_diff_parser.add_argument("--diff-file", required=True, help="Path to the diff file")

    # review_and_refactor
    review_and_refactor_parser = subparsers.add_parser("review_and_refactor", help="Improve code quality while maintaining existing functionality")
    review_and_refactor_parser.add_argument("--project-name", required=True, help="Name of the project")

    # generate_performance_tests
    generate_performance_tests_parser = subparsers.add_parser("generate_performance_tests", help="Create tests to measure and ensure application performance")
    generate_performance_tests_parser.add_argument("--project-name", required=True, help="Name of the project")

    # upgrade_dependencies
    upgrade_dependencies_parser = subparsers.add_parser("upgrade_dependencies", help="Safely update project dependencies to their latest compatible versions")
    upgrade_dependencies_parser.add_argument("--project-name", required=True, help="Name of the project")

    # bootstrap_database_migrations
    bootstrap_database_migrations_parser = subparsers.add_parser("bootstrap_database_migrations", help="Set up and manage database schema changes for PostgreSQL")
    bootstrap_database_migrations_parser.add_argument("--project-name", required=True, help="Name of the project")

    # generate_docs_snapshot
    generate_docs_snapshot_parser = subparsers.add_parser("generate_docs_snapshot", help="Automatically create or update project documentation")
    generate_docs_snapshot_parser.add_argument("--project-name", required=True, help="Name of the project")

    # generate_or_update_local_deployment
    generate_or_update_local_deployment_parser = subparsers.add_parser("generate_or_update_local_deployment", help="Configure or update the local development environment")
    generate_or_update_local_deployment_parser.add_argument("--project-name", required=True, help="Name of the project")

    # generate_or_update_production_deployment
    generate_or_update_production_deployment_parser = subparsers.add_parser("generate_or_update_production_deployment", help="Prepare or update Kubernetes configurations for production deployment")
    generate_or_update_production_deployment_parser.add_argument("--project-name", required=True, help="Name of the project")

    args = parser.parse_args()

    if args.action == "create_prd":
        create_prd(args.project_context_file)
    elif args.action == "edit_prd":
        edit_prd(args.project_name, args.prd_file)
    elif args.action == "start_project":
        start_project(args.project_name)
    elif args.action == "git_push":
        git_push(args.project_name, args.commit_message)
    elif args.action == "run_tests":
        run_tests(args.project_name)
    elif args.action == "deploy":
        deploy(args.project_name)
    elif args.action == "generate_new_project_code":
        generate_new_project_code(args.project_name, args.language)
    elif args.action == "edit_project_code":
        edit_project_code(args.project_name, args.file_path)
    elif args.action == "generate_tests_for_diff":
        generate_tests_for_diff(args.project_name, args.diff_file)
    elif args.action == "review_and_refactor":
        review_and_refactor(args.project_name)
    elif args.action == "generate_performance_tests":
        generate_performance_tests(args.project_name)
    elif args.action == "upgrade_dependencies":
        upgrade_dependencies(args.project_name)
    elif args.action == "bootstrap_database_migrations":
        bootstrap_database_migrations(args.project_name)
    elif args.action == "generate_docs_snapshot":
        generate_docs_snapshot(args.project_name)
    elif args.action == "generate_or_update_local_deployment":
        generate_or_update_local_deployment(args.project_name)
    elif args.action == "generate_or_update_production_deployment":
        generate_or_update_production_deployment(args.project_name)

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

def _get_context_dir(project_name, context_dir=None):
    if context_dir is None:
        project_dir = os.getcwd()
        context_dir = os.path.join(project_dir, '.context')
    return context_dir

if __name__ == "__main__":
    main()
