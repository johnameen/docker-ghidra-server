#!/usr/bin/env python3

#####
# multiple servers on the same machine, multiple docker containers
# - Multiple ports to connect through


import argparse
import json
import os
import socket
import subprocess
import sys

from pprint import pprint
from urllib import request
from urllib.error import HTTPError

RELEASES_PATH       = "releases.json"
GHIDRA_CONFIG_PATH  = ".ghidra_config"
REPO_TAG            = "NationalSecurityAgency/ghidra"
DEFAULT_CONFIG = {
    "users": ["admin"],
    "local": False,
    "ppath": "./projects"
}

def get_choice(exit_prog=True, exit_dialogue=""):
    choice = input("(y/n): ").strip()
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
    
    docker_install = subprocess.Popen(["pip3", "install", "docker"], stdout=subprocess.PIPE)
    docker_install.communicate()

    if docker_install.returncode != 0:
        print("Failed to install docker module")
        exit(-1)

    print("docker module installed successfully")
    import docker

class Releases():
    def __init__(self):
        self._releases = {}
        self.latest_release = 0

        self.get_releases()

    def get_releases(self):
        if not self._releases:
            self.load_releases()
        
        return self._releases

    def load_releases(self, releases_path=RELEASES_PATH):
        if not file_check(releases_path):
            # TODO: Backup to git zip pull? Seems like potentially bad idea
            print("Could not find releases file: {releases_path}. Bailing out...")
            exit(-1)
        
        releases = {}
        with open(releases_path, "r") as releases_f:
            try:
                releases = json.load(releases_f)
            except json.decoder.JSONDecodeError as e:
                print(f"Couldn't json decode releases file: {releases_path}")
                exit(-1)
        
        self._releases = releases

        return self._releases

    def get_latest_release(self):
        if not self._releases:
            self.load_releases()
        
        # Find latest version in releases.json
        rel_split = lambda s: tuple(s.split('.'))
        rels = [rel_split(ver) for ver in self._releases["release-hashes"].keys()]

        latest_rel = max(rels)

        return latest_rel, self._releases["release-hashes"][latest_rel]
    
    # Returns True if version passed in is greater than local version saved
    def cmp_release_add(self, latest_release, latest_release_hash):
        # TODO: Check for valid release no. Check for valid release hash

        if (latest_release := tuple(latest_release.split('.'))) > self.get_latest_release():
            self._releases["release-hashes"][latest_release] = latest_release_hash
        
            with open("releases.json", "w") as releases_f:
                json.dump(self._releases, releases_f)

            return True
        
        return False

class GitHandler():
    GIT_API_LATEST_URL  = f"https://api.github.com/repos/{REPO_TAG}/releases/latest"
    GIT_API_TAG_URL     = f"https://api.github.com/repos/{REPO_TAG}/git/ref/tags/%s"
    GIT_API_TAG_SHA_URL = f"https://api.github.com/repos/{REPO_TAG}/git/tags/%s"

    def __init__(self):
        self.ghidra_args = {}

    def req_json_url(url):
        req_latest = request.Request(url, method="GET")

        try:
            resp = request.urlopen(req_latest)
        except HTTPError as e:
            print(f"Could not open url {url}")
            return None

        return resp.read()

    # TODO: All todos in this thing
    # - Make sure that json isn't trying to decode None types being returned by req_json_url above
    # - If anything breaks, just fallback on releases.json
    # - Check node_id's and make sure things are kosher
    def get_ghidra_release(self):
        releases = Releases()

        download_url, tag_sha, tag_name, zip_file_name = "", "", "", ""
        git_latest_json = GitHandler.req_json_url(GitHandler.GIT_API_LATEST_URL)

        ## Testing ##
        # with open("tests/test.json", "r") as test_f:
        #     test_json = test_f.read()
        #     git_latest_json = test_json

        try:
            release_resp = json.loads(git_latest_json)
        except json.decoder.JSONDecodeError as e:   # TODO: Handle failed json decode
            print(f"Todo: Handle this properly: {e}")

        if "tag_name" in release_resp:
            tag_name = release_resp["tag_name"]
        else: # TODO: Handle this case
            print("'tag_name' not in release_resp json")
            exit(-1)

        version_number = tag_name.split("_")[1] # TODO: Add checks for this

        # If there is a newer version, go ahead and build this container
        # if there isn't, check to see if we already have a local image built
        if not releases.cmp_release_add(version_number):
            if check_local_ghidra(version_number):
                return

        if "assets" in release_resp:
            if isinstance(release_resp["assets"], list) and len(release_resp["assets"]) > 0:
                release_resp_first_dwnld = release_resp["assets"][0]

                download_url = release_resp_first_dwnld["browser_download_url"]
                zip_file_name = release_resp_first_dwnld["name"]

        # TODO: Uncomment out
        git_tag_json = GitHandler.req_json_url(GitHandler.GIT_API_TAG_URL % tag_name)
        
        ## Testing ##
        with open("tests/test_tag.json", "r") as test_tag_f:
            git_tag_json = test_tag_f.read()

        try:
            # tag_resp = json.loads(resp.read())
            tag_resp = json.loads(git_tag_json)
        except json.decoder.JSONDecodeError as e:
            print(f"Errored decoding json: {e}") # TODO: Handle error properly
            exit()

        if 'object' in tag_resp:
            tag_obj = tag_resp['object']
            if 'sha' in tag_obj:
                tag_sha = tag_obj['sha']
            if 'type' in tag_obj:
                tag_type = tag_obj['type']
            
        if tag_type != "commit":
            git_tagsha_json = GitHandler.req_json_url(GitHandler.GIT_API_TAG_SHA_URL % tag_sha)

            try:
                tagsha_resp = json.loads(git_tagsha_json)
            except json.decoder.JSONDecodeError as e:
                print(f"Errored decoding json: {e}") # TODO: Handle error properly
                exit()

            if 'object' in tagsha_resp:
                if 'sha' in tagsha_resp['object']: tag_sha = tagsha_resp['object']['sha']

            with open("tests/test_tagsha.json", "w") as test_tagsha_f:
                json.dump(tagsha_resp, test_tagsha_f)

        if not tag_sha or not download_url or not zip_file_name or not version_number:
            print("Couldn't find most recent sha from git repo. Using default from file list")
            # TODO: Add in lookup for most recent from saved releases.json
            exit(0) # Exit for now

        self.ghidra_args["tag_name"]       = tag_name
        self.ghidra_args["download_url"]   = download_url
        self.ghidra_args["zip_file_name"]  = zip_file_name
        self.ghidra_args["version_number"] = version_number

        return self.ghidra_args

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

    warn_conf_s = "'{conf_key}' config not found in {config_path}. Defaulting to {conf_key}: {conf_default}"
    for conf_key, conf_default in DEFAULT_CONFIG.items():
        if conf_key not in config:
            print(warn_conf_s.format(conf_key, GHIDRA_CONFIG_PATH, conf_default=conf_default))
            config[conf_key] = conf_default

    return config

def start_docker_daemon():
    s = subprocess.Popen(["systemctl", "start", "docker"], stdout=subprocess.PIPE)
    ret_code = s.wait()

    return ret_code == 0

def get_ip(private=True):
    if private:
        ip = (socket.gethostbyname(socket.gethostname()))
    else:
        try:
            ip = (socket.gethostbyname("www.google.com"))
        except socket.error as e:
            print(f"Was not able to get global IP. Got {e}. Bailing out...")
            exit(-1)
    
    return ip

def build_env_file(ghidra_args):
    # Build .env file
    with open(".env", "w") as env_f:
        env_f.writelines(f"{arg_key}={arg_value}\n" for arg_key, arg_value in ghidra_args.items())
        env_f.write("BUILD_TYPE=prebuild\n")

# TODO: Add build env variables for docker-compose file
def build_ghidra_image():
    subprocess.Popen(["docker-compose", "build", "ghidra-server"])

def main(config):
    client = None
    gh = GitHandler()

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

    gh.get_ghidra_release()

    current_ghidra_release = f"ghidra:ghidra{gh.ghidra_args['version_number']}"

    # Check to see if ghidra docker container is built
    def check_ghidra_image():
        nonlocal current_ghidra_release, client
        image_built = False
        for image in client.images.list():
            if current_ghidra_release in image.tags:
                image_built = True
                break
        return image_built

    build_env_file(gh.ghidra_args)
    if not check_ghidra_image():
        build_ghidra_image()
        if not check_ghidra_image():
            print("Could not build image")  # TODO: Fix this to be useful
            exit()

    ip = get_ip(config["local"])



    print(ip)
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
                        help="Set server to only be accessible locally (private IP)"
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
        
        if not file_check(GHIDRA_CONFIG_PATH): # TODO: REMOVE NOT
            print("Config file exists, update with current config?", end="")
            if get_choice(False):
                with open(GHIDRA_CONFIG_PATH, "w") as config_f:
                    json.dump(config, config_f)
        else:
            with open(GHIDRA_CONFIG_PATH, "w") as config_f:
                json.dump(config, config_f)

    main(config)