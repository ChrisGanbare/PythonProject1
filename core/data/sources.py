"""
数据源层 - 支持多种数据输入方式

对标 Flourish 的数据绑定能力
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, List
from pathlib import Path
import pandas as pd
import json


class DataSource(ABC):
    """数据源协议"""
    
    @abstractmethod
    def load(self) -> pd.DataFrame:
        """加载数据"""
        pass
    
    @abstractmethod
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        """验证数据格式"""
        pass


class CSVSource(DataSource):
    """CSV 数据源"""
    
    def __init__(
        self, 
        path: Union[str, Path],
        encoding: str = "utf-8",
        **kwargs
    ):
        self.path = Path(path)
        self.encoding = encoding
        self.kwargs = kwargs
    
    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.path}")
        
        return pd.read_csv(
            self.path,
            encoding=self.encoding,
            **self.kwargs
        )
    
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        df = self.load()
        return schema.validate(df)


class ExcelSource(DataSource):
    """Excel 数据源"""
    
    def __init__(
        self,
        path: Union[str, Path],
        sheet_name: Optional[str] = None,
        **kwargs
    ):
        self.path = Path(path)
        self.sheet_name = sheet_name
        self.kwargs = kwargs
    
    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.path}")
        
        return pd.read_excel(
            self.path,
            sheet_name=self.sheet_name,
            **self.kwargs
        )
    
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        df = self.load()
        return schema.validate(df)


class GoogleSheetsSource(DataSource):
    """Google Sheets 数据源"""
    
    def __init__(
        self,
        url: str,
        credentials: Optional[Dict[str, Any]] = None,
        sheet_name: str = "Sheet1"
    ):
        self.url = url
        self.credentials = credentials
        self.sheet_name = sheet_name
    
    def load(self) -> pd.DataFrame:
        # TODO: 实现 Google Sheets API 集成
        # 目前使用 gspread 库
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            if self.credentials:
                creds = Credentials.from_service_account_info(
                    self.credentials,
                    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
                )
                client = gspread.authorize(creds)
                sheet = client.open_by_url(self.url).worksheet(self.sheet_name)
                data = sheet.get_all_records()
                return pd.DataFrame(data)
            else:
                raise ValueError("Credentials required for Google Sheets")
                
        except ImportError:
            raise ImportError(
                "Install gspread: pip install gspread google-auth"
            )
    
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        df = self.load()
        return schema.validate(df)


class APIDataSource(DataSource):
    """API 数据源"""
    
    def __init__(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data_path: str = "data",
        **kwargs
    ):
        self.endpoint = endpoint
        self.method = method
        self.params = params or {}
        self.headers = headers or {}
        self.data_path = data_path
        self.kwargs = kwargs
    
    def load(self) -> pd.DataFrame:
        import requests
        
        response = requests.request(
            method=self.method,
            url=self.endpoint,
            params=self.params,
            headers=self.headers,
            **self.kwargs
        )
        response.raise_for_status()
        
        data = response.json()
        
        # 支持嵌套数据提取
        if self.data_path:
            for key in self.data_path.split("."):
                data = data.get(key, [])
        
        return pd.DataFrame(data)
    
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        df = self.load()
        return schema.validate(df)


class InlineDataSource(DataSource):
    """内联数据源（Dict/List）"""
    
    def __init__(self, data: Union[Dict, List]):
        self.data = data
    
    def load(self) -> pd.DataFrame:
        return pd.DataFrame(self.data)
    
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        df = self.load()
        return schema.validate(df)


class JSONSource(DataSource):
    """JSON 文件数据源"""
    
    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
    
    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"JSON file not found: {self.path}")
        
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return pd.DataFrame(data)
    
    def validate(self, schema: 'DataSchema') -> tuple[bool, list]:
        df = self.load()
        return schema.validate(df)


# 便捷工厂函数
def load_data(
    source: Union[str, Path, Dict, List],
    **kwargs
) -> pd.DataFrame:
    """
    便捷加载数据
    
    Args:
        source: 数据源 (路径、Dict、List)
        **kwargs: 传递给具体数据源的参数
    
    Returns:
        pd.DataFrame
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        suffix = path.suffix.lower()
        
        if suffix == ".csv":
            return CSVSource(path, **kwargs).load()
        elif suffix in [".xlsx", ".xls"]:
            return ExcelSource(path, **kwargs).load()
        elif suffix == ".json":
            return JSONSource(path).load()
        elif source.startswith("http"):
            return APIDataSource(source, **kwargs).load()
    
    elif isinstance(source, (dict, list)):
        return InlineDataSource(source).load()
    
    raise ValueError(f"Unknown data source type: {type(source)}")


# 延迟导入避免循环依赖
from .schema import DataSchema
