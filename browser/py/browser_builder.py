import os
from json_extender import (
    ExtendedJSONDecoder,
    ExtendedJSONEncoder,
)
from utils import read_data_path

import io
import fitz
import re
import json
import constants
from datetime import datetime

# bs4 is for reading documents, not creating them.
from lxml.html import fromstring, tostring, builder, HtmlElement

HOME = os.path.dirname(__file__)
HTML_FPATH = os.path.join(HOME, "../index.html")
FRAGMENT_PATH = os.path.join(HOME, "../fragments")

IMG_PATH = os.path.join(HOME, "../img")
FILES_PATH = os.path.join(HOME, "../files")
SCROLL_LIST_ID = "exp-scroll-list"
DISPLAY_DIV_ID = "exp-display-div"

WEBPAGE_MANIFEST_FPATH = os.path.join(HOME, "../files/manifest.json")


DISPLAY_ID_PREFIX = "expe"
SCROLL_ID_PREFIX = "scroll"


def get_badge(text: str, badge_type: str):
    return builder.SPAN(text, **{"class": f"badge text-bg-{badge_type}"})


def get_var_dump(logging_dir: str):
    files = os.listdir(logging_dir)
    var_dump = [x for x in files if x.startswith("var_dump")]
    if len(var_dump):
        jobj = json.loads(
            io.open(
                os.path.join(logging_dir, var_dump[0]), "r", encoding="utf8"
            ).read(),
            cls=ExtendedJSONDecoder,
        )
        return jobj
    return {}


def get_manifest(logging_dir: str):
    files = os.listdir(logging_dir)
    manifest = [x for x in files if x.startswith("manifest")]
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
    fname = os.path.splitext(os.path.basename(pdf_path))[0]
    img_fpath = os.path.join(IMG_PATH, f"{fname}.jpeg")
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
    return "_".join([title, date])


def create_bs_scroll_item(title: str, body: str, date: str, figs):
    main_elem = builder.BUTTON(
        **{
            "id": get_id_from_title_date(title, date, SCROLL_ID_PREFIX),
            "data-bs-toggle": "collapse",
            "data-bs-target": f"#{get_id_from_title_date(title, date,DISPLAY_ID_PREFIX)}",
            "class": "list-group-item list-group-item-action py-3 lh-sm",
            "aria-controls": get_id_from_title_date(title, date, SCROLL_ID_PREFIX),
        }
    )

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


def get_fragment(filename: str):
    raw_html = io.open(
        os.path.join(FRAGMENT_PATH, f"{filename}.html"), "r", encoding="utf8"
    ).read()
    return fromstring(raw_html)


def create_scroller():
    return get_fragment("scroller")


def get_svg_logos():
    return get_fragment("logos")


def get_b_divider():
    return get_fragment("b_divider")


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
        var_dump = get_var_dump(logging_dir)
        manifest = get_manifest(logging_dir)
        if manifest:
            logging_div.append(
                dict_to_table(pretty_manifest(manifest, "dict"), "Manifest")
            )
        if var_dump:
            logging_div.append(dict_to_table(var_dump, "Dumped variables"))
        if not manifest and not var_dump:
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


def populate_from_data(experiment_path, title: str, date: str):
    main_div = builder.DIV(
        builder.H1(
            get_folder_link(href=experiment_path),
            " ",
            os.path.basename(experiment_path),
            **{"class": "text-truncate"},
        ),
        **{
            "class": "accordion-collapse collapse",
            "data-bs-parent": f"#{DISPLAY_DIV_ID}",
        },
    )
    main_div.set("id", get_id_from_title_date(title, date, DISPLAY_ID_PREFIX))
    for run in os.listdir(experiment_path):
        run_div = populate_run(experiment_path, run)
        main_div.append(run_div)
    return main_div


def is_timestamp_newer(new: str, ref: str):
    ts_new = datetime.strptime(new, constants.DATETIME_FORMAT)
    ts_ref = datetime.strptime(ref, constants.DATETIME_FORMAT)
    return ts_new > ts_ref


def save_webpage_manifest(jobj: dict):
    fstream = io.open(WEBPAGE_MANIFEST_FPATH, "w+", encoding="utf8")
    fstream.write(
        json.dumps(jobj, indent=4, ensure_ascii=False, cls=ExtendedJSONEncoder)
    )
    fstream.close()


def add_to_browser(date, experiment, experiment_path):
    self_id = get_id_from_title_date(
        title=experiment, date=date, prefix=DISPLAY_ID_PREFIX
    )
    html, exp_scroll_list, display_container_div = get_scroll_list_and_display()
    experiments_id = [y.get("id") for y in display_container_div.findall(".//*[@id]")]
    if self_id not in experiments_id:
        append_scroll_and_display(
            display_container_div, exp_scroll_list, date, experiment, experiment_path
        )
        save_html(html)
    else:
        raise ValueError("adding an experiment that's already there?")


def get_scroll_list_and_display():
    html = load_html()
    scroll_list = html.findall(f""".//*[@id='{SCROLL_LIST_ID}']""")[0]
    display_conainer_div = html.findall(f""".//*[@id='{DISPLAY_DIV_ID}']""")[0]

    return html, scroll_list, display_conainer_div


def load_html():
    html_str = io.open(HTML_FPATH, "r", encoding="utf8").read()
    return fromstring(html_str)


def rebuild_browser():
    main_div = fromstring("<div id='main'></div>")
    display_container_div = builder.DIV(
        **{"class": "scrollarea container", "id": DISPLAY_DIV_ID}
    )
    main_div.set("class", "d-flex flex-nowrap")
    scroller = create_scroller()
    exp_scroll_list = scroller.findall(f""".//*[@id='{SCROLL_LIST_ID}']""")[0]
    data_path, calendar = get_calendar()
    calendar = sorted(filter(lambda x: not x.startswith("_"), calendar))
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
    main_div.append(get_b_divider())
    main_div.append(display_container_div)
    out_html = get_fragment("base")
    out_body = out_html.find("body")
    out_body.text = None
    out_body.append(main_div)
    save_html(out_html)


def save_html(out_html):
    f_out = io.open(
        HTML_FPATH,
        "wb+",
    )
    f_out.write(b"<!doctype html>\n")
    f_out.write(tostring(out_html, pretty_print=True, encoding="utf8"))
    f_out.close()


def append_scroll_and_display(
    display_container_div, exp_scroll_list, date, experiment, experiment_path
):
    figs = build_n_figs_div(experiment_path, height="64px", width="64px", n_img=3)
    experiment_display_div = populate_from_data(experiment_path, experiment, date)
    display_container_div.append(experiment_display_div)

    manifest = get_manifest(
        os.path.join(experiment_path, os.listdir(experiment_path)[0], "logging")
    )

    scroll_item = create_bs_scroll_item(
        experiment, pretty_manifest(manifest), date, figs
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


def load_webpage_manifest():
    return json.loads(
        io.open(WEBPAGE_MANIFEST_FPATH, "r", encoding="utf8").read(),
        cls=ExtendedJSONDecoder,
    )


def build_webpage_manifest():
    jobj = {}
    data_path, calendar = get_calendar()
    calendar = sorted(filter(lambda x: not x.startswith("_"), calendar))
    for date in calendar:
        date_path = os.path.join(data_path, date)
        experiments = os.listdir(date_path)
        for experiment in experiments:
            experiment_path = os.path.join(date_path, experiment)
            jobj[experiment] = get_latest_timestamp(experiment, experiment_path)

    save_webpage_manifest(jobj)


def check_img_folder(refresh: bool = False):
    if not os.path.isdir(IMG_PATH):
        os.makedirs(IMG_PATH)
    if refresh:
        to_be_removed = []
        for filename in os.listdir(IMG_PATH):
            to_be_removed.append(os.remove(os.path.join(IMG_PATH, filename)))
        if not len(to_be_removed):
            print("No images to remove")
            return
        x = input(f"Do you want to clear {len(to_be_removed)} images?")
        if x == "Y":
            for fpath in to_be_removed:
                print(f"Removing {fpath}")
                os.remove(fpath)
        else:
            pass


if __name__ == "__main__":
    check_img_folder(True)
    rebuild_browser()
