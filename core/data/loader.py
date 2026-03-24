"""
数据引擎 — 多源数据加载、验证与追溯

支持 CSV、Excel、SQL、API 等多种数据源，提供统一的数据加载协议。
所有数据源均记录元数据，支持数据来源追溯。
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import pandas as pd


@dataclass
class DataSourceMetadata:
    """数据源元数据，用于追溯和审计"""

    source_type: str
    source_path_or_url: str
    loaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    row_count: int = 0
    column_count: int = 0
    file_hash: str | None = None  # 文件哈希，用于验证数据完整性
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source": self.source_path_or_url,
            "loaded_at": self.loaded_at,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "file_hash": self.file_hash,
            **self.custom_metadata,
        }


class DataSource(Protocol):
    """数据源协议 — 所有数据源必须实现此接口"""

    def load(self) -> pd.DataFrame:
        """加载数据"""
        ...

    def validate(self) -> list[str]:
        """验证数据，返回错误列表"""
        ...

    def get_metadata(self) -> DataSourceMetadata:
        """获取数据源元数据"""
        ...


class BaseDataSource(ABC):
    """数据源基类，提供通用功能"""

    def __init__(self):
        self._df: pd.DataFrame | None = None
        self._metadata: DataSourceMetadata | None = None
        self._validation_errors: list[str] = []

    @abstractmethod
    def _do_load(self) -> pd.DataFrame:
        """子类实现具体加载逻辑"""
        pass

    def load(self) -> pd.DataFrame:
        """加载数据并缓存"""
        if self._df is None:
            self._df = self._do_load()
            self._update_metadata()
        return self._df

    @abstractmethod
    def validate(self) -> list[str]:
        """验证数据"""
        pass

    @abstractmethod
    def get_metadata(self) -> DataSourceMetadata:
        """获取元数据"""
        pass

    def _update_metadata(self):
        """更新元数据"""
        if self._df is not None and self._metadata:
            self._metadata.row_count = len(self._df)
            self._metadata.column_count = len(self._df.columns)

    def _compute_file_hash(self, path: Path) -> str:
        """计算文件 SHA256 哈希"""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


class CSVSource(BaseDataSource):
    """CSV 文件数据源"""

    def __init__(
        self,
        path: str | Path,
        encoding: str = "utf-8",
        delimiter: str = ",",
        **kwargs,
    ):
        super().__init__()
        self.path = Path(path)
        self.encoding = encoding
        self.delimiter = delimiter
        self.kwargs = kwargs

        self._metadata = DataSourceMetadata(
            source_type="csv",
            source_path_or_url=str(self.path),
        )

    def _do_load(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.path}")

        self._metadata.file_hash = self._compute_file_hash(self.path)
        return pd.read_csv(
            self.path,
            encoding=self.encoding,
            sep=self.delimiter,
            **self.kwargs,
        )

    def validate(self) -> list[str]:
        errors = []
        if not self.path.exists():
            errors.append(f"File not found: {self.path}")
        elif not self.path.suffix.lower() == ".csv":
            errors.append(f"Invalid file extension: {self.path.suffix}")

        if self._df is not None:
            if self._df.empty:
                errors.append("DataFrame is empty")
            if self._df.isnull().all().all():
                errors.append("All values are null")

        return errors

    def get_metadata(self) -> DataSourceMetadata:
        if self._metadata is None:
            self._metadata = DataSourceMetadata(
                source_type="csv",
                source_path_or_url=str(self.path),
            )
        return self._metadata


class ExcelSource(BaseDataSource):
    """Excel 文件数据源"""

    def __init__(
        self,
        path: str | Path,
        sheet_name: str | int = 0,
        **kwargs,
    ):
        super().__init__()
        self.path = Path(path)
        self.sheet_name = sheet_name
        self.kwargs = kwargs

        self._metadata = DataSourceMetadata(
            source_type="excel",
            source_path_or_url=str(self.path),
        )

    def _do_load(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.path}")

        self._metadata.file_hash = self._compute_file_hash(self.path)
        return pd.read_excel(
            self.path,
            sheet_name=self.sheet_name,
            **self.kwargs,
        )

    def validate(self) -> list[str]:
        errors = []
        if not self.path.exists():
            errors.append(f"File not found: {self.path}")
        elif not self.path.suffix.lower() in [".xlsx", ".xls"]:
            errors.append(f"Invalid file extension: {self.path.suffix}")

        if self._df is not None and self._df.empty:
            errors.append("DataFrame is empty")

        return errors

    def get_metadata(self) -> DataSourceMetadata:
        if self._metadata is None:
            self._metadata = DataSourceMetadata(
                source_type="excel",
                source_path_or_url=str(self.path),
            )
        return self._metadata


class APISource(BaseDataSource):
    """API 数据源"""

    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        response_parser: str = "json",
        **kwargs,
    ):
        super().__init__()
        import requests

        self.url = url
        self.method = method
        self.headers = headers or {}
        self.params = params
        self.json_data = json_data
        self.response_parser = response_parser
        self.kwargs = kwargs
        self._requests = requests

        self._metadata = DataSourceMetadata(
            source_type="api",
            source_path_or_url=url,
            custom_metadata={
                "method": method,
                "params": params,
            },
        )

    def _do_load(self) -> pd.DataFrame:
        response = self._requests.request(
            method=self.method,
            url=self.url,
            headers=self.headers,
            params=self.params,
            json=self.json_data,
            **self.kwargs,
        )
        response.raise_for_status()

        if self.response_parser == "json":
            data = response.json()
            # 处理嵌套 JSON
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            return pd.DataFrame(data)
        elif self.response_parser == "csv":
            return pd.read_csv(filepath_or_buffer=response.text)
        else:
            raise ValueError(f"Unsupported response parser: {self.response_parser}")

    def validate(self) -> list[str]:
        errors = []
        if not self.url.startswith(("http://", "https://")):
            errors.append(f"Invalid URL: {self.url}")

        if self._df is not None and self._df.empty:
            errors.append("API returned empty data")

        return errors

    def get_metadata(self) -> DataSourceMetadata:
        if self._metadata is None:
            self._metadata = DataSourceMetadata(
                source_type="api",
                source_path_or_url=self.url,
                custom_metadata={
                    "method": self.method,
                    "params": self.params,
                },
            )
        return self._metadata


class SQLSource(BaseDataSource):
    """SQL 数据库数据源"""

    def __init__(
        self,
        connection_string: str,
        query: str,
        params: tuple | None = None,
    ):
        super().__init__()
        self.connection_string = connection_string
        self.query = query
        self.params = params

        self._metadata = DataSourceMetadata(
            source_type="sql",
            source_path_or_url=connection_string.split("@")[-1] if "@" in connection_string else connection_string,
            custom_metadata={
                "query": query,
            },
        )

    def _do_load(self) -> pd.DataFrame:
        return pd.read_sql(self.query, self.connection_string, params=self.params)

    def validate(self) -> list[str]:
        errors = []
        if not self.query.strip().upper().startswith("SELECT"):
            errors.append("Only SELECT queries are allowed")

        if self._df is not None and self._df.empty:
            errors.append("Query returned empty result")

        return errors

    def get_metadata(self) -> DataSourceMetadata:
        if self._metadata is None:
            self._metadata = DataSourceMetadata(
                source_type="sql",
                source_path_or_url=self.connection_string.split("@")[-1]
                if "@" in self.connection_string
                else self.connection_string,
                custom_metadata={"query": self.query},
            )
        return self._metadata


class DataSourceRegistry:
    """数据源注册表 — 工厂模式创建数据源"""

    _registry: dict[str, type[BaseDataSource]] = {}

    @classmethod
    def register(cls, source_type: str, source_class: type[BaseDataSource]):
        """注册数据源类型"""
        cls._registry[source_type] = source_class

    @classmethod
    def create(cls, source_type: str, **kwargs) -> BaseDataSource:
        """创建数据源实例"""
        if source_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown source type: {source_type}. Available: {available}"
            )
        return cls._registry[source_type](**kwargs)

    @classmethod
    def list_types(cls) -> list[str]:
        """列出已注册的数据源类型"""
        return list(cls._registry.keys())


# 注册默认数据源
DataSourceRegistry.register("csv", CSVSource)
DataSourceRegistry.register("excel", ExcelSource)
DataSourceRegistry.register("api", APISource)
DataSourceRegistry.register("sql", SQLSource)


@dataclass
class DataSourceConfig:
    """数据源配置 — 用于从配置文件创建数据源"""

    source_type: str
    source_config: dict[str, Any]
    validation_rules: list[dict[str, Any]] = field(default_factory=list)


def create_data_source_from_config(config: DataSourceConfig | dict) -> BaseDataSource:
    """从配置创建数据源"""
    if isinstance(config, dict):
        config = DataSourceConfig(**config)

    source = DataSourceRegistry.create(
        config.source_type, **config.source_config
    )

    # 可选：应用验证规则
    # 可在后续实现验证规则引擎

    return source


# 使用示例
if __name__ == "__main__":
    # 示例 1: 直接创建
    csv_source = CSVSource("data/sales.csv")
    df = csv_source.load()
    print(f"Loaded {len(df)} rows from CSV")

    # 示例 2: 通过注册表创建
    source = DataSourceRegistry.create(
        "api",
        url="https://api.example.com/data",
        headers={"Authorization": "Bearer token"},
    )
    df = source.load()

    # 示例 3: 从配置创建
    config = {
        "source_type": "excel",
        "source_config": {
            "path": "data/financial_report.xlsx",
            "sheet_name": "Q4 Summary",
        },
    }
    source = create_data_source_from_config(config)
    df = source.load()

    # 验证
    errors = source.validate()
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("Data validation passed")

    # 获取元数据
    metadata = source.get_metadata()
    print(f"Metadata: {metadata.to_dict()}")
