DROP TABLE IF EXISTS staging.lookup_report_types; 
CREATE UNLOGGED TABLE staging.lookup_report_types (
	code                                                                  int,                --
	value                                                                 varchar,            --
	description                                                           varchar             --
);
