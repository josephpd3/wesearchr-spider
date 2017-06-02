import requests
import json
import scrapy
from wesearchr.items import Bounty


class WeSearchr(scrapy.Spider):
    '''WeSearchr Bounty Spider

    This spider will start at both the landing page and the discovery page and pull bounties from various categories.

    Currently built off of the base Spider class, but can also be built with a generic one such as the CrawlSpider: https://docs.scrapy.org/en/latest/topics/spiders.html#crawlspider
    '''

    name = 'wesearchr'

    def start_requests(self):
       
        discover = json.loads(requests.get('http://www.wesearchr.com/api/discover/newest?page=1').text)   
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

        item = Bounty(
            url = 'unknown',
            title=title,
            min_bounty = 'unknown',
            cur_bounty = 'unknown',
            time_rem = deadline,
            contributions ='unknown',
            goal = goal,
            why = why,
            requirements = requirements,
            updates = 'unknown',
            content_links = 'unknown'
        )

        yield item
      
      
