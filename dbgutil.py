# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file dbgutil.py
This file contains some debugging utilities.

Currently, it is only used for memory profiling.
"""
import dtlogger

pympler = False

try:
    # try to use pympler when possible
    from pympler import muppy, summary

    pympler = True
except ImportError:
    # otherwise use tracemalloc
    import linecache
    import tracemalloc


def display_mem_usage_tm(key_type='lineno', limit=10):
    snapshot = tracemalloc.take_snapshot()
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    dtlogger.debug("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        dtlogger.debug("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            dtlogger.debug('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        dtlogger.debug("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    dtlogger.debug("Total allocated size: %.1f KiB" % (total / 1024))


def display_mem_usage_mp():
    all_objects = muppy.get_objects()
    sum1 = summary.summarize(all_objects)
    summary.print_(sum1)


def display_mem_usage(key_type='lineno', limit=10):
    if pympler:
        display_mem_usage_mp()
    else:
        display_mem_usage_tm(key_type, limit)
