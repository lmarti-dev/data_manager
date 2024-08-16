import io
import json
import os
import re
import uuid
from datetime import datetime

import data_manager.constants as constants

# will change this to PyMuPDF, though they are keeping the legacy import alive
import fitz
from data_manager.json_extender import (
    ExtendedJSONDecoder,
    ExtendedJSONEncoder,
)

# bs4 is for reading documents, not creating them.
from lxml.html import HtmlElement, builder, fromstring, tostring
from data_manager.utils import (
    read_data_path,
    read_browser_path,
    get_project_list,
    delete_experiments_without_data,
    get_all_experiment_paths,
    setup_browser_folder,
)

HOME = os.path.dirname(__file__)

FRAGMENT_PATH = os.path.join(HOME, "./browser/fragments")
HTML_FILENAME = "index.html"
IMG_DIR = "img/"

SCROLL_LIST_ID = "exp-scroll-list"
SCROLL_TITLE_ID = "scroller-title-container"
DISPLAY_DIV_ID = "exp-display-div"
DISPLAY_ID_PREFIX = "display_item"
SCROLL_ID_PREFIX = "scroll_item"
PROJECT_SELECT_DROPDOWN_ID = "project-select-dropdown"
PROJECT_SELECT_ACTIVE_TEXT_ID = "project-select-active-text"


def get_badge(text: str, badge_type: str) -> HtmlElement:
    return builder.SPAN(text, **{"class": f"badge text-bg-{badge_type}"})


def get_var_dump(logging_dir: str):
    files = os.listdir(logging_dir)
    var_dumps = [x for x in files if x.startswith("var_dump")]
    if len(var_dumps) >= 1:
        jobj = []
        for var_dump in var_dumps:
            jobj.append(
                json.loads(
                    io.open(
                        os.path.join(logging_dir, var_dump), "r", encoding="utf8"
                    ).read(),
                    cls=ExtendedJSONDecoder,
                )
            )
        return jobj
    return []


def get_project_id(project):
    return "project-" + re.sub(r"\W", "-", project)


def get_project_class(project):
    return "part-of-" + get_project_id(project=project)


def get_project_dropdown():
    projects: list = get_project_list()
    all_projects = ["all projects"] + projects + [constants.OTHER_PROJECT]
    dropdown = get_fragment("dropdown")
    dropdown.classes.add("mx-3")

    dropdown.set("id", PROJECT_SELECT_DROPDOWN_ID)
    dropdown_active_text: HtmlElement = dropdown.xpath(
        "//button[contains(@class,'dropdown-toggle')]"
    )[0]
    dropdown_active_text.set("id", PROJECT_SELECT_ACTIVE_TEXT_ID)
    dropdown_active_text.text = all_projects[0]
    dropdown_menu: HtmlElement = dropdown.xpath("//div[@class='dropdown-menu']")[0]
    for project in all_projects:
        dropdown_menu.append(
            fromstring(
                f"<button class='dropdown-item' href='#' id='{get_project_id(project)}'>{project}</button>"
            )
        )
    return dropdown


def get_manifest(logging_dir: str):
    files = os.listdir(logging_dir)
    manifest = [x for x in files if x.startswith(constants.MANIFEST_FILENAME)]
    if len(manifest):
        jobj = json.loads(
            io.open(
                os.path.join(logging_dir, manifest[0]), "r", encoding="utf8"
            ).read(),
            cls=ExtendedJSONDecoder,
        )
        return jobj
    return {}


def pretty_manifest(manifest: dict, which: str = "list"):
    if which == "list":
        manifest_list = []
        for k, v in manifest.items():
            if "timestamp" in k:
                pass
            elif "main_file" in k:
                link = f"file://{normal_path(v)}"
                code = builder.A(builder.CODE(os.path.basename(v)), **{"href": link})
                manifest_list.append(code)
            elif "note" in k:
                manifest_list.append(v)
        return manifest_list
    elif which == "dict":
        manifest_dict = {}
        for k, v in manifest.items():
            if "timestamp" in k:
                pass
            elif "main_file" in k:
                link = f"file://{normal_path(v)}"
                code = builder.A(builder.CODE(os.path.basename(v)), **{"href": link})
                manifest_dict["main file"] = code
            elif "note" in k:
                manifest_dict["notes"] = v
        return manifest_dict


def get_data(data_dir: str):
    files = os.listdir(data_dir)
    fpath = os.path.join(data_dir, files[0])
    print(f"loading {fpath}")
    jobj = json.loads(
        io.open(fpath, "r", encoding="utf8").read(),
        cls=ExtendedJSONDecoder,
    )
    return jobj


def get_calendar():
    data_path = read_data_path()
    return data_path, os.listdir(data_path)


def normal_path(path):
    return re.sub(r"\\", "/", os.path.abspath(path))


def convert_pdf(pdf_path):
    img_uuid = f"img_{uuid.uuid4()}"
    img_fpath = os.path.join(
        os.path.join(read_browser_path(), IMG_DIR), f"{img_uuid}.jpeg"
    )
    if not os.path.isfile(img_fpath):
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pixmap = page.get_pixmap(dpi=300)
        pixmap.save(img_fpath)
    return img_fpath


def get_img_from_pdf(dirname, filename, height: str, width: str):
    pdf_fpath = os.path.join(dirname, filename)
    img_fpath = convert_pdf(pdf_fpath)
    link = builder.A()
    link.set("href", f"file://{normal_path(pdf_fpath)}")
    img = builder.IMG(
        **{
            "src": f"file://{normal_path(img_fpath)}",
            "width": width,
            "height": height,
            "type": "image",
            "loading": "lazy",
        },
    )
    link.append(img)
    return link


def get_id_from_title_date(title: str, date: str, prefix: str = None):
    if prefix is not None:
        return "_".join([prefix, title, date])
    else:
        return "_".join([title, date])


def get_id_from_browser_data(browser_data: dict, prefix: str):
    if prefix is not None:
        return "_".join([prefix, browser_data["uuid"]])
    else:
        return browser_data["uuid"]


def create_bs_scroll_item(
    title: str, body: str, date: str, figs, browser_data: dict = None
):

    main_elem: HtmlElement = builder.BUTTON(
        **{
            "id": get_id_from_browser_data(browser_data, SCROLL_ID_PREFIX),
            "data-bs-toggle": "collapse",
            "data-bs-target": f"#{get_id_from_browser_data(browser_data,DISPLAY_ID_PREFIX)}",
            "class": "list-group-item list-group-item-action py-3 lh-sm",
            "aria-controls": get_id_from_browser_data(browser_data, SCROLL_ID_PREFIX),
        }
    )

    if browser_data is not None:
        project = browser_data["project"]
        project_class = get_project_class(project)
        main_elem.classes.add(project_class)

    # a_elem.a.set("aria-current","true")

    div_elem = builder.DIV()
    div_elem.set("class", "d-flex w-100 align-items-center justify-content-between")

    strong_elem = builder.STRONG()
    strong_elem.set("class", "mb-1 text-truncate")
    strong_elem.text = title

    div_elem.append(strong_elem)

    small_elem = builder.SMALL()
    small_elem.text = date.replace("_", "/")
    div_elem.append(small_elem)

    main_elem.append(div_elem)

    if not isinstance(body, list):
        body = [body]
    for item in body:
        content_elem = builder.DIV()
        content_elem.set("class", "col-10 mb-1 small")
        if isinstance(item, HtmlElement):
            content_elem.append(item)
        elif isinstance(item, str):
            content_elem.text = item
        main_elem.append(content_elem)

    if figs is not None:
        main_elem.append(figs)
    return main_elem


def get_fragment(filename: str) -> HtmlElement:
    raw_html = io.open(
        os.path.join(FRAGMENT_PATH, f"{filename}.html"), "r", encoding="utf8"
    ).read()
    return fromstring(raw_html)


def create_scroller():
    return get_fragment("scroller")


def get_svg_logos():
    return get_fragment("logos")


def get_b_divider(which):
    if which == "h":
        return get_fragment("b_divider_horizontal")
    elif which == "v":
        return get_fragment("b_divider_vertical")


def get_change_theme():
    return get_fragment("change_theme")


def build_n_figs_div(dir, n_img: int = 3, height: str = "auto", width: str = "300px"):
    div_elem = builder.DIV()
    div_elem.set("class", "col-10 mb-1 small")
    curr_img = 0

    for dirpath, directories, files in os.walk(dir):
        for f in files:
            if f.endswith(".pdf"):
                div_elem.append(
                    get_img_from_pdf(dirpath, f, height=height, width=width)
                )
                curr_img += 1
            if curr_img > n_img - 1:
                return div_elem
    return div_elem


def dict_to_description_list(d: dict):
    dl = builder.DL(**{"class": "row"})
    for k, v in d.items():
        dt = builder.DT(str(k), **{"class": "col"})
        dl.append(dt)
        dd = builder.DD(str(v), **{"class": "col"})
        dl.append(dd)
    return dl


def process_item(parent, child):
    if isinstance(child, dict):
        if len(child.keys()) > 1:
            parent.append(dict_to_table(child, add_class="table-striped"))
        else:
            parent.append(dict_to_description_list(child))
    elif isinstance(child, str):
        parent.text = child
    elif isinstance(child, HtmlElement):
        parent.append(child)
    else:
        parent.append(builder.DIV(str(child)))
    return parent


def dict_to_table(d: dict, t: str = None, add_class: str = None):
    table = builder.TABLE(**{"class": f"table {add_class}"})
    tbody = builder.TBODY()
    if t:
        tr = builder.TR()
        th = builder.TH(t)
        tr.append(th)
        # EMPTY ONE FOR AESTHETICS
        tr.append(builder.TH())
        tbody.append(tr)
    for k, v in d.items():
        if not k.startswith("__"):
            tr = builder.TR()
            tdk = builder.TD()
            tdk = process_item(tdk, k)
            tdv = builder.TD()
            tdv = process_item(tdv, v)
            tr.append(tdk)
            tr.append(tdv)
            tbody.append(tr)
    table.append(tbody)
    return table


def populate_run(experiment_path, run):
    run_path = os.path.join(experiment_path, run)

    run_div = builder.DIV(builder.H2(run))

    logging_dir = os.path.join(run_path, "logging")
    fig_dir = os.path.join(run_path, "figures")
    data_dir = os.path.join(run_path, "data")
    if os.path.isdir(fig_dir):
        fig_div = builder.DIV(builder.H3("Figures"))
        fig_div.append(build_n_figs_div(fig_dir, n_img=100))
        run_div.append(fig_div)
    if os.path.isdir(logging_dir):
        title = builder.H3("Logging")
        logging_div = builder.DIV(title, **{"class": "container"})
        var_dumps = get_var_dump(logging_dir)
        manifest = get_manifest(logging_dir)
        if manifest:
            logging_div.append(
                dict_to_table(pretty_manifest(manifest, "dict"), "Manifest")
            )
        if len(var_dumps):
            for vind, var_dump in enumerate(var_dumps):
                logging_div.append(
                    dict_to_table(var_dump, f"Dumped variables {vind+1}")
                )
        if not manifest and not var_dumps:
            title.text = title.text + " "
            title.append(get_badge("Empty", "warning"))
        run_div.append(logging_div)
    if os.path.isdir(data_dir):
        title = builder.H3("Data")
        data_div = builder.DIV(title, **{"class": "container"})
        data_list = builder.UL(**{"class": "list-group"})
        data_files = os.listdir(data_dir)
        for data_file in data_files:
            data_li = builder.LI(**{"class": "list-group-item"})
            data_li.append(
                builder.A(
                    data_file,
                    **{
                        "href": f"file://{normal_path(os.path.join(data_dir,data_file))}"
                    },
                )
            )
            data_list.append(data_li)
        if not len(data_list):
            title.append(get_badge("Empty", "warning"))
        data_div.append(data_list)
        run_div.append(data_div)

    return run_div


def get_folder_link(href: str):
    return builder.A(
        builder.I(**{"class": "bi bi-folder-symlink"}), **{"href": f"file://{href}"}
    )


def load_json(fpath: str):
    return json.loads(
        io.open(
            fpath,
            "r",
            encoding="utf8",
        ).read(),
        cls=ExtendedJSONDecoder,
    )


def get_browser_data(experiment_path):
    browser_data = load_json(
        os.path.join(
            experiment_path,
            constants.BROWSER_FOLDER,
            constants.LOGGING_DIR,
            constants.MANIFEST_FILENAME + ".json",
        )
    )
    if "project" not in browser_data.keys():
        browser_data["project"] = constants.OTHER_PROJECT
    return browser_data


def get_tag_div(taglist: list):
    if not len(taglist):
        return None
    container_div = builder.DIV(builder.SPAN("Tagged with "), **{"class": "container"})
    for tag in taglist:
        container_div.append(builder.SPAN(" "))
        container_div.append(get_badge(tag, "primary"))
    return container_div


def populate_display_page(experiment_path, browser_data: dict = None):
    title_text = os.path.basename(experiment_path)
    has_browser_data = False
    if browser_data is not None:
        title_text = browser_data["display_name"]
        taglist = browser_data["tag_list"]
        project = browser_data["project"]
        has_browser_data = True

    main_div = builder.DIV(
        builder.H1(
            get_folder_link(href=experiment_path),
            " ",
            title_text,
            **{"class": "text-truncate"},
        ),
        **{
            "class": "accordion-collapse collapse mb-2",
            "data-bs-parent": f"#{DISPLAY_DIV_ID}",
        },
    )
    if has_browser_data:
        main_div.append(builder.P("Part of ", get_badge(project, "info"), " project"))
        tag_div = get_tag_div(taglist)
        if tag_div is not None:
            main_div.append(tag_div)

    main_div.set("id", get_id_from_browser_data(browser_data, DISPLAY_ID_PREFIX))
    for run in os.listdir(experiment_path):
        if not run.startswith("__"):
            run_div = populate_run(experiment_path, run)
            main_div.append(run_div)

    return main_div


def is_timestamp_newer(new: str, ref: str):
    ts_new = datetime.strptime(new, constants.DATETIME_FORMAT)
    ts_ref = datetime.strptime(ref, constants.DATETIME_FORMAT)
    return ts_new > ts_ref


def add_to_browser(date, experiment, experiment_path):
    browser_data = get_browser_data(experiment_path=experiment_path)
    self_id = get_id_from_browser_data(browser_data, prefix=DISPLAY_ID_PREFIX)
    html, exp_scroll_list, display_container_div = get_scroll_list_and_display()
    try:
        experiments_id = [
            y.get("id") for y in display_container_div.findall(".//*[@id]")
        ]
    except Exception:
        raise ValueError("Could not search in div, did you setup the html file?")
    if self_id not in experiments_id:
        append_scroll_and_display(
            display_container_div, exp_scroll_list, date, experiment, experiment_path
        )
        save_html(html)
    else:
        print(f"Experiment id: {self_id}")
        print("Experiment already present, skipping (or uuid collision?)")


def get_scroll_list_and_display():
    html = load_html()
    scroll_list = html.findall(f""".//*[@id='{SCROLL_LIST_ID}']""")[0]
    display_conainer_div = html.findall(f""".//*[@id='{DISPLAY_DIV_ID}']""")[0]

    return html, scroll_list, display_conainer_div


def load_html() -> HtmlElement:
    html_str = io.open(
        os.path.join(read_browser_path(), HTML_FILENAME), "r", encoding="utf8"
    ).read()
    return fromstring(html_str)


def build_base():
    out_html = get_fragment("base")
    out_head: HtmlElement = out_html.find("head")

    js_dir = os.path.join(HOME, "browser/js")
    for script in os.listdir(js_dir):
        script_element = builder.SCRIPT(
            **{"src": (f"file://{normal_path(os.path.join(js_dir, script))}")}
        )
        out_head.append(script_element)
    css_dir = os.path.join(HOME, "browser/css")
    for style_file in os.listdir(css_dir):
        style_element = builder.LINK(
            **{
                "rel": "stylesheet",
                "href": f"file://{normal_path(os.path.join(css_dir, style_file))}",
            }
        )
        out_head.append(style_element)
    return out_html


def rebuild_browser(populate: bool = True):
    setup_browser_folder()
    main_div = fromstring("<div id='main'></div>")
    display_container_div = builder.DIV(
        **{"class": "scrollarea container", "id": DISPLAY_DIV_ID}
    )
    main_div.set("class", "d-flex flex-nowrap")
    scroller: HtmlElement = create_scroller()
    scroller.findall(f""".//*[@id='{SCROLL_TITLE_ID}']""")[0].append(
        get_project_dropdown()
    )
    exp_scroll_list = scroller.findall(f""".//*[@id='{SCROLL_LIST_ID}']""")[0]
    data_path, calendar = get_calendar()
    calendar = sorted(filter(lambda x: not x.startswith("_"), calendar))
    if populate:
        for date in calendar:
            date_path = os.path.join(data_path, date)
            # print(f"Processing {date}...")
            experiments = os.listdir(date_path)
            for experiment in experiments:
                # print(f" - Processing {experiment}...")
                experiment_path = os.path.join(date_path, experiment)

                append_scroll_and_display(
                    display_container_div,
                    exp_scroll_list,
                    date,
                    experiment,
                    experiment_path,
                )
    main_div.append(get_svg_logos())
    main_div.append(get_change_theme())
    main_div.append(scroller)
    main_div.append(get_b_divider("v"))
    main_div.append(display_container_div)
    out_html = build_base()
    out_body = out_html.find("body")
    out_body.text = None
    out_body.append(main_div)
    save_html(out_html)

    print(f"Created data browser at {os.path.join(read_browser_path(), HTML_FILENAME)}")


def save_html(out_html):
    f_out = io.open(
        os.path.join(read_browser_path(), HTML_FILENAME),
        "wb+",
    )
    f_out.write(b"<!doctype html>\n")
    f_out.write(tostring(out_html, pretty_print=True, encoding="utf8"))
    f_out.close()


def append_scroll_and_display(
    display_container_div, exp_scroll_list, date, experiment, experiment_path
):
    figs = build_n_figs_div(experiment_path, height="64px", width="64px", n_img=3)
    browser_data = get_browser_data(experiment_path=experiment_path)
    experiment_display_div = populate_display_page(experiment_path, browser_data)
    display_container_div.append(experiment_display_div)

    manifest = get_manifest(
        os.path.join(experiment_path, os.listdir(experiment_path)[0], "logging")
    )

    scroll_item = create_bs_scroll_item(
        experiment, pretty_manifest(manifest), date, figs, browser_data
    )
    exp_scroll_list.append(scroll_item)


def get_latest_timestamp(experiment, experiment_path):
    last_run = os.listdir(experiment_path)[-1]
    manifest = get_manifest(os.path.join(experiment_path, last_run, "logging"))
    # yucky back compatibility
    if "timestamp" in manifest.keys():
        return manifest["timestamp"]
    elif "__timestamp" in manifest.keys():
        return manifest["__timestamp"]
    else:
        raise KeyError(f"manifest of {experiment} has no timestamp")


def check_img_folder(refresh: bool = False, bypass_prompts: bool = False):
    img_path = os.path.join(read_browser_path(), IMG_DIR)
    if not os.path.isdir(img_path):
        os.makedirs(img_path)
    if refresh:
        to_be_removed = []
        for filename in os.listdir(img_path):
            to_be_removed.append(os.path.join(img_path, filename))
        if not len(to_be_removed):
            print("No images to remove")
            return
        choice = False
        if not bypass_prompts:
            x = input(f"Do you want to clear {len(to_be_removed)} images?")
            choice = x == "Y"

        if choice or bypass_prompts:
            for fpath in to_be_removed:
                if fpath is not None:
                    print(f"Removing {fpath}")
                    os.remove(fpath)


def build_uuid_dict():
    uuids = {}
    experiment_paths = get_all_experiment_paths()
    for experiment_path in experiment_paths:
        dirname = os.path.join(
            experiment_path,
            constants.BROWSER_FOLDER,
            "logging/manifest.json",
        )
        jobj = load_json(dirname)
        uuids[jobj["uuid"]] = experiment_path
    return uuids


def refresh_browser():
    delete_experiments_without_data(read_data_path())
    html = load_html()
    experiments_browser_uuids = [
        y.get("id").replace(SCROLL_ID_PREFIX + "_", "")
        for y in html.findall(".//*[@id]")
        if SCROLL_ID_PREFIX + "_" in y.get("id")
    ]
    data_uuids = build_uuid_dict()
    for browser_uuid in experiments_browser_uuids:
        if browser_uuid not in data_uuids.keys():
            scroll_toremove = html.findall(
                f".//*[@id='{SCROLL_ID_PREFIX}_{browser_uuid}']"
            )[0]
            scroll_toremove.getparent().remove(scroll_toremove)
            display_toremove = html.findall(
                f".//*[@id='{DISPLAY_ID_PREFIX}_{browser_uuid}']"
            )[0]
            display_toremove.getparent().remove(display_toremove)
            print(f"Removed {browser_uuid} from browser")
    save_html(html)


if __name__ == "__main__":
    # print("Processing images")
    # check_img_folder(True, True)
    print("Rebuilding browser")
    rebuild_browser(False)
    # print("Refreshing browser")
    # refresh_browser()
