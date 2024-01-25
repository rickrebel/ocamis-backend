import requests
import json
from bs4 import BeautifulSoup


class Scrapper:
    base_url = "https://www.vademecum.es"
    common_path = "G:/Mi unidad/YEEKO/Nosotrxs/Cero desabasto/Bases de datos/Medicamentos/"
    json_path = f"{common_path}vademecum.json"

    def __init__(self):
        self.all_components = []
        try:
            with open(self.json_path, encoding="utf-8") as json_file:
                self.all_components = json.load(json_file)
        except Exception as e:
            print("error en load_json:", e)
        self.soup = None
        self.ready_urls = set()
        self.all_keys = {}
        self.component = {}
        self.current_group = None

    def get_header(self):
        return self.soup.find(
            "h1", text="Compendio Nacional de Insumos para la Salud - México")

    def explore_group(self, group_id):
        url = f"https://www.vademecum.es/cnis/{group_id}/a?cc=mx"
        # scrapper = Scrapper(sub_url)
        response = requests.get(url)
        soup2 = BeautifulSoup(response.text, 'html.parser')
        self.current_group = {"id": group_id, "urls": []}

        header = soup2.find("h1", text="Compendio Nacional de Insumos para la Salud - México")
        group_a = header.find_next_sibling("a")
        print("group_a:", group_a)
        group_name = group_a.find("b")
        self.current_group["name"] = group_name.string.strip()
        ul = header.find_next_sibling("ul")
        lis = ul.find_all("li")
        for li in lis:
            href = li.find("a")["href"]
            self.current_group["urls"].append(href)

    def explore_components(self):
        # print("current_group:", self.current_group)
        for sub_url in self.current_group["urls"]:
            self.explore_component(sub_url)

    def explore_component(self, sub_url):

        print("sub_url:", sub_url)

        if sub_url in self.ready_urls:
            return
        try:
            response = requests.get(f"{self.base_url}{sub_url}")
            self.soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print("error en build_component:", e)
            print("sub_url:", sub_url)
            return
        self.component = {
            "parent_group": self.current_group["name"],
            "group_id": self.current_group["id"]
        }

        try:
            header = self.get_header()
            parent_header = header.parent
            contents = parent_header.contents
            group = header.find_next_sibling("h3")
            self.component["group_name"] = group.string.split(":")[-1].strip()
        except Exception as e:
            print("error en get_title:", e)
            print("sub_url:", sub_url)
            return
        component_name = None
        try:
            component_name = parent_header.find("h2").string.strip()
        except Exception as e:
            print("sub_url:", sub_url)
        if not component_name:
            try:
                title = self.soup.find("title")
                component_name = title.string
                component_name = component_name.replace("CNIS ", "")
                component_name = component_name.upper().strip()
            except Exception as e:
                print("error en component_name y title:", e)
                print("sub_url:", sub_url)
                return

        self.component["name"] = component_name

        try:
            level = contents[5]
            self.component["level"] = level.replace("\n", "").strip()
            last_edition = contents[8]
            self.component["last_edition"] = last_edition.replace("\n", "").strip()
        except Exception as e:
            self.component["title_raw"] = parent_header.text.strip()
            print("error en get_level:", e)
            print("sub_url:", sub_url)

        # keys = soup.find_all("b", text="Clave")
        body_tables = self.soup.find_all("div", class_="divTableBody")
        if not body_tables:
            print("No body_tables")
            print("sub_url:", sub_url)
            return
        try:
            self.get_keys(body_tables)
        except Exception as e:
            print("error en get_complements:", e)
            print("sub_url:", sub_url)
            return

        try:
            parent_div = body_tables[0].parent
            next_div = parent_div.find_next_sibling("div")
            self.component["complements"] = next_div.text.strip()
        except Exception as e:
            print("error en get_complements:", e)
            print("sub_url:", sub_url)
        self.all_components.append(self.component)
        self.ready_urls.add(sub_url)

    def get_keys(self, body_tables):

        cell_names = ["key", "description", "indications", "way"]
        all_keys = []
        for body_table in body_tables:
            rows = body_table.find_all("div", class_="divTableRow")
            for row in rows:
                key = {}
                cells = row.find_all("div", class_="divTableCell")
                # print("cells:", cells)
                for cell_name, cell in zip(cell_names, cells):
                    divs = cell.find_all("div")
                    real_content = divs[1]
                    text = real_content.text
                    # delete \n at the beginning and end
                    text = text.strip()
                    if cell_name == "description":
                        lines = text.split("\n")
                        lines = [line.strip() for line in lines if line.strip()]
                        key["presentation_name"] = lines[0]
                        key["presentation_description"] = lines[-1]
                        container = lines[1:-1]
                        container = " ".join(container)
                        key["container_description"] = container.strip()
                    key[cell_name] = text
                all_keys.append(key)
        self.component["keys"] = all_keys

    def build_all_keys(self):
        for component in self.all_components:
            for key in component["keys"]:
                self.all_keys.setdefault(key["key"], []).append(key)

    def save_json(self, encoding="utf-8"):

        with open(self.json_path, "w", encoding=encoding) as file:
            json.dump(self.all_components, file, indent=4, ensure_ascii=False)
