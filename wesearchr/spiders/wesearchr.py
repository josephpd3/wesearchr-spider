import requests
import json
import scrapy
import re

from wesearchr.items import Bounty


class WeSearchr(scrapy.Spider):
    '''WeSearchr Bounty Spider

    This spider will start at both the landing page and the discovery page and pull bounties from various categories.

    Currently built off of the base Spider class, but can also be built with a generic one such as the CrawlSpider: https://docs.scrapy.org/en/latest/topics/spiders.html#crawlspider
    '''

    name = 'wesearchr'

    def start_requests(self):
       
        discover = json.loads(requests.get('http://www.wesearchr.com/api/discover/tag/politics').text)
        while discover:
            for bounty in discover['data']:
                url = 'https://www.wesearchr.com/bounties/' + bounty['slug']  
                yield scrapy.Request(url, self.parse_bounty) 
            new_page = discover['next_page_url']     
            discover = json.loads(requests.get(new_page).text)
            

    #def collect_bounties(self, response):
        #start_requests should probably call this instead of directly calling parse_bounty

    def parse_bounty(self, response):

        title = response.xpath('//div[@class="row"]/h1/text()').extract_first()
        goal = response.xpath('//div[@class="single-project-content"]/p/text()')[0].extract()
        why = response.xpath('//div[@class="single-project-content"]/p/text()')[1].extract()
        requirements = response.xpath('//div[@class="single-project-content"]/p/text()')[3].extract()
        
        #could be used to get time_rem, but might be more useful as deadline
        deadline = response.xpath('normalize-space(//div[@class="bounty-data data-group deadline"])').extract()

        snapshot = response.xpath('//div[@class="project-snapshot"]')

        # Get min and current bounty
        min_bounty = self.grab_min_bounty(response)
        cur_bounty = self.grab_raised_bounty(response)

        item = Bounty(
            url=response.url,
            title=title,
            min_bounty=min_bounty,
            cur_bounty=cur_bounty,
            time_rem=deadline,
            contributions='unknown',
            goal=goal,
            why=why,
            requirements=requirements,
            updates='unknown',
            content_links='unknown'
        )

        yield item

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
