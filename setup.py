from setuptools import setup, find_packages
import os

readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="apexminer-studio",
    version="1.0.0",
    description="Universal Multi-GPU & CPU Cryptocurrency Mining Suite with Cyber HUD Visualizer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ApexMiner Contributors",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "customtkinter>=5.2.0",
        "psutil>=5.9.0",
        "darkdetect>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "apexminer=app.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Topic :: System :: Hardware",
    ],
)
