import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CrowdLaunch AI｜海外众筹智能运营工作台",
  description: "面向海外众筹项目的机会研究、Launch Plan、广告增长与 Backer 舆情智能工作台。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
