# 雷达信号多维参数联合智能分选系统

## 项目简介

本系统用于雷达信号的多维参数分析和智能分类，支持数据导入、参数分析、聚类处理和可视化展示等功能。结合机器学习算法提供智能分选能力。

## 功能特点

- 支持 Excel 格式的雷达信号数据导入
- 多维参数数据可视化
- 基于密度的信号聚类分析
- 机器学习模型辅助分类
- 实时数据处理和结果展示
- 交互式操作界面
- 结果导出与保存

## 系统要求

- Python >= 3.12
- 操作系统：Windows 10/11

## 安装方法

1. 克隆项目到本地

   ```bash
   git clone https://github.com/yourusername/RadarIdentifySystem.git
   cd RadarIdentifySystem
   ```

2. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

## 使用说明

1. 启动程序

   ```bash
   python main.py
   ```

   或使用打包好的可执行文件直接运行

2. 数据导入
   - 点击"浏览"按钮选择Excel文件
   - 点击"导入"按钮开始处理数据

3. 参数设置
   - 设置聚类参数（epsilon_CF, epsilon_PW, min_pts等）
   - 选择处理模式

4. 数据处理
   - 点击"开始处理"进行数据分析
   - 实时查看处理结果
   - 保存分析结果到指定目录

## 数据格式要求

输入Excel文件需包含以下列：

- CF (载频)
- PW (脉宽)
- DOA (到达角)
- PA (幅度)
- TOA (到达时间)

## 开发文档

### 项目结构

```
project/
├── cores/                  # 核心功能模块
│   ├── ThreadWorker.py     # 多线程处理
│   ├── data_processor.py   # 数据处理
│   ├── cluster_processor.py # 聚类处理
│   ├── model_predictor.py  # 机器学习预测
│   ├── plot_manager.py     # 绘图管理
│   ├── params_extractor.py # 参数提取
│   ├── roughly_clustering.py # 粗聚类处理
│   └── log_manager.py      # 日志管理
├── ui/                     # 用户界面模块
│   ├── main_window.py      # 主窗口
│   ├── ui_functions.py     # UI功能函数
│   ├── data_controller.py  # 数据控制器
│   ├── plot_widget.py      # 绘图小部件
│   ├── style_manager.py    # 样式管理
│   ├── switch_widget.py    # 开关小部件
│   ├── loading_spinner.py  # 加载动画
│   └── rectangle_animation.py # 矩形动画
├── model_wm/               # 模型文件
├── resources/              # 资源文件目录
├── logs/                   # 日志目录
├── results/                # 结果输出目录
├── main.py                 # 主程序入口
├── build.py                # 构建脚本
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明文档
```

### 主要模块说明

- `data_processor.py`: 负责数据加载和预处理
- `cluster_processor.py`: 实现聚类算法
- `model_predictor.py`: 实现机器学习预测功能
- `main_window.py`: 实现用户界面
- `data_controller.py`: 数据流控制和管理
- `plot_manager.py`: 图形绘制和数据可视化

## 依赖包

- PyQt5 ~= 5.15.11
- Matplotlib ~= 3.9.2
- NumPy ~= 2.0.2
- Pandas ~= 2.2.3
- TensorFlow ~= 2.18.0
- Keras ~= 3.7.0
- Scikit-learn ~= 1.6.0
- SciPy ~= 1.14.1
- Pillow ~= 11.0.0
- OpenPyXL ~= 3.1.5

## 常见问题

1. Q: 程序无法启动？
   A: 检查Python版本和依赖包是否正确安装

2. Q: 数据导入失败？
   A: 确认Excel文件格式是否符合要求

3. Q: 处理速度慢？
   A: 调整聚类参数，减小数据量或提升计算机配置

## 更新日志

### v1.0.0 (2024-05)

- 完整实现雷达信号处理和分析功能
- 支持多种数据可视化方式
- 集成机器学习模型进行智能分类
- 优化UI界面和用户体验

## 贡献指南

欢迎提交问题和改进建议！

1. Fork 项目
2. 创建新的分支
3. 提交更改
4. 发起 Pull Request

## 许可证

本项目采用 GPL 3.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 邮箱：[1564228136@qq.com]

## 致谢

感谢所有为本项目做出贡献的开发者。
