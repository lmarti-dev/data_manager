from data_manager.utils import init_settings
from data_manager.browser_builder import rebuild_browser


def init_data_manager():
    data_dirname = input("Please input a path to create the data folder:")
    html_browser_dirname = input(
        "Please input a path to create the data browser folder:"
    )
    output = "!!!"
    initial_projects = []
    while output != "":
        print(
            "Now, initialize a few project names. They will be the only project names allowed in the code, but this can always be changed in settings.ini. Press enter on an empty line to finish."
        )
        output = input("Project name:")
        initial_projects.append(output)

    init_settings(
        data_dirname=data_dirname,
        html_browser_dirname=html_browser_dirname,
        initial_projects=initial_projects,
    )
    rebuild_browser()


if __name__ == "__main__":
    init_data_manager()
