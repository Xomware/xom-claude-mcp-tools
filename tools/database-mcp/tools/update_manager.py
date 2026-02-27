"""Database update manager tool."""

import os
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger


class UpdateManager:
    """Manages safe database updates."""

    def __init__(self):
        """Initialize update manager."""
        db_url = self._build_connection_string()
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _build_connection_string(self) -> str:
        """Build database connection string.

        Returns:
            SQLAlchemy connection string
        """
        driver = os.getenv("DB_DRIVER", "postgresql")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "xomware")

        if driver == "postgresql":
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        elif driver == "mysql":
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"{driver}://{user}:{password}@{host}:{port}/{database}"

    async def update(
        self, table: str, data: Dict[str, Any], conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update records in the database.

        Args:
            table: Table name
            data: Column names and values to update
            conditions: WHERE conditions

        Returns:
            Update result
        """
        try:
            # Build UPDATE query
            set_clause = ", ".join([f"{k}=:{k}" for k in data.keys()])
            where_clause = " AND ".join([f"{k}=:{k}_cond" for k in conditions.keys()])

            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

            # Prepare parameters
            params = {**data}
            for k, v in conditions.items():
                params[f"{k}_cond"] = v

            session = self.SessionLocal()
            try:
                result = session.execute(text(query), params)
                session.commit()

                logger.info(f"Updated {result.rowcount} rows in {table}")
                return {
                    "status": "success",
                    "table": table,
                    "rows_affected": result.rowcount,
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Update error: {e}")
            return {"error": str(e)}

    async def insert(
        self, table: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a new record.

        Args:
            table: Table name
            data: Column names and values

        Returns:
            Insert result
        """
        try:
            columns = ", ".join(data.keys())
            values_clause = ", ".join([f":{k}" for k in data.keys()])

            query = f"INSERT INTO {table} ({columns}) VALUES ({values_clause})"

            session = self.SessionLocal()
            try:
                result = session.execute(text(query), data)
                session.commit()

                logger.info(f"Inserted record into {table}")
                return {
                    "status": "success",
                    "table": table,
                    "rows_affected": result.rowcount,
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Insert error: {e}")
            return {"error": str(e)}

    async def delete(
        self, table: str, conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete records (with safety checks).

        Args:
            table: Table name
            conditions: WHERE conditions

        Returns:
            Delete result
        """
        try:
            # Require at least one condition to prevent accidental full table delete
            if not conditions:
                return {"error": "Delete requires at least one condition"}

            where_clause = " AND ".join([f"{k}=:{k}" for k in conditions.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"

            session = self.SessionLocal()
            try:
                result = session.execute(text(query), conditions)
                session.commit()

                logger.info(f"Deleted {result.rowcount} rows from {table}")
                return {
                    "status": "success",
                    "table": table,
                    "rows_affected": result.rowcount,
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"error": str(e)}

    async def bulk_update(
        self, table: str, records: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk update multiple records.

        Args:
            table: Table name
            records: List of records to update

        Returns:
            Bulk update result
        """
        try:
            session = self.SessionLocal()
            try:
                total_affected = 0
                for record in records:
                    # Assuming first field is the ID
                    keys = list(record.keys())
                    id_key = keys[0]
                    id_value = record[id_key]

                    set_clause = ", ".join([f"{k}=:{k}" for k in keys[1:]])
                    query = f"UPDATE {table} SET {set_clause} WHERE {id_key}=:{id_key}"

                    result = session.execute(text(query), record)
                    total_affected += result.rowcount

                session.commit()

                logger.info(f"Bulk updated {total_affected} rows in {table}")
                return {
                    "status": "success",
                    "table": table,
                    "rows_affected": total_affected,
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Bulk update error: {e}")
            return {"error": str(e)}
