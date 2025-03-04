import re
import time


class RegexFormat:
    limit_errors = 20

    def __init__(self, re_format, cases=None, case=None, new_value='',
                 measure_times=0):
        if isinstance(re_format, list):
            self.re_formats = re_format
        elif isinstance(re_format, str):
            print("Single format", re_format)
            formats = re_format.split("°")
            print("Formats", formats)
            self.re_formats = [re.compile(r_format) for r_format in formats]
        else:
            self.re_formats = [re_format]
        self.re_format = None
        if len(self.re_formats) == 1:
            self.re_format = self.re_formats[0]
        self.cases = [case] if case else cases
        self.new_value = new_value
        self.show_success = True
        self.show_errors = True
        self.errors_count = 0
        self.measure_times = measure_times

    def execute(self, action='is_match', new_value=None):
        for re_format in self.re_formats:
            start_time = time.time()
            print(f"\n----- {re_format} -----")
            self.errors_count = 0
            if action == 'is_match':
                if self.measure_times:
                    self.match_time(re_format, self.measure_times)
                else:
                    self.is_match(re_format)
            elif action == 'replace':
                self.replace(re_format, new_value)
            else:
                print("Action not found")
                break
            time_elapsed = time.time() - start_time
            print(f"Time elapsed: {time_elapsed}")

    def match_time(self, re_format, num_runs=1000):
        import timeit
        # run_time = timeit.timeit(my_function, number=num_runs)
        self.show_errors = False
        self.show_success = False
        run_time = timeit.timeit(lambda: self.is_match(re_format), number=num_runs)
        print(f"Time average: {run_time / num_runs}")

    def is_match(self, re_format):
        final_format = re_format or self.re_format
        many_errors = False
        for case in self.cases:
            if not many_errors:
                many_errors = self.errors_count > self.limit_errors
                if many_errors and self.show_errors:
                    print("Too many errors")
            # if self.show_errors and self.errors_count > self.limit_errors:
            #     print("Too many errors")
            #     break
            if not re.match(final_format, case):
                if self.show_errors and not many_errors:
                    print(f"No match: {case}")
                self.errors_count += 1
            elif self.show_success:
                print(f"Match: {case}")
        if not self.measure_times:
            print(f"Errors: {self.errors_count} of {len(self.cases)} cases")

    def replace(self, re_format, new_value=None):
        if new_value:
            self.new_value = new_value
        final_format = re_format or self.re_format
        for case in self.cases:
            re_format = re.compile(final_format)
            final_name = re.sub(re_format, self.new_value, case)
            print(f"{case} -> {final_name}")


def cie_10_codes(measure_times=0):
    all_codes = [
        "B449",
        "R568",
        "I10X",
        "M819",
        "K40K",
        "K746",
        "U071"
    ]
    keys_res = [
        re.compile(r'^[A-Z][0-9]{2}(?:\.?[0-9]{1,2})?$'),
        re.compile(r'^[A-Z][0-9]{2}(?:\.?[0-9]{1,2})?X?$'),
    ]

    regex_format = RegexFormat(keys_res, cases=all_codes, measure_times=measure_times)
    regex_format.execute(action='is_match')


# cie_10_codes(0)


def clues_chihuahua(measure_times=0):
    # from scripts.tests.regex_format import RegexFormat
    examples = [
        "CHSSA000664",
    ]
    keys_res = [
        re.compile(r'^[A-Z][^AEIOU](?:IMS|IST|SSA|IMO)\d{6}$'),
    ]
    regex_format = RegexFormat(keys_res, cases=examples, measure_times=measure_times)
    regex_format.execute(action='is_match')


def medicine_keys(measure_times=0):
    from scripts.tests.all_medicines import all_keys
    sep = r'[\.-]?'
    keys_res = [
        # re.compile(r'^\d?(\d{2}|HO|MH)[\.-]?\d{2,3}[\.-]?\d{4}[\.-]?\d{0,4}$'),
        # re.compile(r'^\d?\d{2}[\.-]?\d{3}[\.-]?\d{4}[\.-]?\d{0,4}$'),
        # re.compile(r'^(\d{2,3}[\.-]?\d{3}[\.-]?\d{4}'
        #            r'|HO[\.-]?\d{2}[\.-]?\d{2}'
        #            r'|MH[\.-]?\d{2}[\.-]?\d{4})[\.-]?\d{0,4}$'),
        # re.compile(r'^(\d{2,3}[\.-]?\d{2,4}[\.-]?\d{3,4}'
        #            r'|HO[\.-]?\d{2}[\.-]?\d{2}'
        #            r'|MH[\.-]?\d{2}[\.-]?\d{4})[\.-]?\d{0,4}$'),
        # re.compile(r'^('
        #            r'\d{2,3}[\.-]?\d{3}[\.-]?\d{4}[\.-]?\d{0,4}'
        #            r'|\d{3}[\.-]?\d{2,4}[\.-]?\d{3,4}'
        #            r'|HO[\.-]?\d{2}[\.-]?\d{2}[\.-]?\d{3}'
        #            r'|MH[\.-]?\d{2}[\.-]?\d{4}[\.-]?\d{0,4})$'),
        # re.compile(r'^('
        #            r'\d{2,3}[\.-]?\d{3}[\.-]?\d{4}[\.-]?\d{0,4}'
        #            r'|\d{3}[\.-]?\d{2,4}[\.-]?\d{4}'
        #            r'|060[\.-]?463[\.-]?164'
        #            r'|HO[\.-]?\d{2}[\.-]?\d{2}[\.-]?\d{3}'
        #            r'|MH[\.-]?\d{2}[\.-]?\d{4}[\.-]?\d{0,4})$'),
        re.compile(r'^('
                   r'0?[1|2|3|4][0|5][\.-]?\d{3}[\.-]?\d{4}[\.-]?0?\d{0,3}'
                   r'|\d{3}[\.-]?\d{2,4}[\.-]?\d{4}'
                   r'|060[\.-]?463[\.-]?164'
                   r'|HO[\.-]?\d{2}[\.-]?\d{2}[\.-]?\d{3}'
                   r'|MH[\.-]?\d{2}[\.-]?\d{4}[\.-]?\d{0,4})$'),
    ]

    seq_cases = [
        "123456",
        "1234567",
        "12345678",
        "123456789",
        "1234567890",
        "12345678901",
        "123456789012",
        "1234567890123",
        "12345678901234",
        "123456789012345",
        "1234567890123456",
    ]

    example_cases = [
        "010000650702",
        "10000650702",
        "10.000.6507.02",
        "35.157.0048",
        "130.258.0400",
        "606.908.0544",
        "010.000.6507.02",
        "010.000.6102.00"

        "060.463.164",  # 3 al final
        "535.15.0022",  # 2 en medio
        "513.9501.0119",  # 4 en medio
        "537.8057.2253",  # 4 en medio

        "HO.01.01.001",
        "HO.02.06.001",
        "MH.01.0001.00",
        "HO0101001",
        "MH010000100",
    ]
    # key_cases = all_keys + example_cases
    # key_cases = example_cases + seq_cases
    key_cases = seq_cases + all_keys

    regex_format = RegexFormat(
        keys_res, cases=key_cases, measure_times=measure_times)
    regex_format.show_success = False
    regex_format.show_errors = True
    regex_format.limit_errors = 200
    regex_format.execute(action='is_match')


# medicine_keys(0)


def init_examples():
    case_tests = [
        "UNIDAD DE MEDICINA FAMILIAR NO.",
        "UNIDAD DE MEDICINA FAMILIAR NO",
        "U MEDICA FAMILIAR",
    ]

    re_no_point = re.compile(r'(\sNO.?)$')
    regex_format = RegexFormat(re_no_point, cases=case_tests)
    # regex_format.replace()

    re_consul = re.compile(r'( CONSULTA MEDICINA FAMILIAR)')
    regex_format = RegexFormat(re_consul, cases=case_tests)
    # regex_format.replace(new_value='|CONSULTA MEDICINA FAMILIAR')


def inai_examples():
    import re
    example = '"cosas iniciales":"cosas iniciales","DescripcionSolicitud":"cosas "intermedias"","FechaRespuesta":"cosas finales"'
    second_pattern = r'^(.*?)"DescripcionSolicitud":"(.*?)","FechaRespuesta":"(.*)"$'
    second_pattern = re.compile(second_pattern)
    line_matches = second_pattern.findall(example)
    print(len(line_matches[0]))


def cofepris_codes(measure_times=0, from_file=False):
    # No match: 004H2015 SSA validar
    # No match: 019H2015 SSA validar
    # No match: 006P2016 SSA validar
    # No match: 007P2016 SSA validar
    # No match: 044m86 SSA
    # No match: 008RH2018 SSA validar
    # No match: 003P2018 SSA validar
    # No match: 009RH2018 SSA validar
    import json
    file_path = "C:/Users/Ricardo/dev/desabasto/slate3k_pdf_imss/media/cofepris_data.json"
    if from_file:
        examples = []
        with open(file_path, encoding="utf-8", mode="r") as file:
            all_keys = json.load(file)
        for key in all_keys:
            examples.append(key["Número de Registro:"])
    else:
        examples = [
            "001M84, SSA IV",
            "001M84, SSAIV",
            "004M2020 SSA",
            "293M2018 SSA",
            "003P96 SSA",
            # New examples for new regex
            "89570 SSA",
            "123M2012, SSA IV",
            "82231, SSA IV",
        ]
    keys_res = [
        # re.compile(r'^\d{3,4}[A-Z]\d{2,4}(?:,? SSA)?\s?(?:IV)?$'),
        # new regex
        # re.compile(r'^(0?\d{2,4}/?[RV]?[A-Z]/?\d{2,4}|\d{3,5})\s?(?:,?SSA)?\s?(?:IV)?$'),
        re.compile(r'^(0?\d{2,4}/?[RV]?[A-Z]/?\d{2,4}|\d{3,5}(NF)?)[\s|,]{0,3}(SSA)\s?(?:IV)?$'),
        re.compile(r'^(0?\d{2,4}/?[RV]?[A-Z]/?\d{2,4}|\d{3,5}(NF)?)[\s|,]{0,3}(SSA)\s?(?:[IV]{1,3})?$'),
        # re.compile(r'^\d{3,4}[A-Z]\d{2,4}\s?(?:,?SSA)?\s?(?:IV)?$'),
    ]
    regex_format = RegexFormat(keys_res, cases=examples, measure_times=measure_times)
    # regex_format.show_success = False
    regex_format.execute(action='is_match')


cofepris_codes(0, False)
