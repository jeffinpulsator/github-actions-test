import os
import subprocess
import tempfile
import importlib.util
import re


def load_version(path):
    spec = importlib.util.spec_from_file_location("version", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VERSION_NAME, module.BUILD_NO

def version_tuple(version):
    return tuple(map(int, version.split(".")))


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
        raise Exception(
            f"BUILD_NO must be greater than main.\n"
            f"Main BUILD_NO : {main_build}\n"
            f"PR BUILD_NO   : {pr_build}"
        )
    
    if pr_version == main_version:
        raise Exception(
            f"VERSION_NAME must be different from main.\n"
            f"Main VERSION_NAME : {main_version}\n"
            f"PR VERSION_NAME   : {pr_version}"
        )

    if version_tuple(pr_version) <= version_tuple(main_version):
        raise Exception(
            f"PR version ({pr_version}) must be greater than main version ({main_version})"
        )

    tag_name = f"v{pr_version}"
    
    print()
    print(f"Checking Git tag: {tag_name}")
    
    result = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    if result.returncode == 0:
        raise Exception(
            f"Git tag already exists: {tag_name}"
        )
    
    print(f"Tag {tag_name} does not exist.")

    print()
    print("Updating sdkconfig...")
    
    sdkconfig_path = "sdkconfig"
    
    if not os.path.exists(sdkconfig_path):
        raise Exception("sdkconfig file not found")
    
    with open(sdkconfig_path, "r") as f:
        sdkconfig = f.read()
    
    sdkconfig = re.sub(
        r'^CONFIG_BUILD_NUMBER=.*$',
        f'CONFIG_BUILD_NUMBER={pr_build}',
        sdkconfig,
        flags=re.MULTILINE,
    )
    
    with open(sdkconfig_path, "w") as f:
        f.write(sdkconfig)
    
    print("sdkconfig updated.")

    print()
    print("Version check PASSED")

except subprocess.CalledProcessError:
    print("version.py not found on main.")
    print("Treating this as the initial release.")
