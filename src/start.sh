#!/bin/bash

# Execute download_data.py to fetch the data files
python src/download_data.py

# Execute import_data.py to import data into DuckDB
python src/import_data.py

# Execute import_data_postgres.py to import data into PostgreSQL
python src/import_data_postgres.py