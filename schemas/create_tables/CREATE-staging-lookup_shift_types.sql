DROP TABLE IF EXISTS staging.lookup_shift_types; 
CREATE UNLOGGED TABLE staging.lookup_shift_types (
	code                                                                  int,                --
	value                                                                 varchar,            --
	description                                                           varchar             --
);
