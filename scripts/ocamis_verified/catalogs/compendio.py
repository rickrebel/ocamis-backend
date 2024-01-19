import pdfplumber
import re
from scripts.ocamis_verified.catalogs.standard import (
    calculate_standard, some_is_standard, AssignKeys, is_content_title)


def join_words(words):
    all_texts = []
    for elem in words:
        if isinstance(elem, str):
            all_texts.append(elem)
        else:
            all_texts.append(elem["text"])
    return " ".join(all_texts)


def is_every_upper(text):
    if len(text) > 4:
        text = text.replace(" o ", " O ")
    alpha_chars = [char for char in text if char.isalpha()]
    if len(alpha_chars) < 2:
        return False
    alpha_text = "".join(alpha_chars)
    if alpha_text in [
        "ADN", "UI", "GLP", "IX", "VII", "II", "XIII", "UIK", "KIU", "PEU",
        "FSHUI", "HTBZ", "KD", "ML", "CYPA", "HT", "DL", "UD", "CRM", "BFVF",
        "DICC", "FLURY", "LEP", "PMWI", "UFC", "RA", "OKA", "UFP", "HB",
        "VIII", "CF", "PMW", "LEPC", "REC", "NF", "USP", "ALHPA"]:
        return False
    return all([char.isupper() for char in alpha_chars])


class ProcessPDF:
    headers = {
        "key": "Clave", "desc": "Descripción",
        "ind": "Indicaciones", "way": "Vía de administración y Dosis"}
    way_lower = headers["way"].lower()
    print("way_lower", way_lower)
    headers_inverse = {v: k for k, v in headers.items()}
    headers_values = list(headers.values())
    body = [
        "generalidades", "riesgo en el embarazo",
        "efectos adversos", "contraindicaciones y precauciones",
        "interacciones"]
    init_extrange = [
        "Comprimido", "Tableta", "TABLETA Oral", "Colorio", "Cápsula",
        "Solución inyectable", "Colirio", "Suspensión inyectable", "Solución"]
    sure_inits = [
        "Tableta de liberación prolongada",
        "Tableta de liberación prolongada.",
        "Solución estéril elasto-viscosa para",
        "aplicación intra-articular Cada ml",
        "Lubricante viscoelástico transparente",
        "y estéril mediante el uso de calor",
        "húmedo.",
        "Solución estéril elasto-viscosa de",
        "aplicación intra-articular.",
        "POLVO (Fórmula de Osmolaridad",
        "Baja)",
        "ANTIALACRÁN o",
        "Solución que se utiliza para repone",
        "temporalmente la capa deteriorada de",
        "Glicosaminoglicano (GAG) del epitelio",
        "de la vejiga. Solución estéril y libre de",
        "pirógenos.",
    ]

    def __init__(self, path_file):
        self.format_key = re.compile(r"\d{3}\.\d{3}\.\d{4}\.\d{2}")
        self.path_file = path_file
        self.all_components = []
        self.last_place = "headers"
        self.last_group = "UNKNOWN"
        self.first_page = None

    def __call__(self, pages=1, pages_range=None):
        # if not pages:
        #     pages = [0]
        first_p = 0
        last_p = pages
        if pages_range:
            first_p, last_p = pages_range
        with (pdfplumber.open(self.path_file) as pdf):
            component = None
            last_is_title = False
            for page in pdf.pages[first_p:last_p]:
                words = page.extract_words(
                    x_tolerance=1, y_tolerance=3, keep_blank_chars=True)
                if not self.first_page:
                    self.first_page = words

                for word in words:
                    text = word["text"].strip()
                    if not text:
                        continue
                    # is_key = self.format_key.match(text)
                    is_left = word["x0"] < 90
                    is_group = False
                    if is_left:
                        is_group = "Grupo Nº" in text

                    if is_group:
                        self.last_group = text.split(": ")[1]
                        if component:
                            self.add_component(component)
                            component = None
                        last_is_title = False
                        continue
                    elif is_left:
                        is_upper = is_every_upper(text)
                        if is_upper:
                            height = word["bottom"] - word["top"]
                            if height > 6.8:
                                if last_is_title:
                                    component["titles"].append(text)
                                else:
                                    if component:
                                        self.add_component(component)
                                    component = self.create_component(text)
                                last_is_title = True
                                continue
                    if not component:
                        print("No component ----------")
                        print("text:", text)
                        continue
                    self.last_place = self.row(text)
                    try:
                        word["text"] = text
                        component[self.last_place].append(word)
                        # component[self.last_place].append(text)
                    except KeyError:
                        print(f"Error: {text}")
                        print(f"Last place: {self.last_place}")
                    # if self.way in text:
                    if self.last_place == "way":
                        self.last_place = "table"
                    last_is_title = False
            self.add_component(component)

    def create_component(self, text):
        new_component = {"titles": [text], "table": [], "others": []}
        for elem in self.body:
            new_component[elem] = []
        for elem in self.headers.keys():
            new_component[elem] = []
        return new_component

    def row(self, text):
        lower = text.lower()
        lower = lower.replace("*", "")
        lower = lower.replace("vías", "vía")
        if text in self.headers_values:
            return self.headers_inverse[text]
        elif text in ["Indicaciónes"]:
            return "ind"
        if self.last_place == "ind":
            if len(text) > 15 and lower == self.way_lower:
                print("$$$$$$$ Forced way")
                return "way"
            elif "vía de administración" in lower:
                print("$$$$$$$ Forced way 2")
                return "way"
        elif lower in self.body:
            return lower
        return self.last_place

    def add_component(self, component):
        if not component:
            print("Empty component ###################")
            return
        component_name = join_words(component["titles"])
        print("-- component_name", component_name)
        new_table = {"keys": [], "values": [], "descriptions": [],
                     "indications": [], "ways": []}
        presentations = []
        if not component["desc"]:
            print("No desc ###################")
            print("component", component)
            return
        descr = component["desc"][0]

        # end_key = table[0]["x1"]
        inits = []
        for word in component["table"]:
            text = word["text"]
            cleaned_text = text.replace(" ", "")
            if "." in cleaned_text[0]:
                cleaned_text = cleaned_text[1:]
            if text == "010.000.1755.0":
                cleaned_text = "010.000.1755.00"
            is_key = self.format_key.match(cleaned_text)
            if is_key:
                # print("key found:", text)
                word["descriptions"] = []
                word["text"] = cleaned_text
                new_table["keys"].append(word)
            else:
                inits.append(word["x0"])
                new_table["values"].append(word)
        # print("desc", descr)
        if not inits:
            print("No inits ###################")
            print("component", component)
            return
        defs = {"center": descr["x0"] + (descr["x1"] - descr["x0"]) / 2,
                "left": min(inits)}
        defs["right"] = defs["left"] + (defs["center"] - defs["left"] - 2) * 2
        ind = component["ind"][0]
        indications = {"center": ind["x0"] + (ind["x1"] - ind["x0"]) / 2,
                       "left": defs["right"] + 4}
        indications["right"] = indications["left"] + (
                indications["center"] - indications["left"]) * 2

        last_is_upper = False
        new_title = False
        for word in new_table["values"]:
            text = word["text"]
            if word["x0"] < defs["right"]:
                every_upper = is_every_upper(text)
                if not every_upper:
                    every_upper = text in [
                        "Solución inyectable.", "Pirfenidona Gel.",
                        "Granulado Oral", "Solución inyectable:"]
                if not every_upper:
                    if last_is_upper and text in ["O"]:
                        every_upper = True
                    if not last_is_upper and not presentations:
                        if text in self.init_extrange:
                            every_upper = True
                if not every_upper:
                    if component_name == "EVEROLIMUS":
                        if text in self.init_extrange:
                            every_upper = True
                    if text in self.sure_inits:
                        every_upper = True
                # print("text:", every_upper, text)
                if every_upper:
                    # print("every_upper", last_is_upper, text)
                    new_title = True
                    if last_is_upper:
                        presentations[-1]["names"].append(text)
                    else:
                        pres = word.copy()
                        pres.update({
                            "keys": [], "descriptions": [], "names": [text],
                            "words": [], "content_titles": []})
                        presentations.append(pres)
                else:
                    try:
                        if new_title:
                            presentations[-1]["content_titles"].append(word)
                            new_title = is_content_title(text)
                        else:
                            presentations[-1]["words"].append(word)
                    except IndexError:
                        print("Error in word ###################")
                        print("text:", every_upper, text)
                        print("word", word)
                        print("presentations", presentations)

                last_is_upper = every_upper
            elif word["x0"] < indications["right"]:
                new_table["indications"].append(word)
            else:
                new_table["ways"].append(word)

        if not presentations:
            print("No presentations ###################")
            print("component", component)
            return

        def add_key(index, key_data):
            # print("add_key", index, key_data)
            presentations[index]["keys"].append(key_data)

        current_pres = 0
        for (i, key) in enumerate(new_table["keys"]):
            try:
                next_pres = presentations[current_pres + 1]
                if next_pres["doctop"] < key["doctop"]:
                    current_pres += 1
            except IndexError:
                pass
            add_key(current_pres, key)

        assign_keys = AssignKeys(presentations, component_name, new_table)
        assign_keys()

        final_presentations = []
        # print("assign_keys.presentations", assign_keys.presentations)

        for pres in assign_keys.presentations:
            final_pres = {
                "name": join_words(pres["names"]),
                "content_title": join_words(pres["content_titles"]),
                "content": join_words(pres["descriptions"]),
                "keys": []
            }
            for key in pres["keys"]:
                final_pres["keys"].append({
                    "key": key["text"],
                    "description": join_words(key["descriptions"])
                })
            final_presentations.append(final_pres)

        component["name"] = component_name
        component["presentations"] = final_presentations
        component["group"] = self.last_group
        # component["indications"] = new_table["indications"]
        # component["ways"] = new_table["ways"]
        del component["table"]

        self.all_components.append(component)
