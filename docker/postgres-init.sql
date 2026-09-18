-- Runs once, on first boot of an empty Postgres data volume.
-- Postgres' official entrypoint creates only the single database named by
-- POSTGRES_DB, so the test database has to be created here.
--
-- Kept separate from the app database because the test suite drops and
-- recreates its entire schema on every run.
CREATE DATABASE app_test;
