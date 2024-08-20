import argparse
import os
import sys

from data_manager.browser_builder import (
    check_img_folder,
    rebuild_browser,
    refresh_browser,
)
from data_manager.utils import init_settings, read_data_path


def init_data_folder():
    data_path = read_data_path()
    if not os.path.isdir(data_path):
        os.makedirs(data_path)


def init_data_manager():
    data_dirname = input("Please input a path to create the data folder:")
    html_browser_dirname = input(
        "Please input a path to create the data browser folder:"
    )
    output = None
    initial_projects = []
    print(
        "Now, initialize a few project names. They will be the only project names allowed in the code, but this can always be changed in settings.ini. Press enter on an empty line to finish."
    )
    while output != "":
        output = input("Project name:")
        if output != "":
            initial_projects.append(output)

    init_settings(
        data_dirname=data_dirname,
        html_browser_dirname=html_browser_dirname,
        initial_projects=str(initial_projects),
    )

    init_data_folder()

    rebuild_browser()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c",
        "--check-img",
        action="store_true",
        help="Check if the image folder exists",
    )
    group.add_argument(
        "-d",
        "--delete-img",
        action="store_true",
        help="Delete all images in the image folder",
    )
    group.add_argument(
        "-r",
        "--rebuild-browser",
        action="store_true",
        help="Rebuild the browser data from scratch",
    )
    group.add_argument(
        "-f",
        "--refresh-browser",
        action="store_true",
        help="Remove all projects that have been deleted",
    )
    group.add_argument(
        "-i",
        "--init-man",
        action="store_true",
        help="Initialize data manager options",
    )

    args = parser.parse_args()

    if not len(sys.argv) > 1:
        args = parser.parse_args("--init-man")

    if args.check_img:
        print("Checking images")
        check_img_folder(False, False)
    elif args.delete_img:
        print("Removing images")
        check_img_folder(True, False)
    elif args.rebuild_browser:
        print("Rebuilding browser")
        rebuild_browser(False)
    elif args.refresh_browser:
        print("Refreshing browser")
        refresh_browser()
    elif args.init_man:

        init_data_manager()
