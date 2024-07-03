create sequence catalog_delegation_id_seq
    as integer;

alter sequence catalog_delegation_id_seq owner to user_desabasto;

create sequence catalog_entity_id_seq
    as integer;

alter sequence catalog_entity_id_seq owner to user_desabasto;

create sequence catalog_jurisdiction_id_seq;

alter sequence catalog_jurisdiction_id_seq owner to user_desabasto;

create sequence catalog_municipality_id_seq
    as integer;

alter sequence catalog_municipality_id_seq owner to user_desabasto;

create sequence catalog_tipology_id_seq
    as integer;

alter sequence catalog_tipology_id_seq owner to user_desabasto;

create sequence category_anomaly_id_seq
    as integer;

alter sequence category_anomaly_id_seq owner to user_desabasto;

create sequence category_statuscontrol_id_seq
    as integer;

alter sequence category_statuscontrol_id_seq owner to user_desabasto;

create sequence category_transparencyindex_id_seq
    as integer;

alter sequence category_transparencyindex_id_seq owner to user_desabasto;

create sequence category_transparencylevel_anomalies_id_seq
    as integer;

alter sequence category_transparencylevel_anomalies_id_seq owner to user_desabasto;

create sequence category_transparencylevel_file_formats_id_seq
    as integer;

alter sequence category_transparencylevel_file_formats_id_seq owner to user_desabasto;

create sequence category_transparencylevel_id_seq
    as integer;

alter sequence category_transparencylevel_id_seq owner to user_desabasto;

create sequence data_param_cleanfunction_id_seq
    as integer;

alter sequence data_param_cleanfunction_id_seq owner to user_desabasto;

create sequence desabasto_clues_id_seq
    as integer;

alter sequence desabasto_clues_id_seq owner to user_desabasto;

create sequence desabasto_institution_id_seq
    as integer;

alter sequence desabasto_institution_id_seq owner to user_desabasto;

create sequence inai_filecontrol_anomalies_id_seq
    as integer;

alter sequence inai_filecontrol_anomalies_id_seq owner to user_desabasto;

create sequence inai_filecontrol_id_seq
    as integer;

alter sequence inai_filecontrol_id_seq owner to user_desabasto;

create sequence inai_monthentity_id_seq
    as integer;

alter sequence inai_monthentity_id_seq owner to user_desabasto;

create sequence inai_namecolumn_id_seq
    as integer;

alter sequence inai_namecolumn_id_seq owner to user_desabasto;

create sequence inai_petition_months_agency_id_seq;

alter sequence inai_petition_months_agency_id_seq owner to user_yeeko;

create sequence inai_transformation_id_seq
    as integer;

alter sequence inai_transformation_id_seq owner to user_desabasto;

create sequence report_reportcovid_id_seq
    as integer;

alter sequence report_reportcovid_id_seq owner to user_desabasto;

create table if not exists auth_group
(
    id   serial
        primary key,
    name varchar(150) not null
        unique
);

alter table auth_group
    owner to user_desabasto;

create index if not exists auth_group_name_a6ea08ec_like
    on auth_group (name varchar_pattern_ops);

create table if not exists auth_user
(
    id           serial
        primary key,
    password     varchar(128)             not null,
    last_login   timestamp with time zone,
    is_superuser boolean                  not null,
    username     varchar(150)             not null
        unique,
    first_name   varchar(150)             not null,
    last_name    varchar(150)             not null,
    email        varchar(254)             not null,
    is_staff     boolean                  not null,
    is_active    boolean                  not null,
    date_joined  timestamp with time zone not null
);

alter table auth_user
    owner to user_desabasto;

create index if not exists auth_user_username_6821ab7c_like
    on auth_user (username varchar_pattern_ops);

create table if not exists auth_user_groups
(
    id       serial
        primary key,
    user_id  integer not null
        constraint auth_user_groups_user_id_6a12ed8b_fk_auth_user_id
            references auth_user
            deferrable initially deferred,
    group_id integer not null
        constraint auth_user_groups_group_id_97559544_fk_auth_group_id
            references auth_group
            deferrable initially deferred,
    constraint auth_user_groups_user_id_group_id_94350c0c_uniq
        unique (user_id, group_id)
);

alter table auth_user_groups
    owner to user_desabasto;

create index if not exists auth_user_groups_group_id_97559544
    on auth_user_groups (group_id);

create index if not exists auth_user_groups_user_id_6a12ed8b
    on auth_user_groups (user_id);

create table if not exists authtoken_token
(
    key     varchar(40)              not null
        primary key,
    created timestamp with time zone not null,
    user_id integer                  not null
        unique
        constraint authtoken_token_user_id_35299eff_fk_auth_user_id
            references auth_user
            deferrable initially deferred
);

alter table authtoken_token
    owner to user_desabasto;

create index if not exists authtoken_token_key_10f0b77e_like
    on authtoken_token (key varchar_pattern_ops);

create table if not exists geo_typology
(
    id                integer default nextval('catalog_tipology_id_seq'::regclass) not null
        constraint catalog_tipology_pkey
            primary key,
    clave             varchar(50)                                                  not null,
    name              varchar(255)                                                 not null,
    public_name       varchar(255),
    alternative_names jsonb,
    aggregate_to_id   integer
        constraint catalog_typology_aggregate_to_id_35cf4cf2_fk_catalog_t
            references geo_typology
            deferrable initially deferred,
    is_aggregate      boolean
);

alter table geo_typology
    owner to user_desabasto;

alter sequence catalog_tipology_id_seq owned by geo_typology.id;

create index if not exists catalog_typology_aggregate_to_id_35cf4cf2
    on geo_typology (aggregate_to_id);

create table if not exists transparency_anomaly
(
    id            integer default nextval('category_anomaly_id_seq'::regclass) not null
        constraint category_anomaly_pkey
            primary key,
    public_name   varchar(255)                                                 not null,
    name          varchar(25)                                                  not null,
    is_public     boolean                                                      not null,
    description   text,
    icon          varchar(20),
    "order"       integer                                                      not null,
    color         varchar(30),
    is_calculated boolean                                                      not null
);

alter table transparency_anomaly
    owner to user_desabasto;

alter sequence category_anomaly_id_seq owned by transparency_anomaly.id;

create table if not exists category_columntype
(
    id          serial
        primary key,
    name        varchar(80) not null,
    public_name varchar(120),
    description text,
    "order"     integer     not null
);

alter table category_columntype
    owner to user_desabasto;

create table if not exists category_datebreak
(
    id           serial
        primary key,
    name         varchar(50)  not null,
    public_name  varchar(120) not null,
    "order"      integer      not null,
    break_params jsonb,
    "group"      varchar(10)  not null
);

alter table category_datebreak
    owner to user_desabasto;

create table if not exists category_fileformat
(
    id          serial
        primary key,
    short_name  varchar(20) not null,
    public_name varchar(80) not null,
    suffixes    jsonb,
    readable    boolean     not null,
    addl_params jsonb       not null,
    "order"     integer     not null
);

alter table category_fileformat
    owner to user_desabasto;

create table if not exists category_filetype
(
    name        varchar(255) not null
        constraint category_filetype_name_12a49012_pk
            primary key,
    description text,
    is_default  boolean      not null,
    has_data    boolean      not null,
    is_original boolean      not null,
    "order"     integer      not null,
    addl_params jsonb,
    color       varchar(20),
    "group"     varchar(10)  not null,
    public_name varchar(255)
);

alter table category_filetype
    owner to user_desabasto;

create index if not exists category_filetype_name_12a49012_like
    on category_filetype (name varchar_pattern_ops);

create table if not exists category_invalidreason
(
    id          serial
        primary key,
    name        varchar(120) not null,
    description text
);

alter table category_invalidreason
    owner to user_desabasto;

create table if not exists category_negativereason
(
    id          serial
        primary key,
    name        varchar(120) not null,
    description text
);

alter table category_negativereason
    owner to user_desabasto;

create table if not exists category_statuscontrol
(
    id          integer default nextval('category_statuscontrol_id_seq'::regclass) not null
        primary key,
    "group"     varchar(10)                                                        not null,
    name        varchar(120)                                                       not null,
    public_name varchar(255)                                                       not null,
    color       varchar(30),
    icon        varchar(20),
    description text,
    addl_params jsonb,
    "order"     integer                                                            not null
);

alter table category_statuscontrol
    owner to user_desabasto;

create table if not exists transparency_transparencyindex
(
    id           integer default nextval('category_transparencyindex_id_seq'::regclass) not null
        constraint category_transparencyindex_pkey
            primary key,
    short_name   varchar(20)                                                            not null,
    public_name  varchar(80)                                                            not null,
    description  text,
    scheme_color varchar(90),
    viz_params   jsonb                                                                  not null,
    order_viz    integer                                                                not null
);

alter table transparency_transparencyindex
    owner to user_desabasto;

alter sequence category_transparencyindex_id_seq owned by transparency_transparencyindex.id;

create table if not exists transparency_transparencylevel
(
    id                    integer default nextval('category_transparencylevel_id_seq'::regclass) not null
        constraint category_transparencylevel_pkey
            primary key,
    short_name            varchar(20)                                                            not null,
    public_name           varchar(80)                                                            not null,
    value                 integer                                                                not null,
    description           text,
    other_conditions      jsonb                                                                  not null,
    color                 varchar(20),
    final_level_id        integer
        constraint category_transparenc_final_level_id_ddb12f1e_fk_category_
            references transparency_transparencylevel
            deferrable initially deferred,
    transparency_index_id bigint                                                                 not null
        constraint transparency_transpa_transparency_index_i_9be9a099_fk_transpare
            references transparency_transparencyindex
            deferrable initially deferred,
    order_viz             integer                                                                not null,
    value_ctrls           integer                                                                not null,
    value_pets            integer                                                                not null,
    viz_params            jsonb                                                                  not null,
    is_default            boolean                                                                not null
);

alter table transparency_transparencylevel
    owner to user_desabasto;

alter sequence category_transparencylevel_id_seq owned by transparency_transparencylevel.id;

create table if not exists transparency_transparencylevel_anomalies
(
    id                   integer default nextval('category_transparencylevel_anomalies_id_seq'::regclass) not null
        constraint category_transparencylevel_anomalies_pkey
            primary key,
    transparencylevel_id integer                                                                          not null
        constraint category_transparenc_transparencylevel_id_5d65cf0d_fk_category_
            references transparency_transparencylevel
            deferrable initially deferred,
    anomaly_id           integer                                                                          not null
        constraint category_transparenc_anomaly_id_1ef70b12_fk_category_
            references transparency_anomaly
            deferrable initially deferred,
    constraint category_transparencylev_transparencylevel_id_ano_5a13665e_uniq
        unique (transparencylevel_id, anomaly_id)
);

alter table transparency_transparencylevel_anomalies
    owner to user_desabasto;

alter sequence category_transparencylevel_anomalies_id_seq owned by transparency_transparencylevel_anomalies.id;

create index if not exists category_transparencylevel_anomalies_anomaly_id_1ef70b12
    on transparency_transparencylevel_anomalies (anomaly_id);

create index if not exists category_transparencylevel_transparencylevel_id_5d65cf0d
    on transparency_transparencylevel_anomalies (transparencylevel_id);

create table if not exists transparency_transparencylevel_file_formats
(
    id                   integer default nextval('category_transparencylevel_file_formats_id_seq'::regclass) not null
        constraint category_transparencylevel_file_formats_pkey
            primary key,
    transparencylevel_id integer                                                                             not null
        constraint category_transparenc_transparencylevel_id_5f339cbc_fk_category_
            references transparency_transparencylevel
            deferrable initially deferred,
    fileformat_id        integer                                                                             not null
        constraint category_transparenc_fileformat_id_db36ecbe_fk_category_
            references category_fileformat
            deferrable initially deferred,
    constraint category_transparencylev_transparencylevel_id_fil_55bd3f2a_uniq
        unique (transparencylevel_id, fileformat_id)
);

alter table transparency_transparencylevel_file_formats
    owner to user_desabasto;

alter sequence category_transparencylevel_file_formats_id_seq owned by transparency_transparencylevel_file_formats.id;

create index if not exists category_transparencylevel_file_formats_fileformat_id_db36ecbe
    on transparency_transparencylevel_file_formats (fileformat_id);

create index if not exists category_transparencylevel_transparencylevel_id_5f339cbc
    on transparency_transparencylevel_file_formats (transparencylevel_id);

create index if not exists category_transparencylevel_final_level_id_ddb12f1e
    on transparency_transparencylevel (final_level_id);

create index if not exists transparency_transparencylevel_transparency_index_id_9be9a099
    on transparency_transparencylevel (transparency_index_id);

create table if not exists classify_task_statustask
(
    name         varchar(80) not null
        primary key,
    public_name  varchar(120),
    description  text,
    "order"      integer     not null,
    icon         varchar(30),
    color        varchar(30),
    is_completed boolean     not null,
    macro_status varchar(30)
);

alter table classify_task_statustask
    owner to user_desabasto;

create index if not exists classify_task_statustask_name_608b5fd2_like
    on classify_task_statustask (name varchar_pattern_ops);

create table if not exists classify_task_taskfunction
(
    name         varchar(100) not null
        primary key,
    model_name   varchar(100),
    public_name  varchar(120),
    is_active    boolean      not null,
    is_from_aws  boolean      not null,
    is_queueable boolean      not null
);

alter table classify_task_taskfunction
    owner to user_desabasto;

create table if not exists classify_task_stage
(
    name             varchar(80)  not null
        primary key,
    public_name      varchar(120) not null,
    description      text,
    "order"          integer      not null,
    icon             varchar(30),
    main_function_id varchar(100)
        constraint classify_task_stage_main_function_id_1695d403_fk_classify_
            references classify_task_taskfunction
            deferrable initially deferred,
    next_stage_id    varchar(80)
        unique
        constraint classify_task_stage_next_stage_id_fa38a3f0_fk_classify_
            references classify_task_stage
            deferrable initially deferred,
    action_text      varchar(120)
);

alter table classify_task_stage
    owner to user_desabasto;

create index if not exists classify_task_stage_name_f117f402_like
    on classify_task_stage (name varchar_pattern_ops);

create index if not exists classify_task_stage_next_stage_id_fa38a3f0_like
    on classify_task_stage (next_stage_id varchar_pattern_ops);

create index if not exists classify_task_stage_retry_function_id_a653b62e
    on classify_task_stage (main_function_id);

create index if not exists classify_task_stage_retry_function_id_a653b62e_like
    on classify_task_stage (main_function_id varchar_pattern_ops);

create table if not exists classify_task_stage_available_next_stages
(
    id            integer generated by default as identity
        primary key,
    from_stage_id varchar(80) not null
        constraint classify_task_stage__from_stage_id_70cd69a8_fk_classify_
            references classify_task_stage
            deferrable initially deferred,
    to_stage_id   varchar(80) not null
        constraint classify_task_stage__to_stage_id_2dedc5ee_fk_classify_
            references classify_task_stage
            deferrable initially deferred,
    constraint classify_task_stage_avai_from_stage_id_to_stage_i_d9489518_uniq
        unique (from_stage_id, to_stage_id)
);

alter table classify_task_stage_available_next_stages
    owner to user_desabasto;

create index if not exists classify_task_stage_avai_from_stage_id_70cd69a8_like
    on classify_task_stage_available_next_stages (from_stage_id varchar_pattern_ops);

create index if not exists classify_task_stage_avai_to_stage_id_2dedc5ee_like
    on classify_task_stage_available_next_stages (to_stage_id varchar_pattern_ops);

create index if not exists classify_task_stage_availa_from_stage_id_70cd69a8
    on classify_task_stage_available_next_stages (from_stage_id);

create index if not exists classify_task_stage_available_next_stages_to_stage_id_2dedc5ee
    on classify_task_stage_available_next_stages (to_stage_id);

create table if not exists classify_task_stage_re_process_stages
(
    id            integer generated by default as identity
        primary key,
    from_stage_id varchar(80) not null
        constraint classify_task_stage__from_stage_id_1c6ae89d_fk_classify_
            references classify_task_stage
            deferrable initially deferred,
    to_stage_id   varchar(80) not null
        constraint classify_task_stage__to_stage_id_0315b599_fk_classify_
            references classify_task_stage
            deferrable initially deferred,
    constraint classify_task_stage_re_p_from_stage_id_to_stage_i_abcf343b_uniq
        unique (from_stage_id, to_stage_id)
);

alter table classify_task_stage_re_process_stages
    owner to user_desabasto;

create index if not exists classify_task_stage_re_p_from_stage_id_1c6ae89d_like
    on classify_task_stage_re_process_stages (from_stage_id varchar_pattern_ops);

create index if not exists classify_task_stage_re_process_stages_from_stage_id_1c6ae89d
    on classify_task_stage_re_process_stages (from_stage_id);

create index if not exists classify_task_stage_re_process_stages_to_stage_id_0315b599
    on classify_task_stage_re_process_stages (to_stage_id);

create index if not exists classify_task_stage_re_process_stages_to_stage_id_0315b599_like
    on classify_task_stage_re_process_stages (to_stage_id varchar_pattern_ops);

create index if not exists classify_task_taskfunction_name_229c8352_like
    on classify_task_taskfunction (name varchar_pattern_ops);

create table if not exists data_param_datagroup
(
    id              serial
        primary key,
    public_name     varchar(80) not null,
    is_default      boolean     not null,
    can_has_percent boolean     not null,
    color           varchar(20) not null,
    name            varchar(40),
    "order"         integer     not null
);

alter table data_param_datagroup
    owner to user_desabasto;

create table if not exists data_param_collection
(
    id             serial
        primary key,
    name           varchar(225) not null,
    model_name     varchar(225) not null,
    description    text,
    data_group_id  integer      not null
        constraint data_param_collectio_data_group_id_134c04bd_fk_data_para
            references data_param_datagroup
            deferrable initially deferred,
    cat_params     jsonb        not null,
    open_insertion boolean      not null,
    app_label      varchar(40)  not null,
    snake_name     varchar(225) not null
);

alter table data_param_collection
    owner to user_desabasto;

create index if not exists data_param_collection_data_group_id_134c04bd
    on data_param_collection (data_group_id);

create table if not exists data_param_datatype
(
    id          serial
        primary key,
    name        varchar(50) not null,
    description text,
    addl_params jsonb       not null,
    is_common   boolean     not null,
    "order"     integer     not null,
    public_name varchar(225)
);

alter table data_param_datatype
    owner to user_desabasto;

create table if not exists data_param_parametergroup
(
    id            serial
        primary key,
    name          varchar(120) not null,
    description   text,
    data_group_id integer      not null
        constraint data_param_parameter_data_group_id_4960ae25_fk_data_para
            references data_param_datagroup
            deferrable initially deferred
);

alter table data_param_parametergroup
    owner to user_desabasto;

create table if not exists data_param_finalfield
(
    id                 serial
        primary key,
    name               varchar(120) not null,
    verbose_name       varchar(255),
    addl_params        jsonb,
    is_required        boolean      not null,
    is_common          boolean      not null,
    verified           boolean      not null,
    collection_id      integer      not null
        constraint data_param_finalfiel_collection_id_48465136_fk_data_para
            references data_param_collection
            deferrable initially deferred,
    data_type_id       integer
        constraint data_param_finalfiel_data_type_id_c59c4a89_fk_data_para
            references data_param_datatype
            deferrable initially deferred,
    dashboard_hide     boolean      not null,
    in_data_base       boolean      not null,
    variations         jsonb,
    parameter_group_id integer
        constraint data_param_finalfiel_parameter_group_id_8ae951d8_fk_data_para
            references data_param_parametergroup
            deferrable initially deferred,
    need_for_viz       boolean      not null,
    is_unique          boolean      not null,
    regex_format       varchar(255),
    match_use          varchar(16),
    included_code      varchar(12)  not null
);

alter table data_param_finalfield
    owner to user_desabasto;

create table if not exists data_param_cleanfunction
(
    id                  integer default nextval('data_param_cleanfunction_id_seq'::regclass) not null
        primary key,
    name                varchar(80)                                                          not null,
    public_name         varchar(120),
    description         text,
    priority            smallint                                                             not null,
    for_all_data        boolean                                                              not null,
    addl_params         jsonb,
    restricted_field_id integer
        constraint data_param_cleanfunc_restricted_field_id_8337d749_fk_data_para
            references data_param_finalfield
            deferrable initially deferred,
    column_type_id      integer
        constraint data_param_cleanfunc_column_type_id_8587f41a_fk_category_
            references category_columntype
            deferrable initially deferred,
    ready_code          varchar(12)                                                          not null
);

alter table data_param_cleanfunction
    owner to user_desabasto;

create index if not exists data_param_cleanfunction_column_type_id_8587f41a
    on data_param_cleanfunction (column_type_id);

create index if not exists data_param_cleanfunction_restricted_field_id_8337d749
    on data_param_cleanfunction (restricted_field_id);

create index if not exists data_param_finalfield_collection_id_48465136
    on data_param_finalfield (collection_id);

create index if not exists data_param_finalfield_data_type_id_c59c4a89
    on data_param_finalfield (data_type_id);

create index if not exists data_param_finalfield_parameter_group_id_8ae951d8
    on data_param_finalfield (parameter_group_id);

create index if not exists data_param_parametergroup_data_group_id_4960ae25
    on data_param_parametergroup (data_group_id);

create table if not exists desabasto_alliances
(
    id        serial
        primary key,
    name      varchar(180) not null,
    page_url  varchar(180),
    logo      varchar(100) not null,
    level     integer      not null,
    email     varchar(255),
    page_help varchar(255),
    phone     varchar(255)
);

alter table desabasto_alliances
    owner to user_desabasto;

create table if not exists desabasto_disease
(
    id   serial
        primary key,
    name varchar(50) not null
);

alter table desabasto_disease
    owner to user_desabasto;

create table if not exists desabasto_alliances_diseases_litigation
(
    id           serial
        primary key,
    alliances_id integer not null
        constraint desabasto_alliances__alliances_id_2bb603c8_fk_desabasto
            references desabasto_alliances
            deferrable initially deferred,
    disease_id   integer not null
        constraint desabasto_alliances__disease_id_7e185c9c_fk_desabasto
            references desabasto_disease
            deferrable initially deferred,
    constraint desabasto_alliances_dise_alliances_id_disease_id_e3599f07_uniq
        unique (alliances_id, disease_id)
);

alter table desabasto_alliances_diseases_litigation
    owner to user_desabasto;

create index if not exists desabasto_alliances_diseases_litigation_alliances_id_2bb603c8
    on desabasto_alliances_diseases_litigation (alliances_id);

create index if not exists desabasto_alliances_diseases_litigation_disease_id_7e185c9c
    on desabasto_alliances_diseases_litigation (disease_id);

create table if not exists desabasto_alliances_diseases_management
(
    id           serial
        primary key,
    alliances_id integer not null
        constraint desabasto_alliances__alliances_id_adafdefc_fk_desabasto
            references desabasto_alliances
            deferrable initially deferred,
    disease_id   integer not null
        constraint desabasto_alliances__disease_id_74477bca_fk_desabasto
            references desabasto_disease
            deferrable initially deferred,
    constraint desabasto_alliances_dise_alliances_id_disease_id_ae555ca2_uniq
        unique (alliances_id, disease_id)
);

alter table desabasto_alliances_diseases_management
    owner to user_desabasto;

create index if not exists desabasto_alliances_diseases_management_alliances_id_adafdefc
    on desabasto_alliances_diseases_management (alliances_id);

create index if not exists desabasto_alliances_diseases_management_disease_id_74477bca
    on desabasto_alliances_diseases_management (disease_id);

create table if not exists desabasto_group
(
    id     serial
        primary key,
    name   varchar(255) not null,
    number integer
);

alter table desabasto_group
    owner to user_desabasto;

create table if not exists desabasto_component
(
    id                 serial
        primary key,
    name               varchar(255) not null,
    short_name         varchar(255),
    alias              varchar(255),
    presentation_count integer      not null,
    frequency          integer,
    group_id           integer
        constraint desabasto_component_group_id_f41fa428_fk_desabasto_group_id
            references desabasto_group
            deferrable initially deferred,
    presentations_raw  text,
    origen_cvmei       boolean      not null,
    is_relevant        boolean      not null,
    is_vaccine         boolean      not null,
    medicine_type      varchar(255)
);

alter table desabasto_component
    owner to user_desabasto;

create index if not exists desabasto_component_group_id_f41fa428
    on desabasto_component (group_id);

create table if not exists geo_institution
(
    id          integer default nextval('desabasto_institution_id_seq'::regclass) not null
        constraint desabasto_institution_pkey
            primary key,
    name        varchar(255)                                                      not null,
    code        varchar(20)                                                       not null,
    public_name varchar(255),
    public_code varchar(20),
    relevance   integer                                                           not null
);

alter table geo_institution
    owner to user_desabasto;

alter sequence desabasto_institution_id_seq owned by geo_institution.id;

create table if not exists desabasto_presentationtype
(
    id                 serial
        primary key,
    name               varchar(255) not null,
    common_name        varchar(255),
    alias              varchar(255),
    presentation_count integer      not null,
    agrupated_in_id    integer
        constraint desabasto_presentati_agrupated_in_id_67252b42_fk_desabasto
            references desabasto_presentationtype
            deferrable initially deferred,
    origen_cvmei       boolean      not null
);

alter table desabasto_presentationtype
    owner to user_desabasto;

create table if not exists desabasto_presentation
(
    id                    serial
        primary key,
    component_id          integer not null
        constraint desabasto_presentati_component_id_8ba98148_fk_desabasto
            references desabasto_component
            deferrable initially deferred,
    presentation_type_id  integer
        constraint desabasto_presentati_presentation_type_id_d49dc5f0_fk_desabasto
            references desabasto_presentationtype
            deferrable initially deferred,
    description           text,
    presentation_type_raw varchar(255),
    clave                 varchar(20),
    official_name         text,
    official_attributes   text,
    short_attributes      text,
    origen_cvmei          boolean not null,
    group_id              integer
        constraint desabasto_presentation_group_id_614d45af_fk_desabasto_group_id
            references desabasto_group
            deferrable initially deferred
);

alter table desabasto_presentation
    owner to user_desabasto;

create table if not exists desabasto_container
(
    id              serial
        primary key,
    presentation_id integer
        constraint desabasto_container_presentation_id_0e4b75c5_fk_desabasto
            references desabasto_presentation
            deferrable initially deferred,
    name            text        not null,
    key             varchar(20) not null,
    key2            varchar(20),
    is_current      boolean,
    short_name      text,
    origen_cvmei    boolean
);

alter table desabasto_container
    owner to user_desabasto;

create index if not exists desabasto_container_presentation_id_0e4b75c5
    on desabasto_container (presentation_id);

create index if not exists desabasto_presentation_component_id_8ba98148
    on desabasto_presentation (component_id);

create index if not exists desabasto_presentation_group_id_614d45af
    on desabasto_presentation (group_id);

create index if not exists desabasto_presentation_presentation_type_id_d49dc5f0
    on desabasto_presentation (presentation_type_id);

create index if not exists desabasto_presentationtype_agrupated_in_id_67252b42
    on desabasto_presentationtype (agrupated_in_id);

create table if not exists desabasto_state
(
    id                serial
        primary key,
    inegi_code        varchar(2)  not null,
    name              varchar(50) not null,
    short_name        varchar(20),
    code_name         varchar(6),
    other_names       varchar(255),
    alternative_names jsonb       not null
);

alter table desabasto_state
    owner to user_desabasto;

create table if not exists geo_jurisdiction
(
    id             integer generated by default as identity
        constraint catalog_jurisdiction_pkey
            primary key,
    name           varchar(255) not null,
    key            varchar(50)  not null,
    institution_id integer      not null
        constraint catalog_jurisdiction_institution_id_4f9ecb3e_fk_desabasto
            references geo_institution
            deferrable initially deferred,
    state_id       integer      not null
        constraint catalog_jurisdiction_state_id_3ed5b9ad_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred
);

alter table geo_jurisdiction
    owner to user_desabasto;

alter sequence catalog_jurisdiction_id_seq owned by geo_jurisdiction.id;

create index if not exists catalog_jurisdiction_institution_id_4f9ecb3e
    on geo_jurisdiction (institution_id);

create index if not exists catalog_jurisdiction_state_id_3ed5b9ad
    on geo_jurisdiction (state_id);

create table if not exists geo_municipality
(
    id         integer default nextval('catalog_municipality_id_seq'::regclass) not null
        constraint catalog_municipality_pkey
            primary key,
    inegi_code varchar(6)                                                       not null,
    name       varchar(120)                                                     not null,
    state_id   integer
        constraint catalog_municipality_state_id_8f05caae_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred
);

alter table geo_municipality
    owner to user_desabasto;

alter sequence catalog_municipality_id_seq owned by geo_municipality.id;

create index if not exists catalog_municipality_state_id_8f05caae
    on geo_municipality (state_id);

create table if not exists django_content_type
(
    id        serial
        primary key,
    app_label varchar(100) not null,
    model     varchar(100) not null,
    constraint django_content_type_app_label_model_76bd3d3b_uniq
        unique (app_label, model)
);

alter table django_content_type
    owner to user_desabasto;

create table if not exists auth_permission
(
    id              serial
        primary key,
    name            varchar(255) not null,
    content_type_id integer      not null
        constraint auth_permission_content_type_id_2f476e4b_fk_django_co
            references django_content_type
            deferrable initially deferred,
    codename        varchar(100) not null,
    constraint auth_permission_content_type_id_codename_01ab375a_uniq
        unique (content_type_id, codename)
);

alter table auth_permission
    owner to user_desabasto;

create table if not exists auth_group_permissions
(
    id            serial
        primary key,
    group_id      integer not null
        constraint auth_group_permissions_group_id_b120cbf9_fk_auth_group_id
            references auth_group
            deferrable initially deferred,
    permission_id integer not null
        constraint auth_group_permissio_permission_id_84c5c92e_fk_auth_perm
            references auth_permission
            deferrable initially deferred,
    constraint auth_group_permissions_group_id_permission_id_0cd325b0_uniq
        unique (group_id, permission_id)
);

alter table auth_group_permissions
    owner to user_desabasto;

create index if not exists auth_group_permissions_group_id_b120cbf9
    on auth_group_permissions (group_id);

create index if not exists auth_group_permissions_permission_id_84c5c92e
    on auth_group_permissions (permission_id);

create index if not exists auth_permission_content_type_id_2f476e4b
    on auth_permission (content_type_id);

create table if not exists auth_user_user_permissions
(
    id            serial
        primary key,
    user_id       integer not null
        constraint auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id
            references auth_user
            deferrable initially deferred,
    permission_id integer not null
        constraint auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm
            references auth_permission
            deferrable initially deferred,
    constraint auth_user_user_permissions_user_id_permission_id_14a6b632_uniq
        unique (user_id, permission_id)
);

alter table auth_user_user_permissions
    owner to user_desabasto;

create index if not exists auth_user_user_permissions_permission_id_1fbb5f2c
    on auth_user_user_permissions (permission_id);

create index if not exists auth_user_user_permissions_user_id_a95ead1b
    on auth_user_user_permissions (user_id);

create table if not exists django_admin_log
(
    id              serial
        primary key,
    action_time     timestamp with time zone not null,
    object_id       text,
    object_repr     varchar(200)             not null,
    action_flag     smallint                 not null
        constraint django_admin_log_action_flag_check
            check (action_flag >= 0),
    change_message  text                     not null,
    content_type_id integer
        constraint django_admin_log_content_type_id_c4bce8eb_fk_django_co
            references django_content_type
            deferrable initially deferred,
    user_id         integer                  not null
        constraint django_admin_log_user_id_c564eba6_fk_auth_user_id
            references auth_user
            deferrable initially deferred
);

alter table django_admin_log
    owner to user_desabasto;

create index if not exists django_admin_log_content_type_id_c4bce8eb
    on django_admin_log (content_type_id);

create index if not exists django_admin_log_user_id_c564eba6
    on django_admin_log (user_id);

create table if not exists django_migrations
(
    id      serial
        primary key,
    app     varchar(255)             not null,
    name    varchar(255)             not null,
    applied timestamp with time zone not null
);

alter table django_migrations
    owner to user_desabasto;

create table if not exists django_session
(
    session_key  varchar(40)              not null
        primary key,
    session_data text                     not null,
    expire_date  timestamp with time zone not null
);

alter table django_session
    owner to user_desabasto;

create index if not exists django_session_expire_date_a5c62663
    on django_session (expire_date);

create index if not exists django_session_session_key_c0390e0f_like
    on django_session (session_key varchar_pattern_ops);

create table if not exists formula_drug
(
    uuid              uuid    not null,
    prescribed_amount smallint,
    delivered_amount  smallint,
    price             double precision,
    row_seq           integer,
    rx_id             uuid    not null,
    sheet_file        integer not null,
    delivered_id      varchar(32),
    medicament_id     varchar(32),
    lap_sheet_id      integer not null,
    date_closed       timestamp with time zone,
    date_created      timestamp with time zone
);

alter table formula_drug
    owner to user_desabasto;

create table if not exists formula_rx
(
    uuid_folio         uuid        not null,
    folio_ocamis       varchar(64) not null,
    folio_document     varchar(46) not null,
    iso_year           smallint    not null,
    iso_week           smallint    not null,
    iso_day            smallint,
    date_release       timestamp with time zone,
    date_delivery      timestamp with time zone,
    date_visit         timestamp with time zone,
    month              smallint    not null,
    document_type      varchar(50),
    entity_id          integer     not null,
    area_id            varchar(32),
    delivered_final_id varchar(32),
    diagnosis_id       varchar(32),
    doctor_id          varchar(32),
    medical_unit_id    varchar(32),
    year               smallint
        constraint formula_rx_year_check
            check (year >= 0),
    iso_delegation     smallint
        constraint formula_rx_iso_delegation_check
            check (iso_delegation >= 0)
);

alter table formula_rx
    owner to user_desabasto;

create table if not exists email_sendgrid_sendgridprofile
(
    id               serial
        primary key,
    name             varchar(200) not null
        unique,
    sendgrid_api_key varchar(255) not null,
    webhook_slug     varchar(255),
    from_email       varchar(100) not null,
    "default"        boolean      not null,
    test_emails      varchar(255),
    test_mode        boolean      not null
);

alter table email_sendgrid_sendgridprofile
    owner to user_desabasto;

create index if not exists email_sendgrid_sendgridprofile_name_57e2ed3e_like
    on email_sendgrid_sendgridprofile (name varchar_pattern_ops);

create table if not exists events
(
    event_id    integer      not null
        primary key,
    event_name  varchar(120) not null,
    event_value varchar(256) not null
);

alter table events
    owner to user_desabasto;

create table if not exists formula_documenttype
(
    name varchar(50) not null
);

alter table formula_documenttype
    owner to user_desabasto;

create table if not exists formula_medicalspeciality
(
    id   integer generated by default as identity,
    name varchar(255) not null
);

alter table formula_medicalspeciality
    owner to user_desabasto;

create table if not exists formula_missingfield
(
    uuid           uuid                     not null,
    original_value text,
    final_value    text,
    other_values   jsonb,
    missing_row_id uuid                     not null,
    name_column_id integer                  not null,
    error          text,
    inserted       boolean,
    last_revised   timestamp with time zone not null
);

alter table formula_missingfield
    owner to user_desabasto;

create table if not exists formula_missingrow
(
    uuid          uuid    not null,
    original_data jsonb,
    drug_id       uuid,
    error         text,
    inserted      boolean,
    sheet_file_id integer not null
);

alter table formula_missingrow
    owner to user_desabasto;

create table if not exists geo_entity
(
    id                  integer generated by default as identity
        primary key,
    name                varchar(255) not null,
    acronym             varchar(20)  not null,
    is_clues            boolean      not null,
    population          integer      not null,
    institution_id      integer
        constraint geo_entity_institution_id_579066b6_fk_desabasto_institution_id
            references geo_institution
            deferrable initially deferred,
    state_id            integer
        constraint geo_entity_state_id_775b70c4_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    split_by_delegation boolean      not null,
    is_pilot            boolean      not null,
    assigned_to_id      integer
        constraint geo_entity_assigned_to_id_5d80bbbd_fk_auth_user_id
            references auth_user
            deferrable initially deferred,
    notes               text,
    status_opera_id     integer
        constraint geo_entity_status_opera_id_495120a6_fk_category_
            references category_statuscontrol
            deferrable initially deferred
);

alter table geo_entity
    owner to user_yeeko;

create table if not exists geo_delegation
(
    id               integer default nextval('catalog_delegation_id_seq'::regclass) not null
        constraint catalog_delegation_pkey
            primary key,
    name             varchar(255)                                                   not null,
    other_names      jsonb,
    clues_id         integer
        constraint catalog_delegation_clues_id_37f7ec0a_uniq
            unique,
    institution_id   integer                                                        not null
        constraint catalog_delegation_institution_id_875b3b00_fk_desabasto
            references geo_institution
            deferrable initially deferred,
    state_id         integer                                                        not null
        constraint catalog_delegation_state_id_735f63d1_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    is_clues         boolean                                                        not null,
    is_jurisdiction  boolean                                                        not null,
    jurisdiction_key varchar(255),
    entity_id        integer
        constraint catalog_delegation_entity_id_f3eabeb3_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table geo_delegation
    owner to user_desabasto;

alter sequence catalog_delegation_id_seq owned by geo_delegation.id;

create index if not exists catalog_delegation_entity_id_f3eabeb3
    on geo_delegation (entity_id);

create index if not exists catalog_delegation_institution_id_875b3b00
    on geo_delegation (institution_id);

create index if not exists catalog_delegation_state_id_735f63d1
    on geo_delegation (state_id);

create table if not exists geo_clues
(
    id                      integer default nextval('desabasto_clues_id_seq'::regclass) not null
        constraint desabasto_clues_pkey
            primary key,
    state_id                integer                                                     not null
        constraint desabasto_clues_state_id_b8940d1d_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    institution_id          integer                                                     not null
        constraint desabasto_clues_institution_id_2dab20d4_fk_desabasto
            references geo_institution
            deferrable initially deferred,
    name                    varchar(255)                                                not null,
    is_searchable           boolean                                                     not null,
    typology                varchar(255)                                                not null,
    id_clues                varchar(10)                                                 not null,
    clues                   varchar(20)                                                 not null,
    status_operation        varchar(80)                                                 not null,
    longitude               varchar(20)                                                 not null,
    latitude                varchar(20)                                                 not null,
    locality                varchar(80)                                                 not null,
    locality_inegi_code     varchar(5)                                                  not null,
    jurisdiction            varchar(80)                                                 not null,
    jurisdiction_clave      varchar(5)                                                  not null,
    establishment_type      varchar(80)                                                 not null,
    consultings_general     integer                                                     not null,
    consultings_other       integer                                                     not null,
    beds_hopital            integer                                                     not null,
    beds_other              integer                                                     not null,
    total_unities           integer                                                     not null,
    admin_institution       varchar(80)                                                 not null,
    atention_level          varchar(80)                                                 not null,
    stratum                 varchar(80)                                                 not null,
    real_name               varchar(255),
    alter_clasifs           varchar(255),
    clasif_name             varchar(120),
    prev_clasif_name        varchar(30),
    number_unity            varchar(6),
    is_national             boolean                                                     not null,
    name_in_issten          varchar(255),
    rr_data                 text,
    alternative_names       jsonb,
    typology_obj_id         integer
        constraint desabasto_clues_typology_obj_id_f288747f_fk_catalog_typology_id
            references geo_typology
            deferrable initially deferred,
    last_change             timestamp with time zone,
    postal_code             varchar(6),
    rfc                     varchar(15),
    streat_number           varchar(80),
    street                  varchar(255),
    suburb                  varchar(255),
    type_street             varchar(80),
    typology_cve            varchar(18)                                                 not null,
    key_issste              varchar(12),
    municipality_id         integer
        constraint desabasto_clues_municipality_id_4f390af9_fk_catalog_m
            references geo_municipality
            deferrable initially deferred,
    municipality_inegi_code varchar(5),
    municipality_name       varchar(255),
    delegation_id           integer
        constraint desabasto_clues_delegation_id_781223c5_fk_catalog_delegation_id
            references geo_delegation
            deferrable initially deferred,
    entity_id               integer
        constraint desabasto_clues_entity_id_ea0be12e_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table geo_clues
    owner to user_desabasto;

alter sequence desabasto_clues_id_seq owned by geo_clues.id;

create table if not exists catalog_agency
(
    id                     integer default nextval('catalog_entity_id_seq'::regclass) not null
        constraint catalog_entity_pkey
            primary key,
    addl_params            jsonb,
    vigencia               boolean,
    clues_id               integer
        constraint catalog_entity_clues_id_b6a62f84_fk_desabasto_clues_id
            references geo_clues
            deferrable initially deferred,
    institution_id         integer                                                    not null
        constraint catalog_entity_institution_id_538deef4_fk_desabasto
            references geo_institution
            deferrable initially deferred,
    state_id               integer
        constraint catalog_entity_state_id_edce0bdd_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    name                   varchar(120),
    acronym                varchar(20),
    "idSujetoObligado"     integer,
    "nombreSujetoObligado" varchar(160),
    competent              boolean                                                    not null,
    notes                  text,
    is_pilot               boolean                                                    not null,
    population             integer,
    "nameForInai"          varchar(255),
    entity_id              integer
        constraint catalog_agency_entity_id_12dfc9df_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table catalog_agency
    owner to user_desabasto;

alter sequence catalog_entity_id_seq owned by catalog_agency.id;

create index if not exists catalog_agency_entity_id_12dfc9df
    on catalog_agency (entity_id);

create index if not exists catalog_entity_clues_id_b6a62f84
    on catalog_agency (clues_id);

create index if not exists catalog_entity_institution_id_538deef4
    on catalog_agency (institution_id);

create index if not exists catalog_entity_state_id_edce0bdd
    on catalog_agency (state_id);

alter table geo_delegation
    add constraint catalog_delegation_clues_id_37f7ec0a_fk_desabasto_clues_id
        foreign key (clues_id) references geo_clues
            deferrable initially deferred;

create table if not exists data_param_filecontrol
(
    id                 integer default nextval('inai_filecontrol_id_seq'::regclass) not null
        constraint inai_filecontrol_pkey
            primary key,
    name               varchar(255)                                                 not null,
    format_file        varchar(5),
    other_format       varchar(80),
    final_data         boolean,
    notes              text,
    row_start_data     integer,
    row_headers        integer,
    in_percent         boolean                                                      not null,
    addl_params        jsonb                                                        not null,
    delimiter          varchar(3),
    status_register_id integer
        constraint inai_filecontrol_status_register_id_f77df525_fk_category_
            references category_statuscontrol
            deferrable initially deferred,
    data_group_id      integer                                                      not null
        constraint inai_filecontrol_data_group_id_1e4b72ab_fk_data_para
            references data_param_datagroup
            deferrable initially deferred,
    file_format_id     integer
        constraint inai_filecontrol_file_format_id_13d71389_fk_category_
            references category_fileformat
            deferrable initially deferred,
    all_results        jsonb,
    decode             varchar(10),
    agency_id          integer
        constraint data_param_filecontrol_agency_id_8e31d939_fk_catalog_agency_id
            references catalog_agency
            deferrable initially deferred,
    real_entity_id     integer
        constraint data_param_filecontrol_real_entity_id_1a22f759_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table data_param_filecontrol
    owner to user_desabasto;

alter sequence inai_filecontrol_id_seq owned by data_param_filecontrol.id;

create table if not exists data_param_dictionaryfile
(
    id              integer generated by default as identity
        primary key,
    file            varchar(100)             not null,
    collection_id   integer                  not null
        constraint data_param_dictionar_collection_id_1e6de10b_fk_data_para
            references data_param_collection
            deferrable initially deferred,
    unique_field_id integer
        constraint data_param_dictionar_unique_field_id_e31863ef_fk_data_para
            references data_param_finalfield
            deferrable initially deferred,
    file_control_id integer
        constraint data_param_dictionar_file_control_id_bba864f7_fk_data_para
            references data_param_filecontrol
            deferrable initially deferred,
    last_update     timestamp with time zone not null,
    entity_id       integer
        constraint data_param_dictionaryfile_entity_id_d84757e1_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table data_param_dictionaryfile
    owner to user_desabasto;

create index if not exists data_param_dictionaryfile_collection_id_1e6de10b
    on data_param_dictionaryfile (collection_id);

create index if not exists data_param_dictionaryfile_entity_id_d84757e1
    on data_param_dictionaryfile (entity_id);

create index if not exists data_param_dictionaryfile_file_control_id_bba864f7
    on data_param_dictionaryfile (file_control_id);

create index if not exists data_param_dictionaryfile_unique_field_id_e31863ef
    on data_param_dictionaryfile (unique_field_id);

create table if not exists data_param_dictionaryfile_final_fields
(
    id                integer generated by default as identity
        primary key,
    dictionaryfile_id integer not null
        constraint data_param_dictionar_dictionaryfile_id_71b7ecde_fk_data_para
            references data_param_dictionaryfile
            deferrable initially deferred,
    finalfield_id     integer not null
        constraint data_param_dictionar_finalfield_id_b4c0d487_fk_data_para
            references data_param_finalfield
            deferrable initially deferred,
    constraint data_param_dictionaryfil_dictionaryfile_id_finalf_c06fa2b5_uniq
        unique (dictionaryfile_id, finalfield_id)
);

alter table data_param_dictionaryfile_final_fields
    owner to user_desabasto;

create index if not exists data_param_dictionaryfile__dictionaryfile_id_71b7ecde
    on data_param_dictionaryfile_final_fields (dictionaryfile_id);

create index if not exists data_param_dictionaryfile_final_fields_finalfield_id_b4c0d487
    on data_param_dictionaryfile_final_fields (finalfield_id);

create index if not exists data_param_filecontrol_entity_id_6318f2ad
    on data_param_filecontrol (agency_id);

create index if not exists data_param_filecontrol_real_entity_id_1a22f759
    on data_param_filecontrol (real_entity_id);

create index if not exists inai_filecontrol_data_group_id_1e4b72ab
    on data_param_filecontrol (data_group_id);

create index if not exists inai_filecontrol_file_format_id_13d71389
    on data_param_filecontrol (file_format_id);

create index if not exists inai_filecontrol_status_register_id_f77df525
    on data_param_filecontrol (status_register_id);

create table if not exists data_param_filecontrol_anomalies
(
    id             integer default nextval('inai_filecontrol_anomalies_id_seq'::regclass) not null
        constraint inai_filecontrol_anomalies_pkey
            primary key,
    filecontrol_id integer                                                                not null
        constraint inai_filecontrol_ano_filecontrol_id_e3772254_fk_inai_file
            references data_param_filecontrol
            deferrable initially deferred,
    anomaly_id     integer                                                                not null
        constraint inai_filecontrol_ano_anomaly_id_5481b668_fk_category_
            references transparency_anomaly
            deferrable initially deferred,
    constraint inai_filecontrol_anomali_filecontrol_id_anomaly_i_4508c38a_uniq
        unique (filecontrol_id, anomaly_id)
);

alter table data_param_filecontrol_anomalies
    owner to user_desabasto;

alter sequence inai_filecontrol_anomalies_id_seq owned by data_param_filecontrol_anomalies.id;

create index if not exists inai_filecontrol_anomalies_anomaly_id_5481b668
    on data_param_filecontrol_anomalies (anomaly_id);

create index if not exists inai_filecontrol_anomalies_filecontrol_id_e3772254
    on data_param_filecontrol_anomalies (filecontrol_id);

create table if not exists data_param_namecolumn
(
    id                integer default nextval('inai_namecolumn_id_seq'::regclass) not null
        constraint inai_namecolumn_pkey
            primary key,
    name_in_data      text,
    position_in_data  integer,
    required_row      boolean                                                     not null,
    child_column_id   integer
        constraint data_param_namecolum_child_column_id_1da1bb86_fk_data_para
            references data_param_namecolumn
            deferrable initially deferred,
    column_type_id    integer                                                     not null
        constraint inai_namecolumn_column_type_id_c878ea88_fk_category_
            references category_columntype
            deferrable initially deferred,
    data_type_id      integer
        constraint inai_namecolumn_data_type_id_bb1598cb_fk_data_param_datatype_id
            references data_param_datatype
            deferrable initially deferred,
    file_control_id   integer
        constraint inai_namecolumn_file_control_id_44fccf26_fk_inai_filecontrol_id
            references data_param_filecontrol
            deferrable initially deferred,
    final_field_id    integer
        constraint inai_namecolumn_final_field_id_bc12cd08_fk_data_para
            references data_param_finalfield
            deferrable initially deferred,
    parent_column_id  integer
        constraint inai_namecolumn_parent_column_id_8006e790_fk_inai_namecolumn_id
            references data_param_namecolumn
            deferrable initially deferred,
    seq               integer,
    last_update       timestamp with time zone                                    not null,
    alternative_names jsonb
);

alter table data_param_namecolumn
    owner to user_desabasto;

alter sequence inai_namecolumn_id_seq owned by data_param_namecolumn.id;

create index if not exists inai_namecolumn_children_row_id_537eb025
    on data_param_namecolumn (child_column_id);

create index if not exists inai_namecolumn_column_type_id_c878ea88
    on data_param_namecolumn (column_type_id);

create index if not exists inai_namecolumn_data_type_id_bb1598cb
    on data_param_namecolumn (data_type_id);

create index if not exists inai_namecolumn_file_control_id_44fccf26
    on data_param_namecolumn (file_control_id);

create index if not exists inai_namecolumn_final_field_id_bc12cd08
    on data_param_namecolumn (final_field_id);

create index if not exists inai_namecolumn_parent_row_id_a93a718d
    on data_param_namecolumn (parent_column_id);

create table if not exists data_param_transformation
(
    id                integer default nextval('inai_transformation_id_seq'::regclass) not null
        constraint inai_transformation_pkey
            primary key,
    addl_params       jsonb,
    clean_function_id integer                                                         not null
        constraint inai_transformation_clean_function_id_45058f81_fk_data_para
            references data_param_cleanfunction
            deferrable initially deferred,
    file_control_id   integer
        constraint inai_transformation_file_control_id_ef06d32e_fk_inai_file
            references data_param_filecontrol
            deferrable initially deferred,
    name_column_id    integer
        constraint inai_transformation_name_column_id_5be44dd6_fk_inai_name
            references data_param_namecolumn
            deferrable initially deferred
);

alter table data_param_transformation
    owner to user_desabasto;

alter sequence inai_transformation_id_seq owned by data_param_transformation.id;

create index if not exists inai_transformation_clean_function_id_45058f81
    on data_param_transformation (clean_function_id);

create index if not exists inai_transformation_file_control_id_ef06d32e
    on data_param_transformation (file_control_id);

create index if not exists inai_transformation_name_column_id_5be44dd6
    on data_param_transformation (name_column_id);

create index if not exists desabasto_clues_delegation_id_781223c5
    on geo_clues (delegation_id);

create index if not exists desabasto_clues_entity_id_ea0be12e
    on geo_clues (entity_id);

create index if not exists desabasto_clues_institution_id_2dab20d4
    on geo_clues (institution_id);

create index if not exists desabasto_clues_municipality_id_4f390af9
    on geo_clues (municipality_id);

create index if not exists desabasto_clues_state_id_b8940d1d
    on geo_clues (state_id);

create index if not exists desabasto_clues_tipology_obj_id_49ff25ab
    on geo_clues (typology_obj_id);

create table if not exists desabasto_responsable
(
    id             serial
        primary key,
    name           varchar(255) not null,
    emails         varchar(255) not null,
    position       varchar(255) not null,
    institution_id integer
        constraint desabasto_responsabl_institution_id_1e59b1fd_fk_desabasto
            references geo_institution
            deferrable initially deferred,
    state_id       integer
        constraint desabasto_responsable_state_id_bce1d614_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    clues_id       integer
        constraint desabasto_responsable_clues_id_3abcc852_fk_desabasto_clues_id
            references geo_clues
            deferrable initially deferred,
    notes          text,
    update_date    date,
    is_covid       boolean      not null,
    petition_date  date
);

alter table desabasto_responsable
    owner to user_desabasto;

create index if not exists desabasto_responsable_clues_id_3abcc852
    on desabasto_responsable (clues_id);

create index if not exists desabasto_responsable_institution_id_1e59b1fd
    on desabasto_responsable (institution_id);

create index if not exists desabasto_responsable_state_id_bce1d614
    on desabasto_responsable (state_id);

create index if not exists geo_entity_institution_id_579066b6
    on geo_entity (institution_id);

create index if not exists geo_entity_state_id_775b70c4
    on geo_entity (state_id);

create index if not exists geo_entity_assigned_to_id_5d80bbbd
    on geo_entity (assigned_to_id);

create index if not exists geo_entity_status_opera_id_495120a6
    on geo_entity (status_opera_id);

create table if not exists inai_behavior
(
    name        varchar(80) not null
        primary key,
    public_name varchar(80) not null,
    description text,
    icon        varchar(80),
    color       varchar(80),
    is_merge    boolean     not null,
    is_valid    boolean     not null
);

alter table inai_behavior
    owner to user_yeeko;

create index if not exists inai_behavior_name_e5d5fdcc_like
    on inai_behavior (name varchar_pattern_ops);

create table if not exists inai_entitymonth
(
    id                  integer default nextval('inai_monthentity_id_seq'::regclass) not null
        constraint inai_monthentity_pkey
            primary key,
    year_month          varchar(10)                                                  not null,
    agency_id           integer
        constraint inai_monthagency_agency_id_fc5d52c0_fk_catalog_agency_id
            references catalog_agency
            deferrable initially deferred,
    entity_id           integer
        constraint inai_monthagency_entity_id_6ed9b5e5_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred,
    duplicates_count    integer                                                      not null,
    last_crossing       timestamp with time zone,
    rx_count            integer                                                      not null,
    shared_count        integer                                                      not null,
    drugs_count         integer                                                      not null,
    last_transformation timestamp with time zone,
    last_insertion      timestamp with time zone,
    last_merge          timestamp with time zone,
    month               smallint,
    year                smallint,
    stage_id            varchar(80)                                                  not null
        constraint inai_entitymonth_stage_id_06adec7e_fk_classify_task_stage_name
            references classify_task_stage
            deferrable initially deferred,
    status_id           varchar(80)                                                  not null
        constraint inai_entitymonth_status_id_eac0d393_fk_classify_
            references classify_task_statustask
            deferrable initially deferred
);

alter table inai_entitymonth
    owner to user_desabasto;

alter sequence inai_monthentity_id_seq owned by inai_entitymonth.id;

create index if not exists inai_monthagency_entity_id_6ed9b5e5
    on inai_entitymonth (entity_id);

create index if not exists inai_monthentity_entity_id_dc39254a
    on inai_entitymonth (agency_id);

create index if not exists inai_entitymonth_stage_id_06adec7e
    on inai_entitymonth (stage_id);

create index if not exists inai_entitymonth_stage_id_06adec7e_like
    on inai_entitymonth (stage_id varchar_pattern_ops);

create index if not exists inai_entitymonth_status_id_eac0d393
    on inai_entitymonth (status_id);

create index if not exists inai_entitymonth_status_id_eac0d393_like
    on inai_entitymonth (status_id varchar_pattern_ops);

create table if not exists inai_entityweek
(
    id                  integer generated by default as identity
        primary key,
    iso_year            smallint,
    iso_week            smallint,
    year                smallint,
    month               smallint,
    year_month          varchar(10),
    drugs_count         integer not null,
    rx_count            integer not null,
    duplicates_count    integer not null,
    shared_count        integer not null,
    last_crossing       timestamp with time zone,
    last_transformation timestamp with time zone,
    entity_id           integer
        constraint inai_entityweek_entity_id_0e4dd3ed_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred,
    entity_month_id     integer
        constraint inai_entityweek_entity_month_id_eb5cc9f2_fk_inai_entitymonth_id
            references inai_entitymonth
            deferrable initially deferred,
    year_week           varchar(8),
    iso_delegation      smallint
        constraint inai_entityweek_iso_delegation_check
            check (iso_delegation >= 0),
    last_insertion      timestamp with time zone,
    last_merge          timestamp with time zone,
    cancelled           integer,
    complete            integer,
    denied              integer,
    error               integer,
    over_delivered      integer,
    partial             integer,
    unavailable         integer,
    unknown             integer,
    zero                integer,
    crosses             jsonb,
    constraint inai_entityweek_entity_id_year_week_iso__285ba5db_uniq
        unique (entity_id, year_week, iso_delegation, year_month)
);

alter table inai_entityweek
    owner to user_yeeko;

create index if not exists inai_entityweek_entity_id_0e4dd3ed
    on inai_entityweek (entity_id);

create index if not exists inai_entityweek_entity_month_id_eb5cc9f2
    on inai_entityweek (entity_month_id);

create table if not exists inai_petition
(
    id                   serial
        primary key,
    ask_extension        boolean,
    notes                text,
    folio_petition       varchar(50) not null,
    folio_complain       integer,
    agency_id            integer     not null
        constraint inai_petition_agency_id_10bc9803_fk_catalog_agency_id
            references catalog_agency
            deferrable initially deferred,
    status_data_id       integer
        constraint inai_petition_status_data_id_b40287ca_fk_category_
            references category_statuscontrol
            deferrable initially deferred,
    status_petition_id   integer
        constraint inai_petition_status_petition_id_83687ec4_fk_category_
            references category_statuscontrol
            deferrable initially deferred,
    description_petition text,
    description_response text,
    id_inai_open_data    integer,
    info_queja_inai      jsonb,
    send_petition        date,
    send_response        date,
    status_complain_id   integer
        constraint inai_petition_status_complain_id_6a43b655_fk_category_
            references category_statuscontrol
            deferrable initially deferred,
    description_complain text,
    invalid_reason_id    integer
        constraint inai_petition_invalid_reason_id_7f7ffceb_fk_category_
            references category_invalidreason
            deferrable initially deferred,
    real_entity_id       integer
        constraint inai_petition_real_entity_id_7522e915_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table inai_petition
    owner to user_desabasto;

create index if not exists inai_petition_entity_id_d2c6f7b0
    on inai_petition (agency_id);

create index if not exists inai_petition_invalid_reason_id_7f7ffceb
    on inai_petition (invalid_reason_id);

create index if not exists inai_petition_real_entity_id_7522e915
    on inai_petition (real_entity_id);

create index if not exists inai_petition_status_complain_id_6a43b655
    on inai_petition (status_complain_id);

create index if not exists inai_petition_status_data_id_b40287ca
    on inai_petition (status_data_id);

create index if not exists inai_petition_status_petition_id_83687ec4
    on inai_petition (status_petition_id);

create table if not exists inai_petition_entity_months
(
    id             integer generated by default as identity
        constraint inai_petition_months_agency_pkey
            primary key,
    petition_id    integer not null
        constraint inai_petition_months_petition_id_bfdb5740_fk_inai_peti
            references inai_petition
            deferrable initially deferred,
    entitymonth_id integer not null
        constraint inai_petition_months_entitymonth_id_4c5a1c09_fk_inai_enti
            references inai_entitymonth
            deferrable initially deferred,
    constraint inai_petition_months_age_petition_id_monthagency__86126698_uniq
        unique (petition_id, entitymonth_id)
);

alter table inai_petition_entity_months
    owner to user_yeeko;

alter sequence inai_petition_months_agency_id_seq owned by inai_petition_entity_months.id;

create index if not exists inai_petition_months_agency_monthagency_id_5369ff0b
    on inai_petition_entity_months (entitymonth_id);

create index if not exists inai_petition_months_agency_petition_id_bfdb5740
    on inai_petition_entity_months (petition_id);

create table if not exists inai_petitionbreak
(
    id            serial
        primary key,
    date          date,
    date_break_id integer not null
        constraint inai_petitionbreak_date_break_id_cd1fe807_fk_category_
            references category_datebreak
            deferrable initially deferred,
    petition_id   integer not null
        constraint inai_petitionbreak_petition_id_07f79431_fk_inai_petition_id
            references inai_petition
            deferrable initially deferred
);

alter table inai_petitionbreak
    owner to user_desabasto;

create index if not exists inai_petitionbreak_date_break_id_cd1fe807
    on inai_petitionbreak (date_break_id);

create index if not exists inai_petitionbreak_petition_id_07f79431
    on inai_petitionbreak (petition_id);

create table if not exists inai_petitionfilecontrol
(
    id              serial
        primary key,
    file_control_id integer not null
        constraint inai_petitionfilecon_file_control_id_f170fdc6_fk_inai_file
            references data_param_filecontrol
            deferrable initially deferred,
    petition_id     integer not null
        constraint inai_petitionfilecon_petition_id_006d55bb_fk_inai_peti
            references inai_petition
            deferrable initially deferred
);

alter table inai_petitionfilecontrol
    owner to user_desabasto;

create index if not exists inai_petitionfilecontrol_file_control_id_f170fdc6
    on inai_petitionfilecontrol (file_control_id);

create index if not exists inai_petitionfilecontrol_petition_id_006d55bb
    on inai_petitionfilecontrol (petition_id);

create table if not exists inai_petitionmonth
(
    id              serial
        primary key,
    entity_month_id integer not null
        constraint inai_petitionmonth_entity_month_id_11bf547c_fk_inai_enti
            references inai_entitymonth
            deferrable initially deferred,
    petition_id     integer not null
        constraint inai_petitionmonth_petition_id_dae3941b_fk_inai_petition_id
            references inai_petition
            deferrable initially deferred
);

alter table inai_petitionmonth
    owner to user_desabasto;

create index if not exists inai_petitionmonth_month_entity_id_b4f036f1
    on inai_petitionmonth (entity_month_id);

create index if not exists inai_petitionmonth_petition_id_dae3941b
    on inai_petitionmonth (petition_id);

create table if not exists inai_petitionnegativereason
(
    id                 serial
        primary key,
    is_main            boolean not null,
    negative_reason_id integer not null
        constraint inai_petitionnegativ_negative_reason_id_16c0c766_fk_category_
            references category_negativereason
            deferrable initially deferred,
    petition_id        integer not null
        constraint inai_petitionnegativ_petition_id_f82e67bd_fk_inai_peti
            references inai_petition
            deferrable initially deferred
);

alter table inai_petitionnegativereason
    owner to user_desabasto;

create index if not exists inai_petitionnegativereason_negative_reason_id_16c0c766
    on inai_petitionnegativereason (negative_reason_id);

create index if not exists inai_petitionnegativereason_petition_id_f82e67bd
    on inai_petitionnegativereason (petition_id);

create table if not exists inai_replyfile
(
    id           integer generated by default as identity
        primary key,
    file         varchar(150),
    date         timestamp with time zone not null,
    text         text,
    url_download varchar(400),
    notes        text,
    addl_params  jsonb,
    has_data     boolean                  not null,
    petition_id  integer                  not null
        constraint inai_replyfile_petition_id_4731843e_fk_inai_petition_id
            references inai_petition
            deferrable initially deferred,
    file_type_id varchar(255)
        constraint inai_replyfile_file_type_id_05fe4519_fk_category_filetype_name
            references category_filetype
            deferrable initially deferred
);

alter table inai_replyfile
    owner to user_desabasto;

create table if not exists inai_datafile
(
    id                       serial
        primary key,
    file                     varchar(150)             not null,
    date                     timestamp with time zone not null,
    notes                    text,
    error_process            jsonb,
    total_rows               integer                  not null,
    petition_file_control_id integer
        constraint inai_datafile_petition_file_contro_ad279dd3_fk_inai_peti
            references inai_petitionfilecontrol
            deferrable initially deferred,
    status_process_id        integer
        constraint inai_datafile_status_process_id_185287c1_fk_category_
            references category_statuscontrol
            deferrable initially deferred,
    all_results              jsonb,
    zip_path                 text,
    directory                varchar(255),
    sample_data              jsonb,
    sheet_names              jsonb,
    suffix                   varchar(10),
    reply_file_id            integer
        constraint inai_datafile_reply_file_id_9167cbb8_fk_inai_replyfile_id
            references inai_replyfile
            deferrable initially deferred,
    stage_id                 varchar(80)
        constraint inai_datafile_stage_id_5691c20b_fk_classify_task_stage_name
            references classify_task_stage
            deferrable initially deferred,
    status_id                varchar(80)
        constraint inai_datafile_status_id_29038ef7_fk_classify_
            references classify_task_statustask
            deferrable initially deferred,
    filtered_sheets          jsonb,
    warnings                 jsonb,
    entity_id                integer
        constraint inai_datafile_entity_id_ae5221b6_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred
);

alter table inai_datafile
    owner to user_desabasto;

create index if not exists inai_datafile_entity_id_ae5221b6
    on inai_datafile (entity_id);

create index if not exists inai_datafile_petition_file_control_id_ad279dd3
    on inai_datafile (petition_file_control_id);

create index if not exists inai_datafile_reply_file_id_9167cbb8
    on inai_datafile (reply_file_id);

create index if not exists inai_datafile_stage_id_5691c20b
    on inai_datafile (stage_id);

create index if not exists inai_datafile_stage_id_5691c20b_like
    on inai_datafile (stage_id varchar_pattern_ops);

create index if not exists inai_datafile_status_id_29038ef7
    on inai_datafile (status_id);

create index if not exists inai_datafile_status_id_29038ef7_like
    on inai_datafile (status_id varchar_pattern_ops);

create index if not exists inai_datafile_status_process_id_185287c1
    on inai_datafile (status_process_id);

create table if not exists inai_sheetfile
(
    id               integer generated by default as identity
        primary key,
    file             varchar(255) not null,
    matched          boolean,
    sheet_name       varchar(255),
    sample_data      jsonb,
    total_rows       integer      not null,
    data_file_id     integer      not null
        constraint inai_sheetfile_data_file_id_e53306bb_fk_inai_datafile_id
            references inai_datafile
            deferrable initially deferred,
    file_type_id     varchar(255)
        constraint inai_sheetfile_file_type_id_2f671cec_fk_category_filetype_name
            references category_filetype
            deferrable initially deferred,
    error_process    jsonb,
    stage_id         varchar(80)  not null
        constraint inai_sheetfile_stage_id_0611f4e5_fk_classify_task_stage_name
            references classify_task_stage
            deferrable initially deferred,
    status_id        varchar(80)  not null
        constraint inai_sheetfile_status_id_ff1677f2_fk_classify_
            references classify_task_statustask
            deferrable initially deferred,
    warnings         jsonb,
    year_month       varchar(8),
    duplicates_count integer      not null,
    rx_count         integer      not null,
    behavior_id      varchar(80)  not null
        constraint inai_sheetfile_behavior_id_65611e94_fk_inai_behavior_name
            references inai_behavior
            deferrable initially deferred,
    shared_count     integer      not null,
    constraint inai_sheetfile_data_file_id_sheet_name__683b9c44_uniq
        unique (data_file_id, sheet_name, file_type_id)
);

alter table inai_sheetfile
    owner to user_desabasto;

create index if not exists inai_sheetfile_behavior_id_65611e94
    on inai_sheetfile (behavior_id);

create index if not exists inai_sheetfile_behavior_id_65611e94_like
    on inai_sheetfile (behavior_id varchar_pattern_ops);

create index if not exists inai_sheetfile_data_file_id_e53306bb
    on inai_sheetfile (data_file_id);

create index if not exists inai_sheetfile_file_type_id_2f671cec
    on inai_sheetfile (file_type_id);

create index if not exists inai_sheetfile_file_type_id_2f671cec_like
    on inai_sheetfile (file_type_id varchar_pattern_ops);

create index if not exists inai_sheetfile_stage_id_0611f4e5
    on inai_sheetfile (stage_id);

create index if not exists inai_sheetfile_stage_id_0611f4e5_like
    on inai_sheetfile (stage_id varchar_pattern_ops);

create index if not exists inai_sheetfile_status_id_ff1677f2
    on inai_sheetfile (status_id);

create index if not exists inai_sheetfile_status_id_ff1677f2_like
    on inai_sheetfile (status_id varchar_pattern_ops);

create table if not exists inai_crossingsheet
(
    id               integer generated by default as identity
        primary key,
    duplicates_count integer not null,
    last_crossing    timestamp with time zone,
    sheet_file_1_id  integer not null
        constraint inai_crossingsheet_sheet_file_1_id_b35d0a40_fk_inai_shee
            references inai_sheetfile
            deferrable initially deferred,
    sheet_file_2_id  integer not null
        constraint inai_crossingsheet_sheet_file_2_id_26f6f792_fk_inai_shee
            references inai_sheetfile
            deferrable initially deferred,
    shared_count     integer not null,
    entity_week_id   integer
        constraint inai_crossingsheet_entity_week_id_1bc36908_fk_inai_enti
            references inai_entityweek
            deferrable initially deferred,
    entity_month_id  integer
        constraint inai_crossingsheet_entity_month_id_d8a2e11c_fk_inai_enti
            references inai_entitymonth
            deferrable initially deferred
);

alter table inai_crossingsheet
    owner to user_yeeko;

create index if not exists inai_crossingsheet_entity_month_id_d8a2e11c
    on inai_crossingsheet (entity_month_id);

create index if not exists inai_crossingsheet_entity_week_id_1bc36908
    on inai_crossingsheet (entity_week_id);

create index if not exists inai_crossingsheet_sheet_file_1_id_b35d0a40
    on inai_crossingsheet (sheet_file_1_id);

create index if not exists inai_crossingsheet_sheet_file_2_id_26f6f792
    on inai_crossingsheet (sheet_file_2_id);

create table if not exists inai_lapsheet
(
    id                 integer generated by default as identity
        primary key,
    lap                integer not null,
    inserted           boolean,
    general_error      varchar(255),
    rx_count           integer not null,
    drugs_count        integer not null,
    missing_rows       integer not null,
    missing_fields     integer not null,
    row_errors         jsonb,
    field_errors       jsonb,
    sheet_file_id      integer not null
        constraint inai_lapsheet_sheet_file_id_6f159183_fk_inai_sheetfile_id
            references inai_sheetfile
            deferrable initially deferred,
    discarded_count    integer not null,
    total_count        integer not null,
    area_count         integer not null,
    diagnosis_count    integer not null,
    doctor_count       integer not null,
    medical_unit_count integer not null,
    medicament_count   integer not null,
    last_edit          timestamp with time zone,
    processed_count    integer not null,
    valid_insert       boolean not null,
    real_missing_rows  integer not null,
    cat_inserted       boolean,
    missing_inserted   boolean,
    constraint inai_lapsheet_sheet_file_id_lap_e39ac7f1_uniq
        unique (sheet_file_id, lap)
);

alter table inai_lapsheet
    owner to user_desabasto;

create index if not exists inai_lapsheet_sheet_file_id_6f159183
    on inai_lapsheet (sheet_file_id);

create index if not exists inai_replyfile_file_type_id_05fe4519
    on inai_replyfile (file_type_id);

create index if not exists inai_replyfile_file_type_id_05fe4519_like
    on inai_replyfile (file_type_id varchar_pattern_ops);

create index if not exists inai_replyfile_petition_id_4731843e
    on inai_replyfile (petition_id);

create table if not exists inai_sheetfile_entity_months
(
    id             integer generated by default as identity
        primary key,
    sheetfile_id   integer not null
        constraint inai_sheetfile_entit_sheetfile_id_c9aee29b_fk_inai_shee
            references inai_sheetfile
            deferrable initially deferred,
    entitymonth_id integer not null
        constraint inai_sheetfile_entit_entitymonth_id_6432c43e_fk_inai_enti
            references inai_entitymonth
            deferrable initially deferred,
    constraint inai_sheetfile_entity_mo_sheetfile_id_entitymonth_fe0c4344_uniq
        unique (sheetfile_id, entitymonth_id)
);

alter table inai_sheetfile_entity_months
    owner to user_yeeko;

create index if not exists inai_sheetfile_entity_months_entitymonth_id_6432c43e
    on inai_sheetfile_entity_months (entitymonth_id);

create index if not exists inai_sheetfile_entity_months_sheetfile_id_c9aee29b
    on inai_sheetfile_entity_months (sheetfile_id);

create table if not exists inai_tablefile
(
    id               integer generated by default as identity
        primary key,
    file             varchar(255) not null,
    collection_id    integer
        constraint inai_tablefile_collection_id_08a710b6_fk_data_para
            references data_param_collection
            deferrable initially deferred,
    is_for_edition   boolean      not null,
    lap_sheet_id     integer
        constraint inai_tablefile_lap_sheet_id_815679f6_fk_inai_lapsheet_id
            references inai_lapsheet
            deferrable initially deferred,
    iso_week         smallint
        constraint inai_tablefile_iso_week_189ee009_check
            check (iso_week >= 0),
    year             smallint
        constraint inai_tablefile_year_c7262341_check
            check (year >= 0),
    iso_year         smallint
        constraint inai_tablefile_iso_year_check
            check (iso_year >= 0),
    month            smallint
        constraint inai_tablefile_month_check
            check (month >= 0),
    year_month       varchar(8),
    entity_week_id   integer
        constraint inai_tablefile_entity_week_id_8a7b5d7f_fk_inai_entityweek_id
            references inai_entityweek
            deferrable initially deferred,
    inserted         boolean      not null,
    drugs_count      integer      not null,
    duplicates_count integer      not null,
    rx_count         integer      not null,
    shared_count     integer      not null,
    year_week        varchar(8),
    iso_delegation   smallint
        constraint inai_tablefile_iso_delegation_check
            check (iso_delegation >= 0),
    entity_id        integer
        constraint inai_tablefile_entity_id_a3e69938_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred,
    constraint inai_tablefile_lap_sheet_id_collection__377c6865_uniq
        unique (lap_sheet_id, collection_id, is_for_edition, year, iso_week, iso_delegation)
);

alter table inai_tablefile
    owner to user_desabasto;

create index if not exists inai_tablefile_collection_id_08a710b6
    on inai_tablefile (collection_id);

create index if not exists inai_tablefile_entity_id_a3e69938
    on inai_tablefile (entity_id);

create index if not exists inai_tablefile_entity_week_id_8a7b5d7f
    on inai_tablefile (entity_week_id);

create index if not exists inai_tablefile_lap_sheet_id_815679f6
    on inai_tablefile (lap_sheet_id);

create table if not exists intl_medicine_clasificationsource
(
    id            serial
        primary key,
    name          varchar(255) not null,
    instituciones text,
    notes         text
);

alter table intl_medicine_clasificationsource
    owner to user_desabasto;

create table if not exists intl_medicine_internatinalterapeticgroup
(
    id          serial
        primary key,
    name        varchar(255) not null,
    description text
);

alter table intl_medicine_internatinalterapeticgroup
    owner to user_desabasto;

create table if not exists intl_medicine_internationalmedicine
(
    id            serial
        primary key,
    name          varchar(255) not null,
    original_name varchar(255),
    without_equal boolean      not null,
    component_id  integer
        unique
        constraint intl_medicine_intern_component_id_a7bb8513_fk_desabasto
            references desabasto_component
            deferrable initially deferred
);

alter table intl_medicine_internationalmedicine
    owner to user_desabasto;

create table if not exists intl_medicine_priorizedmedsource
(
    id                        serial
        primary key,
    clasification_source_id   integer not null
        constraint intl_medicine_priori_clasification_source_e5613740_fk_intl_medi
            references intl_medicine_clasificationsource
            deferrable initially deferred,
    international_medicine_id integer not null
        constraint intl_medicine_priori_international_medici_67d82e9a_fk_intl_medi
            references intl_medicine_internationalmedicine
            deferrable initially deferred
);

alter table intl_medicine_priorizedmedsource
    owner to user_desabasto;

create index if not exists intl_medicine_priorizedmed_clasification_source_id_e5613740
    on intl_medicine_priorizedmedsource (clasification_source_id);

create index if not exists intl_medicine_priorizedmed_international_medicine_id_67d82e9a
    on intl_medicine_priorizedmedsource (international_medicine_id);

create table if not exists med_cat_area
(
    key             varchar(255),
    name            text,
    description     text,
    is_aggregate    boolean,
    entity_id       integer     not null,
    hex_hash        varchar(32) not null,
    aggregate_to_id varchar(32)
);

alter table med_cat_area
    owner to user_yeeko;

create table if not exists med_cat_delivered
(
    hex_hash        varchar(32) not null,
    name            varchar(80) not null,
    description     text,
    is_aggregate    boolean,
    aggregate_to_id varchar(32)
);

alter table med_cat_delivered
    owner to user_yeeko;

create table if not exists med_cat_diagnosis
(
    cie10           varchar(40),
    text            text,
    motive          text,
    is_aggregate    boolean,
    hex_hash        varchar(32) not null,
    own_key         varchar(255),
    aggregate_to_id varchar(32)
);

alter table med_cat_diagnosis
    owner to user_yeeko;

create table if not exists med_cat_doctor
(
    clave                varchar(30),
    full_name            varchar(255),
    medical_speciality   varchar(255),
    professional_license varchar(20),
    is_aggregate         boolean,
    entity_id            integer     not null,
    hex_hash             varchar(32) not null,
    aggregate_to_id      varchar(32)
);

alter table med_cat_doctor
    owner to user_yeeko;

create table if not exists med_cat_medicalunit
(
    hex_hash         varchar(32) not null,
    delegation_name  varchar(255),
    state_name       varchar(255),
    name             varchar(255),
    attention_level  varchar(80),
    clues_key        varchar(12),
    own_key          varchar(255),
    key_issste       varchar(12),
    typology_key     varchar(18),
    typology_name    varchar(255),
    clues_id         integer,
    delegation_id    integer,
    entity_id        integer     not null,
    jurisdiction_key varchar(50)
);

alter table med_cat_medicalunit
    owner to user_yeeko;

create table if not exists med_cat_medicament
(
    hex_hash                 varchar(32) not null,
    key2                     varchar(20),
    own_key2                 varchar(255),
    medicine_type            varchar(90),
    component_name           text,
    presentation_description text,
    container_name           text,
    component_id             integer,
    container_id             integer,
    entity_id                integer,
    presentation_id          integer,
    presentation_type        varchar(255)
);

alter table med_cat_medicament
    owner to user_yeeko;

create table if not exists perfil_templatebase
(
    id                  serial
        primary key,
    subject             varchar(200)             not null,
    from_name           varchar(200)             not null,
    name                varchar(200),
    body                text                     not null,
    created             timestamp with time zone not null,
    sendgrid_profile_id integer
        constraint perfil_templatebase_sendgrid_profile_id_0915ee4a_fk_email_sen
            references email_sendgrid_sendgridprofile
            deferrable initially deferred,
    description         text
);

alter table perfil_templatebase
    owner to user_desabasto;

create table if not exists perfil_emailrecord
(
    id                  serial
        primary key,
    send_email          boolean                  not null,
    user_id             integer
        constraint perfil_emailrecord_user_id_4bc9e166_fk_auth_user_id
            references auth_user
            deferrable initially deferred,
    email               varchar(120),
    template_base_id    integer
        constraint perfil_emailrecord_template_base_id_ebd7cdaf_fk_perfil_te
            references perfil_templatebase
            deferrable initially deferred,
    created             timestamp with time zone not null,
    x_message_id        varchar(120),
    sg_message_id       varchar(120),
    status              varchar(20)              not null,
    status_date         timestamp with time zone,
    type_message        varchar(100),
    sendgrid_profile_id integer
        constraint perfil_emailrecord_sendgrid_profile_id_c09fa6df_fk_email_sen
            references email_sendgrid_sendgridprofile
            deferrable initially deferred
);

alter table perfil_emailrecord
    owner to user_desabasto;

create table if not exists perfil_emaileventhistory
(
    id              serial
        primary key,
    event           varchar(20)              not null,
    response_date   timestamp with time zone not null,
    event_data      text                     not null,
    email_record_id integer                  not null
        constraint perfil_emaileventhis_email_record_id_daa725d8_fk_perfil_em
            references perfil_emailrecord
            deferrable initially deferred
);

alter table perfil_emaileventhistory
    owner to user_desabasto;

create index if not exists perfil_emaileventhistory_email_record_id_daa725d8
    on perfil_emaileventhistory (email_record_id);

create index if not exists perfil_emailrecord_sendgrid_profile_id_c09fa6df
    on perfil_emailrecord (sendgrid_profile_id);

create index if not exists perfil_emailrecord_template_base_id_ebd7cdaf
    on perfil_emailrecord (template_base_id);

create index if not exists perfil_emailrecord_user_id_4bc9e166
    on perfil_emailrecord (user_id);

create table if not exists perfil_massmailing
(
    id               serial
        primary key,
    template_base_id integer
        constraint perfil_massmailing_template_base_id_5ee914cd_fk_perfil_te
            references perfil_templatebase
            deferrable initially deferred,
    created          timestamp with time zone not null,
    filter_kwargs    text,
    exclude_kwargs   text,
    order_by_args    text
);

alter table perfil_massmailing
    owner to user_desabasto;

create index if not exists perfil_massmailing_template_base_id_5ee914cd
    on perfil_massmailing (template_base_id);

create index if not exists perfil_templatebase_sendgrid_profile_id_0915ee4a
    on perfil_templatebase (sendgrid_profile_id);

create table if not exists report_persona
(
    id              serial
        primary key,
    informer_name   varchar(255),
    email           varchar(255),
    phone           varchar(255),
    want_litigation boolean,
    want_management boolean
);

alter table report_persona
    owner to user_desabasto;

create table if not exists desabasto_report
(
    id                serial
        primary key,
    medicine_type     varchar(30),
    medication_name   varchar(255),
    state_id          integer
        constraint desabasto_report_state_id_e89cc68a_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    institution_id    integer
        constraint desabasto_report_institution_id_371475c4_fk_desabasto
            references geo_institution
            deferrable initially deferred,
    institution_raw   varchar(255),
    clues_id          integer
        constraint desabasto_report_clues_id_b1bba7e1_fk_desabasto_clues_id
            references geo_clues
            deferrable initially deferred,
    is_other          boolean                  not null,
    hospital_name_raw varchar(255),
    has_corruption    boolean,
    narration         text,
    informer_name     varchar(255),
    email             varchar(255),
    phone             varchar(255),
    informer_type     varchar(20)              not null,
    created           timestamp with time zone not null,
    origin_app        varchar(100)             not null,
    disease_raw       text,
    validated         boolean,
    testimony         text,
    want_litigation   boolean,
    validator         integer,
    validated_date    timestamp with time zone,
    pending           boolean                  not null,
    public_testimony  boolean,
    sent_email        boolean,
    sent_responsible  boolean,
    session_ga        varchar(255),
    age               integer,
    persona_id        integer
        constraint desabasto_report_persona_id_674cca54_fk_report_persona_id
            references report_persona
            deferrable initially deferred,
    gender            varchar(40)
);

alter table desabasto_report
    owner to user_desabasto;

create index if not exists desabasto_report_clues_id_b1bba7e1
    on desabasto_report (clues_id);

create index if not exists desabasto_report_institution_id_371475c4
    on desabasto_report (institution_id);

create index if not exists desabasto_report_persona_id_674cca54
    on desabasto_report (persona_id);

create index if not exists desabasto_report_state_id_e89cc68a
    on desabasto_report (state_id);

create table if not exists desabasto_supply
(
    id                 serial
        primary key,
    report_id          integer not null
        constraint desabasto_supply_report_id_d4bd7b67_fk_desabasto_report_id
            references desabasto_report
            deferrable initially deferred,
    component_id       integer
        constraint desabasto_supply_component_id_3614eb49_fk_desabasto
            references desabasto_component
            deferrable initially deferred,
    presentation_id    integer
        constraint desabasto_supply_presentation_id_16b752a9_fk_desabasto
            references desabasto_presentation
            deferrable initially deferred,
    medicine_type      varchar(20),
    medicine_name_raw  varchar(255),
    presentation_raw   varchar(255),
    medicine_real_name varchar(255),
    disease_id         integer
        constraint desabasto_supply_disease_id_2fc77f62_fk_desabasto_disease_id
            references desabasto_disease
            deferrable initially deferred
);

alter table desabasto_supply
    owner to user_desabasto;

create index if not exists desabasto_supply_component_id_3614eb49
    on desabasto_supply (component_id);

create index if not exists desabasto_supply_disease_id_2fc77f62
    on desabasto_supply (disease_id);

create index if not exists desabasto_supply_presentation_id_16b752a9
    on desabasto_supply (presentation_id);

create index if not exists desabasto_supply_report_id_d4bd7b67
    on desabasto_supply (report_id);

create table if not exists desabasto_testimonymedia
(
    id         serial
        primary key,
    report_id  integer not null
        constraint desabasto_testimonym_report_id_da97d6c6_fk_desabasto
            references desabasto_report
            deferrable initially deferred,
    media_file varchar(100),
    url        varchar(200)
);

alter table desabasto_testimonymedia
    owner to user_desabasto;

create index if not exists desabasto_testimonymedia_report_id_da97d6c6
    on desabasto_testimonymedia (report_id);

create table if not exists report_covidreport
(
    id              integer default nextval('report_reportcovid_id_seq'::regclass) not null
        constraint report_reportcovid_pkey
            primary key,
    created         timestamp with time zone                                       not null,
    municipality_id integer
        constraint report_reportcovid_municipality_id_c43a1e7a_fk_catalog_m
            references geo_municipality
            deferrable initially deferred,
    persona_id      integer
        constraint report_reportcovid_persona_id_d93bcc7c_fk_report_persona_id
            references report_persona
            deferrable initially deferred,
    state_id        integer
        constraint report_reportcovid_state_id_3cbb5819_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    other_location  varchar(255),
    age             integer,
    comorbilities   jsonb,
    gender          varchar(40),
    special_group   varchar(80)
);

alter table report_covidreport
    owner to user_desabasto;

alter sequence report_reportcovid_id_seq owned by report_covidreport.id;

create table if not exists report_complementreport
(
    id               serial
        primary key,
    key              varchar(30)  not null,
    testimony        text,
    public_testimony boolean,
    validated        boolean,
    validator        integer,
    validated_date   timestamp with time zone,
    pending          boolean      not null,
    session_ga       varchar(255),
    has_corruption   boolean,
    narration        text,
    origin_app       varchar(100) not null,
    covid_report_id  integer
        unique
        constraint report_complementrep_covid_report_id_be28c788_fk_report_co
            references report_covidreport
            deferrable initially deferred,
    report_id        integer
        unique
        constraint report_complementrep_report_id_69598f2d_fk_desabasto
            references desabasto_report
            deferrable initially deferred,
    notes            text
);

alter table report_complementreport
    owner to user_desabasto;

create index if not exists report_reportcovid_municipality_id_c43a1e7a
    on report_covidreport (municipality_id);

create index if not exists report_reportcovid_persona_id_d93bcc7c
    on report_covidreport (persona_id);

create index if not exists report_reportcovid_state_id_3cbb5819
    on report_covidreport (state_id);

create table if not exists report_dosiscovid
(
    id              serial
        primary key,
    is_success      boolean not null,
    other_location  varchar(255),
    brand           varchar(255),
    round_dosis     varchar(60),
    date            date,
    reason_negative text,
    municipality_id integer
        constraint report_dosiscovid_municipality_id_0225e0db_fk_catalog_m
            references geo_municipality
            deferrable initially deferred,
    state_id        integer
        constraint report_dosiscovid_state_id_352fdafb_fk_desabasto_state_id
            references desabasto_state
            deferrable initially deferred,
    covid_report_id integer
        constraint report_dosiscovid_covid_report_id_2fb81b8d_fk_report_co
            references report_covidreport
            deferrable initially deferred
);

alter table report_dosiscovid
    owner to user_desabasto;

create index if not exists report_dosiscovid_covid_report_id_2fb81b8d
    on report_dosiscovid (covid_report_id);

create index if not exists report_dosiscovid_municipality_id_0225e0db
    on report_dosiscovid (municipality_id);

create index if not exists report_dosiscovid_state_id_352fdafb
    on report_dosiscovid (state_id);

create table if not exists task_asynctask
(
    id                bigint generated by default as identity
        primary key,
    request_id        varchar(100),
    function_name     varchar(100),
    function_after    varchar(100),
    original_request  jsonb,
    params_after      jsonb,
    result            jsonb,
    traceback         text,
    date_start        timestamp with time zone,
    date_end          timestamp with time zone,
    data_file_id      integer
        constraint task_asynctask_data_file_id_2e02da79_fk_inai_datafile_id
            references inai_datafile
            deferrable initially deferred,
    file_control_id   integer
        constraint task_asynctask_file_control_id_5810f52e_fk_data_para
            references data_param_filecontrol
            deferrable initially deferred,
    parent_task_id    bigint
        constraint task_asynctask_parent_task_id_5412debc_fk_task_asynctask_id
            references task_asynctask
            deferrable initially deferred,
    petition_id       integer
        constraint task_asynctask_petition_id_61e5f2dc_fk_inai_petition_id
            references inai_petition
            deferrable initially deferred,
    status_task_id    varchar(80)
        constraint task_asynctask_status_task_id_91c2c63f_fk_classify_
            references classify_task_statustask
            deferrable initially deferred,
    user_id           integer
        constraint task_asynctask_user_id_3d52732b_fk_auth_user_id
            references auth_user
            deferrable initially deferred,
    date_arrive       timestamp with time zone,
    subgroup          varchar(100),
    task_function_id  varchar(100)
        constraint task_asynctask_task_function_id_5dfac4c3_fk_classify_
            references classify_task_taskfunction
            deferrable initially deferred,
    is_current        boolean not null,
    errors            jsonb,
    reply_file_id     integer
        constraint task_asynctask_reply_file_id_56070d9e_fk_inai_replyfile_id
            references inai_replyfile
            deferrable initially deferred,
    is_massive        boolean not null,
    sheet_file_id     integer
        constraint task_asynctask_sheet_file_id_5597a2d0_fk_inai_sheetfile_id
            references inai_sheetfile
            deferrable initially deferred,
    date_sent         timestamp with time zone,
    entity_week_id    integer
        constraint task_asynctask_entity_week_id_b375db52_fk_inai_entityweek_id
            references inai_entityweek
            deferrable initially deferred,
    entity_month_id   integer
        constraint task_asynctask_entity_month_id_310e4e44_fk_inai_entitymonth_id
            references inai_entitymonth
            deferrable initially deferred,
    entity_id         integer
        constraint task_asynctask_entity_id_889e4b79_fk_geo_entity_id
            references geo_entity
            deferrable initially deferred,
    finished_function varchar(100)
);

alter table task_asynctask
    owner to user_desabasto;

create index if not exists task_asynctask_data_file_id_2e02da79
    on task_asynctask (data_file_id);

create index if not exists task_asynctask_entity_id_889e4b79
    on task_asynctask (entity_id);

create index if not exists task_asynctask_entity_month_id_310e4e44
    on task_asynctask (entity_month_id);

create index if not exists task_asynctask_entity_week_id_b375db52
    on task_asynctask (entity_week_id);

create index if not exists task_asynctask_file_control_id_5810f52e
    on task_asynctask (file_control_id);

create index if not exists task_asynctask_parent_task_id_5412debc
    on task_asynctask (parent_task_id);

create index if not exists task_asynctask_petition_id_61e5f2dc
    on task_asynctask (petition_id);

create index if not exists task_asynctask_reply_file_id_56070d9e
    on task_asynctask (reply_file_id);

create index if not exists task_asynctask_sheet_file_id_5597a2d0
    on task_asynctask (sheet_file_id);

create index if not exists task_asynctask_status_task_id_91c2c63f
    on task_asynctask (status_task_id);

create index if not exists task_asynctask_status_task_id_91c2c63f_like
    on task_asynctask (status_task_id varchar_pattern_ops);

create index if not exists task_asynctask_task_function_id_5dfac4c3
    on task_asynctask (task_function_id);

create index if not exists task_asynctask_task_function_id_5dfac4c3_like
    on task_asynctask (task_function_id varchar_pattern_ops);

create index if not exists task_asynctask_user_id_3d52732b
    on task_asynctask (user_id);

create table if not exists task_platform
(
    id                 bigint generated by default as identity
        primary key,
    version            varchar(10) not null,
    has_constrains     boolean     not null,
    create_constraints jsonb,
    delete_constraints jsonb
);

alter table task_platform
    owner to user_yeeko;

create materialized view if not exists drugs_and_prescriptions as
SELECT drug.sheet_file         AS sheet_id,
       pres.entity_id,
       pres.month,
       pres.iso_week,
       pres.iso_year,
       pres.uuid_folio,
       pres.delivered_final_id AS delivered
FROM formula_rx pres
         JOIN formula_drug drug ON pres.uuid_folio = drug.rx_id;

alter materialized view drugs_and_prescriptions owner to user_yeeko;

create materialized view if not exists drugs_and_prescriptions_custom as
SELECT csf.sheet_id,
       csf.entity_id,
       pres.month,
       pres.iso_week,
       pres.iso_year,
       pres.uuid_folio,
       pres.delivered_final_id AS delivered
FROM formula_drug drug
         JOIN custom_sheet_files csf ON drug.sheet_file = csf.sheet_id
         JOIN formula_rx pres ON pres.uuid_folio = drug.rx_id;

alter materialized view drugs_and_prescriptions_custom owner to user_yeeko;

create materialized view if not exists drugs_and_prescriptions_valid as
SELECT vsf.sheet_id,
       vsf.entity_id,
       pres.month,
       pres.iso_week,
       pres.iso_year,
       pres.uuid_folio,
       pres.delivered_final_id AS delivered
FROM formula_drug drug
         JOIN valid_sheet_files vsf ON drug.sheet_file = vsf.sheet_id
         JOIN formula_rx pres ON pres.uuid_folio = drug.rx_id;

alter materialized view drugs_and_prescriptions_valid owner to user_yeeko;

create materialized view if not exists formula_review_uniques as
SELECT formula_drug.rx_id      AS uuid,
       formula_rx.iso_year,
       formula_rx.month,
       formula_rx.iso_week,
       formula_drug.lap_sheet_id,
       formula_drug.sheet_file AS sheet_file_id
FROM formula_drug
         JOIN formula_rx ON formula_drug.rx_id = formula_rx.uuid_folio;

alter materialized view formula_review_uniques owner to user_yeeko;

create materialized view if not exists mat_merge_sheetfiles_not as
SELECT sheetfile.id AS sheetfile_id,
       datafile.entity_id
FROM inai_sheetfile sheetfile
         JOIN inai_datafile datafile ON sheetfile.data_file_id = datafile.id
WHERE sheetfile.behavior_id::text = 'need_merge'::text
   OR sheetfile.behavior_id::text = 'merged'::text;

alter materialized view mat_merge_sheetfiles_not owner to user_yeeko;

create materialized view if not exists prescriptions_by_delivered as
SELECT inst.code,
       ent.name                         AS entity_name,
       presc.iso_year,
       presc.month,
       df.name                          AS delivered_short_name,
       count(DISTINCT presc.uuid_folio) AS prescription_count,
       sum(drug.prescribed_amount)      AS total_prescribed_amount,
       sum(drug.delivered_amount)       AS total_delivered_amount
FROM geo_entity ent
         JOIN geo_institution inst ON ent.institution_id = inst.id
         JOIN formula_rx presc ON ent.id = presc.entity_id
         JOIN formula_drug drug ON presc.uuid_folio = drug.rx_id
         JOIN med_cat_delivered df ON presc.delivered_final_id::text = df.hex_hash::text
GROUP BY ent.name, inst.code, presc.iso_year, presc.month, df.name
ORDER BY ent.name, inst.code, presc.iso_year, presc.month, df.name;

alter materialized view prescriptions_by_delivered owner to user_yeeko;

create materialized view if not exists prescriptions_simple_by_delivered as
SELECT inst.code,
       ent.name                AS entity_name,
       presc.iso_year,
       presc.month,
       df.name                 AS delivered_short_name,
       count(presc.uuid_folio) AS prescription_count
FROM geo_entity ent
         JOIN geo_institution inst ON ent.institution_id = inst.id
         JOIN formula_rx presc ON ent.id = presc.entity_id
         JOIN med_cat_delivered df ON presc.delivered_final_id::text = df.hex_hash::text
GROUP BY ent.name, inst.code, presc.iso_year, presc.month, df.name
ORDER BY ent.name, inst.code, presc.iso_year, presc.month, df.name;

alter materialized view prescriptions_simple_by_delivered owner to user_yeeko;

create or replace view custom_sheet_files(sheet_id, entity_id) as
SELECT sf.id AS sheet_id,
       datafile.entity_id
FROM inai_sheetfile sf
         JOIN inai_datafile datafile ON sf.data_file_id = datafile.id
WHERE sf.behavior_id::text <> 'invalid'::text;

alter table custom_sheet_files
    owner to user_yeeko;

create or replace view valid_sheet_files(sheet_id, entity_id) as
SELECT sf.id AS sheet_id,
       datafile.entity_id
FROM inai_sheetfile sf
         JOIN inai_datafile datafile ON sf.data_file_id = datafile.id
WHERE sf.behavior_id::text <> 'invalid'::text;

alter table valid_sheet_files
    owner to user_yeeko;

create or replace view mat_merge_sheetfiles(sheetfile_id, entity_id) as
SELECT sheetfile.id AS sheetfile_id,
       datafile.entity_id
FROM inai_sheetfile sheetfile
         JOIN inai_datafile datafile ON sheetfile.data_file_id = datafile.id
WHERE sheetfile.behavior_id::text = 'need_merge'::text
   OR sheetfile.behavior_id::text = 'merged'::text;

alter table mat_merge_sheetfiles
    owner to user_yeeko;

