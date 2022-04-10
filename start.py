#!/usr/bin/env python3

import argparse
import json
import os
import sys

GHIDRA_CONFIG_PATH=".ghidra_config"

def get_choice(exit_prog=True, exit_dialogue=""):
    choice = input("(y/n): ")
    choice = choice.strip()
    if not choice:
        if exit_prog:
            if exit_dialogue:
                print(exit_dialogue)
            exit(1)
        else:
            return False
    if choice[0].lower() != "y":
        if exit_prog:
            if exit_dialogue:
                print(exit_dialogue)
            exit(1)
        else:
            return False
    
    return True

try:
    import docker
except ModuleNotFoundError:
    print("Was unable to load the docker module. Would you like to install it?", end="")
    get_choice()
    
    import subprocess
    docker_install = subprocess.Popen(["pip3", "install", "docker"], stdout=subprocess.PIPE)
    docker_install.communicate()

    if docker_install.returncode != 0:
        print("Failed to install docker module")
        exit(-1)

    print("docker module installed successfully")
    import docker

def file_check(path):
    if os.path.exists(path) and not os.path.isdir(path):
        return True
    return False

def check_ppath_folder(ppath) -> None:
    if os.path.exists(ppath):
        if not os.path.isdir(ppath):
            print(f"Project path: {ppath} is a file, not a directory. Bailing out...")
            exit(-1)
    else:
        try:
            os.mkdir(ppath)
        # TODO: Except specific exceptions.
        except Exception as e:
            print(f"Could not create project directory: {ppath}. Got: {e}. Bailing out...")
            exit(-1)

def parse_config_file():
    config = {}

    if not file_check(GHIDRA_CONFIG_PATH):
        with open(GHIDRA_CONFIG_PATH, "w") as config_f:
            config = json.load(config_f)
    
    if not isinstance(config, dict) or not config:
        config = {"users": ["admin"]}

    if "users" not in config:
        print("'users' config not found in .ghidra_configs. Defaulting to users: ['admin']")
        config["users"] = ["admin"]
    if "local" not in config:
        print("'local' config not found in .ghidra_configs. Defaulting to global config")
        config["local"] = False
    if "ppath" not in config:
        print("'ppath' config not found in .ghidra_configs. Defaulting to path: ./projects")
        config["ppath"] = "./projects"

    return config
def start_docker_daemon():
    s = subprocess.Popen(["systemctl", "start", "docker"], stdout=subprocess.PIPE)
    ret_code = s.wait()

    return ret_code == 0

def main(config):
    client = None
    try:
        client = docker.from_env()
    # TODO: Specify exception for when daemon is not running
    except Exception as e:
        print(f"Docker daemon not running. Got: {e}")
        print("Would you like to try and start the docker daemon?")

        exit(-1)

    # TODO: Figure out if this is even possible. What the issue may be
    if not client:
        print("Something is wrong with docker")
        exit(-1)

    for image in client.images.list():
        print(image)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0] if len(sys.argv)>0 else "start.py", 
                                     description="Helps start a ghidra server in a docker container")

    parser.add_argument("-u", "--users",
                        action="extend",
                        nargs="+",
                        default=[],
                        help="Users to add to the server. Uses .ghidra_users file automatically"
    )
    parser.add_argument("-l", "--local",
                        action="store_true",
                        default=False,
                        help="Set server to only be accessible locally"
    )
    parser.add_argument("-c", "--config",
                        action="store_true",
                        default=False,
                        help="Use .ghidra_config file"
    )
    parser.add_argument("-p", "--ppath",
                        type=str,
                        default="./projects",
                        help="Path where projects are stored"
    )

    args = parser.parse_args()

    config = {}

    if args.config:
        config = parse_config_file()
    else:
        config["users"] = ["admin"] if not args.users else args.users
        config["ppath"] = "./projects" if not args.ppath else args.ppath
        config["local"] = args.local
        if file_check(GHIDRA_CONFIG_PATH):
            print("Config file exists, update with current config?", end="")
            if get_choice():
                with open(GHIDRA_CONFIG_PATH, "w") as config_f:
                    json.dump(config, config_f)
        else:
            with open(GHIDRA_CONFIG_PATH, "w") as config_f:
                json.dump(config, config_f)
    
    main(config)