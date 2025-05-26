import os
import sys
import subprocess
import shutil

def run(cmd, check=True, **kwargs):
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, **kwargs)

# Ensure running as root
if os.geteuid() != 0:
    print("This script must be run with sudo or as root.")
    sys.exit(1)

# 1. Apply sysctl setting
sysctl_conf = '/etc/sysctl.d/99-custom-settings.conf'
with open(sysctl_conf, 'w') as f:
    f.write('fs.inotify.max_user_instances=4096\n')
print(f"Written sysctl config to {sysctl_conf}")
run(['sysctl', '-p', sysctl_conf])

# 2. Install system dependencies
run(['apt-get', 'update'])
# git
if not shutil.which('git'):
    run(['apt-get', 'install', '-y', 'git'])
# docker (install or upgrade)
run(['apt-get', 'install', '-y', 'docker.io'])
# Start / enable Docker service
run(['systemctl', 'daemon-reload'])
run(['systemctl', 'enable', '--now', 'docker'])
# python3-pip
if not shutil.which('pip3'):
    run(['apt-get', 'install', '-y', 'python3-pip'])

# 3. Clone omnia repo if needed
dest_dir = os.path.join(os.getcwd(), 'omnia')
if not os.path.isdir(dest_dir):
    run(['git', 'clone', 'https://github.com/egzakutacno/omnia.git', dest_dir])
else:
    print(f"Repo already cloned at {dest_dir}")

# 4. Generate Dockerfile
dockerfile_path = os.path.join(os.getcwd(), 'Dockerfile')
with open(dockerfile_path, 'w') as f:
    f.write(
        'FROM eniocarboni/docker-ubuntu-systemd:focal\n'
        'RUN apt-get update && apt-get install -y wget curl\n'
        'RUN wget https://downloads-builds.myria.com/node/install.sh -O - | bash\n'
    )
print(f"Generated Dockerfile at {dockerfile_path}")

# 5. Build Docker image
run(['docker', 'build', '-t', 'myria-custom-image:latest', '.'])

# 6. Prompt for imenik entries
imenik_content = []
print("\nEnter container/API pairs. Leave container name blank to finish and resume the app.")
while True:
    name = input('Container name: ').strip()
    if not name:
        break
    api_key = input('API key: ').strip()
    imenik_content.append(f"Container name: {name}\nAPI key: {api_key}\n")

# Write imenik.txt both to repo and home directory
imenik_repo = os.path.join(dest_dir, 'imenik.txt')
imenik_home = os.path.expanduser('~/imenik.txt')
for path in (imenik_repo, imenik_home):
    with open(path, 'w') as f:
        f.write("\n".join(imenik_content) + "\n")
    print(f"Written imenik to {path}")

# 7. Install Python dependencies
run(['pip3', 'install', 'pexpect'])

# 8. Run rec.py
rec_script = os.path.join(dest_dir, 'rec.py')
if os.path.isfile(rec_script):
    run(['python3', rec_script])
else:
    print(f"Could not find rec.py at {rec_script}")
