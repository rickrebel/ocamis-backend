
def replace_petition_month_by_months_agency():
    from inai.models import Petition
    all_petitions = Petition.objects.all()
    for petition in all_petitions:
        month_agencies_ids = petition.petition_months.values_list(
            "month_record_id", flat=True)
        petition.month_records.set(month_agencies_ids)


def assign_provider_to_month_agency():
    from geo.models import Agency
    from inai.models import MonthRecord
    all_agencies = Agency.objects.all()
    for agency in all_agencies:
        provider = agency.provider
        if provider:
            month_agencies = MonthRecord.objects.filter(agency=agency)
            month_agencies.update(provider=provider)


def assign_year_month_to_sheet_files(provider_id):
    from respond.models import DataFile
    import re
    all_data_files = DataFile.objects.filter(provider_id=provider_id)
    regex_year_month = re.compile(r"_(20\d{4})")
    for data_file in all_data_files:
        file_name = data_file.file.url.split("/")[-1]
        year_month = regex_year_month.search(file_name)
        if year_month:
            year_month_str = year_month.group(1)
            year_month_str = year_month_str[:4] + "-" + year_month_str[4:]
            data_file.sheet_files.update(year_month=year_month_str)
        else:
            continue


def add_line_to_year_months():
    from inai.models import MonthRecord
    from respond.models import SheetFile
    all_year_months = MonthRecord.objects.values_list(
        "year_month", flat=True).distinct()
    for year_month in all_year_months:
        new_ym = year_month[:4] + "-" + year_month[4:]
        month_agencies = MonthRecord.objects.filter(year_month=year_month)
        month_agencies.update(year_month=new_ym)
        sheet_files = SheetFile.objects.filter(year_month=year_month)
        sheet_files.update(year_month=new_ym)


def assign_year_week_to_week_records():
    from respond.models import TableFile
    from inai.models import WeekRecord
    all_week_records = WeekRecord.objects.all()
    for week_record in all_week_records:
        iso_week = week_record.iso_week
        iso_year = week_record.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        week_record.year_week = year_week
        week_record.save()
    all_table_files = TableFile.objects.filter(iso_week__isnull=False)
    for table_file in all_table_files:
        iso_week = table_file.iso_week
        iso_year = table_file.iso_year
        year_week = f"{iso_year}-{iso_week:02d}"
        table_file.year_week = year_week
        table_file.save()


def assign_year_month_to_month_records():
    from inai.models import MonthRecord
    all_month_records = MonthRecord.objects.all()
    for month_record in all_month_records:
        year_month = month_record.year_month
        year, month = year_month.split("-")
        month_record.year = year
        month_record.month = month
        month_record.save()


def save_month_records():
    from inai.models import MonthRecord
    from respond.models import SheetFile
    all_sheet_files = SheetFile.objects.filter(
        month_records__isnull=True, year_month__isnull=False)
    for sheet_file in all_sheet_files:
        try:
            month_record = MonthRecord.objects.get(
                provider=sheet_file.data_file.provider, year_month=sheet_file.year_month)
            sheet_file.month_records.add(month_record)
        except MonthRecord.DoesNotExist:
            print("year_month does not exist", sheet_file.year_month)



