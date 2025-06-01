from setuptools import setup, find_packages

setup(
    name="hiv_program_tracker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "sqlmodel>=0.0.8",
        "alembic>=1.7.0",
        "asyncpg>=0.25.0",
    ],
) 