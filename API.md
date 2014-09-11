# Script Server HTTP+JSON API

The API is based on HTTP and JSON. You use it by sending HTTP requests to the API endpoints described below. For example, if your server runs on the same machine as the client, on port 5000, you can get a list of jobs by sending a GET request to http://localhost:5000/api/jobs and parsing the JSON code returned.

All endpoints except for `/api/info` and `/api/login` require that you log in first. We use cookies for this, which lets us use the same mechanism for the API and web interface, so on the client side you have to make sure cookies are stored and used for subsequent requests.

The file `curl.txt` shows how to use the API from the command line.

## /api/info

Send a GET request to get some basic information on the server. The response is a JSON object with the number of scripts currently running, the number of script in the queue, the server's name, the script server version number and the current username:

```
{
    "jobs_running": 1,
    "jobs_waiting": 3,
    "name": "myserver",
    "username": "joe",
    "version": "0.1.0"
}
```

Username is `null` if the client is not loggged in.

## /api/login

Send a POST request to log in. The message body must be a JSON object containing username and password, for example

    {"username":"joe", "password":"123"}

## /api/logout

Send a POST request to log out.

## /api/run

Send a POST request to submit a script to the server. The message body is simply the script. If successful, the response is a JSON object with the new job's id:

    {"job_id": 123}

## /api/jobs

Send a GET request to get a list of jobs. The response is a JSON array:

```
[
    {
        "job_id": 1,
        "status": "done",
        "user": "joe"
    },
    // more jobs ...
]
```

## /api/jobs/*job_id*

Request information or an action with regard to the job, where *job_id* is a numeric id.

### GET request
Send a GET request to get more detailed information about a specific job. If successful, returns a JSON object with

* the script
* the user that submitted it
* script output on standard out and standard err
* start and end times (`null` if the script has not been started/ended)
* script status: `waiting`, `running`, `done` or `failed`.

Example:

```
{
    "end": "2014-09-11T06:27:02",
    "err": "",
    "job_id": 1,
    "out": "Hello, World!\n",
    "script": "print(\"Hello, World!\")",
    "start": "2014-09-11T06:27:02",
    "status": "done",
    "user": "admin"
}
```

### POST request
Send a POST request with a JSON object containing a single field "command" to request an action to be taken with regard to the script:

    {"command": "terminate"}

Currently, there are only two commands: `terminate` and `kill` request that the server sends the TERM or KILL signal to the interpreter. Both are only possible for scripts with state `running`.

## /api/files/*path*
Access to files and directories on the server, where *path* indicates a file or directory in the user's directory. For example, if the user's directory on the server is `/home/joe/data`, the the API endpoint `/api/files/foo/bar` refers to `/home/joe/data/foo/bar`.

### GET
If *path* refers to a file, the file is returned.

If *path* refers to a directory, a directory listing in the form of a JSON array is returned. Each entry contains the file name, file size in bytes (not for directories) and the last-modified date. For example:

```
[
    {
        "mtime": "2014-07-31T07:08:31",
        "name": "myfile.pdf",
        "size": 123456
    },
    {
        "mtime": "2014-07-31T07:07:57",
        "name": "mydirectory"
    }
]
```

### POST
POST requests are used for file system operations on the server. The request body must be a JSON object containing the key `command` to indicate which action to take. So far, there are three possible commands:

The `move` command is for moving the file or directory indicated by *path* to the path given by key `to`. Example:

    {"command": "move", "to": "/test"}

Analogously, the `copy` command is for copying a file or directory:

    {"command": "copy", "to": "/test"}

The `mkdir` command is for creating a new directory, whose name is given by the key `name`, under *path*. Example:

    {"command": "mkdir", "name": "foo"}

### PUT
Use a PUT request to upload a file.

### DELETE
Use a DELETE request to delete a file on the server. If *path* is a directory, it is deleted recursively.
