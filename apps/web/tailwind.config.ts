import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // 晨光书斋 · 明亮主题扩展色
        parchment: {
          50: "hsl(40 30% 98%)",
          100: "hsl(40 24% 96%)",
          200: "hsl(38 20% 94%)",
          300: "hsl(38 18% 90%)",
          400: "hsl(35 15% 85%)",
          500: "hsl(35 12% 78%)",
        },
        cream: {
          DEFAULT: "hsl(38 20% 98%)",
          light: "hsl(40 25% 99%)",
          dark: "hsl(35 18% 94%)",
        },
        sunlight: {
          DEFAULT: "hsl(38 50% 65%)",
          light: "hsl(38 45% 75%)",
          dark: "hsl(38 45% 55%)",
        },
        ink: {
          DEFAULT: "hsl(30 15% 18%)",
          light: "hsl(30 12% 35%)",
          muted: "hsl(30 10% 45%)",
          faint: "hsl(30 8% 60%)",
        },
        seal: {
          DEFAULT: "hsl(0 55% 45%)",
          light: "hsl(0 50% 55%)",
          dark: "hsl(0 50% 38%)",
        },
        gold: {
          DEFAULT: "hsl(38 45% 58%)",
          light: "hsl(38 40% 68%)",
          dark: "hsl(38 40% 48%)",
        },
        // 墨韵书房 · 暗色主题扩展色
        inkwell: {
          DEFAULT: "hsl(25 12% 8%)",
          light: "hsl(25 10% 12%)",
          muted: "hsl(25 10% 16%)",
        },
        ancient: {
          DEFAULT: "hsl(35 25% 22%)",
          light: "hsl(35 20% 28%)",
          dark: "hsl(35 25% 18%)",
        },
        candle: {
          DEFAULT: "hsl(38 40% 55%)",
          light: "hsl(38 35% 65%)",
          glow: "hsl(38 40% 55% / 0.15)",
        },
      },
      fontFamily: {
        // CRG: Expose separate typography roles so luxury titles do not share the same face as UI controls.
        display: ["var(--font-display)", "Cormorant Garamond", "Noto Serif SC", "serif"],
        serif: ["var(--font-noto-serif)", "Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", "SimSun", "serif"],
        sans: ["var(--font-inter)", "var(--font-noto-sans)", "Inter", "Noto Sans SC", "system-ui", "sans-serif"],
        numeric: ["var(--font-inter)", "DIN Alternate", "Avenir Next", "Segoe UI", "system-ui", "sans-serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        // 书页翻页动画
        "page-flip-in": {
          "0%": { transform: "perspective(1600px) rotateY(-95deg) scale(0.98)", opacity: "0" },
          "100%": { transform: "perspective(1600px) rotateY(0deg) scale(1)", opacity: "1" },
        },
        "page-flip-out": {
          "0%": { transform: "perspective(1600px) rotateY(0deg) scale(1)", opacity: "1" },
          "100%": { transform: "perspective(1600px) rotateY(85deg) scale(0.98)", opacity: "0" },
        },
        "page-slide-in": {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        "page-slide-out": {
          "0%": { transform: "translateX(0)", opacity: "1" },
          "100%": { transform: "translateX(-100%)", opacity: "0" },
        },
        // 墨水显现
        "ink-reveal": {
          "0%": { opacity: "0", filter: "blur(4px)" },
          "100%": { opacity: "1", filter: "blur(0px)" },
        },
        "ink-char-reveal": {
          "0%": { opacity: "0", filter: "blur(3px)", transform: "translateY(4px)" },
          "100%": { opacity: "1", filter: "blur(0px)", transform: "translateY(0)" },
        },
        // 水墨晕开（暗色加强版）
        "ink-bloom": {
          "0%": { opacity: "0", filter: "blur(12px) brightness(1.3)", transform: "scale(0.92)" },
          "40%": { opacity: "0.5", filter: "blur(6px) brightness(1.05)" },
          "100%": { opacity: "1", filter: "blur(0) brightness(1)", transform: "scale(1)" },
        },
        // 水墨晕开（更强烈版）
        "ink-spread": {
          "0%": { opacity: "0", filter: "blur(16px) brightness(1.4)", transform: "scale(0.88)" },
          "30%": { opacity: "0.4", filter: "blur(8px) brightness(1.1)" },
          "100%": { opacity: "1", filter: "blur(0) brightness(1)", transform: "scale(1)" },
        },
        // 书签弹跳
        "bookmark-bounce": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-3px)" },
        },
        // 纸张悬浮
        "paper-lift": {
          "0%": { transform: "translateY(0) rotateX(0)", boxShadow: "0 1px 3px rgba(44,24,16,0.05)" },
          "100%": { transform: "translateY(-2px) rotateX(1deg)", boxShadow: "0 8px 20px -4px rgba(44,24,16,0.08), 0 4px 8px -2px rgba(44,24,16,0.04)" },
        },
        "paper-hover-lift": {
          "0%": { transform: "translateY(0) rotateX(0) rotateY(0) translateZ(0)", boxShadow: "0 1px 3px rgba(44,24,16,0.05)" },
          "100%": { transform: "translateY(-3px) rotateX(2deg) rotateY(-1deg) translateZ(4px)", boxShadow: "0 12px 40px rgba(44,24,16,0.08), 0 4px 12px rgba(44,24,16,0.04)" },
        },
        // 涟漪墨水
        "ripple-ink": {
          "0%": { transform: "scale(0.5)", opacity: "0" },
          "40%": { opacity: "1" },
          "100%": { transform: "scale(2.5)", opacity: "0" },
        },
        // 文字呼吸
        "text-breathe": {
          "0%, 100%": { letterSpacing: "0.01em" },
          "50%": { letterSpacing: "0.03em" },
        },
        // 数字滚动
        "counter-roll": {
          "0%": { transform: "translateY(100%)", opacity: "0", filter: "blur(4px)" },
          "100%": { transform: "translateY(0)", opacity: "1", filter: "blur(0)" },
        },
        // 金色微光
        "shimmer": {
          "0%": { backgroundPosition: "-1000px 0" },
          "100%": { backgroundPosition: "1000px 0" },
        },
        // 光影缓慢移动（明亮模式）
        "sunlight-shift": {
          "0%, 100%": { opacity: "0.06", transform: "translateX(0) scale(1)" },
          "33%": { opacity: "0.04", transform: "translateX(20px) scale(1.05)" },
          "66%": { opacity: "0.08", transform: "translateX(-10px) scale(0.98)" },
        },
        // 印章盖印
        "seal-stamp": {
          "0%": { opacity: "0", transform: "scale(1.3) rotate(-3deg)" },
          "40%": { opacity: "1", transform: "scale(0.95) rotate(1deg)" },
          "60%": { transform: "scale(1.02) rotate(-0.5deg)" },
          "100%": { transform: "scale(1) rotate(0)" },
        },
        // 页面淡入
        "page-fade-in": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        // 页面整体微妙浮动
        "page-float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-2px)" },
        },
        // 树影缓慢移动
        "shadow-drift": {
          "0%": { transform: "translate(0, 0) rotate(0deg)", opacity: "0.02" },
          "33%": { transform: "translate(8px, -4px) rotate(0.5deg)", opacity: "0.025" },
          "66%": { transform: "translate(-4px, 6px) rotate(-0.3deg)", opacity: "0.018" },
          "100%": { transform: "translate(2px, -2px) rotate(0.2deg)", opacity: "0.022" },
        },
        // 烛光脉动
        "candle-pulse": {
          "0%, 100%": { opacity: "0.04", transform: "scale(1)" },
          "25%": { opacity: "0.055", transform: "scale(1.02)" },
          "50%": { opacity: "0.035", transform: "scale(0.99)" },
          "75%": { opacity: "0.05", transform: "scale(1.01)" },
        },
        // Toast 滑入
        "toast-in": {
          "0%": { opacity: "0", transform: "translateY(-16px) scale(0.96)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "toast-out": {
          "0%": { opacity: "1", transform: "translateY(0) scale(1)" },
          "100%": { opacity: "0", transform: "translateY(-12px) scale(0.96)" },
        },
        // 页面翻页淡入（更强版）
        "page-turn-in": {
          "0%": { opacity: "0", transform: "perspective(1000px) rotateY(-8deg) translateX(-20px)" },
          "100%": { opacity: "1", transform: "perspective(1000px) rotateY(0deg) translateX(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "page-flip-in": "page-flip-in 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards",
        "page-flip-out": "page-flip-out 0.5s cubic-bezier(0.55, 0.085, 0.68, 0.53) forwards",
        "page-slide-in": "page-slide-in 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards",
        "page-slide-out": "page-slide-out 0.4s ease-in forwards",
        "ink-reveal": "ink-reveal 0.6s ease-out forwards",
        "ink-char-reveal": "ink-char-reveal 0.4s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
        "ink-bloom": "ink-bloom 0.8s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
        "ink-spread": "ink-spread 1.2s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
        "bookmark-bounce": "bookmark-bounce 0.3s ease-out",
        "paper-lift": "paper-lift 0.3s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
        "paper-hover-lift": "paper-hover-lift 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards",
        "ripple-ink": "ripple-ink 0.6s ease-out forwards",
        "text-breathe": "text-breathe 5s ease-in-out infinite",
        "counter-roll": "counter-roll 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards",
        "shimmer": "shimmer 2s linear infinite",
        "sunlight-shift": "sunlight-shift 8s ease-in-out infinite",
        "seal-stamp": "seal-stamp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards",
        "page-fade-in": "page-fade-in 0.5s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
        "page-float": "page-float 6s ease-in-out infinite",
        "shadow-drift": "shadow-drift 20s ease-in-out infinite alternate",
        "candle-pulse": "candle-pulse 4s ease-in-out infinite",
        "toast-in": "toast-in 0.4s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
        "toast-out": "toast-out 0.3s ease-in forwards",
        "page-turn-in": "page-turn-in 0.6s cubic-bezier(0.22, 0.61, 0.36, 1) forwards",
      },
      boxShadow: {
        // 晨光书斋 · 温暖柔和阴影
        "warm-sm": "0 1px 3px rgba(60,40,20,0.04), 0 1px 2px rgba(60,40,20,0.03)",
        "warm": "0 4px 12px rgba(60,40,20,0.05), 0 2px 4px rgba(60,40,20,0.03)",
        "warm-lg": "0 8px 24px rgba(60,40,20,0.06), 0 4px 8px rgba(60,40,20,0.04)",
        "warm-xl": "0 16px 40px rgba(60,40,20,0.07), 0 8px 16px rgba(60,40,20,0.04)",
        "gold-glow": "0 0 12px rgba(201,169,110,0.2), 0 0 4px rgba(201,169,110,0.1)",
        "gold-glow-lg": "0 0 24px rgba(201,169,110,0.25), 0 0 8px rgba(201,169,110,0.15)",
        // 墨韵书房 · 暗色发光
        "dark-sm": "0 1px 3px rgba(0,0,0,0.3), inset 0 1px 0 rgba(201,169,110,0.04)",
        "dark": "0 4px 12px rgba(0,0,0,0.35), inset 0 1px 0 rgba(201,169,110,0.05)",
        "dark-lg": "0 8px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(201,169,110,0.06)",
        "dark-xl": "0 16px 40px rgba(0,0,0,0.45), inset 0 1px 0 rgba(201,169,110,0.08)",
        "candle-glow": "0 0 16px rgba(184,155,110,0.12), 0 0 4px rgba(184,155,110,0.06)",
      },
      backgroundImage: {
        // 光影渐变
        "sunlight-top": "radial-gradient(ellipse 60% 50% at 85% 5%, rgba(201,169,122,0.10) 0%, transparent 55%)",
        "sunlight-left": "radial-gradient(ellipse 50% 40% at 15% 10%, rgba(184,155,122,0.06) 0%, transparent 50%)",
        "sunlight-bottom": "radial-gradient(ellipse 80% 30% at 50% 100%, rgba(184,155,122,0.03) 0%, transparent 50%)",
        // 烛光渐变
        "candle-top": "radial-gradient(ellipse 50% 40% at 50% 25%, rgba(184,155,122,0.04) 0%, transparent 55%)",
        "candle-vignette": "radial-gradient(ellipse 90% 80% at 50% 50%, transparent 40%, rgba(0,0,0,0.25) 100%)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
