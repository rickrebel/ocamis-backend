
prev_with = [
    "Caja", "caja colectiva", "envase", "caja de cartón", "el envase",
    "envase ampolleta", "envase de plomo", "envase frasco ámbar",
    "envase frasco gotero", "envase gotero", "envase pluma",
    "envase presurizado", "envases", "frasco ampula", "frasco",
    "Jeringa prellenada", "pluma precargada", "pluma", "Un frasco ámpula",
    "Vial y/o frasco ámpula", "barra", "tubo", "Frasco-ámpula",
    "Frasco ámpula",
    "Envase gotero de plástico depresible", "Jeringa prellenada"
]
previous_lower = [prev.lower() for prev in prev_with]


def calculate_standard(description):
    import re
    description = description.lower()
    for prev in previous_lower:
        real_prev = f"{prev} con"
        if description.startswith(real_prev):
            return True
    re_pattern_1 = re.compile(r"(\d+) envases con")
    if re_pattern_1.match(description):
        return True
    if description == "envase":
        return True
    starts = ("envase: ", "envase ", "barra de", "una dosis de", "frasco de")
    if description.startswith(starts):
        return True
    # example "4 envases con ..."
    re_pattern_2 = re.compile(r"envase para (\d+)")
    if re_pattern_2.match(description):
        return True
    # if not is_standard:
    #     print("description", description)
    return False


def some_is_standard(descriptions):
    for description in descriptions:
        if calculate_standard(description):
            return True
    return False


def count_standards(words):
    descriptions = [word["text"].strip() for word in words]
    count = 0
    for description in descriptions:
        if calculate_standard(description):
            count += 1
    return count


def is_content_title(text, strict=False):
    if "contiene Abemaciclib" in text:
        return True
    if strict:
        lower = text.lower()
        if lower.endswith(" contiene"):
            return True
        if lower.endswith(":") and "contiene" in lower:
            return True
    else:
        if text.endswith(":"):
            return True
        if " contiene" in text.lower():
            return True
    return False


def count_content_titles(words, strict=False):
    count = 0
    for word in words:
        if is_content_title(word["text"], strict):
            count += 1
    return count


class AssignKeys:

    def __init__(self, presentations, component_name, new_table):
        self.presentations = presentations
        self.component_name = component_name
        self.new_table = new_table
        self.show_errors = True
        self.all_errors = []
        # self.keys_started = False
        # self.current_key = 0

    def __call__(self):
        same_count = len(self.presentations) == len(self.new_table["keys"])
        for pres in self.presentations:
            keys = pres["keys"]
            if not keys:
                if same_count:
                    try:
                        last_line = pres["words"].pop()
                        last_line["descriptions"] = []
                        pres["keys"].append(last_line)
                    except IndexError:
                        print("Caso especial ###################")
                        self.print_errors(pres)
                        continue
                else:
                    self.print_errors(pres)
                    continue
            if not pres["descriptions"] and pres["content_titles"]:
                pres["descriptions"] = pres["content_titles"]
                pres["content_titles"] = []
            self.assign_keys(pres)

    def assign_keys(self, pres):
        keys = pres["keys"]
        current_key = 0
        first_key_top = keys[0]["doctop"]

        standard_count = count_standards(pres["words"])
        is_simple = standard_count == len(keys)
        keys_reached = -1

        for (i, word) in enumerate(pres["words"]):
            if is_simple:
                is_standard = calculate_standard(word["text"])
                keys_reached += 1 if is_standard else 0
                if keys_reached == -1:
                    pres["descriptions"].append(word)
                else:
                    pres["keys"][keys_reached]["descriptions"].append(word)
                continue

            if word["doctop"] + 2 < first_key_top:
                pres["descriptions"].append(word)
                continue
            if word["doctop"] + 2 > keys[current_key]["doctop"]:
                is_standard = calculate_standard(word["text"])
                # if is_standard:
                #     self.add_count()
                if not is_standard:
                    # print("word", word["text"])
                    next_words = pres["words"][i + 1:]
                    next_words = [w["text"] for w in next_words]
                    some_standard = some_is_standard(next_words)
                    if not some_standard:
                        if pres["content_titles"]:
                            last_word = pres["descriptions"][-1]
                            last_is_standard = calculate_standard(last_word["text"])
                            if last_is_standard:
                                pres["keys"][current_key]["descriptions"].append(last_word)
                                pres["descriptions"].pop()
                        is_standard = True
                        # pres["descriptions"].append(word)
                        # continue
                    # else:
                    #     self.add_count()
                if not is_standard and current_key == 0:
                    pres["descriptions"].append(word)
                    continue
                try:
                    next_key = keys[current_key + 1]
                    if word["doctop"] + 2 > next_key["doctop"]:
                        current_key += 1
                except IndexError:
                    pass
            # if current_key == 0:
            #     pres["descriptions"].append(word)
            # else:
            pres["keys"][current_key]["descriptions"].append(word)

    def print_errors(self, presentation):
        print("No keys ###################")
        print("component_name", self.component_name)
        self.all_errors.append({
            "component_name": self.component_name,
            "presentation": presentation,
            "presentations": self.presentations,
            "new_table_keys": self.new_table["keys"]
        })
        if self.show_errors:
            print("pres", presentation)
            for pres_elem in self.presentations:
                print("pres[names]", pres_elem["names"])
            print("new_table[keys]", self.new_table["keys"])
        # print("all_presentations:\n", presentations)
