"""
Database Tool

Tool for database operations and queries.
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .base_tool import BaseTool, ToolConfig, ToolType, ToolCapability, ToolResult


class DatabaseTool(BaseTool):
    """
    Tool for database operations.
    
    Capabilities:
    - Execute SQL queries
    - Insert/Update/Delete operations
    - Database schema operations
    - Transaction management
    - Query optimization
    """
    
    def __init__(self, config: Optional[ToolConfig] = None):
        if config is None:
            config = ToolConfig(
                name="Database Tool",
                tool_type=ToolType.DATABASE,
                description="Database operations tool",
                capabilities=[ToolCapability.READ, ToolCapability.WRITE],
                timeout=60,
                rate_limit=100
            )
        super().__init__(config)
        
        # Database connection
        self.engine = None
        self.session_factory = None
        self.connection_string = None
        
        # Query cache
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute database operation with given parameters."""
        operation = parameters.get("operation", "select")
        query = parameters.get("query", "")
        table = parameters.get("table", "")
        data = parameters.get("data", {})
        conditions = parameters.get("conditions", {})
        limit = parameters.get("limit", 100)
        
        if not query and not table:
            return ToolResult(
                success=False,
                error="Either query or table must be provided"
            )
        
        try:
            if operation == "select":
                result = await self._select_query(query, table, conditions, limit)
            elif operation == "insert":
                result = await self._insert_data(table, data)
            elif operation == "update":
                result = await self._update_data(table, data, conditions)
            elif operation == "delete":
                result = await self._delete_data(table, conditions)
            elif operation == "execute":
                result = await self._execute_raw_query(query)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported operation: {operation}"
                )
            
            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "operation": operation,
                    "table": table,
                    "rows_affected": result.get("rows_affected", 0)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Database operation failed: {str(e)}"
            )
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate database operation parameters."""
        operation = parameters.get("operation", "select")
        
        if operation == "select":
            return "query" in parameters or "table" in parameters
        elif operation in ["insert", "update", "delete"]:
            return "table" in parameters
        elif operation == "execute":
            return "query" in parameters
        else:
            return False
    
    async def _select_query(self, query: str, table: str, conditions: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """Execute SELECT query."""
        if query:
            # Use raw SQL query
            sql_query = query
        else:
            # Build query from table and conditions
            sql_query = f"SELECT * FROM {table}"
            
            if conditions:
                where_clause = " AND ".join([f"{k} = :{k}" for k in conditions.keys()])
                sql_query += f" WHERE {where_clause}"
            
            sql_query += f" LIMIT {limit}"
        
        # Check cache
        cache_key = f"select_{hash(sql_query)}_{hash(str(conditions))}"
        if cache_key in self.query_cache:
            cached_result = self.query_cache[cache_key]
            if self._is_cache_valid(cached_result):
                return cached_result["data"]
        
        # Execute query
        result = await self._execute_query(sql_query, conditions)
        
        # Cache result
        self.query_cache[cache_key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        return result
    
    async def _insert_data(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into table."""
        if not data:
            return {"rows_affected": 0, "error": "No data provided"}
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        sql_query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        result = await self._execute_query(sql_query, data)
        return result
    
    async def _update_data(self, table: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Update data in table."""
        if not data:
            return {"rows_affected": 0, "error": "No data provided"}
        
        if not conditions:
            return {"rows_affected": 0, "error": "No conditions provided for update"}
        
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = :where_{k}" for k in conditions.keys()])
        
        sql_query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        # Combine data and conditions with different prefixes
        params = {**data, **{f"where_{k}": v for k, v in conditions.items()}}
        
        result = await self._execute_query(sql_query, params)
        return result
    
    async def _delete_data(self, table: str, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Delete data from table."""
        if not conditions:
            return {"rows_affected": 0, "error": "No conditions provided for delete"}
        
        where_clause = " AND ".join([f"{k} = :{k}" for k in conditions.keys()])
        sql_query = f"DELETE FROM {table} WHERE {where_clause}"
        
        result = await self._execute_query(sql_query, conditions)
        return result
    
    async def _execute_raw_query(self, query: str) -> Dict[str, Any]:
        """Execute raw SQL query."""
        result = await self._execute_query(query, {})
        return result
    
    async def _execute_query(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query with parameters."""
        if not self.engine:
            return {"error": "Database not connected"}
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), parameters)
                
                # Handle different types of queries
                if query.strip().upper().startswith("SELECT"):
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, column in enumerate(columns):
                            row_dict[column] = row[i]
                        data.append(row_dict)
                    
                    return {
                        "data": data,
                        "rows_affected": len(data)
                    }
                else:
                    return {
                        "rows_affected": result.rowcount,
                        "message": "Query executed successfully"
                    }
                    
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached query result is still valid."""
        if "timestamp" not in cached_result:
            return False
        
        age = (datetime.now() - cached_result["timestamp"]).total_seconds()
        return age < self.cache_ttl
    
    async def connect(self, connection_string: str) -> bool:
        """Connect to database."""
        try:
            self.connection_string = connection_string
            self.engine = create_async_engine(connection_string)
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            print(f"Connected to database: {connection_string}")
            return True
            
        except Exception as e:
            print(f"Database connection failed: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            print("Disconnected from database")
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table."""
        if not self.engine:
            return {"error": "Database not connected"}
        
        try:
            # Get table schema
            schema_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
            
            result = await self._execute_query(schema_query, {"table_name": table_name})
            
            return {
                "table_name": table_name,
                "columns": result.get("data", []),
                "column_count": len(result.get("data", []))
            }
            
        except Exception as e:
            return {"error": f"Failed to get table info: {str(e)}"}
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.engine:
            return {"error": "Database not connected"}
        
        try:
            # Get table count
            table_count_query = """
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
            
            result = await self._execute_query(table_count_query, {})
            table_count = result.get("data", [{}])[0].get("table_count", 0)
            
            return {
                "table_count": table_count,
                "connection_string": self.connection_string,
                "cache_size": len(self.query_cache)
            }
            
        except Exception as e:
            return {"error": f"Failed to get database stats: {str(e)}"}
    
    def clear_query_cache(self) -> None:
        """Clear query cache."""
        self.query_cache.clear()
    
    def set_cache_ttl(self, ttl: int) -> None:
        """Set cache TTL in seconds."""
        self.cache_ttl = ttl
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
