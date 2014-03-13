import json
import uploadToGithub as up


def main(stat_reports_path, testing):
    git_urls = json.loads(open(stat_reports_path, 'r').read().rstrip())
    up.deleteAll(git_urls, testing)

    return