Samba.ai feed generators
=======================

This repository contains / will contain exporters for different eshop platforms. Each exporter will produce feeds for samba.ai marketing platform. We decided to make this project opensource for simplifying work with user modifications and possibility of reuse of some parts of the project. Please share your modifications with us.

Currently I'm working on exporter for prestashop platform, testing it with peewee ORM. Since it is not possible for me to get rid of some annoyances of peewee, it is quite possible that I'll rewrite this exporter later.

Prestashop exporter
-------------------

Written in python3. Exports data directly from mysql, can emulate calculation of sales. Whole configuration is in config.py file.

Instalation on linux (simplified, for more info see **docs** directory):
* download this repository
* copy **prestastashop** directory to your target location
* edit configuration in **config.py**
* create directory set in **OUTPUT\_DIRECTORY**
* add **exporter.py** script to your crontab. suggested execution time is 0:30 every day.
* configure your webserver to enable access to **OUTPUT\_DIRECTORY**, limit access to this directory, possibly by simple authentication (user:password)
* setup feed uris at samba.ai website, possibly in form of https://user:password@yourserver/yourdirectory/feedname.xml

