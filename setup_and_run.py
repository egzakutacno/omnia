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

# Install git if missing
if not shutil.which('git'):
    run(['apt-get', 'install', '-y', 'git'])

# Install Docker
run(['apt-get', 'install', '-y', 'docker.io'])
run(['systemctl', 'daemon-reload'])
run(['systemctl', 'enable', '--now', 'docker'])

# Install pip if missing
if not shutil.which('pip3'):
    run(['apt-get', 'install', '-y', 'python3-pip'])

# 3. Clone omnia repo if needed
dest_dir = '/root/omnia'
if not os.path.isdir(dest_dir):
    run(['git', 'clone', 'https://github.com/egzakutacno/omnia.git', dest_dir])
else:
    print(f"Repo already cloned at {dest_dir}")

# 4. Generate Dockerfile in /root/omnia
dockerfile_path = os.path.join(dest_dir, 'Dockerfile')
with open(dockerfile_path, 'w') as f:
    f.write(
        'FROM eniocarboni/docker-ubuntu-systemd:focal\n'
        'RUN apt-get update && apt-get install -y wget curl\n'
        'RUN wget https://downloads-builds.myria.com/node/install.sh -O - | bash\n'
    )
print(f"Generated Dockerfile at {dockerfile_path}")

# 5. Build Docker image from /root/omnia
os.chdir(dest_dir)
run(['docker', 'build', '-t', 'myria-custom-image:latest', '.'])

# 6. Prompt for imenik entries
imenik_content = []
print("\nEnter container/API pairs. IMPORTANT! Leave container name blank to finish and resume the app. IMPORTANT!")
while True:
    name = input('Container name: ').strip()
    if not name:
        break
    api_key = input('API key: ').strip()
    imenik_content.append(f"Container name: {name}\nAPI key: {api_key}\n")

# Write imenik.txt to /root/omnia
imenik_path = os.path.join(dest_dir, 'imenik.txt')
with open(imenik_path, 'w') as f:
    f.write("\n".join(imenik_content) + "\n")
print(f"Written imenik to {imenik_path}")

# 7. Install Python dependency
run(['pip3', 'install', 'pexpect'])

# 8. Run rec.py from /root/omnia
rec_script = os.path.join(dest_dir, 'rec.py')
if os.path.isfile(rec_script):
    run(['python3', rec_script])
else:
    print(f"Could not find rec.py at {rec_script}")

# 9. Set restart policy for all running containers
try:
    run(['bash', '-c', 'docker ps --format "{{.Names}}" | xargs -r -I {} docker update --restart always {}'])
    print("Set all running containers to restart always.")
except subprocess.CalledProcessError as e:
    print(f"Failed to set restart policy for containers: {e}")
