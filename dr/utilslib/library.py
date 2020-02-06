# coding: utf-8
"""
This module includes utility functions and classes
"""

import os
import sys
import time
import functools
import logging
from datetime import datetime
import json
import yaml

logging.basicConfig(format='%(asctime)-15s %(name)s:%(lineno)s - %(funcName)s() %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def dynamic_method_call(*args, **kwargs):
    method_prefix = kwargs.get('method_prefix', '')
    method_suffix = kwargs.get('method_suffix', '')
    try:
        method_text = kwargs['method_text']
        object = kwargs['method_object']
    except KeyError as e:
        raise e
    method_name = "{}{}{}".format(method_prefix, method_text, method_suffix)
    try:
        target_func = getattr(object, method_name)
    except AttributeError as e:
        raise e
    if callable(target_func):
        [kwargs.pop(x, None) for x in ['method_object', 'method_prefix', 'method_text', 'method_suffix']]
        return target_func(*args, **kwargs)


def k8s_chunk_wrapper(func, limit=100, next_item=''):
    """
    Function wrapper to process kubernetes client calls that get lists of items in chunks

    Args:
    func      -- The function to be called
    limit     -- The maximum number records to process in each call
    next_item -- The next item to process, set to '' to start at beginning.

    Returns:
    Nothing
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        all_items = []
        next_item = ''

        while next_item is not None:
            kwargs["next"] = next_item
            try:
                results = func(*args, **kwargs)
                next_item = results.metadata._continue
            except Exception as e:
                raise e
            log.debug("Items retruned by {} in this chunk...\n{}".format(func.__name__, results.items))
            all_items += results.items
        return all_items
    return wrapper


def retry_wrapper(func, max_tries=5, delay=1, report=False):
    """
    Function wrapper to automatically retry failed operations

    Args:
    func      -- The function to be called
    max_tries -- The maximum number of retries, defaults to 5
    delay     -- Delay between each retry, defaults to 2 seconds
    report    -- Indicate whether to report errors, defaults to False

    Returns:
    Results returned by function called
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tries = 0
        while True:
            tries += 1
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if tries < max_tries:
                    time.sleep(delay ** tries)
                    continue
                if report:
                    log.error(
                        "Operation: {0}, retried {1:d} times but failed, "
                        "exception {2}", func.__name__, max_tries, e)
                raise e
    return wrapper


def timing_wrapper(func):
    """
    Function wrapper to automatically retry failed operations

    Args:
    func      -- The function to be called

    Returns:
    Results returned by function called
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            started = datetime.utcnow()
            return func(*args, **kwargs)
        finally:
            finished = datetime.utcnow()
            elapsed = finished - started
            log.debug("Operation: {0}, Elapsed: {1}".format(func.__name__, str(elapsed)))
    return wrapper


def _max_len(my_items,
             item_name='name',
             min_len=4):
    """
    Return the maximum length of a specified field in a list of items
    Args:
    my_items       The list of dictionaries or objects to process
    item_name      The dictionary key or object attribute
    min_len        The minimum length to return

    Returns:
    max_len        The maximum length of the field specified.
    """
    max_len = min_len
    my_list = my_items
    if isinstance(my_items, dict):
        my_list = my_items.itervalues()
    for item in my_list:
        if isinstance(item, dict):
            l = (len(item[item_name])
                 if (item_name in item and item[item_name])else 0)
        else:
            it = getattr(item, item_name, str(item))
            l = len(it) if it is not None else 0
        max_len = (l if l > max_len else max_len)
    return max_len
