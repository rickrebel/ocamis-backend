from scripts.s3_cleaning.clean_bucket import CleanBucket


x = CleanBucket(aws_location="data_files/")
x.excluded_dirs.append("catalog/")
x()

x = CleanBucket(aws_location="data_files/aws_errors")
x. excluded_dirs = []
x.get_files_in_s3()
x.report_orphans()
