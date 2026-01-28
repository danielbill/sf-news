"""测试配置"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.storage import TimelineDB
from src.models import Article, SourceType


@pytest.fixture
def test_db(tmp_path):
    """测试数据库"""
    # 创建测试数据库目录
    test_db_dir = tmp_path / "data" / "db"
    test_db_dir.mkdir(parents=True, exist_ok=True)

    # 使用 patch 模拟 Path 构造函数，重定向到测试目录
    with patch('src.storage.timeline_db.Path') as mock_path_class:
        # 让 mock 的 Path 类正常工作，但重定向 db 路径
        def side_effect(path):
            path_str = str(path)
            if "data/db" in path_str:
                path_str = path_str.replace("data/db", str(test_db_dir))
            return Path(path_str)

        mock_path_class.side_effect = side_effect

        # 同时需要支持 Path 的除法操作
        real_path = Path
        mock_path_class.__truediv__ = lambda self, other: real_path(str(self) / other)

        db = TimelineDB()
        db.init_db()

        yield db


@pytest.fixture
def sample_article():
    """示例文章"""
    return Article(
        title="马斯克宣布星舰发射计划",
        url="https://example.com/musk-starship",
        source=SourceType.CANKAOXIAOXI,
        timestamp=datetime.now(),
    )
