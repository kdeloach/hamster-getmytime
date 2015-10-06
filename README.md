## Hamster GetMyTime

Submit timesheet data from [Hamster Indicator](https://apps.ubuntu.com/cat/applications/precise/hamster-indicator/)
directly to [GetMyTime](http://www.getmytime.com/).

New activities in Hamster must be created in the following format:

`<client name>@<activity>, <description> <tags>`

Example:

`ACME@software development, fixing some bugs... #billable`

### Usage

```bash
./hamster.py <start_date> <end_date> | ./getmytime.py <username> <password> --from-json
```

### Help

```
./hamster.py -h
usage: hamster.py [-h] [start_time] [end_time]

positional arguments:
  start_time
  end_time

optional arguments:
  -h, --help  show this help message and exit
```

```
./getmytime.py -h
usage: getmytime.py [-h] [--dry-run] [--from-json] username password

positional arguments:
  username
  password

optional arguments:
  -h, --help   show this help message and exit
  --dry-run
  --from-json  Read JSON data from stdin
```
