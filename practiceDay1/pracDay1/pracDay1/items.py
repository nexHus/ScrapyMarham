import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
import json

# Helper to convert numbers like "7,344" or "15 Yrs" or "100%" to int
def getIntDoctor(value):
    if not value or str(value).strip() == '':
        return None
    try:
        # Handle percentages like "100%" by removing the % sign
        clean_value = str(value).replace(",", "").replace("%", "").split(" ")[0]
        return int(clean_value)
    except (ValueError, TypeError, AttributeError):
        return None

class doctorMainPage(scrapy.Item):
    typeOfDoc = scrapy.Field(output_processor=TakeFirst())
    totalNumOfDocs = scrapy.Field(input_processor=MapCompose(getIntDoctor), output_processor=TakeFirst())
    detailOfTypeDoc = scrapy.Field(output_processor=TakeFirst())
    
    # Doctor-specific fields
    name = scrapy.Field(output_processor=TakeFirst())
    profile_url = scrapy.Field(output_processor=TakeFirst())
    image_url = scrapy.Field(output_processor=TakeFirst())
    specialization = scrapy.Field(output_processor=TakeFirst())
    qualifications = scrapy.Field(output_processor=TakeFirst())
    experience = scrapy.Field(input_processor=MapCompose(getIntDoctor), output_processor=TakeFirst())
    reviews = scrapy.Field(input_processor=MapCompose(getIntDoctor), output_processor=TakeFirst())
    satisfaction = scrapy.Field(input_processor=MapCompose(getIntDoctor), output_processor=TakeFirst())
    areas_of_interest = scrapy.Field(output_processor=Join(", "))
    consultations = scrapy.Field()  # Store as JSON string
