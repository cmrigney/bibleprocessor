Bible Processor
==============

Web app that provides various tools for studying the Bible. Thanks to [this repo for the data.](https://github.com/robertrouse/KJV-bible-database-with-metadata-MetaV-)

Dependencies
-------

 * Python 2.7+
 * web.py
 * MongoDB Server
 * pymongo

Setup
--------

Make sure you have the Mongo DB server running.

 - Run `python readBible.py` to import the data into the MongoDB database
 - Run `python testweb.py` to run the web server.  Browse to `http://localhost:8080`
