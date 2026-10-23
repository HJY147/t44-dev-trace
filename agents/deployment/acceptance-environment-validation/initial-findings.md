第一次953执行25项通过；第一次Ruff发现run.py遗漏SERVICES导入，已实际修正后重新核验，未降低守卫。
官方GitHub文档明确dispatch需default branch存在；本仓库default=main，main/.github/workflows API返回404。首次未给含?API路径shell引号导致zsh glob失败，已正确引用重查；未把错误当配置存在。
本机OpenSSL为LibreSSL3.3.6，CMS AES256-GCM真实传输核验留给托管Linux环境check，不假称已本机验证。
