import subprocess
from pathlib import Path

env_file = Path(".env")
if not env_file.exists():
    print(".env file not found")
    exit(1)

with open(env_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue

    key, val = line.split("=", 1)
    key = key.strip()
    val = val.strip()

    if not val:
        continue

    print(f"Removing old {key} from Vercel Production...")
    subprocess.run(f'npx vercel env rm {key} production -y', shell=True)

    print(f"Adding updated {key} to Vercel Production...")
    p = subprocess.Popen(f'npx vercel env add {key} production', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=val.encode('utf-8'))
    print(stdout.decode('utf-8', errors='ignore'))
    print(stderr.decode('utf-8', errors='ignore'))

print("All environment variables updated on Vercel!")
