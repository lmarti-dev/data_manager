import os
from data_manager import read_data_path, ExtendedJSONDecoder
from bs4 import BeautifulSoup, NavigableString
import io
import json
import fitz


HOME = os.path.dirname(__file__)
BASE_FPATH = os.path.join(HOME, "../base.html")
HTML_FPATH = os.path.join(HOME, "../index.html")
IMG_PATH = os.path.join(HOME, "../img")
FILES_PATH = os.path.join(HOME, "../files")


def get_calendar():
    data_path = read_data_path()
    return data_path, os.listdir(data_path)


def convert_pdf(pdf_path):
    fname = os.path.splitext(os.path.basename(pdf_path))[0]
    img_fpath = os.path.join(IMG_PATH, f"{fname}.jpeg")
    if not os.path.isfile(img_fpath):
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pixmap = page.get_pixmap(dpi=300)
        pixmap.save(img_fpath)
    return img_fpath


def get_title_and_content(
    dirname: os.PathLike, h: str, cl: str, title: str, content: BeautifulSoup
):
    soup = BeautifulSoup(f"<div class='{cl}'></div>", "html.parser")
    title_div = soup.new_tag("div", **{"class": f"{cl}-title"})
    title_h = soup.new_tag(h)
    if dirname is not None:
        title_a = soup.new_tag("a", href=f"file:///{dirname}")
        title_a.string = title
        title_h.append(title_a)
    else:
        title_h.string = title
    title_div.append(title_h)
    soup.div.append(title_div)
    content_div = soup.new_tag("div", **{"class": f"{cl}-content"})
    if content != "":
        if isinstance(content, list):
            for item in content:
                content_div.append(item)
        else:
            content_div.append(content)
        soup.div.append(content_div)
        return soup


def get_sub_content(
    dirname,
    heading_level,
    div_class,
    folder_name,
    func: callable = lambda x, y: y,
):
    folder_path = os.path.join(dirname, folder_name)
    items = os.listdir(folder_path)
    content = [
        func(
            folder_path,
            item,
        )
        for item in items
    ]

    soup = get_title_and_content(
        folder_path, heading_level, folder_name, folder_name, content
    )

    return soup


def manage_data(dirname: os.PathLike, item: str):
    soup = BeautifulSoup("<div class='item'></div>", "html.parser")
    if os.path.basename(dirname) == "logging":
        if item.endswith(".json"):
            jobj = json.loads(
                io.open(os.path.join(dirname, item), "r", encoding="utf8").read(),
                cls=ExtendedJSONDecoder,
            )
            if item.startswith("manifest"):
                h_div = soup.new_tag("h6")
                h_div.string = "manifest"
                soup.div.append(h_div)
                for k in jobj.keys():
                    if isinstance(jobj[k], str):
                        p_div = soup.new_tag("p")
                        k_div = soup.new_tag("b")
                        k_div.string = str(k)
                        p_div.append(k_div)
                        p_div.append(jobj[k])
                        soup.div.append(p_div)
            elif item.startswith("var_dump"):
                h_div = soup.new_tag("h6")
                h_div.string = "var_dump"
                soup.div.append(h_div)
                for k in jobj.keys():
                    if not k.startswith("__"):
                        max_len = 100
                        p_div = soup.new_tag("p")
                        k_div = soup.new_tag("b")
                        k_div.string = str(k)
                        p_div.append(k_div)
                        disp_s = str(jobj[k])
                        if len(disp_s) > max_len:
                            disp_s = disp_s[:max_len] + "..."
                        p_div.append(disp_s)
                        soup.div.append(p_div)
            else:
                return ""
            return soup
    elif os.path.basename(dirname) == "figures":
        if item.endswith(".pdf"):
            pdf_fpath = os.path.join(dirname, item)
            img_fpath = convert_pdf(pdf_fpath)
            link = soup.new_tag("a", href=f"file://{pdf_fpath}")
            img = soup.new_tag(
                "img",
                **{
                    "src": f"file://{img_fpath}",
                    "width": 500,
                    "height": 300,
                    "type": "image",
                    "loading": "lazy",
                },
            )
            link.append(img)
            soup.div.append(link)
            return soup
    return ""


def build_html():
    soup = BeautifulSoup("<div id='main'></div>", "html.parser")
    data_path, calendar = get_calendar()
    calendar = sorted(filter(lambda x: not x.startswith("_"), calendar))
    date_content_list = []
    for date in calendar:
        date_path = os.path.join(data_path, date)
        print(f"Processing {date}...")
        experiments = os.listdir(date_path)
        experiment_content_list = []
        for experiment in experiments:
            print(f" - Processing {experiment}...")
            experiment_path = os.path.join(date_path, experiment)
            runs = os.listdir(experiment_path)
            run_content_list = []
            for run in runs:
                print(f"  # Processing {run}...")
                run_path = os.path.join(experiment_path, run)
                folders = os.listdir(run_path)
                folder_content_list = []
                for folder in folders:
                    print(f"   ~ Processing {folder}...")
                    if folder != "data":
                        folder_content_list.append(
                            get_sub_content(
                                dirname=run_path,
                                heading_level="h5",
                                folder_name=folder,
                                div_class="folder",
                                func=manage_data,
                            )
                        )
                run_content_list.append(
                    get_title_and_content(
                        run_path, "h4", "run", run, folder_content_list
                    )
                )
            experiment_content_list.append(
                get_title_and_content(
                    experiment_path, "h3", "experiment", experiment, run_content_list
                )
            )
        date_content_list.append(
            get_title_and_content(
                date_path, "h2", "date", date, experiment_content_list
            )
        )
    soup.div.append(
        get_title_and_content(
            None, "h1", "browser", "Experiment Browser", date_content_list
        )
    )
    f_stream = io.open(BASE_FPATH, "r", encoding="utf8")
    f_content = f_stream.read()

    out_soup = BeautifulSoup(f_content, "html.parser")
    out_soup.body.clear()
    out_soup.body.append(soup)
    f_stream.close()

    f_out = io.open(HTML_FPATH, "w+", encoding="utf8")
    f_out.write(out_soup.prettify())
    f_out.close()


def check_img_folder():
    if not os.path.isdir(IMG_PATH):
        os.makedirs(IMG_PATH)


if __name__ == "__main__":
    check_img_folder()
    build_html()
