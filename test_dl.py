import subprocess, sys
r = subprocess.run([sys.executable, "gofile_dl.py", "RE0cXfkA",
                    r"%TEMP%\sirhurt_gofile_test\SirHurt V5.zip"],
                   capture_output=True, text=True)
print(r.returncode)
print(r.stdout[-2000:])
print(r.stderr[-3000:])
