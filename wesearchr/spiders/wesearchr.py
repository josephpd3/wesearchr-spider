import requests
import json
import scrapy
import re
import logging
import time

import wesearchr.settings as settings

from wesearchr.items import Bounty
from json import JSONDecodeError

from bs4 import BeautifulSoup
from scrapy.utils.response import get_base_url
from urllib.parse import urljoin


class WeSearchr(scrapy.Spider):
    '''WeSearchr Bounty Spider

    This spider will start at both the landing page and the discovery page and pull bounties from various categories.

    Currently built off of the base Spider class, but can also be built with a generic one such as the CrawlSpider: https://docs.scrapy.org/en/latest/topics/spiders.html#crawlspider
    '''

    name = 'wesearchr'

    # A dict to hold information we can glean from the
    # initial list of bounties gotten through requests
    slug_to_summary_blob = {}

    def start_requests(self):
        """
        Start chain of requests from starting URLs
        """
        discover_url = 'https://www.wesearchr.com/api/discover/newest?page={}'
        page_no = 1

        while True:
            discover = json.loads(requests.get(discover_url.format(page_no)).text)

            for bounty in discover['data']:
                # Since we're iterating over JSON blobs of these already,
                # we can store some goodies while we're at it.
                self.slug_to_summary_blob[bounty['slug']] = bounty

                url = 'https://www.wesearchr.com/bounties/' + bounty['slug']  
                yield scrapy.Request(url, self.parse_bounty)

            if discover['next_page_url'] is None:
                break
            page_no += 1


    def parse_bounty(self, response):
        """
        Parse a bounty page
        """
        self.base_url = get_base_url(response)

        try:
            slug = response.url.split('/')[-1]
            bounty_id = self.get_bounty_id(slug)
            deadline = self.get_bounty_deadline(slug)
            status = self.get_bounty_status(slug)

            title = response.xpath('//div[@class="row"]/h1/text()').extract_first()

            # Get min and current bounty
            min_bounty = self.grab_min_bounty(response)
            cur_bounty = self.grab_raised_bounty(response)

            about = self.get_about(response)
            contributions = self.get_contributions(bounty_id)
            updates = self.get_updates(response)

            content_links = self.get_content_links(response)

            item = Bounty(
                bounty_id=bounty_id,
                url=response.url,
                title=title,
                status=status,
                min_bounty=min_bounty,
                cur_bounty=cur_bounty,
                deadline=deadline,
                contributions=contributions,
                about=about,
                updates=updates,
                content_links=content_links
            )

            yield item

        except Exception as e:
            # While we keep developing, this is a decent lazy
            # solution to figure out any errors that propagate
            # all the way up to this function
            self.logger.error(slug)
            self.logger.exception('message')

    def get_about(self, response):
        """
        Get about fields: goal, why, requirements
        """
        goal = None
        why = None
        requirements = None

        # grab about block from div
        about_block = response.css('div.project-about')
        about_block_sections = about_block.css('div.single-project-content')

        # Don't grab sub-section if it doesn't exist
        try:
            goal = BeautifulSoup(about_block_sections[0].extract(), 'html.parser') \
                   .get_text() \
                   .replace('\n', '')
        except KeyError:
            pass

        # Don't grab sub-section if it doesn't exist
        try:
            why = BeautifulSoup(about_block_sections[1].extract(), 'html.parser') \
                  .get_text() \
                  .replace('\n', '')
        except KeyError:
            pass

        # Don't grab sub-section if it doesn't exist
        try:
            requirements = BeautifulSoup(about_block_sections[2].extract(), 'html.parser') \
                           .get_text() \
                           .replace('\n', '')
        except KeyError:
            pass

        return {
            'goal': goal,
            'why': why,
            'requirements': requirements
        }

    def get_content_links(self, response):
        """
        Get the links to content from the body of the bounty
        """
        links_list = response.css('div.project').css('a').xpath('@href').extract()
        fully_qualified_links = []

        # Complete a link to be fully-qualified if it is relative, otherwise leave it
        for link in links_list:
            fql = urljoin(self.base_url, link) if link.startswith('/') else link
            fully_qualified_links.append(fql)

        return list(set(fully_qualified_links))

    def get_bounty_id(self, slug):
        """
        Get the id of a bounty page given the slug
        """
        return self.slug_to_summary_blob[slug]['id']

    def get_bounty_deadline(self, slug):
        """
        Get the bounty deadline date given the slug
        """
        # You never know if some wont have deadlines!
        return self.slug_to_summary_blob[slug].get('deadline', None)

    def get_bounty_status(self, slug):
        """
        Get the bounty status given the slug
        """
        return self.slug_to_summary_blob[slug].get('status', None)

    def get_contributions(self, bounty_id):
        """
        Get contributions given bounty id
        """
        contributions = []
        contrib_page_str = 'https://www.wesearchr.com/api/bounties/{}/contributions?page={}'
        page_no = 1 # start off at square one...

        # Keep grabbing pages til it runs dry!
        while True:
            try:
                # Pause between contributions page requests to reduce aggressiveness of crawl
                time.sleep(settings.CONTRIB_PAUSE)
                page_request = requests.get(contrib_page_str.format(bounty_id, page_no)).text
                contrib_page = json.loads(page_request)
            except JSONDecodeError:
                # If no contributions result, return the empty list
                return contributions

            # Add next page to our growing list...
            contributions.extend(contrib_page['data'])

            if contrib_page['next_page_url'] is None:
                break
            page_no += 1

        return contributions

    def get_updates(self, response):
        """
        Get updates on bounty
        """
        updates = []
        # Make it easier to pull out dates from inline js
        datestring_pat = 'moment\.utc\(\\\'([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})'

        try:
            updates_container = response.css('div.project-updates-top')[0]
        except IndexError:
            # If nothing results, no updates for this bounty;
            # return empty list
            return updates

        # Now, the information for a single update lives
        # in two adjacent divs, so we're gonna do some voodoo here
        updates_child_divs = updates_container.xpath('.//div')
        num_updates = int(len(updates_child_divs) / 2) # Floor it!

        for idx in range(num_updates):
            # Remember these are in pairs when indexing divs
            date_block = updates_child_divs[idx * 2].extract()
            # Pull out date from inline js
            date = re.search(datestring_pat, date_block).groups()[0]
            text = updates_child_divs[(idx * 2) + 1].xpath('.//p/text()').extract()[0]

            # pop it on the list!
            updates.append({
                'date': date,
                'text': text
            })

        return updates

    def grab_raised_bounty(self, response):
        """
        Grab bounty raised so far from response
        """
        amount_raised_text = response.css('div.bounty-data')[0].css('div').extract()[-1]
        # This is squirreled away in some inline javascript...
        amount_raised_match = re.search('document\.write\(\\\'([0-9]+)\\\'', amount_raised_text)
        return int(amount_raised_match.groups()[0])

    def grab_min_bounty(self, response):
        """
        Grab minimum required bounty from response
        """
        min_bounty_text = response.css('div.bounty-data')[1].css('div').extract()[-1]
        min_bounty_match = re.search('document\.write\(\\\'([0-9]+)\\\'', min_bounty_text)

        # Some bounties don't have a minimum requirement;
        # Scrapy will take None and translate it to
        # null in JSON, so no worries!
        if min_bounty_match is None:
            return None

        # ...otherwise, we good!
        return int(min_bounty_match.groups()[0])
