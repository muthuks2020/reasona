"""
Built-in Neural Tools for common operations.

These tools provide basic functionality that agents commonly need,
including calculations, web requests, file operations, and more.
"""

from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

import httpx

from reasona.tools.base import NeuralTool


class Calculator(NeuralTool):
    """
    Perform mathematical calculations safely.
    
    Supports basic arithmetic, trigonometry, and common math functions.
    """
    
    name = "calculator"
    description = "Evaluate mathematical expressions safely"
    
    # Safe math functions
    SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "floor": math.floor,
        "ceil": math.ceil,
        "pi": math.pi,
        "e": math.e,
    }
    
    def execute(self, expression: str) -> dict[str, Any]:
        """
        Evaluate a mathematical expression.
        
        Args:
            expression: Math expression to evaluate (e.g., "2 + 2", "sqrt(16)")
        
        Returns:
            Dictionary with result and expression.
        """
        try:
            # Create safe evaluation context
            safe_dict = {"__builtins__": {}}
            safe_dict.update(self.SAFE_FUNCTIONS)
            
            # Evaluate expression
            result = eval(expression, safe_dict)
            
            return {
                "expression": expression,
                "result": result,
                "success": True,
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "success": False,
            }


class WebSearch(NeuralTool):
    """
    Search the web for information.
    
    Note: This is a placeholder that simulates web search.
    For production use, integrate with a real search API.
    """
    
    name = "web_search"
    description = "Search the web for information on a topic"
    
    def execute(
        self,
        query: str,
        num_results: int = 5,
    ) -> dict[str, Any]:
        """
        Search the web.
        
        Args:
            query: Search query string.
            num_results: Number of results to return.
        
        Returns:
            Dictionary with search results.
        """
        # Placeholder - in production, integrate with a search API
        return {
            "query": query,
            "note": "Web search requires API integration. Consider using Tavily, Serper, or similar services.",
            "results": [],
        }


class HttpRequest(NeuralTool):
    """
    Make HTTP requests to external APIs.
    
    Supports GET, POST, PUT, DELETE methods with headers and body.
    """
    
    name = "http_request"
    description = "Make HTTP requests to external APIs"
    
    def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        body: Optional[Union[str, dict]] = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Make an HTTP request.
        
        Args:
            url: The URL to request.
            method: HTTP method (GET, POST, PUT, DELETE).
            headers: Optional request headers.
            body: Optional request body (string or dict for JSON).
            timeout: Request timeout in seconds.
        
        Returns:
            Dictionary with response data.
        """
        try:
            with httpx.Client(timeout=timeout) as client:
                # Prepare body
                json_body = None
                data_body = None
                
                if body:
                    if isinstance(body, dict):
                        json_body = body
                    else:
                        data_body = body
                
                response = client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_body,
                    content=data_body,
                )
                
                # Try to parse JSON response
                try:
                    response_body = response.json()
                except:
                    response_body = response.text
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                    "success": response.is_success,
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }


class FileReader(NeuralTool):
    """
    Read content from files on the filesystem.
    
    Supports text files with optional encoding specification.
    """
    
    name = "file_reader"
    description = "Read content from a file"
    
    def execute(
        self,
        path: str,
        encoding: str = "utf-8",
        max_bytes: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Read a file.
        
        Args:
            path: Path to the file to read.
            encoding: File encoding (default: utf-8).
            max_bytes: Maximum bytes to read (optional).
        
        Returns:
            Dictionary with file content and metadata.
        """
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return {
                    "error": f"File not found: {path}",
                    "success": False,
                }
            
            if not file_path.is_file():
                return {
                    "error": f"Not a file: {path}",
                    "success": False,
                }
            
            # Read file
            if max_bytes:
                content = file_path.read_bytes()[:max_bytes].decode(encoding)
            else:
                content = file_path.read_text(encoding=encoding)
            
            return {
                "path": str(file_path.absolute()),
                "content": content,
                "size_bytes": file_path.stat().st_size,
                "success": True,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }


class FileWriter(NeuralTool):
    """
    Write content to files on the filesystem.
    
    Supports creating new files and appending to existing ones.
    """
    
    name = "file_writer"
    description = "Write content to a file"
    
    def execute(
        self,
        path: str,
        content: str,
        mode: str = "write",
        encoding: str = "utf-8",
    ) -> dict[str, Any]:
        """
        Write to a file.
        
        Args:
            path: Path to the file to write.
            content: Content to write.
            mode: Write mode - "write" (overwrite) or "append".
            encoding: File encoding (default: utf-8).
        
        Returns:
            Dictionary with operation result.
        """
        try:
            file_path = Path(path)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            write_mode = "a" if mode == "append" else "w"
            
            with open(file_path, write_mode, encoding=encoding) as f:
                f.write(content)
            
            return {
                "path": str(file_path.absolute()),
                "bytes_written": len(content.encode(encoding)),
                "mode": mode,
                "success": True,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }


class ShellCommand(NeuralTool):
    """
    Execute shell commands.
    
    WARNING: Use with caution. This tool can execute arbitrary commands.
    Consider sandboxing or restricting available commands in production.
    """
    
    name = "shell_command"
    description = "Execute a shell command"
    
    def execute(
        self,
        command: str,
        timeout: float = 30.0,
        shell: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a shell command.
        
        Args:
            command: The command to execute.
            timeout: Execution timeout in seconds.
            shell: Whether to run in a shell (default: True).
        
        Returns:
            Dictionary with command output and exit code.
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0,
            }
            
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "success": False,
            }
        except Exception as e:
            return {
                "command": command,
                "error": str(e),
                "success": False,
            }


class DateTime(NeuralTool):
    """
    Get current date/time and perform date calculations.
    """
    
    name = "datetime"
    description = "Get current date/time or perform date calculations"
    
    def execute(
        self,
        operation: str = "now",
        format: str = "%Y-%m-%d %H:%M:%S",
        timezone_name: str = "UTC",
    ) -> dict[str, Any]:
        """
        Perform date/time operations.
        
        Args:
            operation: Operation type - "now", "date", "time", "timestamp".
            format: Output format string (strftime).
            timezone_name: Timezone name (default: UTC).
        
        Returns:
            Dictionary with date/time information.
        """
        now = datetime.now(timezone.utc)
        
        if operation == "now":
            return {
                "datetime": now.strftime(format),
                "timestamp": now.timestamp(),
                "timezone": "UTC",
                "iso": now.isoformat(),
            }
        elif operation == "date":
            return {
                "date": now.strftime("%Y-%m-%d"),
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "weekday": now.strftime("%A"),
            }
        elif operation == "time":
            return {
                "time": now.strftime("%H:%M:%S"),
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
            }
        elif operation == "timestamp":
            return {
                "timestamp": now.timestamp(),
                "timestamp_ms": int(now.timestamp() * 1000),
            }
        else:
            return {
                "error": f"Unknown operation: {operation}",
                "success": False,
            }


class JsonParser(NeuralTool):
    """
    Parse, validate, and manipulate JSON data.
    """
    
    name = "json_parser"
    description = "Parse, validate, and extract data from JSON"
    
    def execute(
        self,
        json_string: str,
        path: Optional[str] = None,
        operation: str = "parse",
    ) -> dict[str, Any]:
        """
        Parse or manipulate JSON data.
        
        Args:
            json_string: JSON string to parse.
            path: Optional JSONPath-like path to extract (e.g., "data.users[0].name").
            operation: Operation - "parse", "validate", "prettify".
        
        Returns:
            Dictionary with parsed data or validation result.
        """
        try:
            data = json.loads(json_string)
            
            if operation == "validate":
                return {
                    "valid": True,
                    "type": type(data).__name__,
                }
            
            if operation == "prettify":
                return {
                    "formatted": json.dumps(data, indent=2),
                    "success": True,
                }
            
            # Handle path extraction
            if path:
                result = data
                for part in path.split("."):
                    # Handle array indexing
                    if "[" in part and "]" in part:
                        key = part[:part.index("[")]
                        index = int(part[part.index("[") + 1:part.index("]")])
                        if key:
                            result = result[key]
                        result = result[index]
                    else:
                        result = result[part]
                return {
                    "path": path,
                    "value": result,
                    "success": True,
                }
            
            return {
                "data": data,
                "type": type(data).__name__,
                "success": True,
            }
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": str(e),
                "success": False,
            }
        except (KeyError, IndexError, TypeError) as e:
            return {
                "error": f"Path extraction failed: {e}",
                "success": False,
            }
