from scripts.s3_cleaning.clean_bucket import CleanBucket


x = CleanBucket(aws_location="data_files/req_")
x.get_files_in_s3()
x.get_files_in_db()


x = CleanBucket(aws_location="data_files/")
x()

x = CleanBucket(aws_location="data_files/aws_errors")
x. excluded_dirs = []
x.get_files_in_s3()
x.report_orphans()
