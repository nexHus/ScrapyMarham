import scrapy
from pracDay1.items import doctorMainPage
from scrapy.loader import ItemLoader
import json


class DoctorSpider(scrapy.Spider):
    name = "doctor"
    start_urls = ["https://www.marham.pk/doctors"]
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
           "AUTOTHROTTLE_ENABLED": True,
    "AUTOTHROTTLE_START_DELAY": 2,
    "AUTOTHROTTLE_MAX_DELAY": 10,
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
    "AUTOTHROTTLE_DEBUG": False,
    }

    def parse(self, response):
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
                # No doctor list page, yield specialty only
                loader = ItemLoader(item=doctorMainPage(), selector=doctor)
                loader.add_value('typeOfDoc', typeOfDoc)
                loader.add_value('totalNumOfDocs', totalNumOfDocs)
                loader.add_value('detailOfTypeDoc', detailOfTypeDoc)
                yield loader.load_item()

    def listOfDrs(self, response):
        # Get specialty data from meta
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
            # drProfLink = ''

            # Experience & satisfaction
            experience = doc.css('div.col-4:nth-of-type(2) p.text-bold.text-sm::text').get(default='').strip()
            satisfaction = doc.css('div.col-4:nth-of-type(3) p.text-bold.text-sm::text').get(default='').strip()
            loader.add_value('experience', experience)
            loader.add_value('satisfaction', satisfaction)

            # Areas of interest
            interests = [i.strip() for i in doc.css("div.horizontal-scroll span.chips-highlight::text").getall()]
            loader.add_value('areas_of_interest', interests)

            # Consultation info
            consultations = []
            for c in doc.css("div.selectAppointmentOrOc"):
                consultations.append({
                    "type": c.css("p.text-bold.text-blue::text").get(),
                    "hospital": c.attrib.get("data-hospitalName"),
                    "city": c.attrib.get("data-hospitalCity"),
                    "address": c.attrib.get("data-hospitalAddress"),
                    "fee": c.attrib.get("data-amount"),
                    "discounted_fee": c.attrib.get("data-discountedFee"),
                    "link": c.attrib.get("data-onClickUrl"),
                    "hospital_type": c.attrib.get("data-hospitalType"),
                    "available_today": c.css("p.text-sm.text-wrap::text, p.text-sm::text").get(),
                })
            loader.add_value('consultations', json.dumps(consultations))

            if drProfLink:
                print("were are going in for ", drProfLink)
                # Pass the loader forward to inner profile
                yield response.follow(drProfLink, self.parse_doctor_profile, meta={'loader': loader})
            else:
                yield loader.load_item()

    def parse_doctor_profile(self, response):
        """Parse inside the doctor profile page"""
        loader = response.meta['loader']

        # Example: Reviews section
        section = response.css('#reviews-scroll div.row.shadow-card')
        noOfReview = section.css('h2.mb-0::text').get(default='').strip()
        loader.add_value('reviews', noOfReview)

        rating = section.css('span.tag-highlight-round::text').get(default='').strip()
        loader.add_value('rating', rating  )

        # You can add more profile fields here if needed

        yield loader.load_item()
