import scrapy
from pracDay1.items import doctorMainPage
from scrapy.loader import ItemLoader
class doctor(scrapy.Spider):
    name = "doctor"
    start_urls = [
        "https://www.marham.pk/doctors"
    ]

    def parse(self, response):
        doctorBox = response.xpath("//div[@id='popularSpecialtiesContainer']//div[@class='col-12 col-md-4 specialty-card-wrapper']")
        for doctor in doctorBox:
            loader = ItemLoader(item=doctorMainPage(), selector=doctor)
            # Extract the text inside the <a> tag within h3
            loader.add_xpath('typeOfDoc', ".//div[@class='specialty-content']//h3/a/text()")
            # print(item['typeOfDoc'])
            loader.add_xpath('totalNumOfDocs', ".//div[@class='specialty-content']//div[@class='specialty-meta']//a/text()")
            yield loader.load_item()
            # print(item['typeOfDoc'])
        