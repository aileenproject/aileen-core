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
        "Click",
        "django==1.11.19",
        "django-bootstrap3",
        "django-geojson",
        "django-leaflet",
        "django-pandas",
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
    # license="Apache",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
    ],
    long_description="""\
            Humanitarian Aid agencies want to count beneficiaries for the purposes of capacity planning.
            The Aileen package helps to automate the majority of the manual counting of attendance by
            looking at Wifi traffic. This data can be very useful in combination with manual impressions.
""",
)
