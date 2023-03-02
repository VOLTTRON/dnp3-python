import argparse
import sys

from packaging.version import Version

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("current_version")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--major", action='store_true', help="Increment to minor release version.")
    group.add_argument("--minor", action='store_true', help="Increment to minor release version.")
    group.add_argument("--patch", action='store_true', help="Increment to patch release")
    group.add_argument("--prerelease", action='store_true', help="Increment a pre-release")
    
    opts = parser.parse_args()
    
    current_version = Version(opts.current_version)
    
    #print(current_version.__dict__)
    #sys.exit(0)
    if current_version.is_prerelease and opts.prerelease:
        new_version = f"{current_version.major}.{current_version.minor}.{current_version.micro}{current_version.pre[0]}{current_version.pre[1] + 1}"
    else:
        if opts.patch:       
            new_version = f"{current_version.major}.{current_version.minor}.{current_version.micro + 1}"
        elif opts.minor:
            new_version = f"{current_version.major}.{current_version.minor + 1}.0"
        elif opts.major:
            new_version = f"{current_version.major + 1}.0.0"
        elif opts.prerelease:
            new_version = f"{current_version.major}.{current_version.minor}.{current_version.micro + 1}b0"
        else:
            raise ValueError("Invalid option specified!")
    
    print(new_version)
    #current_version.pre = (current_version.pre[0], current_version.pre[1] + 1)
    #print(current_version.__dict__)