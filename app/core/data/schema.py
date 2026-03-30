"""
数据模式定义
"""

from dataclasses import dataclass, field
from typing import List, Dict
import pandas as pd


@dataclass
class DataSchema:
    """数据模式定义"""
    
    required_columns: List[str] = field(default_factory=list)
    optional_columns: List[str] = field(default_factory=list)
    column_types: Dict[str, str] = field(default_factory=dict)
    
    def validate(self, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """验证数据是否符合模式"""
        errors = []
        
        # 检查必需列
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # 检查类型（更宽松的检查）
        for col, expected_type in self.column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                
                # 宽松的数字类型检查
                if expected_type == "number":
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        errors.append(f"Column '{col}' should be numeric, got {actual_type}")
                # 宽松的日期类型检查
                elif expected_type == "datetime":
                    # 接受 object 类型（字符串日期）或 datetime 类型
                    if not (pd.api.types.is_datetime64_any_dtype(df[col]) or 
                           actual_type == "object"):
                        errors.append(f"Column '{col}' should be datetime-like, got {actual_type}")
                # 严格检查其他类型
                elif expected_type not in actual_type.lower():
                    errors.append(f"Column '{col}' should be {expected_type}, got {actual_type}")
        
        return len(errors) == 0, errors
