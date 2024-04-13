import pdfplumber
import re
import json
from scripts.verified.catalogs.standard import (
    AssignKeys, is_content_title, count_content_titles)


def join_words(words):
    all_texts = []
    for elem in words:
        if isinstance(elem, str):
            all_texts.append(elem.strip())
        else:
            all_texts.append(elem["text"].strip())
    return " ".join(all_texts)


def is_every_upper(text):
    if len(text) > 4:
        text = text.replace(" o ", " O ")
    text = re.sub(r"\(.*?\)", "", text)
    alpha_chars = [char for char in text if char.isalpha()]
    alpha_text = "".join(alpha_chars)
    if alpha_text == "Y":
        return True
    if len(alpha_chars) < 2:
        return False
    if alpha_text in ["ADNr"]:
        return True
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
    nutri_headers = ["administración", "vía de", "descripción",
                     "indicaciones", "clave"]
    way_lower = headers["way"].lower()
    # print("way_lower", way_lower)
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
        "Solución incolora libre de partículas, con pH de",
        "6.9-7.1, viscosidad de 9-15 cps y osmolaridad de",
        "275-300mOsm",
        "SOLUCIÓN INYECTABLE Inmunización activa",
        "ANTIALACRÁN o",
        "Solución que se utiliza para reponer",
        "temporalmente la capa deteriorada de",
        "Glicosaminoglicano (GAG) del epitelio",
        "de la vejiga. Solución estéril y libre de",
        "pirógenos.",
    ]
    spacial_previous = [
        "de la biotransformación de fenitoína",
        "Ninguna con la aplicación conjunta con otras vacunas"
    ]
    bad_align = [
        "VANDETANIB",
        "VACUNA",
        "ALIMENTO",
        "FÓRMULA",
        "FORMULA",
        "VITAMINAS",
        "FACTOR",
        "OCTOCOG",
        "GOTAS LUBRICANTES OCULARES",
    ]

    def __init__(self, path_file, **kwargs):
        self.format_key = re.compile(r"\d{3}\.\d{3}\.\d{4}\.\d{2}")
        self.path_file = path_file
        self.all_components = []
        self.json_path = kwargs.get("json_path")
        self.is_nutrition = kwargs.get("is_nutrition", False)
        if self.json_path:
            try:
                with open(self.json_path, "r", encoding="utf-8") as file:
                    self.all_components = json.load(file)
            except Exception as e:
                print("Error in load_json:", e)
        self.last_place = "headers"
        self.last_group = "VI. Nutriología" if self.is_nutrition else "UNKNOWN"
        self.first_page = None
        self.cut_dosis = None
        self.component_names = []
        self.errors = []

    def __call__(self, pages=1, pages_range=None):
        # if not pages:
        #     pages = [0]
        first_p = 0
        last_p = pages
        if pages_range:
            first_p, last_p = pages_range
        left_limit = 92.3 if self.is_nutrition else 90
        with (pdfplumber.open(self.path_file) as pdf):
            component = None
            last_is_title = False
            next_is_left = False
            is_group = False
            # for (page_number, page) in enumerate(pdf.pages):
            # for page in pdf.pages[first_p:last_p]:
            for (page_number, page) in enumerate(pdf.pages[first_p:last_p]):
                words = page.extract_words(
                    x_tolerance=1, y_tolerance=3, keep_blank_chars=True)
                if not self.first_page:
                    self.first_page = words

                for word in words:
                    text = word["text"].strip()
                    word["page"] = page_number
                    if not text:
                        continue
                    # is_key = self.format_key.match(text)

                    is_left = word["x0"] < left_limit
                    if self.some_special(text, is_left):
                        next_is_left = True

                    if next_is_left:
                        if self.some_header_table(text):
                            next_is_left = False
                        else:
                            is_left = True
                    if is_left and not is_group:
                        is_group = "Grupo Nº" in text

                    is_upper = is_every_upper(text)

                    if is_group and not is_upper:
                        if ": " in text:
                            self.last_group = text.split(": ")[1]
                        else:
                            self.last_group += f" {text}"
                            self.last_group = self.last_group.strip()
                        if component:
                            self.add_component(component)
                            component = None
                        last_is_title = False
                        continue
                    elif is_left:
                        is_group = False
                        height = word["bottom"] - word["top"]
                        if is_upper or (height > 6.8 and last_is_title):
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
        elif self.last_place == "desc":
            if "indic" in lower:
                return "ind"
        if self.last_place == "ind" or self.last_place == "interacciones":
            if len(text) > 15 and lower == self.way_lower:
                print("$$$$$$$ Forced way")
                return "way"
            elif "vía de administración" in lower:
                self.cut_dosis = self.way_lower.replace(lower, "").strip()
                print("$$$$$$$ Forced way 2", self.cut_dosis)
                return "way"
            elif "Vía de" in text:
                self.cut_dosis = self.way_lower.replace("vía de", "").strip()
                print("$$$$$$$ Forced way 2", self.cut_dosis)
                return "way"
            elif self.cut_dosis and lower in self.cut_dosis:
                print("$$$$$$$ Forced way 3")
                return "way"
        elif lower in self.body:
            self.cut_dosis = None
            return lower
        return self.last_place

    def add_component(self, component):
        if not component:
            print("Empty component ###################")
            return
        component_name = join_words(component["titles"])
        component_name = component_name.split(" P á g i n a")[0]
        self.component_names.append(component_name)

        new_table = {"keys": [], "values": [], "descriptions": [],
                     "indications": [], "ways": []}
        presentations = []
        if not component["desc"]:
            print("No desc ###################")
            print("-- component_name", component_name)
            self.errors.append({
                "component_name": component_name,
                "error_type": "No desc",
                "component": component
            })
            # print("component", component)
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
            print("Sin texto después de clave ###################")
            print("-- component_name", component_name)
            self.errors.append({
                "component_name": component_name,
                "error_type": "Sin texto después de clave",
                "component": component
            })
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
            if word["x0"] < defs["right"]:
                new_table["descriptions"].append(word)
            elif word["x0"] < indications["right"]:
                new_table["indications"].append(word)
            else:
                new_table["ways"].append(word)

        desc_lines = []
        last_doctop = None
        for word in new_table["descriptions"]:
            if word["doctop"] == last_doctop:
                desc_lines[-1]["text"] += " " + word["text"]
            else:
                desc_lines.append(word)
            last_doctop = word["doctop"]

        content_title_count = count_content_titles(desc_lines, strict=True)
        available_without_title = content_title_count <= len(new_table["keys"])
        excluded = ["GUSELKUMAB", "PACLITAXEL",
                    "TOXOIDES TETÁNICO Y DIFTÉRICO(Td)"]
        if available_without_title and component_name in excluded:
            available_without_title = False

        for word in desc_lines:
            text = word["text"]
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

                without_pres_title = None
                if available_without_title:
                    if len(presentations) > 0 and not last_is_upper:
                        is_cont_title = is_content_title(text, strict=True)
                        if is_cont_title:
                            last_pres = presentations[-1]
                            has_keys = len(last_pres.get("words", [])) > 0
                            if has_keys:
                                without_pres_title = last_pres
                    if without_pres_title:
                        same_pres = word.copy()
                        same_pres.update({
                            "keys": [], "descriptions": [], "words": [],
                            "content_titles": [],
                            "names": without_pres_title["names"]
                        })
                        presentations.append(same_pres)
                        new_title = True
                try:
                    if new_title:
                        presentations[-1]["content_titles"].append(word)
                        new_title = not is_content_title(text)
                    else:
                        presentations[-1]["words"].append(word)
                except IndexError:
                    print("Error in word ###################")
                    print("-- component_name", component_name)
                    self.errors.append({
                        "component_name": component_name,
                        "error_type": "Error in word",
                        "text": text,
                        "word": word,
                        "presentations": presentations,
                    })

            last_is_upper = every_upper

        if not presentations:
            print("No presentations ###################")
            print("-- component_name", component_name)
            self.errors.append({
                "component_name": component_name,
                "error_type": "No desc",
                "component": component
            })
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
        assign_keys.show_errors = False
        assign_keys()
        self.errors.extend(assign_keys.all_errors)

        final_presentations = []
        # print("assign_keys.presentations", assign_keys.presentations)

        for pres in assign_keys.presentations:
            content_title = join_words(pres["content_titles"])
            content = join_words(pres["descriptions"])
            description = f"{content_title} {content}".strip()
            final_pres = {
                "name": join_words(pres["names"]),
                "content_title": content_title,
                "content": content,
                "description": description,
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

    def save_json(self, path=None, encoding="utf-8"):
        final_path = path or self.json_path
        if not final_path:
            print("No json_path")
            return
        with open(final_path, "w", encoding=encoding) as file:
            json.dump(self.all_components, file, indent=4)

    def some_header_table(self, text):
        if "Clave" in text:
            return True
        if self.is_nutrition:
            lower = text.lower()
            for header in self.nutri_headers:
                if header in lower:
                    return True
        return False

    def some_special(self, text, is_left):
        for elem in self.spacial_previous:
            if elem in text:
                return True
        if is_left and ("SISTEMA" in text or "VACUNA" in text):
            return True
        for elem in self.bad_align:
            if elem in text:
                return True
        return False
