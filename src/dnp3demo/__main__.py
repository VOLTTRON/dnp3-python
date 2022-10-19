from dnp3demo import data_retrieval_demo


def main():
    """Read the Real Python article feed"""

    # If an article ID is given, then show the article
    # if len(sys.argv) > 1:
    #     article = feed.get_article(sys.argv[1])
    #     viewer.show(article)
    #
    # # If no ID is given, then show a list of all articles
    # else:
    #     site = feed.get_site()
    #     titles = feed.get_titles()
    #     viewer.show_list(site, titles)
    data_retrieval_demo.main()


if __name__ == "__main__":
    main()
