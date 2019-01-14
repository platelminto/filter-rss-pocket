# filter-rss-pocket
Filter and add articles from RSS feeds into pocket using AWS DynamoDB. This tool needs to run regularly, so either schedule it using `cron`, or set it up on Heroku using the [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler).

## Setup

### Environment variables

Various environment variables need to be set prior to running the tool:
- `POCKET_CONSUMER_KEY` - Available after creating an app (requiring only 'Add' permissions) in the [pocket developer portal](https://getpocket.com/developer/apps/) - this is unique to your app. 
- `POCKET_ACCESS_TOKEN` - Generated using the guide found at the bottom of [this page](https://github.com/tapanpandita/pocket#OAUTH), using your `POCKET_CONSUMER_KEY` - this is unique to a particular user.
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` - Found under your AWS account [here](https://console.aws.amazon.com/iam/home?#/security_credential).
- `AWS_DEFAULT_REGION` - Must match the region of the DynamoDB database you are using.

### DynamoDB databases

You will need to set up 2 [DynamoDB databases](https://console.aws.amazon.com/dynamodb/home?):

#### feeds

Items in `feeds` require 3 elements, and define which feeds should be read and how they should be filtered:

- `url` (String): The url of the RSS feed. **This is the table's primary key**.
- `filters` (Map): Map with Strings as keys and lists of Strings as values, where the keys are specific keys of the RSS feed dict and the list of Strings defines which words, if present, should be applied as a filter to each feed item.
- `whitelist` (Boolean): Whether the feed's items should only be added if they pass the filter (`true`), or should all items be added _except_ the ones that match the filter (`false`).

These entries have to be **manually** set up on AWS. Below is the JSON for an example item that reads a magazine's RSS feed, only adding articles whose tags include one of 'Science', 'Transportation', or 'Security':

```
{
  "filters": {
    "tags": [
      "Science",
      "Transportation",
      "Security"
    ]
  },
  "url": "https://www.wired.com/feed",
  "whitelist": true
}
```

#### feed_seen

`feed_seen` stores information required to know which feed entries are new, and is **automatically** populated by the tool. You only need to create the table, setting its primary key to `url`.

#### A note on DynamoDB capacity

If you are using provisioned capacity, it is advised to assign the large majority of your write units & a slight majority of your read units to the `feed_seen` database, as it is automatically written to, and will contain more data than the `feeds` database. Either way, this tool will easily remain within [DynamoDB's free tier](https://aws.amazon.com/dynamodb/pricing/provisioned/).
