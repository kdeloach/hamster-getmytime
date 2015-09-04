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
