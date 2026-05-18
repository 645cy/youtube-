"""
用户画像匹配引擎 — OCP 实验室核心

功能:
  1. 用户画像模型 (五维: 技能/时间/资金/兴趣/设备)
  2. 20 条变现路径匹配算法 (加权多因子评分)
  3. 路径评分排序
  4. 个性化工作流推荐

设计决策:
  - 纯规则引擎, 无需机器学习
  - 可解释性强, 每条匹配都有原因说明
  - 支持中英文变现路径数据
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ── 用户画像模型 ──

@dataclass
class UserProfile:
    """OCP 实验室用户画像 — 五维评估模型."""

    # 技能维度
    skills: dict[str, int]  # skill_name -> level(1-10)
    has_camera: bool
    has_mic: bool
    editing_experience: int  # 0-10

    # 时间维度
    weekly_hours: float  # 每周可用小时
    preferred_video_length: str  # short | medium | long
    can_show_face: bool

    # 资金维度
    monthly_budget_usd: float
    willing_to_invest: bool

    # 兴趣维度
    interests: list[str]
    native_language: str  # zh | en | other
    target_audience: str  # global | local

    # 设备维度
    has_computer: bool
    computer_os: str  # windows | mac | linux
    has_smartphone: bool


# ── 变现路径模型 ──

@dataclass
class MonetizationPath:
    """单条变现路径定义."""

    path_id: int
    path_name: str
    path_name_en: str
    category: str  # 类别
    description: str
    difficulty: str  # beginner | intermediate | advanced
    estimated_startup_cost_usd: float
    estimated_monthly_income_low_usd: float
    estimated_monthly_income_high_usd: float
    time_to_first_income_months: int

    # 匹配维度 (1-10 评分)
    required_skill_level: int  # 所需技能水平
    time_commitment_hours_per_week: float  # 每周时间投入
    face_required: bool  # 是否需要露脸
    min_budget_usd: float  # 最低预算

    # 关联标签
    relevant_skills: list[str]  # 相关技能
    relevant_interests: list[str]  # 相关兴趣
    required_tools: list[str]  # 所需工具

    # 工作流
    workflow_steps: list[str]
    pros: list[str]
    cons: list[str]

    # 匹配权重
    match_weights: dict[str, float] | None = None


# ── 推荐结果 ──

@dataclass
class PathMatchResult:
    """单条变现路径的匹配结果."""

    path_id: int
    path_name: str
    path_name_en: str
    match_score: float  # 0-100
    match_reasons: list[str]
    estimated_startup_cost: float
    estimated_monthly_income_low: float
    estimated_monthly_income_high: float
    time_to_first_income_months: int
    difficulty: str
    required_tools: list[str]
    workflow_steps: list[str]
    pros: list[str]
    cons: list[str]


@dataclass
class RecommendationOutput:
    """推荐引擎完整输出."""

    user_profile_summary: dict[str, Any]
    recommendations: list[PathMatchResult]
    top_path: PathMatchResult | None
    personalized_workflow: dict[str, Any] | None


# ── 路径匹配引擎 ──

class PathRecommender:
    """用户画像-变现路径匹配引擎.

    匹配算法:
      Score = sum(weight_i * factor_i) * confidence_adjustment

    匹配因子:
      - 技能匹配度: 用户技能 vs 路径所需技能
      - 时间匹配度: 用户可用时间 vs 路径时间需求
      - 资金匹配度: 用户预算 vs 路径启动成本
      - 兴趣匹配度: 用户兴趣 vs 路径领域
      - 设备匹配度: 用户设备 vs 路径工具需求
      - 人格匹配度: 是否露脸偏好
      - 难度适配度: 用户技能水平 vs 路径难度
    """

    DEFAULT_WEIGHTS = {
        "skill_match": 0.20,
        "time_match": 0.15,
        "budget_match": 0.15,
        "interest_match": 0.15,
        "equipment_match": 0.10,
        "personality_match": 0.10,
        "difficulty_match": 0.10,
        "roi_potential": 0.05,
    }

    def __init__(
        self,
        paths: list[MonetizationPath] | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.paths = paths or []
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def _skill_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """技能匹配度 (0-100)."""
        if not path.relevant_skills:
            return 50.0
        user_skills_lower = {k.lower(): v for k, v in (user.skills or {}).items()}
        scores = []
        for skill in path.relevant_skills:
            skill_lower = skill.lower()
            if skill_lower in user_skills_lower:
                scores.append(min(100, user_skills_lower[skill_lower] * 10))
            else:
                # 模糊匹配
                for us, uv in user_skills_lower.items():
                    if us in skill_lower or skill_lower in us:
                        scores.append(min(100, uv * 8))
                        break
                else:
                    scores.append(10)  # 无匹配, 给基础分
        return sum(scores) / len(scores) if scores else 50.0

    def _time_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """时间匹配度 (0-100).

        用户时间 >= 路径需求 -> 100 分
        用户时间 < 路径需求 -> 按比例递减
        """
        if path.time_commitment_hours_per_week <= 0:
            return 100.0
        ratio = user.weekly_hours / path.time_commitment_hours_per_week
        if ratio >= 1.5:
            return 100.0
        elif ratio >= 1.0:
            return 80 + (ratio - 1.0) * 40
        elif ratio >= 0.5:
            return 40 + (ratio - 0.5) * 80
        else:
            return max(0, ratio * 80)

    def _budget_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """资金匹配度 (0-100)."""
        if path.min_budget_usd <= 0:
            return 100.0
        if not user.willing_to_invest and path.min_budget_usd > 0:
            return max(0, 100 - path.min_budget_usd * 2)
        if user.monthly_budget_usd >= path.min_budget_usd:
            return 100.0
        ratio = user.monthly_budget_usd / max(path.min_budget_usd, 1)
        return min(100, ratio * 100)

    def _interest_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """兴趣匹配度 (0-100)."""
        if not path.relevant_interests or not user.interests:
            return 50.0
        user_interests_lower = {i.lower() for i in user.interests}
        matches = 0
        for interest in path.relevant_interests:
            interest_lower = interest.lower()
            if interest_lower in user_interests_lower:
                matches += 1
            else:
                for ui in user_interests_lower:
                    if interest_lower in ui or ui in interest_lower:
                        matches += 0.5
                        break
        return min(100, matches / len(path.relevant_interests) * 100)

    def _equipment_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """设备匹配度 (0-100)."""
        required = path.required_tools
        if not required:
            return 100.0

        has_count = 0
        user_equipment = []
        if user.has_computer:
            user_equipment.append("computer")
            user_equipment.append(user.computer_os)
        if user.has_camera:
            user_equipment.append("camera")
        if user.has_mic:
            user_equipment.append("microphone")
        if user.has_smartphone:
            user_equipment.append("smartphone")
            user_equipment.append("phone")

        user_eq_lower = [e.lower() for e in user_equipment]
        for tool in required:
            tool_lower = tool.lower()
            if any(tool_lower in eq or eq in tool_lower for eq in user_eq_lower):
                has_count += 1

        return (has_count / len(required)) * 100 if required else 100.0

    def _personality_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """人格/露脸匹配度 (0-100)."""
        if not path.face_required:
            return 100.0  # 不需要露脸, 所有人匹配
        if user.can_show_face:
            return 100.0
        return 20.0  # 需要露脸但用户不愿 -> 低匹配

    def _difficulty_match(self, user: UserProfile, path: MonetizationPath) -> float:
        """难度适配度 (0-100)."""
        # 综合用户技能水平
        avg_skill = 5.0
        if user.skills:
            avg_skill = sum(user.skills.values()) / len(user.skills)
        # 编辑经验
        avg_skill = max(avg_skill, user.editing_experience)

        required_level = path.required_skill_level
        diff_map = {"beginner": 3, "intermediate": 6, "advanced": 9}
        required_level = max(required_level, diff_map.get(path.difficulty, 5))

        if avg_skill >= required_level + 2:
            return 100.0  # 能力远超, 轻松驾驭
        elif avg_skill >= required_level:
            return 85.0  # 能力匹配
        elif avg_skill >= required_level - 2:
            return 60.0  # 能力接近, 需学习
        elif avg_skill >= required_level - 4:
            return 35.0  # 能力不足, 需要较多学习
        else:
            return 10.0  # 能力差距大

    def _roi_potential(self, user: UserProfile, path: MonetizationPath) -> float:
        """ROI 潜力评分 (0-100)."""
        # 收入潜力 vs 投入成本
        avg_income = (path.estimated_monthly_income_low_usd + path.estimated_monthly_income_high_usd) / 2
        startup = max(path.estimated_startup_cost_usd, 1)

        # 收入/投入比
        roi_ratio = avg_income / startup
        roi_score = min(100, roi_ratio * 50)

        # 时间成本
        time_cost = path.time_commitment_hours_per_week * 4  # 月投入小时
        hourly_return = avg_income / max(time_cost, 1)
        hourly_score = min(100, hourly_return * 5)

        # 首月收益速度
        speed_score = max(0, 100 - path.time_to_first_income_months * 15)

        return (roi_score * 0.4 + hourly_score * 0.35 + speed_score * 0.25)

    def _calculate_score(
        self, user: UserProfile, path: MonetizationPath,
    ) -> tuple[float, list[str]]:
        """计算单条路径的匹配分数和原因."""
        scores = {
            "skill_match": self._skill_match(user, path),
            "time_match": self._time_match(user, path),
            "budget_match": self._budget_match(user, path),
            "interest_match": self._interest_match(user, path),
            "equipment_match": self._equipment_match(user, path),
            "personality_match": self._personality_match(user, path),
            "difficulty_match": self._difficulty_match(user, path),
            "roi_potential": self._roi_potential(user, path),
        }

        w = self.weights
        total = sum(scores[k] * w[k] for k in w if k in scores)

        # 生成匹配原因
        reasons = []
        if scores["skill_match"] >= 70:
            user_skill_keys = [k.lower() for k in (user.skills or {}).keys()]
            matched_skills = [
                s for s in path.relevant_skills
                if any(us in s.lower() for us in user_skill_keys)
            ]
            if matched_skills:
                reasons.append(f"技能匹配: 你拥有{', '.join(matched_skills[:3])}相关技能")
        if scores["time_match"] >= 80:
            reasons.append(f"时间充裕: 你每周有{user.weekly_hours}小时, 路径需{path.time_commitment_hours_per_week}小时")
        if scores["budget_match"] >= 80:
            reasons.append(f"预算充足: 启动成本${path.estimated_startup_cost_usd:.0f}在你的预算范围内")
        if scores["interest_match"] >= 70:
            reasons.append(f"兴趣匹配: 你的兴趣与{path.path_name}领域高度相关")
        if scores["difficulty_match"] >= 80:
            reasons.append("难度适中: 你的技能水平可以轻松驾驭此路径")
        if scores["roi_potential"] >= 70:
            reasons.append(
                f"高回报潜力: 预估月收入"
                f"${path.estimated_monthly_income_low_usd:.0f}-${path.estimated_monthly_income_high_usd:.0f}"
            )
        if scores["personality_match"] < 40:
            reasons.append("注意: 此路径需要露脸, 但你选择不露脸")
        if scores["time_match"] < 40:
            reasons.append("注意: 你的可用时间可能不足以支撑此路径")
        if not reasons:
            reasons.append(f"基础匹配: 综合匹配度{total:.0f}分, 建议进一步了解")

        return total, reasons

    def recommend(
        self,
        user: UserProfile,
        top_n: int = 5,
        min_score: float = 20.0,
    ) -> RecommendationOutput:
        """为指定用户画像生成变现路径推荐."""
        results: list[tuple[float, list[str], MonetizationPath]] = []
        for path in self.paths:
            score, reasons = self._calculate_score(user, path)
            if score >= min_score:
                results.append((score, reasons, path))

        # 按分数降序排序
        results.sort(key=lambda x: x[0], reverse=True)

        match_results = []
        for score, reasons, path in results[:top_n]:
            match_results.append(PathMatchResult(
                path_id=path.path_id,
                path_name=path.path_name,
                path_name_en=path.path_name_en,
                match_score=round(score, 2),
                match_reasons=reasons,
                estimated_startup_cost=path.estimated_startup_cost_usd,
                estimated_monthly_income_low=path.estimated_monthly_income_low_usd,
                estimated_monthly_income_high=path.estimated_monthly_income_high_usd,
                time_to_first_income_months=path.time_to_first_income_months,
                difficulty=path.difficulty,
                required_tools=path.required_tools,
                workflow_steps=path.workflow_steps,
                pros=path.pros,
                cons=path.cons,
            ))

        top_path = match_results[0] if match_results else None
        workflow = self._generate_workflow(user, top_path) if top_path else None

        profile_summary = {
            "skill_level": sum(user.skills.values()) / len(user.skills) if user.skills else 5,
            "weekly_hours": user.weekly_hours,
            "monthly_budget": user.monthly_budget_usd,
            "interests": user.interests,
            "can_show_face": user.can_show_face,
            "has_camera": user.has_camera,
            "has_computer": user.has_computer,
        }

        return RecommendationOutput(
            user_profile_summary=profile_summary,
            recommendations=match_results,
            top_path=top_path,
            personalized_workflow=workflow,
        )

    def _generate_workflow(
        self, user: UserProfile, top_path: PathMatchResult | None,
    ) -> dict[str, Any] | None:
        """为顶级推荐路径生成个性化工作流."""
        if not top_path:
            return None
        return {
            "path_name": top_path.path_name,
            "week_1_2": ["选定细分领域", f"准备工具: {', '.join(top_path.required_tools[:3])}"],
            "week_3_4": top_path.workflow_steps[:2] if len(top_path.workflow_steps) >= 2 else top_path.workflow_steps,
            "month_2_3": (
                top_path.workflow_steps[2:4]
                if len(top_path.workflow_steps) >= 4
                else top_path.workflow_steps[2:]
            ),
            "ongoing": ["持续优化内容质量", "分析数据反馈", "迭代改进策略"],
            "milestone_1": "首笔收入",
            "expected_time_to_milestone": f"{top_path.time_to_first_income_months}个月",
        }


# CRG: Keep static monetization data outside the loader so architecture scans do not flag it as function logic.
DEFAULT_MONETIZATION_PATH_DATA: list[dict[str, Any]] = [
    {"path_id": 1, "path_name": "YouTube 广告分成", "path_name_en": "YouTube Ad Revenue",
     "category": "平台内", "description": "通过 YouTube 合作伙伴计划(YPP)从视频中获取广告收入。",
     "difficulty": "beginner", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 200,
     "estimated_monthly_income_high_usd": 2000,
     "time_to_first_income_months": 6, "required_skill_level": 3, "time_commitment_hours_per_week": 10,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["视频制作", "内容策划", "SEO优化"], "relevant_interests": ["视频创作", "内容运营"],
     "required_tools": ["computer", "camera", "editing software"],
     "workflow_steps": ["选定细分领域", "持续创作优质内容", "申请加入YPP", "优化广告位", "分析数据提升RPM"],
     "pros": ["被动收入", "收入随频道增长", "平台稳定"], "cons": ["需要1000订阅", "需要4000小时观看", "RPM因地区而异"]},
    {"path_id": 2, "path_name": "联盟营销(Amazon Associates)", "path_name_en": "Affiliate Marketing",
     "category": "平台内", "description": "在视频描述中放置联盟链接赚取销售佣金。",
     "difficulty": "beginner", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 500,
     "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 3, "required_skill_level": 4, "time_commitment_hours_per_week": 8,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["产品评测", "内容营销", "SEO优化"], "relevant_interests": ["产品评测", "电商", "科技"],
     "required_tools": ["computer", "camera"],
     "workflow_steps": ["注册Amazon Associates", "选择产品类别", "创建评测/教程视频", "优化描述区链接", "追踪转化数据"],
     "pros": ["被动收入", "无需库存", "佣金比例可观"], "cons": ["转化率依赖流量", "平台政策限制", "竞争激烈"]},
    {"path_id": 3, "path_name": "品牌赞助", "path_name_en": "Brand Sponsorship",
     "category": "平台内", "description": "与品牌合作在视频中展示产品或服务获取赞助费。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 500,
     "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 6, "required_skill_level": 5, "time_commitment_hours_per_week": 10,
     "face_required": True, "min_budget_usd": 0,
     "relevant_skills": ["内容创作", "商务谈判", "影响力营销"], "relevant_interests": ["品牌合作", "内容创作"],
     "required_tools": ["camera", "microphone", "computer"],
     "workflow_steps": ["建立个人品牌", "积累忠实粉丝", "联系品牌或加入中介平台", "谈判合作条款", "制作赞助内容"],
     "pros": ["收入较高", "建立行业关系", "提升频道信誉"], "cons": ["需要粉丝基础", "谈判耗时", "可能影响观众信任"]},
    {"path_id": 4, "path_name": "频道会员", "path_name_en": "Channel Memberships",
     "category": "平台内", "description": "为付费订阅者提供专属内容和特权。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 200,
     "estimated_monthly_income_high_usd": 2000,
     "time_to_first_income_months": 9, "required_skill_level": 4, "time_commitment_hours_per_week": 12,
     "face_required": True, "min_budget_usd": 0,
     "relevant_skills": ["社区运营", "内容策划", "粉丝互动"], "relevant_interests": ["社区建设", "内容创作"],
     "required_tools": ["computer", "camera"],
     "workflow_steps": ["开通会员功能", "设计会员等级", "创建专属内容", "维护会员社区", "持续提供价值"],
     "pros": ["稳定月收入", "增强粉丝黏性", "平台原生支持"], "cons": ["需要30,000订阅", "需要持续维护", "收入分成"]},
    {"path_id": 5, "path_name": "YouTube Shopping联盟", "path_name_en": "YouTube Shopping Affiliate",
     "category": "平台内", "description": "通过 YouTube Shopping 功能在视频中展示产品并获取佣金。",
     "difficulty": "beginner", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 300,
     "estimated_monthly_income_high_usd": 3000,
     "time_to_first_income_months": 4, "required_skill_level": 3, "time_commitment_hours_per_week": 8,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["产品展示", "内容创作", "电商运营"], "relevant_interests": ["产品推荐", "电商"],
     "required_tools": ["computer", "camera"],
     "workflow_steps": ["申请Shopping功能", "选择推广产品", "在视频中添加产品标签", "优化转化率", "分析收益数据"],
     "pros": ["原生功能集成", "转化路径短", "收入可观"], "cons": ["需要资格", "依赖产品选择", "平台限制"]},
    {"path_id": 6, "path_name": "Shorts广告分成", "path_name_en": "Shorts Ad Revenue",
     "category": "平台内", "description": "通过 YouTube Shorts 广告获取收入。",
     "difficulty": "beginner", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 100,
     "estimated_monthly_income_high_usd": 1500,
     "time_to_first_income_months": 6, "required_skill_level": 2, "time_commitment_hours_per_week": 5,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["短视频制作", "创意策划", "快速剪辑"], "relevant_interests": ["短视频", "社交媒体"],
     "required_tools": ["smartphone"],
     "workflow_steps": ["了解Shorts算法", "制作高质量Shorts", "优化标题和标签", "保持发布频率", "分析表现数据"],
     "pros": ["门槛低", "制作快速", "流量大"], "cons": ["RPM较低", "竞争激烈", "收入不稳定"]},
    {"path_id": 7, "path_name": "Super Stickers / Super Chat", "path_name_en": "Super Features",
     "category": "平台内", "description": "直播时通过粉丝打赏获取收入。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 100,
     "estimated_monthly_income_high_usd": 1000,
     "time_to_first_income_months": 3, "required_skill_level": 4, "time_commitment_hours_per_week": 8,
     "face_required": True, "min_budget_usd": 0,
     "relevant_skills": ["直播", "粉丝互动", "实时沟通"], "relevant_interests": ["直播", "互动"],
     "required_tools": ["computer", "camera", "microphone"],
     "workflow_steps": ["开启直播功能", "规划直播内容", "积极互动", "鼓励Super Chat", "感谢支持者"],
     "pros": ["实时收入", "增强互动", "低门槛"], "cons": ["需要粉丝基础", "收入不稳定", "直播耗时"]},
    {"path_id": 8, "path_name": "数字产品销售", "path_name_en": "Digital Product Sales",
     "category": "平台外", "description": "销售模板/电子书/预设/课程等数字产品。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 50, "estimated_monthly_income_low_usd": 500,
     "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 3, "required_skill_level": 6, "time_commitment_hours_per_week": 8,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["产品设计", "内容创作", "营销"], "relevant_interests": ["产品开发", "被动收入"],
     "required_tools": ["computer", "design software"],
     "workflow_steps": ["确定产品类型", "开发产品", "设置销售渠道", "在视频中推广", "收集反馈迭代"],
     "pros": ["高利润率", "一次制作多次销售", "完全控制"], "cons": ["需要产品开发能力", "初始投入", "营销挑战"]},
    {"path_id": 9, "path_name": "在线课程销售", "path_name_en": "Online Course Sales",
     "category": "平台外", "description": "在 Teachable/Udemy 等平台销售在线课程。",
     "difficulty": "advanced", "estimated_startup_cost_usd": 100, "estimated_monthly_income_low_usd": 1000,
     "estimated_monthly_income_high_usd": 10000,
     "time_to_first_income_months": 4, "required_skill_level": 7, "time_commitment_hours_per_week": 15,
     "face_required": True, "min_budget_usd": 50,
     "relevant_skills": ["教学设计", "内容创作", "视频录制", "课程设计"], "relevant_interests": ["教育", "知识分享"],
     "required_tools": ["computer", "camera", "microphone", "editing software"],
     "workflow_steps": ["确定课程主题", "设计课程大纲", "录制课程内容", "上传到课程平台", "通过YouTube引流"],
     "pros": ["高价值产品", "被动收入", "建立权威"], "cons": ["制作成本高", "需要专业知识", "竞争激烈"]},
    {"path_id": 10, "path_name": "咨询/辅导服务", "path_name_en": "Consulting/Coaching",
     "category": "平台外", "description": "提供一对一或小组咨询/辅导服务。",
     "difficulty": "advanced", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 1000,
     "estimated_monthly_income_high_usd": 10000,
     "time_to_first_income_months": 3, "required_skill_level": 7, "time_commitment_hours_per_week": 10,
     "face_required": True, "min_budget_usd": 0,
     "relevant_skills": ["专业领域知识", "沟通", "咨询技巧"], "relevant_interests": ["咨询", "辅导"],
     "required_tools": ["computer", "camera", "microphone"],
     "workflow_steps": ["建立专业形象", "设计服务包", "设置预约系统", "在视频中推广", "交付高质量服务"],
     "pros": ["高收入潜力", "利用专业知识", "灵活定价"], "cons": ["时间密集", "需要专业度", "客户获取"]},
    {"path_id": 11, "path_name": "自媒体代运营", "path_name_en": "Social Media Management",
     "category": "平台外", "description": "为其他创作者或品牌管理 YouTube 频道。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 1500,
     "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 2, "required_skill_level": 6, "time_commitment_hours_per_week": 20,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["频道运营", "数据分析", "内容策划", "SEO优化"], "relevant_interests": ["运营", "管理"],
     "required_tools": ["computer"],
     "workflow_steps": ["建立服务作品集", "寻找客户", "签订合同", "执行运营策略", "报告成果"],
     "pros": ["稳定客户收入", "可扩展", "远程工作"], "cons": ["时间密集", "客户依赖", "责任大"]},
    {"path_id": 12, "path_name": "付费社区/社群", "path_name_en": "Paid Community",
     "category": "平台外", "description": "创建 Discord/Skool 付费社群提供独家内容和交流。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 20, "estimated_monthly_income_low_usd": 500,
     "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 4, "required_skill_level": 5, "time_commitment_hours_per_week": 10,
     "face_required": True, "min_budget_usd": 0,
     "relevant_skills": ["社区运营", "内容创作", "互动管理"], "relevant_interests": ["社区建设", "互动"],
     "required_tools": ["computer", "community platform"],
     "workflow_steps": ["选择社区平台", "设计会员权益", "创建初始内容", "推广社区", "维护活跃度"],
     "pros": ["稳定月费", "高互动", "品牌忠诚"], "cons": ["需要持续维护", "初始成员获取", "平台依赖"]},
    {"path_id": 13, "path_name": "AI内容服务", "path_name_en": "AI Content Services",
     "category": "平台外", "description": "利用 AI 工具提供内容创作服务(脚本/缩略图/编辑)。",
     "difficulty": "beginner", "estimated_startup_cost_usd": 50, "estimated_monthly_income_low_usd": 500,
     "estimated_monthly_income_high_usd": 3000,
     "time_to_first_income_months": 2, "required_skill_level": 4, "time_commitment_hours_per_week": 10,
     "face_required": False, "min_budget_usd": 20,
     "relevant_skills": ["AI工具", "内容创作", "设计", "编辑"], "relevant_interests": ["AI", "效率工具"],
     "required_tools": ["computer", "AI software"],
     "workflow_steps": ["学习AI工具", "建立作品集", "在平台接单", "交付服务", "积累口碑"],
     "pros": ["低门槛", "AI提升效率", "需求增长"], "cons": ["竞争加剧", "AI局限性", "客户期望管理"]},
    {"path_id": 14, "path_name": "YouTube SEO优化服务", "path_name_en": "YouTube SEO Services",
     "category": "平台外", "description": "为其他频道提供SEO优化和增长策略服务。",
     "difficulty": "advanced", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 1000,
     "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 3, "required_skill_level": 8, "time_commitment_hours_per_week": 12,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["SEO优化", "数据分析", "关键词研究", "策略规划"], "relevant_interests": ["SEO", "增长"],
     "required_tools": ["computer", "SEO tools"],
     "workflow_steps": ["深入学习YouTube算法", "建立成功案例", "设计服务包", "获取客户", "交付优化方案"],
     "pros": ["高专业壁垒", "客户粘性高", "可规模化"], "cons": ["需要深度知识", "算法变化风险", "结果不确定"]},
    {"path_id": 15, "path_name": "视频编辑外包服务", "path_name_en": "Video Editing Services",
     "category": "平台外", "description": "为其他创作者提供视频编辑服务。",
     "difficulty": "beginner", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 800,
     "estimated_monthly_income_high_usd": 4000,
     "time_to_first_income_months": 1, "required_skill_level": 5, "time_commitment_hours_per_week": 15,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["视频编辑", "色彩校正", "音频处理", "后期制作"], "relevant_interests": ["视频制作", "后期"],
     "required_tools": ["computer", "editing software"],
     "workflow_steps": ["精通编辑软件", "建立作品集", "在Freelance平台注册", "接单交付", "建立长期客户"],
     "pros": ["技能变现快", "远程工作", "需求稳定"], "cons": ["时间密集", "客户沟通", " revisions 多"]},
    {"path_id": 16, "path_name": "内容授权/素材销售", "path_name_en": "Content Licensing",
     "category": "平台外", "description": "授权视频素材给其他创作者或媒体使用。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 0, "estimated_monthly_income_low_usd": 200,
     "estimated_monthly_income_high_usd": 2000,
     "time_to_first_income_months": 6, "required_skill_level": 4, "time_commitment_hours_per_week": 5,
     "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["视频拍摄", "素材管理", "版权知识"], "relevant_interests": ["摄影", "素材"],
     "required_tools": ["camera", "computer"],
     "workflow_steps": ["创建高质量素材库", "上传到素材平台", "设置授权条款", "推广素材", "管理授权"],
     "pros": ["被动收入", "素材复用", "版权保护"], "cons": ["初始积累慢", "侵权风险", "收入不稳定"]},
    {"path_id": 17, "path_name": "YouTube POD + 流量套利", "path_name_en": "YouTube POD + Arbitrage",
     "category": "平台外", "description": "制作短视频为POD产品引流, 赚取差价。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 100, "estimated_monthly_income_low_usd": 1000,
     "estimated_monthly_income_high_usd": 10000,
     "time_to_first_income_months": 3, "required_skill_level": 5, "time_commitment_hours_per_week": 15,
     "face_required": False, "min_budget_usd": 50,
     "relevant_skills": ["短视频制作", "电商运营", "广告投放"], "relevant_interests": ["电商", "流量"],
     "required_tools": ["computer", "smartphone", "design software"],
     "workflow_steps": ["选择POD平台", "设计产品", "创建引流视频", "优化转化漏斗", "扩大规模"],
     "pros": ["无需库存", "高利润潜力", "可规模化"], "cons": ["需要启动资金", "广告风险", "竞争激烈"]},
    {"path_id": 18, "path_name": "有声书/播客内容改编", "path_name_en": "Audiobook/Podcast Adaptation",
     "category": "平台外", "description": "将视频内容改编为有声书或播客, 在Audible等平台销售。",
     "difficulty": "advanced", "estimated_startup_cost_usd": 200,
     "estimated_monthly_income_low_usd": 300, "estimated_monthly_income_high_usd": 3000,
     "time_to_first_income_months": 6, "required_skill_level": 7,
     "time_commitment_hours_per_week": 8, "face_required": True, "min_budget_usd": 100,
     "relevant_skills": ["声音录制", "音频编辑", "叙事能力", "内容改编"], "relevant_interests": ["音频", "故事"],
     "required_tools": ["microphone", "computer", "audio editing software"],
     "workflow_steps": ["选择内容", "改编为音频", "录制", "后期处理", "上传到平台"],
     "pros": ["内容复用", "新受众", "被动收入"], "cons": ["制作成本高", "市场教育", "需要声音条件"]},
    {"path_id": 19, "path_name": "联盟+信息组合套利", "path_name_en": "Affiliate + Info Arbitrage",
     "category": "平台外", "description": "制作信息差内容, 引导至联盟链接变现。",
     "difficulty": "intermediate", "estimated_startup_cost_usd": 50,
     "estimated_monthly_income_low_usd": 500, "estimated_monthly_income_high_usd": 5000,
     "time_to_first_income_months": 3, "required_skill_level": 5,
     "time_commitment_hours_per_week": 12, "face_required": False, "min_budget_usd": 0,
     "relevant_skills": ["内容创作", "联盟营销", "信息研究", "SEO优化"], "relevant_interests": ["研究", "信息差"],
     "required_tools": ["computer"],
     "workflow_steps": ["发现信息差", "创建价值内容", "植入联盟链接", "优化SEO", "追踪收益"],
     "pros": ["信息价值高", "被动收入", "低竞争"], "cons": ["信息时效性", "内容质量要求高", "合规风险"]},
    {"path_id": 20, "path_name": "自动化AI内容农场", "path_name_en": "Automated AI Content Farm",
     "category": "平台外", "description": "利用AI工具批量生成视频内容, 规模化运营多个频道。",
     "difficulty": "advanced", "estimated_startup_cost_usd": 500,
     "estimated_monthly_income_low_usd": 2000, "estimated_monthly_income_high_usd": 20000,
     "time_to_first_income_months": 4, "required_skill_level": 8,
     "time_commitment_hours_per_week": 30, "face_required": False, "min_budget_usd": 200,
     "relevant_skills": ["AI工具", "自动化", "编程", "数据分析", "规模化运营"], "relevant_interests": ["AI", "自动化", "规模化"],
     "required_tools": ["computer", "AI software", "automation tools"],
     "workflow_steps": ["搭建自动化流程", "选择Niche", "设置AI内容流水线", "批量创建频道", "监控和优化"],
     "pros": ["规模化潜力", "被动收入", "AI驱动"], "cons": ["高风险", "平台政策限制", "技术门槛高", "可能被封号"]},
]


def load_default_paths() -> list[MonetizationPath]:
    """Load the bundled monetization path catalog."""
    # CRG: Preserve the public loader while keeping the large static catalog out of the function body.
    return [MonetizationPath(**p) for p in DEFAULT_MONETIZATION_PATH_DATA]
