SRT Sync · Windows 11 独立 EXE 构建项目

功能：
- 批量调整 SRT 歌词时间戳，保留歌词文字与原文件
- 按原曲/处理后歌曲实际时长比例换算（推荐）
- 尝试自动读取 WAV、MP3、M4A、FLAC、AAC 时长；失败时可以手动填秒数
- 按 AU 伸缩百分比换算（需要先确认 AU 参数方向）
- 中文界面，导出为新的 SRT 文件

重要说明：
目前这个 ZIP 是项目文件，不是已经编译好的 EXE。当前环境不能直接在 Windows 上验证并产出可靠的 Windows EXE，因此附带了 GitHub Actions 自动打包配置。你不需要在自己的电脑安装 Python，但需要用 GitHub 网页把项目上传一次，再让云端 Windows 电脑自动打包。

如何取得 EXE（无需安装 Python）：
1. 在 GitHub 网页登录/注册账号，创建一个新的 Public 或 Private repository，名字可用 SRT-Sync。
2. 解压本 ZIP，把里面所有文件和 .github 文件夹一起上传到仓库根目录。注意：要上传 .github/workflows/build-windows.yml，不能漏掉隐藏文件夹。
3. 上传完成后，进入仓库的 Actions 页面，打开 “Build Windows EXE”。
4. 点击 “Run workflow”，再点绿色的 “Run workflow”。如果第一次没有显示工作流，先确认文件路径是 .github/workflows/build-windows.yml，并且文件已提交到 main 分支。
5. 等待任务变绿，点进这次运行记录，在 Artifacts 区域下载 SRT_Sync_Windows11_EXE.zip。
6. 解压后双击 SRT_Sync.exe 即可运行。Windows 可能显示未知发布者提示，这是个人打包程序常见情况；只在你信任自己上传的项目时运行。

使用建议：
- 最稳妥的方法是分别选择原曲音频和 AU 处理后音频，让程序按实际时长计算比例。
- SRT 时间戳按统一比例缩放：新时间戳 = 原时间戳 × 处理后时长 ÷ 原曲时长。
- 只适用于整首歌统一伸缩且没有剪切、拼接或局部变速的情况。
- 变调本身不一定改变时长；如果 AU 处理只改变音高、时长不变，就不要调整 SRT 时间戳。
- “AU 伸缩百分比”模式暂按 100 ÷ 输入百分比换算，务必先用一首短歌比较导出前后实际时长确认方向。优先使用“实际时长比例”模式。

项目包含 app.py、requirements.txt 和 GitHub Actions 自动打包配置。无需本地 Python 的用户只需要 GitHub 网页操作；不想使用 GitHub 的话，也可以把项目交给有 Windows 电脑的人帮忙打包。
