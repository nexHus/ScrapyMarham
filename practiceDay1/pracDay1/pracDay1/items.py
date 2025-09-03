import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
import json
import re

# Helper to convert numbers like "7,344" or "15 Yrs" or "100%" to int
def getIntDoctor(value):
    if not value or str(value).strip() == '':
        return 0
    try:
        # Handle percentages like "100%" by removing the % sign
        clean_value = str(value).replace(",", "").replace("%", "").split(" ")[0]
        return int(clean_value)
    except (ValueError, TypeError, AttributeError):
        return None

def getIntPrice(value):
    if not value or str(value).strip() == '':
        return None
    try:
        # Keep only digits from the string
        clean_value = re.sub(r"[^\d]", "", str(value))
        return int(clean_value) if clean_value else None
    except (ValueError, TypeError, AttributeError):
        return None

def getCityFromProfileUrl(url):
    if not url:
        return None
    # Extract city name from the URL
    parts = url.split("/")
    if len(parts) > 2:
        return parts[2]
    return None
def getIntRating(value):
    """Convert rating like '4/5' into integer 4"""
    if not value:
        return 0
    try:
        return int(str(value).split('/')[0])
    except (ValueError, IndexError):
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
    # consultations = scrapy.Field()  # Store as JSON string
    rating = scrapy.Field(input_processor=MapCompose(getIntRating), output_processor=TakeFirst())
    hospitalName = scrapy.Field()
    fee = scrapy.Field(input_processor=MapCompose(getIntPrice), output_processor=TakeFirst())
    location = scrapy.Field()
    city = scrapy.Field()
