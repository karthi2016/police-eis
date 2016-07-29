DROP TABLE IF EXISTS staging.lookup_eye_colors; 
CREATE UNLOGGED TABLE staging.lookup_eye_colors (
	code                                                                  int,                --
	value                                                                 varchar,            --
	description                                                           varchar             --
);
