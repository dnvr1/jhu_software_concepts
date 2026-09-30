"""Package the Module 5 application for editable local and CI installs."""

from setuptools import setup


setup(
    name="gradcafe-module-5",
    version="0.1.0",
    description="GradCafe analysis application and security exercises",
    py_modules=[
        "analysis_format",
        "app",
        "clean",
        "comment_scores",
        "load_data",
        "models",
        "orm_queries",
        "query_data",
        "run_flask",
        "scrape",
        "scrape_refresh",
        "storage",
    ],
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "Flask>=3.1,<4",
        "SQLAlchemy>=2.0,<3",
        "psycopg[binary]>=3.2,<4",
        "beautifulsoup4>=4.14,<5",
        "Pillow>=11,<13",
        "websocket-client>=1.8,<2",
    ],
    python_requires=">=3.10",
)
