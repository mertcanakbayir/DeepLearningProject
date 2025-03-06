import ee
import geemap
import os
import requests
from PIL import Image
from io import BytesIO

ee.Authenticate()
ee.Initialize(project="eedeneme1")

def get_city_images(
    city_name, 
    output_folder="city_images",
    start_radius=5000,
    end_radius=10000,
    step=1000,
    num_images=5,
    lat=None,
    lon=None,
    start_date="2023-01-01",
    end_date="2023-12-31"
):
    # Koordinatları alma
    if lat is None or lon is None:
        geocoder_result = geemap.geocode(city_name)
        if not geocoder_result:
            print(f"'{city_name}' bulunamadı!")
            return
        first_result = geocoder_result[0]
        lat, lon = first_result.lat, first_result.lng

    point = ee.Geometry.Point(lon, lat)
    
    # Yarıçap aralığını oluştur
    radii = range(start_radius, end_radius + step, step)
    
    # Her yarıçap için işlem yap
    for radius in radii:
        print(f"\n{radius//1000} km yarıçap ile işleniyor...")
        
        # Geometriyi oluştur
        area = point.buffer(radius).bounds()
        
        # Koleksiyonu filtrele
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(point)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .limit(num_images)
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        try:
            images = collection.toList(num_images)
            for i in range(num_images):
                img = ee.Image(images.get(i))
                date = img.date().format("YYYY-MM-dd").getInfo()
                
                # Özel klasör yapısı: city_images/Istanbul/5km
                radius_folder = os.path.join(output_folder, 
                                           f"{city_name}", 
                                           f"{radius//1000}km")
                os.makedirs(radius_folder, exist_ok=True)
                
                output_path = os.path.join(radius_folder, 
                                         f"{city_name}_{date}_r{radius}m.jpg")

                # Görselleştirme parametreleri
                vis_params = {
                    'bands': ['B4', 'B3', 'B2'],
                    'min': 0,
                    'max': 3000,
                    'gamma': 1.2
                }

                # Thumbnail URL al
                thumbnail_url = img.getThumbURL({
                    'region': area,
                    'scale': 10,
                    **vis_params,
                    'format': 'jpg'
                })

                # İndir ve kaydet
                response = requests.get(thumbnail_url)
                Image.open(BytesIO(response.content)).save(output_path)
                print(f"Kaydedildi: {os.path.basename(output_path)}")

        except Exception as e:
            print(f"Hata (r={radius}m): {str(e)}")

# Örnek Kullanım
get_city_images(
    city_name="Istanbul",
    start_radius=5000,
    end_radius=10000,
    step=1000,
    num_images=3
)