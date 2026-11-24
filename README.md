# 📚 网络小说爬虫

一个通过统一入口自动识别站点的小说抓取工具，也可以作为 Gemini CLI Skill 使用。

## 🌐 支持的站点

| 站点 | 网站 |
| --- | --- |
| 半夏小说（繁体） | [xbanxia.cc](https://www.xbanxia.cc/) |
| 半夏小说（简体） | [banx.la](https://www.banx.la/) |
| 52书库 | [52shuku.net](https://www.52shuku.net/vip) |
| 256文学 | [256wx.org](https://www.256wx.org/net) |
| 孙指南 / 醋溜儿 | [sunzhinan.com](https://www.sunzhinan.com/) / [culiu.cc](https://www.culiu.cc/) |
| 思兔网 | [sto520.com](https://www.sto520.com/) |

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 命令行运行

将小说主页链接作为参数传入，程序会自动识别对应站点：

```bash
python3 main.py "<小说主页URL>"
```

**半夏简体站示例：** 先打开 [banx.la](https://www.banx.la/) 并进入要抓取的小说主页，再将该页面链接传给程序：

```bash
python3 main.py "<从 banx.la 复制的小说主页链接>"
```

半夏繁体站也可使用同样的方式，例如访问 [xbanxia.cc](https://www.xbanxia.cc/) 并传入站内小说主页链接。

### 作为 Gemini CLI Skill 使用

在对话中提供小说主页链接即可，例如：

> 帮我下载这部小说：[打开 banx.la 并复制小说主页链接](https://www.banx.la/)

抓取结果默认合并保存为 `.txt` 文件，输出到 `~/Downloads/`。

## 🧩 项目结构

| 文件 / 目录 | 说明 |
| --- | --- |
| `main.py` | 统一入口，根据链接域名分发到对应解析器 |
| `crawl_utils.py` | 通用网页请求、重试、随机暂停、信息提取和文件保存 |
| `parsers/novel_banxia.py` | 半夏小说解析器（支持繁体和简体站） |
| `parsers/novel_52.py` | 52书库解析器 |
| `parsers/novel_256.py` | 256文学解析器 |
| `parsers/novel_sunzhinan.py` | 孙指南 / 醋溜儿解析器 |
| `parsers/novel_situ.py` | 思兔网解析器 |
