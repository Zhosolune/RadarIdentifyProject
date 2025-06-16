# 雷达信号多维参数联合智能分选系统

## 项目简介
本系统用于雷达信号的多维参数分析和智能分类，支持数据导入、参数分析、聚类处理和可视化展示等功能。

## 功能特点
- 支持 Excel 格式的雷达信号数据导入
- 多维参数数据可视化
- 基于密度的信号聚类分析
- 实时数据处理和结果展示
- 交互式操作界面

## 系统要求
- Python >= 3.8
- 操作系统：Windows/Linux/MacOS

## 安装方法
1. 克隆项目到本地   ```bash
   git clone https://github.com/yourusername/radar_processor.git
   cd radar_processor   ```

2. 安装依赖   ```bash
   pip install -e .   ```

## 使用说明
1. 启动程序   ```bash
   radar-processor   ```

2. 数据导入
   - 点击"浏览"按钮选择Excel文件
   - 点击"导入"按钮开始处理数据

3. 参数设置
   - 设置聚类参数（epsilon_CF, epsilon_PW, min_pts）
   - 选择处理模式

4. 数据处理
   - 点击"开始处理"进行数据分析
   - 实时查看处理结果
   - 保存分析结果

## 数据格式要求
输入Excel文件需包含以下列：
- CF (载频)
- PW (脉宽)
- DOA (到达角)
- PA (幅度)
- TOA (到达时间)

## 开发文档
### 项目结构
project/
├── core/ # 核心功能模块
│ ├── data_processor.py # 数据处理
│ ├── cluster_processor.py # 聚类处理
│ └── ...
└── ui/ # 用户界面模块
├── main_window.py # 主窗口
└── ...

### 主要模块说明
- `data_processor.py`: 负责数据加载和预处理
- `cluster_processor.py`: 实现聚类算法
- `main_window.py`: 实现用户界面

## 常见问题
1. Q: 程序无法启动？
   A: 检查Python版本和依赖包是否正确安装

2. Q: 数据导入失败？
   A: 确认Excel文件格式是否符合要求

## 更新日志
### v0.1.0 (2024-03)
- 初始版本发布
- 实现基本的数据处理功能
- 完成用户界面设计

## 贡献指南
欢迎提交问题和改进建议！
1. Fork 项目
2. 创建新的分支
3. 提交更改
4. 发起 Pull Request

## 许可证
本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式
- 作者：[你的名字]
- 邮箱：[your.email@example.com]

## 致谢
感谢所有为本项目做出贡献的开发者。
