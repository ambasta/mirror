from setuptools import setup

setup(
    name="mirror",
    packages=["mirror"],
    zip_safe=False,
    entry_points={"console_scripts": ["mirrorbb2gh=mirror.cli:migrate"]},
    install_requires=["click", "PyGithub", "aiohttp"],
)
