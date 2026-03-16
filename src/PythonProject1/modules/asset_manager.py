"""
素材资产管理模块
处理 Pexels 视频 API、下载、本地缓存等
"""

import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
import hashlib
import json

from config.settings import settings
from models.exceptions import APIError, FileDownloadError
from utils.decorators import retry, log_execution


logger = logging.getLogger(__name__)


class AssetManager:
    """素材资产管理器"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """初始化资产管理器
        
        Args:
            cache_dir: 缓存目录（若为空使用全局配置）
        """
        self.cache_dir = cache_dir or settings.api.pexels_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.pexels_api_key = settings.api.pexels_api_key
        self.pexels_base_url = "https://api.pexels.com/v1"
        
        self._cache_index_file = self.cache_dir / "cache_index.json"
        self._load_cache_index()
        
        logger.info(f"[AssetManager] 初始化完成 | 缓存目录: {self.cache_dir}")
    
    def _load_cache_index(self) -> None:
        """加载缓存索引"""
        if self._cache_index_file.exists():
            try:
                with open(self._cache_index_file, "r", encoding="utf-8") as f:
                    self._cache_index = json.load(f)
            except Exception as e:
                logger.warning(f"[AssetManager] 加载缓存索引失败: {e}")
                self._cache_index = {}
        else:
            self._cache_index = {}
    
    def _save_cache_index(self) -> None:
        """保存缓存索引"""
        try:
            with open(self._cache_index_file, "w", encoding="utf-8") as f:
                json.dump(self._cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[AssetManager] 保存缓存索引失败: {e}")
    
    def _get_cache_key(self, url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()
    
    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(APIError,))
    @log_execution(log_level="info")
    async def search_videos(
        self,
        query: str,
        count: int = 5,
        min_duration: int = 10,
        max_duration: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        搜索 Pexels 视频
        
        Args:
            query: 搜索关键词
            count: 返回数量
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）
        
        Returns:
            视频列表
        
        Raises:
            APIError: API 调用失败
        """
        if not self.pexels_api_key:
            raise APIError(
                "Pexels API 密钥未配置",
                api_name="Pexels",
            )
        
        headers = {"Authorization": self.pexels_api_key}
        params = {
            "query": query,
            "per_page": min(count, 80),
            "orientation": "portrait",  # 竖屏视频
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.pexels_base_url}/videos/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=settings.api.pexels_timeout),
                ) as resp:
                    if resp.status != 200:
                        raise APIError(
                            f"请求失败: {resp.status} {resp.reason}",
                            api_name="Pexels",
                            status_code=resp.status,
                        )
                    
                    data = await resp.json()
                    videos = data.get("videos", [])
                    
                    # 过滤时长
                    filtered_videos = [
                        v for v in videos
                        if min_duration <= v.get("duration", 0) <= max_duration
                    ]
                    
                    logger.info(f"[Pexels] 搜索 '{query}' 返回 {len(filtered_videos)} 个视频")
                    return filtered_videos[:count]
        
        except asyncio.TimeoutError:
            raise APIError(
                f"请求超时（{settings.api.pexels_timeout}秒）",
                api_name="Pexels",
            )
        except aiohttp.ClientError as e:
            raise APIError(
                f"网络请求失败: {str(e)}",
                api_name="Pexels",
            )
    
    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(FileDownloadError,))
    @log_execution(log_level="info")
    async def download_video(
        self,
        video_url: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        force_download: bool = False,
    ) -> Path:
        """
        下载视频（带缓存）
        
        Args:
            video_url: 视频 URL
            progress_callback: 进度回调函数，参数为 (已下载字节, 总字节)
            force_download: 是否强制重新下载（忽略缓存）
        
        Returns:
            本地文件路径
        
        Raises:
            FileDownloadError: 下载失败
        """
        cache_key = self._get_cache_key(video_url)
        
        # 检查缓存
        if cache_key in self._cache_index and not force_download:
            cached_file = Path(self._cache_index[cache_key])
            if cached_file.exists():
                logger.info(f"[AssetManager] 命中缓存: {cached_file}")
                return cached_file
        
        # 生成文件名
        file_ext = video_url.split('.')[-1].split('?')[0] or "mp4"
        local_file = self.cache_dir / f"{cache_key}.{file_ext}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    video_url,
                    timeout=aiohttp.ClientTimeout(total=600),  # 10分钟超时
                ) as resp:
                    if resp.status != 200:
                        raise FileDownloadError(
                            f"HTTP {resp.status}: {resp.reason}",
                            url=video_url,
                        )
                    
                    # 获取文件大小
                    total_size = int(resp.headers.get('content-length', 0))
                    
                    # 下载文件
                    downloaded = 0
                    with open(local_file, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback and total_size > 0:
                                    progress_callback(downloaded, total_size)
                    
                    # 更新缓存索引
                    self._cache_index[cache_key] = str(local_file)
                    self._save_cache_index()
                    
                    logger.info(f"[AssetManager] 下载完成: {local_file} ({downloaded} bytes)")
                    return local_file
        
        except asyncio.TimeoutError:
            raise FileDownloadError(
                "下载超时（>10分钟）",
                url=video_url,
            )
        except aiohttp.ClientError as e:
            raise FileDownloadError(
                f"网络错误: {str(e)}",
                url=video_url,
            )
        except Exception as e:
            raise FileDownloadError(
                f"下载失败: {str(e)}",
                url=video_url,
            )
    
    async def download_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 3,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Path]:
        """
        并发下载多个视频
        
        Args:
            urls: URL 列表
            max_concurrent: 最大并发数
            progress_callback: 全局进度回调
        
        Returns:
            本地文件路径列表
        
        Raises:
            FileDownloadError: 任何下载失败
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(url: str, index: int) -> Path:
            async with semaphore:
                def local_progress(downloaded: int, total: int):
                    if progress_callback:
                        # 汇总所有文件的进度
                        progress_callback(index * 100 + downloaded // 1024, len(urls) * 100)
                
                return await self.download_video(url, progress_callback=local_progress)
        
        tasks = [
            download_with_semaphore(url, idx)
            for idx, url in enumerate(urls)
        ]
        
        return await asyncio.gather(*tasks)
    
    def clear_old_cache(self, max_age_days: int = 30) -> int:
        """
        清理过期缓存
        
        Args:
            max_age_days: 最大缓存天数
        
        Returns:
            清理的文件数量
        """
        if not self._cache_index_file.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        
        for cache_key, file_path in list(self._cache_index.items()):
            file_path = Path(file_path)
            if file_path.exists():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        del self._cache_index[cache_key]
                        removed_count += 1
                        logger.debug(f"[AssetManager] 删除过期缓存: {file_path}")
                    except Exception as e:
                        logger.warning(f"[AssetManager] 删除缓存失败: {e}")
        
        if removed_count > 0:
            self._save_cache_index()
            logger.info(f"[AssetManager] 清理 {removed_count} 个过期缓存文件")
        
        return removed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_size = 0
        file_count = 0
        
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file() and cache_file.name != "cache_index.json":
                file_count += 1
                total_size += cache_file.stat().st_size
        
        return {
            "cache_dir": str(self.cache_dir),
            "file_count": file_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "index_size": len(self._cache_index),
        }

