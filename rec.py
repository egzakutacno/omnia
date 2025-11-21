import os
import subprocess
import pexpect
import time

def read_container_info(file_path):
    container_info = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        container_name = None
        api_key = None
        for line in lines:
            if line.startswith("Container name:"):
                container_name = line.strip().split(": ")[1]
            elif line.startswith("API key:"):
                api_key = line.strip().split(": ")[1]
                if container_name and api_key:
                    container_info[container_name] = api_key
                    container_name = None
                    api_key = None
    return container_info

def create_containers(container_names):
    container_ids = []
    for name in container_names:
        cmd = (
            f'docker run --detach '
            f'--privileged '
            f'--cgroupns=host '
            f'--name {name} '
            f'-v /sys/fs/cgroup:/sys/fs/cgroup:rw '
            f'myria-custom-image:latest'
        )
        container_id = subprocess.check_output(cmd, shell=True).decode().strip()
        container_ids.append(container_id)
    return container_ids

def run_myria_node(api_key, container_name, command):
    process = pexpect.spawn(f'docker exec -it {container_name} myria-node {command}')
    try:
        process.expect_exact('Enter the node API Key:', timeout=10)
        process.sendline(api_key)
        process.wait()
        if process.exitstatus == 0:
            print(f"Successfully executed myria-node {command} with API key: {api_key} on Docker: {container_name}")
        else:
            print(f"Failed to execute myria-node {command} with API key: {api_key} on Docker: {container_name}")
    except pexpect.exceptions.TIMEOUT:
        print(f"Timeout occurred while waiting for API key prompt on Docker: {container_name}. Exiting...")

def manage_myria_nodes(container_info):
    for container_name, api_key in container_info.items():
        stop_command = '--stop'
        start_command = '--start'
        run_myria_node(api_key, container_name, stop_command)
        time.sleep(4)
        run_myria_node(api_key, container_name, start_command)

if __name__ == "__main__":
    imenik_path = '/root/omnia/imenik.txt'
    container_info = read_container_info(imenik_path)
    container_names = list(container_info.keys())
    print("Creating containers...")
    container_ids = create_containers(container_names)
    print("Managing Myria nodes...")
    manage_myria_nodes(container_info)
    print("All tasks completed.")
