import argparse
import subprocess
import sys
from pathlib import Path
import shutil
from src.data_generator import DataGenerator
from src.data_injester import DataInjester
from dotenv import load_dotenv


load_dotenv("cli.env")

BASE_DIR = Path.cwd()
TEMPLATE_DIR = Path(__file__).parent / "templates"

# check if docker and docker compose is installed
def check_dependencies():
    check_command("docker")
    #check_command("docker-compose") if using V1

# check if particular command exist
def check_command(cmd: str):
    if shutil.which(cmd) is None:
        print(f"❌ '{cmd}' not found. Please install it first.")
        sys.exit(1)


# copy the files in the root directors 
def setup_files():
    compose_file = BASE_DIR / "docker-compose.yml"
    env_file = BASE_DIR / ".env"

    if not compose_file.exists():
        shutil.copy(TEMPLATE_DIR / "formbricks" /"docker-compose.yml", compose_file)
        print("✅ Created docker-compose.yml")

    if not env_file.exists():
        shutil.copy(TEMPLATE_DIR /"formbricks"/"formbricks.env", env_file)
        print("✅ Created .env")

# Start the docker compose
def docker_up():
    print("🚀 Starting Formbricks...")
    subprocess.run(
        ["sudo", "docker", "compose", "up", "-d"],
        check=True
    )



"""
    1. Check if the docker command exists (and docker-compose if using V1)
    2. copy the files to root
    3. start the docker
"""
def handle_formbricks_up(args):
    check_dependencies()
    setup_files()
    docker_up()

"""
    Stop the docker
"""
def handle_formbricks_down(args):
    subprocess.run(["sudo","docker", "compose", "down"], check=True)



"""
    Handler for generating surveys and answers via LLM
"""
def handle_formbricks_generate(args):

    obj = DataGenerator()
    obj.generate()

"""
    Handler for uploading generating surveys and answers to formbricks
"""
def handle_formbricks_seed(args):
    obj = DataInjester()
    obj.seed()

def main():
    parser = argparse.ArgumentParser(prog="main.py")
    
    # level 1: main commands
    commands = parser.add_subparsers(dest="command", required=True)

    formbricks_parser = commands.add_parser(
        "formbricks",
        help="Manage Formbricks services"
    )

    # level 2: subcommands under formbricks
    formbricks_subcommands = formbricks_parser.add_subparsers(
        dest="subcommand",
        required=True
    )
    ## --- formbricks up command ---
    up_parser = formbricks_subcommands.add_parser(
        "up",
        help="Start Formbricks using Docker"
    )
    up_parser.set_defaults(func=handle_formbricks_up)
    ## --- formbricks up command - END ---
    
    # --- formbricks down command ---
    down_parser = formbricks_subcommands.add_parser(
        "down", 
        help="Stop the Formbricks Docker images")
    down_parser.set_defaults(func=handle_formbricks_down)
    # --- formbricks down command - END ---

    # --  formbricks generate command --- 
    generate_parser = formbricks_subcommands.add_parser(
        "generate",
        help="Generate questions and answers using the survey description prompts json"
    )
    generate_parser.set_defaults(func=handle_formbricks_generate)
    # --  formbricks generate command - END ---

    # --  formbricks generate command --- 
    seed_parser = formbricks_subcommands.add_parser(
        "seed",
        help="Upload Survey and answers generated via LLM"
    )
    seed_parser.set_defaults(func=handle_formbricks_seed)
    # --  formbricks generate command - END ---
    

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    
    main()