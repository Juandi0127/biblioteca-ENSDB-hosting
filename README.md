# Biblioteca ENSDB

This Flask application provides a simple library portal.  historically it
used an SQLite file; the code now supports MySQL so it can be deployed on
platforms like Railway.

## Local development

1. Create a virtual environment and activate it:

   ```powershell
   python -m venv ll_env
   .\ll_env\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. If you don't set any `MYSQL_*` environment variables the app will use
   SQLite (a file named `biblioteca.db` in the project root).

3. Run the app with `python biblioteca/app.py`.  The first run creates the
   necessary tables and applies migrations automatically.

## Switching to MySQL

Railway (and similar hosts) provide a MySQL addon and expose connection
parameters via environment variables.  When `MYSQL_DATABASE` is present the
application automatically uses MySQL instead of SQLite.

### Creating the database in MySQL Workbench

1. Open MySQL Workbench and connect to your server instance.
2. In the *SQL Editor* open a new query tab and execute:

   ```sql
   CREATE DATABASE IF NOT EXISTS `biblioteca`
   CHARACTER SET utf8mb4
   COLLATE utf8mb4_unicode_ci;
   ```

3. (Optional) select the database and inspect or drop tables; the Python
tool below will create them for you when you run the application.

4. In your system environment (or Railway settings) define variables:

   ```powershell
   setx MYSQL_HOST localhost
   setx MYSQL_USER root
   setx MYSQL_PASSWORD "tu_contraseña"
   setx MYSQL_DATABASE biblioteca
   ```

   Restart your terminal after running `setx` so the variables take effect.

### Importing existing data

If you have an existing `biblioteca.db` file and wish to move the data to
MySQL, run the companion script provided in the repository:

```powershell
python migrate_sqlite_to_mysql.py \
    --sqlite biblioteca.db \
    --mysql-host localhost \
    --mysql-user root \
    --mysql-password tu_contraseña \
    --mysql-db biblioteca
```

This script will create the target database (if needed) copy table
structures, and insert all rows.  You can also preview the generated SQL
in the console before importing.

Alternatively, you can generate a dump manually and import it using
Workbench via "Server \u2192 Data Import".

## Deploying to Railway

1. Create a new project and connect your GitHub repository or push the
   code.
2. Add the MySQL plugin; note the environment variables Railway provides.
3. Create a `Procfile` (already included) with:

   ```text
   web: gunicorn biblioteca.app:app --bind 0.0.0.0:$PORT
   ```

4. Railway automatically installs dependencies from `requirements.txt`.
5. On first deployment the app runs startup code (`crear_tablas()` etc), so
the remote database will be initialised automatically.

## Notes

- Keep `biblioteca.db` locally for testing but do **not** commit it; it's
  ignored by `.gitignore`.
- To reset the database locally simply delete the file and restart the app.
- If you change the schema, use the `aplicar_migraciones()` function to
  evolve existing tables.

Happy coding! 🎓
