# # This package will contain the spiders of your Scrapy project
# #
# # Please refer to the documentation for information on how to create and manage
# # your spiders.



# import scrapy
# from pracDay1.items import doctorMainPage
# from scrapy.loader import ItemLoader
# import json

# class DoctorSpider(scrapy.Spider):
#     name = "doctor"
#     start_urls = ["https://www.marham.pk/doctors"]
#     custom_settings = {
#         'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
#     }

#     def parse(self, response):
#         doctorBox = response.xpath("//div[@id='popularSpecialtiesContainer']//div[@class='col-12 col-md-4 specialty-card-wrapper']")
#         for doctor in doctorBox:
#             # Extract specialty data
#             typeOfDoc = doctor.xpath(".//div[@class='specialty-content']//h3/a/text()").get()
#             totalNumOfDocs = doctor.xpath(".//div[@class='specialty-content']//div[@class='specialty-meta']//a/text()").get()
#             detailOfTypeDoc = doctor.xpath(".//div[@class='specialty-content']/p/text()").get()
#             innerLink = doctor.xpath(".//div[@class='specialty-content']//h3/a/@href").get()
#             meta = {
#                 'typeOfDoc': typeOfDoc,
#                 'totalNumOfDocs': totalNumOfDocs,
#                 'detailOfTypeDoc': detailOfTypeDoc
#             }
#             if innerLink:
#                 yield response.follow(innerLink, self.listOfDrs, meta=meta)
#             else:
#                 # No doctor list page, yield specialty only
#                 loader = ItemLoader(item=doctorMainPage(), selector=doctor)
#                 loader.add_value('typeOfDoc', typeOfDoc)
#                 loader.add_value('totalNumOfDocs', totalNumOfDocs)
#                 loader.add_value('detailOfTypeDoc', detailOfTypeDoc)
#                 yield loader.load_item()

#     def listOfDrs(self, response):
#         # Get specialty data from meta
#         typeOfDoc = response.meta.get('typeOfDoc')
#         totalNumOfDocs = response.meta.get('totalNumOfDocs')
#         detailOfTypeDoc = response.meta.get('detailOfTypeDoc')

#         doctors = response.css("div.row.shadow-card")
#         for doc in doctors:
#             loader = ItemLoader(item=doctorMainPage(), selector=doc)
#             loader.add_value('typeOfDoc', typeOfDoc)
#             loader.add_value('totalNumOfDocs', totalNumOfDocs)
#             loader.add_value('detailOfTypeDoc', detailOfTypeDoc)

#             name = doc.css("a.text-blue h3::text").get()
#             if name:
#                 loader.add_value('name', name.strip())
#             loader.add_value('profile_url', doc.css("a.text-blue::attr(href)").get())
#             loader.add_value('image_url', doc.css("picture source[media='(min-width: 768px)']::attr(srcset)").get())
#             loader.add_value('specialization', doc.css("p.mb-0.mt-10::text").get())
#             loader.add_value('qualifications', doc.css("p.text-sm:nth-of-type(2)::text").get())

#             info_texts = doc.css("div.col-4 p.text-bold::text").getall()
#             loader.add_value('reviews', info_texts[0] if len(info_texts) > 0 else None)
#             loader.add_value('experience', info_texts[1] if len(info_texts) > 1 else None)
#             loader.add_value('satisfaction', info_texts[2] if len(info_texts) > 2 else None)

#             interests = [i.strip() for i in doc.css("div.horizontal-scroll span.chips-highlight::text").getall()]
#             loader.add_value('areas_of_interest', interests)

#             consultations = []
#             for c in doc.css("div.selectAppointmentOrOc"):
#                 consultations.append({
#                     "type": c.css("p.text-bold.text-blue::text").get(),
#                     "hospital": c.attrib.get("data-hospitalName"),
#                     "fee": c.attrib.get("data-amount"),
#                     "link": c.attrib.get("data-onClickUrl")
#                 })
#             loader.add_value('consultations', json.dumps(consultations))

#             item = loader.load_item()

#             # Print for debug
#             print("="*50)
#             for k, v in item.items():
#                 print(f"{k}: {v}")
#             print("="*50)

#             yield item
