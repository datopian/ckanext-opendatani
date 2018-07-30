This script connects to the Northern Ireland SFTP server, downloads files, and update them on the NI CKAN portal.
Each directory on the SFTP server is connected to the CKAN datasets.
Dataset Name is the name of the SFTP folder. The ID of the resource is the name of the file.

## Installation
Inside virtual env install uploader dependencies:

```
pip install -r requirements.txt
```

## Config Settings
These are the required options:
```
```

## Running uploader script

Go to the sftp-script directory and run:

```
python uploader.py
```

## Running tests

Running tests with a ‘-v’ is more verbose, showing which tests
ran.

```
python test_uploader.py -v
```