# weather-streaming

weather.gov

## 1. Get Grid Coordinates (Using Postman)

**Request**:  

```json
GET https://api.weather.gov/points/{latitude},{longitude}
```

```json
{
    "@context": [
        "https://geojson.org/geojson-ld/geojson-context.jsonld",
        {
            "@version": "1.1",
            "wx": "https://api.weather.gov/ontology#",
            "s": "https://schema.org/",
            "geo": "http://www.opengis.net/ont/geosparql#",
            "unit": "http://codes.wmo.int/common/unit/",
            "@vocab": "https://api.weather.gov/ontology#",
            "geometry": {
                "@id": "s:GeoCoordinates",
                "@type": "geo:wktLiteral"
            },
            "city": "s:addressLocality",
            "state": "s:addressRegion",
            "distance": {
                "@id": "s:Distance",
                "@type": "s:QuantitativeValue"
            },
            "bearing": {
                "@type": "s:QuantitativeValue"
            },
            "value": {
                "@id": "s:value"
            },
            "unitCode": {
                "@id": "s:unitCode",
                "@type": "@id"
            },
            "forecastOffice": {
                "@type": "@id"
            },
            "forecastGridData": {
                "@type": "@id"
            },
            "publicZone": {
                "@type": "@id"
            },
            "county": {
                "@type": "@id"
            }
        }
    ],
    "id": "https://api.weather.gov/points/34.0947,-118.4017",
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [
            -118.4017,
            34.0947
        ]
    },
    "properties": {
        "@id": "https://api.weather.gov/points/34.0947,-118.4017",
        "@type": "wx:Point",
        "cwa": "LOX",
        "forecastOffice": "https://api.weather.gov/offices/LOX",
        "gridId": "LOX",
        "gridX": 150,
        "gridY": 48,
        "forecast": "https://api.weather.gov/gridpoints/LOX/150,48/forecast",
        "forecastHourly": "https://api.weather.gov/gridpoints/LOX/150,48/forecast/hourly",
        "forecastGridData": "https://api.weather.gov/gridpoints/LOX/150,48",
        "observationStations": "https://api.weather.gov/gridpoints/LOX/150,48/stations",
        "relativeLocation": {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    -118.402437,
                    34.07923
                ]
            },
            "properties": {
                "city": "Beverly Hills",
                "state": "CA",
                "distance": {
                    "unitCode": "wmoUnit:m",
                    "value": 1721.5263548236
                },
                "bearing": {
                    "unitCode": "wmoUnit:degree_(angle)",
                    "value": 2
                }
            }
        },
        "forecastZone": "https://api.weather.gov/zones/forecast/CAZ368",
        "county": "https://api.weather.gov/zones/county/CAC037",
        "fireWeatherZone": "https://api.weather.gov/zones/fire/CAZ368",
        "timeZone": "America/Los_Angeles",
        "radarStation": "KSOX"
    }
}
```



#### Generating Cluster_ID

```py
python -c "import uuid, base64; print(base64.b64encode(uuid.uuid4().bytes).decode())"
```


#### Generating Topic manually

Kafka'da "auto.create.topics.enable" özelliğinin kapalı olması olabilir. Bu ayar, KRaft (yani Zookeeper'sız Kafka) modunda default olarak false (kapalı) gelir. Yani:

Eğer topic mevcut değilse, Kafka otomatik olarak onu oluşturmaz.

