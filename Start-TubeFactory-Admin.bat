@echo off
:: TubeFactory 管理员启动脚本
:: 用于解决 Windows 上 Next.js dev server 的 spawn EPERM 权限问题
:: 右键此文件 -> 以管理员身份运行

powershell -Command "Start-Process '%~dp0Start-TubeFactory.bat' -Verb runAs"
