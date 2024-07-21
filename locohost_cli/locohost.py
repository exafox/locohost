import argparse
import logging
import json
import os
from datetime import datetime
from pydantic import BaseModel
from instructor import llm_validator
import anthropic


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = anthropic.Anthropic()
logger.debug(f"Anthropic client initialized: {client}")

@llm_validator(client=client, statement="Validate the SnapshotData model")
class SnapshotData(BaseModel):
    """
    A model to represent snapshot data.
    """
    file_text: str
    commit_message: str
    changelog: str

    @classmethod
    def validate_model(cls, client, statement):
        response = client.completions.create(
            model="claude-2",
            prompt=f"{statement}\n\n{cls.schema_json()}",
            max_tokens_to_sample=1000,
        )
        return response.completion

# ========================
# Helper Functions
# ========================

def _create_cot(project_name, context, format='md'):
    logger.debug(f"Creating CoT for project: {project_name}, format: {format}")
    project_dir = os.getcwd()
    context_dir = os.path.join(project_dir, project_name, '.context')
    logger.debug(f"Project directory: {project_dir}")
    logger.debug(f"Context directory: {context_dir}")

    if not os.path.exists(project_dir):
        logger.error(f"Project directory does not exist: {project_dir}")
        return

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
        logger.debug(f"CoT content: {content[:100]}...")  # Log first 100 characters of content
    except IOError as e:
        logger.error(f"Error creating CoT file: {e}")
        logger.exception("Detailed error information:")

def _update_cot(project_name, context, format='md'):
    logger.debug(f"Updating CoT for project: {project_name}, format: {format}")
    project_dir = os.getcwd()
    context_dir = os.path.join(project_dir, project_name, '.context')
    logger.debug(f"Project directory: {project_dir}")
    logger.debug(f"Context directory: {context_dir}")

    if not os.path.exists(context_dir):
        logger.error(f"Context directory does not exist: {context_dir}")
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
                f.write(f"\n\n## Update: {timestamp}\n\n")
                f.write(context)
            logger.debug(f"Updated MD file with new content")
        elif format == 'json':
            with open(cot_file, 'r+') as f:
                data = json.load(f)
                data['updates'] = data.get('updates', []) + [{
                    "timestamp": timestamp,
                    "content": context
                }]
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            logger.debug(f"Updated JSON file with new content")
        else:
            logger.error(f"Unsupported format: {format}")
            return

        logger.info(f"Updated CoT file: {cot_file}")
        logger.debug(f"Updated content: {context[:100]}...")  # Log first 100 characters of updated content
    except IOError as e:
        logger.error(f"Error updating CoT file: {e}")
        logger.exception("Detailed error information:")

import subprocess
import anthropic

def _compress_cot(project_name):
    logger.debug(f"Compressing CoT for project: {project_name}")
    project_dir = os.getcwd()
    context_dir = os.path.join(project_dir, project_name, '.context')
    snapshot_file = os.path.join(context_dir, 'snapshot.md')
    logger.debug(f"Project directory: {project_dir}")
    logger.debug(f"Context directory: {context_dir}")
    logger.debug(f"Snapshot file: {snapshot_file}")

    # 1. Read the current snapshot file
    current_snapshot = ""
    if os.path.exists(snapshot_file):
        with open(snapshot_file, 'r') as f:
            current_snapshot = f.read()
        logger.debug(f"Current snapshot length: {len(current_snapshot)} characters")
    else:
        logger.debug("No existing snapshot file found")

    # 2. Run git diff and parse out changes in .context directory
    git_diff_command = f"git diff -- {context_dir}"
    logger.debug(f"Running git diff command: {git_diff_command}")
    try:
        git_diff_output = subprocess.check_output(git_diff_command, shell=True, text=True)
        logger.debug(f"Git diff output length: {len(git_diff_output)} characters")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git diff: {e}")
        logger.exception("Detailed error information:")
        return

    # 3. Send data to Anthropic for compression and commit message generation
    client = anthropic.Anthropic()
    prompt = f"""
    Please compress the following Chain of Thought (CoT) information LOSSLESSLY. 
    Remove old or outdated information, but take great care not to lose any important signals.
    
    Current snapshot:
    {current_snapshot}
    
    Git diff of changes:
    {git_diff_output}
    
    Provide the compressed result in Markdown format, which may include JSON when appropriate.
    
    After compressing the content, please generate a concise and informative commit message that summarizes the key updates or changes made in this compression.
    
    Return your response in the following format:
    
    COMPRESSED_CONTENT:
    [Your compressed content here]
    
    COMMIT_MESSAGE:
    [Your generated commit message here]
    """

    logger.debug("Sending request to Anthropic API")
    try:
        response = client.completions.create(
            model="claude-2",
            prompt=prompt,
            max_tokens_to_sample=100000,
        )
        logger.debug(f"Received response from Anthropic API, length: {len(response.completion)} characters")
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        logger.exception("Detailed error information:")
        return

    # Parse the response
    completion = response.completion
    parts = completion.split("COMMIT_MESSAGE:")
    compressed_content = parts[0].split("COMPRESSED_CONTENT:")[1].strip()
    commit_message = parts[1].strip() if len(parts) > 1 else ""
    logger.debug(f"Compressed content length: {len(compressed_content)} characters")
    logger.debug(f"Commit message: {commit_message}")

    # 4. Write the response to the new snapshot file
    try:
        with open(snapshot_file, 'w') as f:
            f.write(compressed_content)
        logger.debug(f"Written compressed content to {snapshot_file}")
    except IOError as e:
        logger.error(f"Error writing to snapshot file: {e}")
        logger.exception("Detailed error information:")
        return

    # 5. Commit the changes to git
    git_add_command = f"git add {snapshot_file}"
    git_commit_command = f"git commit -m '{commit_message}'"
    
    logger.debug(f"Running git add command: {git_add_command}")
    try:
        subprocess.run(git_add_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git add: {e}")
        logger.exception("Detailed error information:")
        return

    logger.debug(f"Running git commit command: {git_commit_command}")
    try:
        subprocess.run(git_commit_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running git commit: {e}")
        logger.exception("Detailed error information:")
        return

    logger.info(f"CoT snapshot compressed and updated for project: {project_name}")
    logger.info(f"Commit message: {commit_message}")

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

if __name__ == "__main__":
    main()
