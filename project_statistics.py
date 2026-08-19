"""兼容入口：所有核心统计函数已迁移至 app.services.project_statistics，此文件保留向后兼容。"""

from app.services.project_statistics import (  # noqa: F401
    DEFAULT_FACE_WEIGHTS,
    FACE_INTERNAL_WEIGHTS,
    calculate_optimal_speed_evaluation,
    calculate_surface_stats,
    generate_single_surface_stats,
    generate_stats,
    generate_stats_data,
)
