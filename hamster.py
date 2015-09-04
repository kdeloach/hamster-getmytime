#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import argparse
import math
import json
import os.path
import sqlite3

from datetime import datetime, timedelta


DATE_FORMAT = '%m/%d/%Y %H:%M:%S'


def fetch_rows(start_date, end_date):
    path = os.path.expanduser('~/.local/share/hamster-applet/hamster.db')

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
    """

    with sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        for row in conn.execute(query, (start_date, end_date)):
            start_time = row[0]
            end_time = row[1]
            minutes = int(math.ceil((end_time - start_time).seconds / 60))
            comments = row[4] or ''

            # I find that it is most convenient to input time in hamster
            # by using the following syntax:
            #
            # client name@software development, fixing some bugs... #billable
            #
            # Which means that "client name" maps to `activity` and
            # "software development" maps to `category`.
            #
            # This is the reason why I need to swap `activity` and `category`
            # in the final JSON output.

            yield {
                'start_time': start_time.strftime(DATE_FORMAT),
                'end_time': end_time.strftime(DATE_FORMAT),
                'minutes': minutes,
                'comments': comments,
                'customer': row[2],
                'activity': row[3],
                'tags': row[5],
            }


def main():
    yesterday = datetime.now() - timedelta(days=1)
    tomorrow = datetime.now() + timedelta(days=1)

    parser = argparse.ArgumentParser()
    parser.add_argument('start_time', nargs='?', default=yesterday)
    parser.add_argument('end_time', nargs='?', default=tomorrow)
    args = parser.parse_args()

    data = fetch_rows(args.start_time, args.end_time)
    print(json.dumps(list(data)))


if __name__ == '__main__':
    main()
