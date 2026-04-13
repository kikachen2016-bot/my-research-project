import sys
import os
import subprocess

# Python handles Unicode paths correctly via __file__
script_dir = os.path.dirname(os.path.abspath(__file__))
cfg_path = os.path.join(script_dir, '.venv', 'pyvenv.cfg')

if not os.path.exists(cfg_path):
    print('ERROR: .venv not found. Run install.bat first.')
    input('Press Enter to exit...')
    sys.exit(1)

# Read pyvenv.cfg to find the real venv path
venv_path = None
with open(cfg_path, encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('command'):
            # "command = C:\...\python.exe -m venv G:\...\backend\.venv"
            cmd_line = line.split('=', 1)[1].strip()
            if ' -m venv ' in cmd_line:
                venv_path = cmd_line.split(' -m venv ')[1].strip()
            break

if not venv_path or not os.path.isdir(venv_path):
    venv_path = os.path.join(script_dir, '.venv')

python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')

if not os.path.exists(python_exe):
    print(f'ERROR: python.exe not found at:\n  {python_exe}')
    input('Press Enter to exit...')
    sys.exit(1)

# Kill any process already using port 8000
subprocess.run(
    'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :8000\') do taskkill /PID %a /F /T',
    shell=True, capture_output=True
)

print(f'Starting backend at http://127.0.0.1:8000 ...')
print(f'Python: {python_exe}')

result = subprocess.run(
    [python_exe, '-m', 'uvicorn', 'app.main:app', '--reload', '--host', '127.0.0.1', '--port', '8000'],
    cwd=script_dir
)
sys.exit(result.returncode)
