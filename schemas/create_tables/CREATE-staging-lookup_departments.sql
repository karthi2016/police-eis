DROP TABLE IF EXISTS staging.lookup_departments; 
CREATE UNLOGGED TABLE staging.lookup_departments (
	code                                                                  int,                --
	value                                                                 varchar,            --
	description                                                           varchar             --
);
