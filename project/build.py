import PyInstaller.__main__
from pathlib import Path
import os
import sys
import argparse


def build_app():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='构建雷达信号识别系统')
    parser.add_argument('--onefile', action='store_true', help='打包为单个可执行文件，默认为目录模式')
    parser.add_argument('--optimize', action='store_true', help='优化打包大小，排除不必要的依赖')
    args = parser.parse_args()
    
    # 获取当前目录
    current_dir = Path(__file__).parent

    # 设置图标路径
    icon_path = current_dir / 'resources' / 'icon.ico'

    # 设置主程序路径
    main_path = current_dir / 'main.py'

    # 创建排除文件 - 用于排除不必要的依赖
    excludes_file = current_dir / 'excludes.txt'
    if args.optimize:
        with open(excludes_file, 'w', encoding='utf-8') as f:
            f.write("""
# TensorFlow相关的排除项（只保留核心推理功能）
tensorflow.contrib
tensorflow.examples
tensorflow.keras.applications
tensorflow.keras.datasets
tensorflow.python.debug
tensorflow.python.profiler
tensorflow.python.tools
tensorflow.tools
tensorflow.compiler
tensorflow.lite
tensorflow.data.experimental
tensorflow.distribute

# Matplotlib不必要的后端
matplotlib.backends.backend_gtk
matplotlib.backends.backend_gtk3
matplotlib.backends.backend_wx
matplotlib.backends.backend_macosx

# Jupyter相关
IPython
jupyter
ipykernel
nbconvert
nbformat

# 其他不太可能使用的大型库
tornado
zmq
pytz.zoneinfo
jedi
parso
pydoc_data

# 测试和示例代码
*.test
*.tests
conftest
test
tests
testing
docs
examples
""")

    # PyInstaller参数 (为PyInstaller 6.0+兼容更新)
    pyinstaller_args = [
        str(main_path),  # 主程序路径
        '--name', '雷达信号识别系统',  # 输出文件名
        '--noconsole',  # 不显示控制台窗口
        '--icon', str(icon_path),  # 设置图标
        '--noconfirm',  # 覆盖输出目录
        '--clean',  # 清理临时文件
        
        # 静态链接UCRT (Universal C Runtime)
        # 这是解决Windows 7兼容性问题的最佳方法
        '--target-architecture', 'x64',  # 指定64位架构
        '--uac-admin',  # 请求管理员权限以解决某些系统级访问问题
        
        # 静态链接UCRT的关键参数
        # 注意：确保Visual Studio安装了相应的C++构建工具
        '--runtime-tmpdir', '.',  # 设置临时目录为当前目录，避免权限问题
        
        # 添加模型文件
        '--add-data', 'model_wm;model_wm',  # 添加模型文件
        
        # 隐式导入
        '--hidden-import', 'sklearn.neighbors._partition_nodes',
        '--hidden-import', 'sklearn.tree._partitioner',
        '--hidden-import', 'sklearn.tree._criterion',
        '--hidden-import', 'sklearn.tree._splitter',
        '--hidden-import', 'sklearn.tree._utils',
        '--hidden-import', 'sklearn.neighbors._quad_tree',
        '--hidden-import', 'sklearn.manifold._barnes_hut_tsne',
        '--hidden-import', 'sklearn.utils._cython_blas',
        # 移除可能不存在的模块
        # '--hidden-import', 'sklearn.neighbors._typedefs',
        '--hidden-import', 'sklearn.metrics._pairwise_distances_reduction',
    ]
    
    # 根据命令行参数选择打包模式
    if args.onefile:
        # 单文件模式
        pyinstaller_args.append('--onefile')
        package_type = "单文件"
    else:
        # 目录模式（默认）
        pyinstaller_args.append('--onedir')
        package_type = "目录"
        
    # 如果需要优化大小，添加排除文件
    if args.optimize:
        # 添加排除模块 - 使用正确的格式（无等号）
        pyinstaller_args.extend([
            '--exclude-module', 'tensorflow.contrib',
            '--exclude-module', 'tensorflow.examples',
            '--exclude-module', 'tensorflow.lite',
            '--exclude-module', 'IPython',
            '--exclude-module', 'jupyter',
            '--collect-submodules', 'tensorflow.keras.models',  # 只收集实际需要的TF模块
            '--collect-submodules', 'tensorflow.nn',
            '--collect-data', 'tensorflow.keras.models',
        ])
        
        # 尝试使用UPX，但按照正确的格式传递参数
        upx_dir = os.path.expandvars("%USERPROFILE%/.upx")
        if os.path.exists(upx_dir):
            pyinstaller_args.extend([
                '--upx-dir', upx_dir,
                '--upx',
            ])
            print(f"找到UPX目录: {upx_dir}，将使用UPX压缩")
        
        # 更多排除项
        pyinstaller_args.extend([
            '--exclude-module', 'tkinter',  # 如果不使用tkinter界面
            '--exclude-module', 'PyQt5.QtWebEngineWidgets',  # 排除大型Web引擎组件
            '--exclude-module', 'lib2to3',  # Python转换工具，不需要
        ])
        
        # 禁用某些大型依赖库的自动检测
        os.environ['PYTHONNOUSERSITE'] = '1'  # 避免加载用户site-packages
        
        size_optimized = "（体积优化）"
    else:
        size_optimized = ""

    # 运行PyInstaller
    print("\n=====================================================")
    print(f"正在使用静态链接UCRT方式打包应用程序（{package_type}模式）{size_optimized}...")
    if args.optimize:
        print("已启用体积优化，将排除不必要的依赖项")
        print("这将显著减小生成文件的大小，但可能需要更多测试以确保功能完整")
    print("这将显著提高Windows 7兼容性，但需要较长的编译时间")
    print("=====================================================\n")
    
    # 打印要执行的命令
    cmd_str = "pyinstaller " + " ".join([f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in pyinstaller_args])
    print(f"执行命令: {cmd_str}")
    
    PyInstaller.__main__.run(pyinstaller_args)

    print("\n打包完成！")
    print("\n【重要提示】")
    print(f"1. 已使用静态链接UCRT，提供Windows 7兼容性（{package_type}模式）{size_optimized}")
    
    if args.onefile:
        print("2. 应用已打包为单个可执行文件")
        print("3. 直接分发 dist 目录下的 雷达信号识别系统.exe 文件即可")
        print(f"4. 应用程序位于: {current_dir / 'dist' / '雷达信号识别系统.exe'}")
        print("\n注意：单文件模式可能导致启动速度较慢，因为需要在临时目录解压依赖文件")
    else:
        print("2. 应用已打包为文件夹而非单个可执行文件，确保所有依赖项正确包含")
        print("3. 分发时，请将整个'dist/雷达信号识别系统'文件夹一起分发")
        print("4. 用户应运行文件夹中的'雷达信号识别系统.exe'文件")
        print(f"5. 应用程序位于: {current_dir / 'dist' / '雷达信号识别系统' / '雷达信号识别系统.exe'}")
    
    if args.optimize:
        print("\n优化说明：")
        print("1. 已排除TensorFlow的非核心组件，如示例、调试工具等")
        print("2. 排除了一些可能不需要的库和模块")
        print("3. 如果应用出现ImportError，可能需要调整排除项")
        print("4. 在所有目标平台上充分测试优化后的应用")
    
    print("\n若要测试Windows 7兼容性:")
    print("1. 在Windows 7系统上运行应用程序")
    print("2. 如果仍然出现DLL缺失错误，可考虑包含VC++可再发行组件包")
    print("\n要创建安装包，您可以：")
    if args.onefile:
        print("1. 直接分发单个exe文件")
        print("2. 使用NSIS或Inno Setup创建安装程序，并自动安装VC++运行时")
    else:
        print("1. 将整个文件夹压缩为ZIP文件")
        print("2. 使用NSIS或Inno Setup创建安装程序，并自动安装VC++运行时")
    print("\n使用方法:")
    print("- 默认目录模式打包: python build.py")
    print("- 单文件模式打包: python build.py --onefile")
    print("- 优化文件大小: python build.py --optimize")
    print("- 组合使用: python build.py --onefile --optimize")


if __name__ == '__main__':
    build_app()
