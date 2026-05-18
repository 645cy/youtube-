import type { Metadata, Viewport } from "next"
import { Cormorant_Garamond, Inter, Noto_Serif_SC, Noto_Sans_SC } from "next/font/google"
import "./globals.css"
import ClientLayout from "./ClientLayout"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

const cormorant = Cormorant_Garamond({
  // CRG: Add a dedicated luxury display face for brand/title Latin text instead of reusing UI sans.
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
})

const notoSerifSC = Noto_Serif_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-serif",
  display: "swap",
  preload: true,
})

const notoSansSC = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-sans",
  display: "swap",
  preload: true,
})

export const metadata: Metadata = {
  title: "TubeFactory OCP · Creator Intelligence",
  description:
    "高端 YouTube 内容运营控制台：竞品情报、数据抓取、内容生产与变现规划。",
  applicationName: "TubeFactory",
  keywords: ["YouTube", "内容工厂", "竞品监控", "脚本生成", "变现分析"],
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "TubeFactory OCP · Creator Intelligence",
    description: "面向 YouTube 内容运营的高级情报、生产和变现工作台。",
    type: "website",
    locale: "zh_CN",
  },
}

export const viewport: Viewport = {
  // CRG: Next 14 expects theme color in viewport instead of metadata.
  width: "device-width",
  initialScale: 1,
  themeColor: "#070a12",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="zh-CN"
      suppressHydrationWarning
      className={`${inter.variable} ${cormorant.variable} ${notoSerifSC.variable} ${notoSansSC.variable}`}
    >
      <body className="font-sans antialiased">
        {/* CRG: Root body drops the old book-page default; compatibility now lives in the redesign CSS layer. */}
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
