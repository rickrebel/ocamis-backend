import requests
import json
from bs4 import BeautifulSoup


class Scrapper:
    base_url = "https://www.vademecum.es"
    common_path = "G:/Mi unidad/YEEKO/Nosotrxs/Cero desabasto/Bases de datos/Medicamentos/"
    json_path = f"{common_path}vademecum.json"
    error_complements = {
        "/cnis/010.000.6239.00/3/Labetalol?cc=mx",
        "/cnis/010.000.6239.00/3/Perindopril arginina/amlodipino?cc=mx",
        "/cnis/010.000.6239.00/3/Perindopril arginina/amlodipino besilato/indapamida?cc=mx",
        "/cnis/010.000.7077.00/4/Risankizumab?cc=mx",
        "/cnis/010.000.7078.00/5/Dapagliflozina propanodiol?cc=mx",
        "/cnis/010.000.7078.00/5/Semaglutida?cc=mx",
        "/cnis/010.000.7073.00/8/Diosmina/hesperidina?cc=mx",
        "/cnis/010.000.7069.00/10/Carboximaltosa férrica?cc=mx",
        "/cnis/010.000.7069.00/10/Isatuximab?cc=mx",
        "/cnis/010.000.4340.00/13/Omalizumab?cc=mx",
        "/cnis/010.000.7075.00/14/Fampridina?cc=mx",
        "/cnis/010.000.6302.00/16/Darolutamida?cc=mx",
        "/cnis/010.000.5610.01/16/Lanreótida acetato?cc=mx",
        "/cnis/010.000.6302.00/16/Ponatinib?cc=mx",
        "/cnis/040.000.3215.00/19/Diazepam?cc=mx",
        "/cnis/010.000.4512.01/20/Adalimumab?cc=mx",
        "/cnis/010.000.7074.00/20/Upadacitinib?cc=mx"}

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
        self.component_list = []

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
            a_tag = li.find("a")
            href = a_tag["href"]
            self.current_group["urls"].append(href)
            component_name = a_tag.string.strip().upper()
            comp_obj = {"name": component_name, "url": href}
            self.component_list.append(comp_obj)

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
            group_name = group.string.split(":")[-1].replace("\xA0", " ")
            self.component["group_name"] = group_name.strip()
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

        self.component["name"] = component_name.replace("\xA0", " ")

        try:
            level = contents[5]
            level = level.replace("\xA0", " ").replace("\n", "").strip()
            self.component["level"] = level
            last_edition = contents[8]
            last_edition = last_edition.replace("\xA0", " ")
            self.component["last_edition"] = last_edition.replace("\n", "").strip()
        except Exception as e:
            self.component["title_raw"] = parent_header.text\
                .replace("\xA0", " ").strip()
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
            print("error en get_keys:", e)
            print("sub_url:", sub_url)
            self.error_complements.add(sub_url)
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
        current_keys = []
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
                    text = text.replace("\xA0", " ").strip()
                    if cell_name == "description":
                        lines = text.split("\n")
                        lines = [line.strip() for line in lines
                                 if line.strip()]
                        key["presentation_name"] = lines[0]
                        container = lines[1:-1]
                        container = " ".join(container)
                        container = container.strip()
                        key["presentation_description"] = container
                        key["container_description"] = lines[-1]
                    key[cell_name] = text
                current_keys.append(key)
        self.component["keys"] = current_keys

    def build_all_keys(self):
        for component in self.all_components:
            for key in component["keys"]:
                key["component"] = component
                self.all_keys.setdefault(key["key"], []).append(key)

    def save_json(self, encoding="utf-8"):

        with open(self.json_path, "w", encoding=encoding) as file:
            json.dump(self.all_components, file, indent=4, ensure_ascii=False)
