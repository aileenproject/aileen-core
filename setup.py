from setuptools import setup

setup(
    name="aileen",
    description="The Aileen project - A data-driven service layer for Humanitarian Aid",
    author="Seita BV, PNGK BV",
    author_email="nicolas@seita.nl",
    keywords=[],
    version="0.2.1",
    install_requires=[
        "pre-commit",
        "black",
        "python-dotenv",
        "Click",
        "django==1.11.29",
        "django-bootstrap3",
        "django-geojson",
        "django-leaflet",
        "django-cors-headers",
        "django-pandas",
        "jsonfield",
        "humanize",
        "libtmux",
        "netifaces",
        "numpy",
        "pandas",
        "pexpect",
        "pytz",
        "requests",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "requests"],
    packages=["aileen"],
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
    ],
    long_description="""\The Aileen box gathers data on location and uploads it to the Aileen server.
It works robustly, in low-bandwith environments and in a privacy-friendly manner, if needed.
It is versatile (customisable) w.r.t. to the kind of information being gathered.
""",
    scripts=['bin/aileen-box-install'] #, 'bin/aileen-box-start', 'bin/aileen-box-stop'],
)
