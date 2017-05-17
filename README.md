# WeSearchr Bounty Spider

## Installation and Getting Started

### Installation
For those working with `conda`, you just need to spin up an `env` with `Python 3.6` and `Scrapy`. You may encounter the issue I describe below regarding `lxml`, but the fix is easy (see below). I also `pip freeze`'d the requirements into a file within the repo in case anyone is working with a different environment manager for Python and needs the reference.

For more details, [here are the official docs on installation for Scrapy](https://docs.scrapy.org/en/latest/intro/install.html).

### Issues with Installation
I did have an issue with getting Scrapy to start a project correctly, and I don't know if this problem will present itself otherwise: [I encountered this runtime error with the `lxml` dependency, which seems to have stemmed from a version mismatch. The Stack Overflow comments should help you to resolve it as well.](http://stackoverflow.com/questions/23172384/lxml-runtime-error-reason-incompatible-library-version-etree-so-requires-vers)

### First Steps
I highly recommend checking out [the starter tutorial](https://docs.scrapy.org/en/latest/intro/tutorial.html) followed by [the code used to scrape congressional records](https://github.com/Data4Democracy/assemble/tree/master/congress).

The [Dublin Council Crawler](https://github.com/bstarling/town-council/tree/scrapy-proposal/council_crawler) is a really great example of using the `CrawlSpider` class as a basis. I believe this would be the best one to extend for this task, but I'm open to suggestions (@josephpd3).

I also recommend checking out [the docs on Item Pipelines](https://docs.scrapy.org/en/latest/topics/item-pipeline.html), since they're a pretty great abstraction for handling the items collected by the spider. There's a MongoDB example within there that could definitely be used here with a little tweaking.

### Learning to Work with Scrapy Extraction
Scrapy [comes with a shell that is pretty awesome](https://docs.scrapy.org/en/latest/topics/shell.html#topics-shell) for experimenting and determining what extraction commands to write to get what you want on specific pages.

## Contributing
The same holds here as it does in the [Assemble repository](https://github.com/Data4Democracy/assemble) and all other D4D projects:
* Learning while contributing is absolutely encouraged--please ask any questions you might have in regards to working with Scrapy or the other tools we are using. The docs are well written, but we are all here to help!
* Good Code is Reviewed Code--please help review PRs as you are able! Good, constructive criticism helps us work and learn better together.
* This README belongs to everyone--if you see a mistake that needs correcting, have pertinent or helpful information, or want to share a bugfix that was necessary for the project, please feel free to edit this README. This keeps us all on the same page.
