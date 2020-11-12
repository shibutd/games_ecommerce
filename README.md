Demo site: http://34.107.117.229:8000/

<br />

Create Ecommerce website preview:
```
docker-compose up -d --build
```

Fill website with content:
```
docker-compose exec web python manage.py import_data games/fixtures/product-sample.csv games/fixtures/product-sampleimages/
```

Create virtual orders (20):
```
docker-compose exec web python manage.py mock_orders 20
```
