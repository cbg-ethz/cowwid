#!/usr/bin/env python3

import argparse
import glob
import os
import subprocess
import sys
from typing import List


POLYBOX_TARGETS = {
    "influenza": {
        "polybox_url": "https://bs-pangolin@polybox.ethz.ch/remote.php/dav/files/bs-pangolin/Shared/BAG-INFLUENZA/",
        "target_glob": "/cluster/project/pangolin/processes/influenza/*/working/mutation_frequencies/",
    },
    "rsv": {
        "polybox_url": "https://bs-pangolin@polybox.ethz.ch/remote.php/dav/files/bs-pangolin/Shared/BAG-RSV/",
        "target_glob": "/cluster/project/pangolin/processes/rsv/*/working/MutationFrequencies/",
    },
}


def run_cmd(cmd: List[str]) -> None:
    """Run command and stream stdout/stderr to terminal."""
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def find_latest_files(target_dir_glob: str) -> List[str]:
    """
    For each MutationFrequencies directory, select the lexicographically last file
    (like notebook version using sorted(listdir)[-1]).
    """
    dirs = glob.glob(target_dir_glob)
    dirs.sort()

    files_to_upload = []
    for d in dirs:
        if not os.path.isdir(d):
            continue

        file_list = os.listdir(d)
        file_list = [f for f in file_list if os.path.isfile(os.path.join(d, f))]
        file_list.sort()

        if not file_list:
            print(f"[WARN] No files found in {d}", file=sys.stderr)
            continue

        latest = file_list[-1]
        path = os.path.join(d, latest)
        files_to_upload.append(path)

    return files_to_upload


def print_file_details(path: str) -> None:
    print("Listing file details:")
    run_cmd(["ls", "-l", path])


def upload_file(path: str, polybox_url: str) -> None:
    print("Uploading file:")
    run_cmd(["curl", "--netrc", "--upload-file", path, polybox_url])


def process_target(target_name: str, mode: str) -> None:
    cfg = POLYBOX_TARGETS[target_name]
    polybox_url = cfg["polybox_url"]
    target_glob = cfg["target_glob"]

    print(f"\n=== Target: {target_name.upper()} ===")
    print(f"Searching directories: {target_glob}")
    files_to_upload = find_latest_files(target_glob)

    print("\nFiles selected for upload:")
    for f in files_to_upload:
        print(f"  {f}")

    if not files_to_upload:
        print("[INFO] No files to upload.")
        return

    for f in files_to_upload:
        print()
        print_file_details(f)

        if mode == "dry-run":
            print("[DRY-RUN] Skipping upload.")
        elif mode == "upload":
            upload_file(f, polybox_url)
        else:
            raise ValueError(f"Unknown mode: {mode}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload latest MutationFrequencies files to BAG Polybox targets."
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "upload"],
        required=True,
        help="dry-run prints what would be uploaded; upload performs the upload",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=list(POLYBOX_TARGETS.keys()) + ["all"],
        default=["all"],
        help="Which targets to process (default: all)",
    )

    args = parser.parse_args()

    targets = args.targets
    if "all" in targets:
        targets = list(POLYBOX_TARGETS.keys())

    for t in targets:
        process_target(t, args.mode)


if __name__ == "__main__":
    main()
