import json
from monthlyStatReports import apikey
import uploadToGithub as up


def main(stat_reports_path):
    key = apikey(testing=True)
    git_urls = json.loads(open(stat_reports_path, 'r').read().rstrip())
    up.deleteAll(git_urls, key)

    return