import os

import feedparser
from pocket import Pocket
import boto3

pocket_instance = Pocket(os.environ['POCKET_CONSUMER_KEY'],
                         os.environ['POCKET_ACCESS_TOKEN'])
important_keys = ['title', 'summary', 'id', 'link', 'media_keywords']
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')


class Feed:
    def __init__(self, url, whitelist, filter_words, items):
        self.url = url
        self.whitelist = whitelist
        self.filter_words = filter_words  # todo filter words
        self.items = items


def get_feed(url):
    return feedparser.parse(url)


def pocket_add(url):
    pocket_instance.add(url)
    print('Added url: ' + url)


def filter_entry_keys(entries):
    items = list()

    for entry in entries:
        item = {key: value for (key, value) in entry.items() if (key in important_keys)}
        items.append(item)

    return items


def parse_feeds(feed_data):
    feeds = list()

    for feed_info in feed_data:
        feeds.append(Feed(feed_info['url'], feed_info['whitelist'],
                          feed_info['filter words'], get_feed_items(feed_info['url'])))

    return feeds


def get_feed_items(url):
    return filter_entry_keys(get_feed(url).entries)


def print_info(items):
    for key, value in items.items():
        print(key + ': ' + str(value))


def get_unseen_items(feeds):  # returns unseen items

    unseen_items = dict()

    feed_seen_table = dynamodb.Table('feed_seen')
    seen_items_dict = get_items_from_table(feed_seen_table)
    seen_ids_dict = {item['url']: item['ids'] for item in seen_items_dict}

    for feed in feeds:
        new_items = feed.items.copy()
        if feed.url in seen_ids_dict.keys():
            for item in feed.items:
                if item['id'] in seen_ids_dict[feed.url]:
                    new_items.remove(item)
        unseen_items[feed.url] = new_items

        if new_items:  # if there are new items, update the db entry for it
            feed_seen_table.put_item(
                Item={
                    'url': feed.url,
                    'ids': [item['id'] for item in feed.items]
                }
            )

    return unseen_items


def add_items_to_pocket(items):
    for item_lists in items.values():
        for item in item_lists:
            pocket_add(item['link'])


def get_items_from_table(table):
    response = table.scan()
    data = response['Items']

    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def read_and_add_items():
    feeds = parse_feeds(get_items_from_table(dynamodb.Table('feeds')))
    unseen_items = get_unseen_items(feeds)
    print_info(unseen_items)
    add_items_to_pocket(unseen_items)


if __name__ == '__main__':
    read_and_add_items()
