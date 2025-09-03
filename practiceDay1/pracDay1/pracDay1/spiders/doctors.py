import scrapy
from pracDay1.items import doctorMainPage
from scrapy.loader import ItemLoader


class DoctorSpider(scrapy.Spider):
    name = "doctor"
    start_urls = ["https://www.marham.pk/doctors"]
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
        "FEEDS": {
            "doctors.csv": {"format": "csv", "overwrite": True},  # save results in CSV
        },
        'DOWNLOAD_DELAY': 3,           # 3 sec delay between requests
    'RANDOMIZE_DOWNLOAD_DELAY': True,

    # AutoThrottle settings
    "AUTOTHROTTLE_ENABLED": True,
    "AUTOTHROTTLE_START_DELAY": 2,
    "AUTOTHROTTLE_MAX_DELAY": 15,
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.5,
    "AUTOTHROTTLE_DEBUG": False,

    # Retry settings
    'RETRY_ENABLED': True,
    'RETRY_TIMES': 5,
    'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],
    }

    def parse(self, response):
        """Parse main doctors page with specialties"""
        doctorBox = response.xpath("//div[@id='popularSpecialtiesContainer']//div[@class='col-12 col-md-4 specialty-card-wrapper']")
        for doctor in doctorBox:
            # Extract specialty data
            typeOfDoc = doctor.xpath(".//div[@class='specialty-content']//h3/a/text()").get()
            totalNumOfDocs = doctor.xpath(".//div[@class='specialty-content']//div[@class='specialty-meta']//a/text()").get()
            detailOfTypeDoc = doctor.xpath(".//div[@class='specialty-content']/p/text()").get()
            innerLink = doctor.xpath(".//div[@class='specialty-content']//h3/a/@href").get()

            meta = {
                'typeOfDoc': typeOfDoc,
                'totalNumOfDocs': totalNumOfDocs,
                'detailOfTypeDoc': detailOfTypeDoc
            }

            if innerLink:
                yield response.follow(innerLink, self.listOfDrs, meta=meta)
            else:
                # Specialty only (no doctors list)
                loader = ItemLoader(item=doctorMainPage(), selector=doctor)
                loader.add_value('typeOfDoc', typeOfDoc)
                loader.add_value('totalNumOfDocs', totalNumOfDocs)
                loader.add_value('detailOfTypeDoc', detailOfTypeDoc)
                yield loader.load_item()

    def listOfDrs(self, response):
        """Parse doctors under each specialty"""
        typeOfDoc = response.meta.get('typeOfDoc')
        totalNumOfDocs = response.meta.get('totalNumOfDocs')
        detailOfTypeDoc = response.meta.get('detailOfTypeDoc')

        doctors = response.css("div.row.shadow-card")
        for doc in doctors:
            loader = ItemLoader(item=doctorMainPage(), selector=doc)
            loader.add_value('typeOfDoc', typeOfDoc)
            loader.add_value('totalNumOfDocs', totalNumOfDocs)
            loader.add_value('detailOfTypeDoc', detailOfTypeDoc)

            # Basic doctor info
            name = doc.css("a.text-blue h3::text").get()
            if name:
                loader.add_value('name', name.strip())

            loader.add_value('profile_url', doc.css("a.text-blue::attr(href)").get())
            loader.add_value('image_url', doc.css("picture source[media='(min-width: 768px)']::attr(srcset)").get())
            loader.add_value('specialization', doc.css("p.mb-0.mt-10::text").get())
            loader.add_value('qualifications', doc.css("p.text-sm:nth-of-type(2)::text").get())

            drProfLink = doc.css("a.text-blue.dr_profile_opened_from_listing::attr(href)").get()

            # Experience & satisfaction
            experience = doc.css('div.col-4:nth-of-type(2) p.text-bold.text-sm::text').get(default='').strip()
            satisfaction = doc.css('div.col-4:nth-of-type(3) p.text-bold.text-sm::text').get(default='').strip()
            if len(satisfaction) == 0:
                satisfaction = 0

            loader.add_value('experience', experience)
            loader.add_value('satisfaction', satisfaction)

            # Areas of interest
            interests = [i.strip() for i in doc.css("div.horizontal-scroll span.chips-highlight::text").getall()]
            if len(interests) == 0:
                interests = [typeOfDoc]
            loader.add_value('areas_of_interest', interests)

            # City from hospital data
            city_node = response.css('div.selectAppointmentOrOc:nth-of-type(1)')
            if city_node:
                loader.add_value('city', city_node.attrib.get("data-hospitalcity"))

            if drProfLink:
                yield response.follow(drProfLink, self.parse_doctor_profile, meta={'loader': loader})
            else:
                yield loader.load_item()

    def parse_doctor_profile(self, response):
        """Parse inside the doctor profile page"""
        base_loader = response.meta['loader']

        # Common doctor profile info
        section = response.css('#reviews-scroll div.row.shadow-card')
        noOfReview = section.css('h2.mb-0::text').get(default='').strip()
        if len(noOfReview) == 0:
            noOfReview = 0
        rating = section.css('span.tag-highlight-round::text').get(default='').strip()
        if len(rating) == 0:
            rating = 0

        # Hospital options
        options = response.css('.card-hospital')
        if not options:
            # yield single row if no hospital options
            base_loader.add_value('reviews', noOfReview)
            base_loader.add_value('rating', rating)
            yield base_loader.load_item()
        else:
            for option in options:
                loader = ItemLoader(item=doctorMainPage(), selector=option)

                # Copy base doctor data into this row
                for k, v in base_loader.load_item().items():
                    loader.add_value(k, v)

                loader.add_value('reviews', noOfReview)
                loader.add_value('rating', rating)

                # Hospital-specific details
                loader.add_value(
                    'hospitalName',
                    option.css('p.mb-0.text-bold.text-sm.text-underline::text').get(default='').strip()
                )
                loader.add_value('fee', option.css('p.price::text').get(default='').strip())
                loader.add_value(
                    'location',
                    option.css('a.text-sm.font-size-12 span ::text').get(default='').strip()
                )

                yield loader.load_item()
