# 瑞子 · 个人越狱源

自己写的 iOS 插件放这儿，只收录自用、自己维护的包。

## 源地址

```
https://ruizi8.github.io/
```

Sileo：软件源 → 右上角 ＋ → 粘贴地址 → 添加。

## 收录

| 插件 | 标识 | 版本 | 要求 |
| --- | --- | --- | --- |
| 悬浮歌词 | `com.ruizi.floatinglyric` | 1.0.0 | iOS 16.0+ / Relaxin（RootHide）/ arm64e |

## 怎么加新包

把编好的 `.deb` 丢进 `debs/`，推上去就行：

```bash
git add debs/xxx.deb
git commit -m "add xxx"
git push
```

推上去之后 Actions 会自动跑 `scripts/make_index.py`，重新生成 `Packages` 并提交回来。
GitHub Pages 随即更新，手机上刷新软件源就能看到新版本。

本地想手动生成：

```bash
python3 scripts/make_index.py
```

## 目录

```
Repo/
├── Release                 源信息（名称、架构、说明）
├── Packages                自动生成的索引，别手改
├── debs/                   所有 .deb 都放这
├── icons/                  源图标，命名跟包标识一致
├── scripts/
│   ├── make_index.py       扫描 debs/ 生成 Packages
│   └── make_icon.py        生成源图标（纯标准库，无需 Pillow）
├── index.html              这个网页
└── .nojekyll               让 Pages 原样输出，别走 Jekyll
```

## 注意

- `Packages` 是生成物，手改会被下次自动提交覆盖。
- 同名包放多个版本没问题，索引里按版本号倒序排，Sileo 默认装最新的。
- 图标要和 `Package` 字段完全同名（`icons/com.ruizi.floatinglyric.png`），否则 Sileo 显示默认图标。
- deb 架构要和 `Release` 里的 `Architectures` 对得上（这里是 `iphoneos-arm64e`，RootHide 专用）。
