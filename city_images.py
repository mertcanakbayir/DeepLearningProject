import ee
import geemap
import os
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

ee.Authenticate()
ee.Initialize(project="eedeneme1")

def get_city_images(
    city_name, 
    output_folder="city_images",
    start_radius=5000,
    end_radius=10000,
    step=1000,
    lat=None,
    lon=None,
    start_date="2023-01-01",
    end_date="2023-12-31",
    cloud_threshold=20
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
    
    # Tarih aralıkları
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    intervals = []
    current_dt = start_dt
    while current_dt < end_dt:
        next_dt = current_dt + timedelta(days=30)
        if next_dt > end_dt:
            next_dt = end_dt
        interval_start = current_dt.strftime("%Y-%m-%d")
        interval_end = next_dt.strftime("%Y-%m-%d")
        intervals.append((interval_start, interval_end))
        current_dt = next_dt
    
    radii = range(start_radius, end_radius + step, step)
    
    for radius in radii:
        print(f"\n{radius//1000} km yarıçap ile işleniyor...")
        area = point.buffer(radius).bounds()
        
        for interval_start, interval_end in intervals:
            print(f"Tarih: {interval_start} - {interval_end}")
            
            collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(point)
                .filterDate(interval_start, interval_end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
                .sort("CLOUDY_PIXEL_PERCENTAGE")
            )
            
            
            try:
                count = collection.size().getInfo()
                if count == 0:
                    print("Görüntü bulunamadı.")
                    continue
                
                img = collection.first()
                date = img.date().format("YYYY-MM-dd").getInfo()
                
                radius_folder = os.path.join(output_folder, city_name, f"{radius//1000}km")
                os.makedirs(radius_folder, exist_ok=True)
                output_path = os.path.join(radius_folder, f"{city_name}_{date}_r{radius}m.jpg")

                vis_params = {
                    'bands': ['B4', 'B3', 'B2'],
                    'min': 0,
                    'max': 3000,
                    'gamma': 1.2
                }

                thumbnail_url = img.getThumbURL({
                    'region': area,
                    'scale': 20,
                    **vis_params,
                    'format': 'jpg'
                })

                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    Image.open(BytesIO(response.content)).save(output_path)
                    print(f"Kaydedildi: {os.path.basename(output_path)}")
                else:
                    print(f"Hata kodu: {response.status_code}")

            except Exception as e:
                print(f"Hata: {str(e)}")

# Örnek Kullanım
get_city_images(
    city_name="Ankara",
    start_radius=5000,
    end_radius=20000,
    step=2500
)