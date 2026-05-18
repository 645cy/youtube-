/**
 * UserProfileForm 组件 - OCP变现实验室 Step 1
 * 用户画像表单：技能/可用时间/预算/兴趣/设备
 * 使用 React Hook Form + Zod 表单校验
 */

"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { motion } from "framer-motion"
import { Wrench, Clock, DollarSign, Heart, Camera, ChevronRight, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

const userProfileSchema = z.object({
  skills: z.array(z.string()).min(1, "请至少选择一项技能").max(5, "最多选择5项技能"),
  availableTime: z.number({ invalid_type_error: "请输入可用时间" }).min(1, "每周至少1小时").max(168, "每周最多168小时"),
  budget: z.number({ invalid_type_error: "请输入预算" }).min(0, "预算不能为负数").max(100000, "预算上限 $100,000"),
  interests: z.array(z.string()).min(1, "请至少选择一项兴趣").max(5, "最多选择5项兴趣"),
  equipment: z.array(z.string()).min(0).max(10, "最多选择10项设备"),
  experience: z.enum(["beginner", "intermediate", "advanced", "expert"], { required_error: "请选择经验级别" }),
  targetPlatforms: z.array(z.string()).min(1, "请至少选择一个目标平台"),
})

export type UserProfileFormData = z.infer<typeof userProfileSchema>

const SKILL_OPTIONS = ["视频剪辑", "口播/演讲", "写作", "摄影", "编程", "设计", "数据分析", "营销", "翻译", "音乐制作", "手绘/插画", "3D建模", "动效设计", "配音", "运营"]
const INTEREST_OPTIONS = ["科技数码", "美食烹饪", "旅行探索", "健身运动", "游戏电竞", "电影解说", "知识科普", "财经投资", "时尚穿搭", "宠物生活", "教育学习", "音乐舞蹈", "汽车评测", "家居装修", "园艺种植"]
const EQUIPMENT_OPTIONS = ["手机", "相机（单反/微单）", "麦克风", "补光灯", "三脚架", "电脑（Mac）", "电脑（Windows）", "稳定器", "无人机", "绿幕"]
const PLATFORM_OPTIONS = [{ value: "youtube", label: "YouTube" }, { value: "bilibili", label: "B站" }, { value: "douyin", label: "抖音" }, { value: "xiaohongshu", label: "小红书" }, { value: "tiktok", label: "TikTok" }, { value: "twitter", label: "Twitter/X" }]
const EXPERIENCE_OPTIONS = [{ value: "beginner", label: "新手", desc: "刚开始接触内容创作" }, { value: "intermediate", label: "中级", desc: "有一定经验和粉丝基础" }, { value: "advanced", label: "高级", desc: "全职创作者/团队运作" }, { value: "expert", label: "专家", desc: "行业头部/MCN级别" }]

interface UserProfileFormProps { onSubmit: (data: UserProfileFormData) => void; isLoading?: boolean }

export function UserProfileForm({ onSubmit, isLoading = false }: UserProfileFormProps) {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<UserProfileFormData>({
    resolver: zodResolver(userProfileSchema),
    defaultValues: { skills: [], availableTime: 10, budget: 500, interests: [], equipment: ["手机"], experience: "beginner", targetPlatforms: ["youtube"] },
  })

  const skills = watch("skills") || []
  const interests = watch("interests") || []
  const equipment = watch("equipment") || []
  const targetPlatforms = watch("targetPlatforms") || []
  const experience = watch("experience")

  const toggleArrayValue = (field: keyof UserProfileFormData, value: string) => {
    const current = (watch(field) as string[]) || []
    const updated = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
    setValue(field as never, updated as never, { shouldValidate: true })
  }

  return (
    <motion.form initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6 font-serif tracking-wide">
        <span className="bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-serif">1</span>
        <span>填写画像</span>
        <ChevronRight className="h-4 w-4" />
        <span className="text-muted-foreground/50">查看推荐</span>
        <ChevronRight className="h-4 w-4" />
        <span className="text-muted-foreground/50">执行方案</span>
      </div>

      <div className="paper-card page-corner p-4 md:p-5 bg-background/80 space-y-5">
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 font-serif tracking-wide"><Wrench className="h-4 w-4 text-primary" />你的技能（多选）<span className="text-xs text-muted-foreground font-normal font-serif tracking-wide">已选 {skills.length}/5</span></h3>
          <div className="flex flex-wrap gap-2">{SKILL_OPTIONS.map((skill) => (<Badge key={skill} variant={skills.includes(skill) ? "default" : "outline"} className={cn("cursor-pointer transition-all px-3 py-1.5 font-serif tracking-wider", skills.includes(skill) && "ring-1 ring-primary/50")} onClick={() => toggleArrayValue("skills", skill)}>{skill}</Badge>))}</div>
          {errors.skills && <p className="text-xs text-red-400 mt-2">{errors.skills.message}</p>}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 font-serif tracking-wide"><Clock className="h-4 w-4 text-primary" />每周可用时间（小时）</h3>
            <div className="flex items-center gap-3"><Input type="number" {...register("availableTime", { valueAsNumber: true })} className="max-w-[120px] input-glow font-serif tracking-wide tabular-nums" min={1} max={168} /><span className="text-sm text-muted-foreground font-serif tracking-wide">小时/周</span></div>
            {errors.availableTime && <p className="text-xs text-red-400 mt-2">{errors.availableTime.message}</p>}
          </div>
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 font-serif tracking-wide"><DollarSign className="h-4 w-4 text-primary" />可用预算（USD）</h3>
            <div className="flex items-center gap-3"><Input type="number" {...register("budget", { valueAsNumber: true })} className="max-w-[120px] input-glow font-serif tracking-wide tabular-nums" min={0} /><span className="text-sm text-muted-foreground font-serif tracking-wide">USD</span></div>
            {errors.budget && <p className="text-xs text-red-400 mt-2">{errors.budget.message}</p>}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 font-serif tracking-wide"><Heart className="h-4 w-4 text-primary" />兴趣领域（多选）<span className="text-xs text-muted-foreground font-normal font-serif tracking-wide">已选 {interests.length}/5</span></h3>
          <div className="flex flex-wrap gap-2">{INTEREST_OPTIONS.map((interest) => (<Badge key={interest} variant={interests.includes(interest) ? "default" : "outline"} className={cn("cursor-pointer transition-all px-3 py-1.5 font-serif tracking-wider", interests.includes(interest) && "ring-1 ring-primary/50")} onClick={() => toggleArrayValue("interests", interest)}>{interest}</Badge>))}</div>
          {errors.interests && <p className="text-xs text-red-400 mt-2">{errors.interests.message}</p>}
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 font-serif tracking-wide"><Camera className="h-4 w-4 text-primary" />现有设备（多选）</h3>
          <div className="flex flex-wrap gap-2">{EQUIPMENT_OPTIONS.map((eq) => (<Badge key={eq} variant={equipment.includes(eq) ? "default" : "outline"} className={cn("cursor-pointer transition-all px-3 py-1.5 font-serif tracking-wider", equipment.includes(eq) && "ring-1 ring-primary/50")} onClick={() => toggleArrayValue("equipment", eq)}>{eq}</Badge>))}</div>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 font-serif tracking-wide">经验级别</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{EXPERIENCE_OPTIONS.map((exp) => (<div key={exp.value} onClick={() => setValue("experience", exp.value as never, { shouldValidate: true })} className={cn("cursor-pointer rounded-lg border p-4 transition-all paper-card page-corner paper-hover-lift bg-background/80", experience === exp.value ? "border-primary bg-primary/10 ring-1 ring-primary/30" : "hover:bg-accent")}><div className="font-medium text-sm font-serif tracking-wide">{exp.label}</div><div className="text-xs text-muted-foreground mt-1 tracking-wide leading-relaxed">{exp.desc}</div></div>))}</div>
          {errors.experience && <p className="text-xs text-red-400 mt-2">{errors.experience.message}</p>}
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-3 font-serif tracking-wide">目标平台（多选）</h3>
          <div className="flex flex-wrap gap-2">{PLATFORM_OPTIONS.map((platform) => (<Badge key={platform.value} variant={targetPlatforms.includes(platform.value) ? "default" : "outline"} className={cn("cursor-pointer transition-all px-3 py-1.5 font-serif tracking-wider", targetPlatforms.includes(platform.value) && "ring-1 ring-primary/50")} onClick={() => toggleArrayValue("targetPlatforms", platform.value)}>{platform.label}</Badge>))}</div>
          {errors.targetPlatforms && <p className="text-xs text-red-400 mt-2">{errors.targetPlatforms.message}</p>}
        </div>

        <Button type="submit" size="lg" className="w-full font-serif tracking-wide" disabled={isLoading}>{isLoading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />AI 分析中...</>) : (<><ChevronRight className="ml-2 h-4 w-4" />生成变现方案</>)}</Button>
      </div>
    </motion.form>
  )
}
