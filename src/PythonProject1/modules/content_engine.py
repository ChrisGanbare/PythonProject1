"""
内容生成引擎
提取原脚本的动画逻辑，支持参数化配置
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.font_manager as fm
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
import warnings
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path
import logging

from config.settings import settings, VideoConfig
from models.loan import LoanData, MonthlyPayment
from models.exceptions import RenderError
from utils.decorators import log_execution, retry


logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class ColorScheme:
    """配色方案"""
    
    def __init__(self, name: str = "dark_flourish"):
        """初始化配色方案
        
        Args:
            name: 方案名称（dark_flourish/light_modern/neon_cyberpunk）
        """
        self.name = name
        self._init_colors()
    
    def _init_colors(self) -> None:
        """根据方案名称初始化颜色"""
        if self.name == "dark_flourish":
            # 深色 Flourish 风格
            self.bg_dark = '#0D0D1A'
            self.bg_mid = '#12122A'
            self.bg_card = '#1C1C3A'
            self.bg_card2 = '#1A2040'
            
            self.ei_blue = '#4F9EFF'
            self.ei_blue_dark = '#1E3A8A'
            self.ep_orange = '#FF7F35'
            self.ep_orange_dark = '#92350D'
            
            self.principal_green = '#22D47E'
            self.interest_red = '#F43F5E'
            self.gap_pink = '#EC4899'
            self.accent_gold = '#FBBF24'
            
            self.text_white = '#FFFFFF'
            self.text_gray = '#94A3B8'
            self.text_dim = '#4B5563'
        
        elif self.name == "light_modern":
            # 浅色现代风格
            self.bg_dark = '#FFFFFF'
            self.bg_mid = '#F8F9FA'
            self.bg_card = '#F0F1F3'
            self.bg_card2 = '#E8EAED'
            
            self.ei_blue = '#1F77B4'
            self.ei_blue_dark = '#0D47A1'
            self.ep_orange = '#FF7F0E'
            self.ep_orange_dark = '#D64C0B'
            
            self.principal_green = '#2CA02C'
            self.interest_red = '#D62728'
            self.gap_pink = '#E91E63'
            self.accent_gold = '#FFC107'
            
            self.text_white = '#1A1A1A'
            self.text_gray = '#424242'
            self.text_dim = '#757575'
        
        elif self.name == "neon_cyberpunk":
            # 霓虹朋克风格
            self.bg_dark = '#0A0A0F'
            self.bg_mid = '#1A1A2E'
            self.bg_card = '#16213E'
            self.bg_card2 = '#0F3460'
            
            self.ei_blue = '#00D9FF'
            self.ei_blue_dark = '#0099CC'
            self.ep_orange = '#FF006E'
            self.ep_orange_dark = '#CC0055'
            
            self.principal_green = '#00FF41'
            self.interest_red = '#FF4C59'
            self.gap_pink = '#FF006E'
            self.accent_gold = '#FFB703'
            
            self.text_white = '#FFFFFF'
            self.text_gray = '#C0C0C0'
            self.text_dim = '#808080'
        
        else:
            # 默认方案
            self._init_colors_dark_flourish()
    
    def _init_colors_dark_flourish(self) -> None:
        """默认深色 Flourish 风格"""
        self.name = "dark_flourish"
        self.bg_dark = '#0D0D1A'
        self.bg_mid = '#12122A'
        self.bg_card = '#1C1C3A'
        self.bg_card2 = '#1A2040'
        self.ei_blue = '#4F9EFF'
        self.ei_blue_dark = '#1E3A8A'
        self.ep_orange = '#FF7F35'
        self.ep_orange_dark = '#92350D'
        self.principal_green = '#22D47E'
        self.interest_red = '#F43F5E'
        self.gap_pink = '#EC4899'
        self.accent_gold = '#FBBF24'
        self.text_white = '#FFFFFF'
        self.text_gray = '#94A3B8'
        self.text_dim = '#4B5563'


class ContentEngine:
    """动画内容生成引擎"""
    
    def __init__(
        self,
        loan_data: LoanData,
        video_config: Optional[VideoConfig] = None,
        color_scheme: Optional[ColorScheme] = None,
    ):
        """初始化引擎
        
        Args:
            loan_data: 贷款数据对象
            video_config: 视频配置（若为空使用全局配置）
            color_scheme: 配色方案
        """
        self.loan_data = loan_data
        self.config = video_config or settings.video
        self.colors = color_scheme or ColorScheme("dark_flourish")
        
        # 计算贷款数据
        self._calculate_loan_data()
        
        # 初始化字体
        self._setup_font()
        
        logger.info(f"[ContentEngine] 初始化完成 | 贷款: {loan_data.loan_amount}元 | 利率: {loan_data.annual_rate*100:.1f}%")
    
    def _calculate_loan_data(self) -> None:
        """计算贷款相关数据"""
        ei_payments, ei_monthly = self.loan_data.calculate_equal_interest()
        ep_payments, ep_first, ep_last = self.loan_data.calculate_equal_principal()
        
        self.ei_payments = ei_payments
        self.ep_payments = ep_payments
        self.ei_monthly = ei_monthly
        self.ep_first = ep_first
        self.ep_last = ep_last
        
        # 提取累计利息数据
        self.cum_ei = [p.cumulative_interest for p in ei_payments]
        self.cum_ep = [p.cumulative_interest for p in ep_payments]
        self.gap_list = [self.cum_ei[i] - self.cum_ep[i] for i in range(len(ei_payments))]
        
        self.final_ei = self.cum_ei[-1]
        self.final_ep = self.cum_ep[-1]
        self.final_gap = self.final_ei - self.final_ep
        
        logger.debug(f"[贷款计算] 等额本息: {self.final_ei/10000:.1f}万 | 等额本金: {self.final_ep/10000:.1f}万")
    
    def _setup_font(self) -> None:
        """设置中文字体"""
        preferred = [
            'Microsoft YaHei', 'SimHei', 'PingFang SC',
            'STHeiti', 'Hiragino Sans GB', 'WenQuanYi Micro Hei',
            'Noto Sans CJK SC', 'Source Han Sans SC', 'SimSun',
        ]
        available = {f.name for f in fm.fontManager.ttflist}
        
        for font in preferred:
            if font in available:
                plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                logger.debug(f"[字体] 使用: {font}")
                return
        
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        logger.warning("[字体] 未找到中文字体，使用备用字体")
    
    @log_execution(log_level="info")
    def generate_animation(
        self,
        output_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """生成动画视频
        
        Args:
            output_path: 输出文件路径
            progress_callback: 进度回调函数，参数为 (当前帧, 总帧数)
        
        Returns:
            输出文件路径
        
        Raises:
            RenderError: 渲染失败
        """
        try:
            # 创建输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建画布和轴
            fig, axes = self._create_figure()
            
            # 创建动画
            total_frames = self.config.fps * self.config.total_duration
            
            def update_frame(frame_num: int):
                """更新单帧"""
                if progress_callback:
                    progress_callback(frame_num, total_frames)
                return self._draw_frame(fig, axes, frame_num)
            
            ani = FuncAnimation(
                fig,
                update_frame,
                frames=total_frames,
                init_func=lambda: self._init_animation(fig, axes),
                blit=False,
                interval=1000 / self.config.fps,
                repeat=False,
            )
            
            # 保存视频
            logger.info(f"[渲染] 开始保存视频 | 分辨率: {int(self.config.width)}x{int(self.config.height)} | 帧数: {total_frames}")
            
            writer = FFMpegWriter(
                fps=self.config.fps,
                bitrate=self.config.bitrate,
                extra_args=[
                    '-vcodec', self.config.codec,
                    '-pix_fmt', self.config.pix_fmt,
                    '-preset', self.config.preset,
                    '-crf', str(self.config.crf),
                ],
            )
            
            ani.save(
                str(output_path),
                writer=writer,
                dpi=self.config.dpi,
                savefig_kwargs={'facecolor': self.colors.bg_dark, 'edgecolor': 'none'},
            )
            
            plt.close(fig)
            logger.info(f"[渲染] 完成 | 输出: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"[渲染] 失败: {str(e)}", exc_info=True)
            raise RenderError(f"视频生成失败: {str(e)}", step="animation_generation")
    
    def _create_figure(self) -> tuple:
        """创建图表"""
        fig_w = self.config.width / self.config.dpi
        fig_h = self.config.height / self.config.dpi
        
        fig = plt.figure(figsize=(fig_w, fig_h), facecolor=self.colors.bg_dark)
        
        gs = GridSpec(
            5, 1, figure=fig,
            height_ratios=[0.9, 0.75, 3.0, 3.0, 1.35],
            hspace=0.08,
            left=0.06, right=0.94,
            top=0.97, bottom=0.03,
        )
        
        axes = {
            'title': fig.add_subplot(gs[0]),
            'info': fig.add_subplot(gs[1]),
            'top': fig.add_subplot(gs[2]),
            'bottom': fig.add_subplot(gs[3]),
            'foot': fig.add_subplot(gs[4]),
        }
        
        for ax in axes.values():
            ax.set_facecolor(self.colors.bg_dark)
            ax.axis('off')
        
        return fig, axes
    
    def _init_animation(self, fig, axes) -> List:
        """初始化动画"""
        for ax in axes.values():
            ax.clear()
            ax.set_facecolor(self.colors.bg_dark)
            ax.axis('off')
        return []
    
    def _draw_frame(self, fig, axes, frame_num: int) -> List:
        """绘制单帧"""
        # TODO: 实现具体的帧绘制逻辑（与原脚本一致）
        # 这里是占位符，实现会很长
        return []

