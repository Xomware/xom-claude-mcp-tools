"""Database query executor tool."""

import os
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger


class QueryExecutor:
    """Executes database queries safely."""

    def __init__(self):
        """Initialize query executor."""
        db_url = self._build_connection_string()
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _build_connection_string(self) -> str:
        """Build database connection string from environment variables.

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

    async def execute(
        self, query: str, params: Optional[List] = None
    ) -> Dict[str, Any]:
        """Execute a SELECT query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        try:
            # Prevent dangerous operations
            if any(op in query.upper() for op in ["DROP", "DELETE", "TRUNCATE"]):
                return {"error": "Dangerous operation not allowed"}

            session = self.SessionLocal()
            try:
                result = session.execute(text(query), params or {})
                rows = result.fetchall()

                # Convert to list of dicts
                rows_dict = [dict(row) for row in rows]

                logger.info(f"Executed query, returned {len(rows_dict)} rows")
                return {
                    "status": "success",
                    "row_count": len(rows_dict),
                    "rows": rows_dict,
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {"error": str(e)}

    async def execute_aggregate(
        self, metric: str, table: str, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute an aggregate query.

        Args:
            metric: Metric to aggregate (count, sum, avg, min, max)
            table: Table name
            filters: Optional WHERE conditions

        Returns:
            Aggregate result
        """
        try:
            query_parts = [f"SELECT {metric.upper()}(*) as result FROM {table}"]

            if filters:
                conditions = [f"{k}=:{k}" for k in filters.keys()]
                query_parts.append(f"WHERE {' AND '.join(conditions)}")

            query = " ".join(query_parts)

            session = self.SessionLocal()
            try:
                result = session.execute(text(query), filters or {})
                row = result.fetchone()

                logger.info(f"Executed aggregate query on {table}")
                return {
                    "status": "success",
                    "metric": metric,
                    "result": dict(row) if row else None,
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Aggregate query error: {e}")
            return {"error": str(e)}

    async def list_tables(self) -> Dict[str, Any]:
        """List all tables in the database.

        Returns:
            List of table names
        """
        try:
            from sqlalchemy import inspect

            inspector = inspect(self.engine)
            tables = inspector.get_table_names()

            logger.info(f"Listed {len(tables)} tables")
            return {
                "status": "success",
                "table_count": len(tables),
                "tables": tables,
            }

        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return {"error": str(e)}

    async def describe_table(self, table: str) -> Dict[str, Any]:
        """Get schema information for a table.

        Args:
            table: Table name

        Returns:
            Table schema
        """
        try:
            from sqlalchemy import inspect

            inspector = inspect(self.engine)
            columns = inspector.get_columns(table)

            schema = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                }
                for col in columns
            ]

            logger.info(f"Described table {table}")
            return {
                "status": "success",
                "table": table,
                "column_count": len(schema),
                "columns": schema,
            }

        except Exception as e:
            logger.error(f"Error describing table: {e}")
            return {"error": str(e)}
