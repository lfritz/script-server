# Script Server

The script server provides an HTTP+JSON API that lets users submit scripts which are entered into a queue and run with a configurable interpreter. Each user has a home directory in which their scripts are run; the API provides methods to upload/download/manage files in this directory so users can provide input data and access output data for the scripts.

The intention of the script server is to let users run computationally intensive tasks on a server without logging in to the server at the operating system level. It was originally written for a server version of the BrainVoyager software package (http://brainvoyager.com/), but it now completely independent of BrainVoyager. In principle, it work with any program that's run from the command line and reads scripts over standard input.

The server also has a web interface with the same functionality as the API, although that's still a bit of a work-in-progress.

## Requirements
To run the script server, you need Python 2.7 and the following Python libraries:

* Twisted (http://twistedmatrix.com/)
* Flask (http://flask.pocoo.org/) and two Flask extensions:
    * Flask-RESTful (http://flask-restful.readthedocs.org/)
    * Flask-Bcrypt (https://pythonhosted.org/Flask-Bcrypt/)

It'll probably work with older Python versions, too, but I've only tested 2.7.

## Setup
The script server uses a sqlite database and a configuration file called `script-server.cfg` which contains important settings such as the port it runs on and the name of the database file. To create an initial configuration and database, run

    python setup.py

Edit `script-server.cfg` to change the default settings as needed. The most important settings are `COMMAND` and `ARGS` which specify the script interpreter command and any arguments it should be run with.

# Use
Start the server with

    python script-server.py

You can then access the web interface at http://localhost:5000/ and the JSON API at http://localhost:5000/api/ (assuming you've kept the default port number of 5000). The API is described in detail in `API.md`.

## License
The code is copyright (c) 2014 Brain Innovation B.V., Maastricht, The Netherlands. It is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.