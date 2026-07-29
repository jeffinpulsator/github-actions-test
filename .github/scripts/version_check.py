import os
import subprocess
import tempfile
import importlib.util


def load_version(path):
    spec = importlib.util.spec_from_file_location("version", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VERSION_NAME, module.BUILD_NO


print("Reading version.py from PR...")

pr_version, pr_build = load_version("version.py")

print(f"PR Version : {pr_version}")
print(f"PR Build   : {pr_build}")

print()

print("Checking main branch...")

try:
    data = subprocess.check_output(
        [
            "git",
            "show",
            "origin/main:version.py",
        ],
        text=True,
    )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")

    with open(tmp.name, "w") as f:
        f.write(data)

    main_version, main_build = load_version(tmp.name)

    print(f"Main Version : {main_version}")
    print(f"Main Build   : {main_build}")

    if pr_build <= main_build:
        raise Exception("BUILD_NO must be greater than main")

    print()
    print("Version check PASSED")

except subprocess.CalledProcessError:
    print("version.py not found on main.")
    print("Treating this as the initial release.")
