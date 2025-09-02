import scrapy
from pracDay1.items import doctorMainPage
from scrapy.loader import ItemLoader
import json

class DoctorSpider(scrapy.Spider):
    name = "doctor"
    start_urls = ["https://www.marham.pk/doctors"]
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
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

            name = doc.css("a.text-blue h3::text").get()
            if name:
                loader.add_value('name', name.strip())
            loader.add_value('profile_url', doc.css("a.text-blue::attr(href)").get())
            loader.add_value('image_url', doc.css("picture source[media='(min-width: 768px)']::attr(srcset)").get())
            loader.add_value('specialization', doc.css("p.mb-0.mt-10::text").get())
            loader.add_value('qualifications', doc.css("p.text-sm:nth-of-type(2)::text").get())

            # Extract reviews using multiple approaches
            reviews = None
            import re
            
            # Method 1: Try to extract from profile URL (like dr-name-12345 where 12345 is review count)
            profile_url = doc.css("a.text-blue::attr(href)").get()
            if profile_url:
                # Look for numbers at the end of URL
                url_matches = re.findall(r'-(\d+)$', profile_url)
                if url_matches:
                    reviews = url_matches[0]
                    print(f"RAW REVIEWS VALUE (URL method): {reviews}")
            
            # Method 2: If URL method didn't work, try HTML content extraction
            if not reviews:
                reviews_raw = doc.css("a.dr_profile_opened_from_listing_reviews").getall()
                if reviews_raw:
                    # Get all text content from reviews section and find numbers
                    reviews_text = "".join(reviews_raw)
                    # Look for patterns like "2,026", "1,234", "999" etc.
                    matches = re.findall(r'[\d,]+', reviews_text)
                    if matches:
                        # Take the first number found (should be the review count)
                        reviews = matches[0]
                        print(f"RAW REVIEWS VALUE (HTML method): {reviews}")
            
            # Method 3: Alternative direct text extraction
            if not reviews:
                reviews = doc.css("a.dr_profile_opened_from_listing_reviews p.text-bold::text").get()
                if reviews:
                    reviews = reviews.strip()
                    print(f"RAW REVIEWS VALUE (direct method): {reviews}")
            
            # Method 4: Try to find in any div that contains review-like content
            if not reviews:
                # Look for elements that might contain review counts
                all_text_elements = doc.css("div.col-4 p.text-bold::text").getall()
                for text in all_text_elements:
                    if text and re.match(r'^[\d,]+$', text.strip()):
                        # This could be a review count if it's a pure number
                        possible_reviews = text.strip()
                        # Additional validation: check if nearby text suggests it's reviews
                        reviews = possible_reviews
                        print(f"RAW REVIEWS VALUE (fallback method): {reviews}")
                        break
            
            if not reviews:
                reviews = 0
                print(f"RAW REVIEWS VALUE (no method worked): {reviews}")
            
            loader.add_value('reviews', reviews)
            # Experience and satisfaction as before
            experience, satisfaction = None, None
            for col in doc.css("div.col-4"):
                label = col.css("p.mb-0.text-sm::text").get()
                value = col.css("p.text-bold.text-sm::text").get()
                if not value:
                    value = col.css("p.text-bold::text").get()
                if label and value:
                    label = label.strip().lower()
                    value = value.strip()
                    print(f"DEBUG: label={label}, value={value}")
                    if 'experience' in label:
                        experience = value
                    elif 'satisfaction' in label:
                        satisfaction = value
            print(f"RAW EXTRACTED: reviews={reviews}, experience={experience}, satisfaction={satisfaction}")
            loader.add_value('experience', experience)
            loader.add_value('satisfaction', satisfaction)

            interests = [i.strip() for i in doc.css("div.horizontal-scroll span.chips-highlight::text").getall()]
            loader.add_value('areas_of_interest', interests)

            # Extract all consultation info
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

            item = loader.load_item()

            # Print for debug
            print("="*50)
            for k, v in item.items():
                print(f"{k}: {v}")
            print("="*50)

            yield item
