CREATE TABLE events (event_id integer primary key, event_name varchar(120) NOT NULL, event_value
varchar(256) NOT NULL);


SELECT aws_s3.table_import_from_s3(
'POSTGRES_TABLE_NAME', 'event_id,event_name,event_value', '(format csv, header true)',
'BUCKET_NAME',
'FOLDER_NAME(optional)/FILE_NAME',
'REGION',
'AWS_ACCESS_KEY', 'AWS_SECRET_KEY', 'OPTIONAL_SESSION_TOKEN'
)


CREATE TABLE events (event_id integer primary key, event_name varchar(120) NOT NULL, event_value varchar(256) NOT NULL);


SELECT aws_s3.table_import_from_s3(
'events', 'event_id,event_name,event_value', '(format csv, header true)',
'cdn-desabasto',
'data_files/example.csv',
'us-west-2',
'AKIAICSGL3ROH3GVALGQ', 'fFq7NwQyj/FmdtK/weXRwgrlEArkOatITD/mJYzL'
)

