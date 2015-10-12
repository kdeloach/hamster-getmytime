#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import sys
import argparse
import math
import json
import os.path
import sqlite3
import logging
import itertools

from collections import namedtuple
from datetime import datetime, timedelta


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler(sys.stderr))
log.setLevel(logging.DEBUG)


DATE_FORMAT = '%m/%d/%Y'
DATETIME_FORMAT = '%m/%d/%Y %H:%M:%S'


TimesheetRecord = namedtuple('TimesheetRecord', ['start_time', 'end_time',
                             'customer', 'activity', 'comments', 'tags'])


def fetch_rows(start_date, end_date):
    path = os.path.expanduser('~/.local/share/hamster-applet/hamster.db')
    log.debug(path)

    query = """
        select
            f.start_time,
            f.end_time,
            a.name,
            c.name,
            f.description,
            group_concat(t.name)
        from facts f
        left join activities a on a.id = f.activity_id
        left join categories c on c.id = a.category_id
        left join fact_tags ft on ft.fact_id = f.id
        left join tags t on t.id = ft.tag_id
        where f.end_time is not null
            and f.start_time >= ? and f.end_time < ?
        group by f.id
        order by a.name, c.name, f.start_time
    """

    with sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        result = conn.execute(query, (start_date, end_date))
        rows = (TimesheetRecord(*row) for row in result)
        rows = squash_rows(rows)
        rows = sorted(rows, key=lambda row: row.start_time)
        return format_rows(rows)


def squash_rows(rows):
    keyfn = lambda row: (row.start_time.strftime(DATE_FORMAT),
                         row.customer, row.activity)
    grouped_rows = itertools.groupby(rows, keyfn)
    for key, rows in grouped_rows:
        yield reduce(combine_entries, rows)


def combine_entries(acc, entry):
    # Expand date range to include both entries.
    start_time = min(acc.start_time, entry.start_time)
    end_time = max(acc.end_time, entry.end_time)

    # Separate multiple entry comments with semicolon.
    comments = filter(None, [acc.comments, entry.comments])
    comments = '; '.join(comments).strip()

    # Use the longest tags field.
    # TODO: Union all tags and remove duplicates (comma separated list)
    tags = acc.tags if len(acc.tags) > len(entry.tags) else entry.tags

    return TimesheetRecord(
        start_time,
        end_time,
        acc.customer,
        acc.activity,
        comments,
        tags
    )


def format_rows(rows):
    for row in rows:
        minutes = round_minutes(to_minutes(row.end_time - row.start_time))
        yield {
            'start_time': row.start_time.strftime(DATETIME_FORMAT),
            'end_time': row.end_time.strftime(DATETIME_FORMAT),
            'customer': row.customer,
            'activity': row.activity,
            'comments': row.comments or '',
            'tags': row.tags or '',
            'minutes': minutes,
        }


def to_minutes(delta):
    """
    Convert duration to minutes.
    """
    return int(math.ceil(delta.total_seconds() / 60))


def round_minutes(minutes):
    """
    Round minutes to nearest 15 minute increment.
    """
    i = math.floor(minutes / 15)
    under, over = i * 15, (i + 1) * 15
    d1, d2 = abs(minutes - under), abs(minutes - over)
    # Return the increment closest to the original value.
    return over if d2 <= d1 else under


def test():
    today = datetime.now()
    yesterday = datetime.now() - timedelta(days=1)
    assert to_minutes(today - yesterday) == 24 * 60

    assert to_minutes(timedelta(seconds=0)) == 0
    assert to_minutes(timedelta(seconds=60)) == 1
    assert to_minutes(timedelta(seconds=3600)) == 60

    assert round_minutes(3) == 0
    assert round_minutes(7) == 0
    assert round_minutes(8) == 15
    assert round_minutes(14) == 15
    assert round_minutes(27) == 30
    assert round_minutes(33) == 30
    assert round_minutes(39) == 45
    assert round_minutes(64) == 60


def main():
    test()

    yesterday = datetime.now() - timedelta(days=1)
    tomorrow = datetime.now() + timedelta(days=1)

    parser = argparse.ArgumentParser()
    parser.add_argument('start_time', nargs='?', default=yesterday)
    parser.add_argument('end_time', nargs='?', default=tomorrow)
    args = parser.parse_args()

    if isinstance(args.start_time, basestring):
        args.start_time = datetime.strptime(args.start_time, DATETIME_FORMAT)
    if isinstance(args.end_time, basestring):
        args.end_time = datetime.strptime(args.end_time, DATETIME_FORMAT)

    log.debug(args)

    data = fetch_rows(args.start_time, args.end_time)
    print(json.dumps(list(data)))


if __name__ == '__main__':
    main()
