
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


def is_content_title(text):
    if ":" in text:
        return False
    if " contiene" in text.lower():
        return False
    return True


class AssignKeys:

    def __init__(self, presentations, component_name, new_table):
        self.presentations = presentations
        self.component_name = component_name
        self.new_table = new_table
        # self.keys_started = False
        # self.current_key = 0

    def print_errors(self, presentation):
        print("No keys ###################")
        print("component_name", self.component_name)
        print("pres", presentation)
        for pres_elem in self.presentations:
            print("pres[names]", pres_elem["names"])
        # print("all_presentations:\n", presentations)
        print("new_table[keys]", self.new_table["keys"])

    # def add_count(self):
    #     if self.keys_started:
    #         self.current_key += 1
    #     self.keys_started = True

    def assign_keys(self, pres):
        keys = pres["keys"]
        current_key = 0
        first_key_top = keys[0]["doctop"]
        for (i, word) in enumerate(pres["words"]):
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

    def __call__(self):
        for pres in self.presentations:
            keys = pres["keys"]
            if not keys:
                self.print_errors(pres)
                continue
            if not pres["words"] and pres["content_titles"]:
                pres["words"] = pres["content_titles"]
                pres["content_titles"] = []
            self.assign_keys(pres)
