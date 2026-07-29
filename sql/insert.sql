USE hospital_ops;

-- CSV loading is executed by src/load_mysql.py so row counts, import order,
-- and failures are validated consistently.
--
-- PowerShell:
--   $env:HOSPITAL_DB_URL = "mysql+pymysql://user:password@localhost/hospital_ops"
--   python src/load_mysql.py --truncate
--
-- Run schema.sql before the loader. Then run views.sql and procedures.sql.
