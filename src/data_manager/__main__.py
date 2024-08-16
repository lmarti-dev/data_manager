from data_manager.utils import init_settings, read_data_path
from data_manager.browser_builder import rebuild_browser
import os


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
    init_data_manager()
