import os
import csv
from collections import Counter
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from games import models


class Command(BaseCommand):
    """
    Implement 'import data' command for loading products to database
    from .csv file.
    """
    help = 'Import products in Games4Everyone'

    def add_arguments(self, parser):
        """
        Add command's arguments: 'name of csv file'
        and 'directory of product's images'
        """
        parser.add_argument("csvfile", type=open)
        parser.add_argument("image_basedir", type=str)

    def handle(self, *args, **options):
        self.stdout.write("Importing products")
        c = Counter()

        # read .csv file and create product for every line
        # reader = csv.DictReader(options.pop("csvfile"), delimiter=';')
        reader = csv.DictReader(options.pop("csvfile"), delimiter=';')

        for row in reader:
            product, created = models.Product.objects.get_or_create(
                name=row["name"],
                price=row["price"]
            )
            # create description or slug or update if product exists
            product.description = row["description"]
            product.slug = slugify(row["name"])

            # processing tags
            for import_tag in row["tags"].split("|"):
                tag, tag_created = models.ProductTag.objects.get_or_create(
                    name=import_tag,
                    slug=slugify(import_tag)
                )
                product.tags.add(tag)
                c["tags"] += 1
                if tag_created:
                    c["tags_created"] += 1

            # processing image
            with open(os.path.join(options["image_basedir"],
                                   row["image_filename"],), "rb",) as f:
                image = models.ProductImage(
                    product=product,
                    image=ImageFile(f, name=row["image_filename"]),
                )
                image.save()
                c["images"] += 1

            product.save()
            c["products"] += 1
            if created:
                c["products_created"] += 1

        # Display info about processed products
        self.stdout.write(
            "Products processed={0} (created={1})".format(
                c["products"], c["products_created"])
        )

        self.stdout.write(
            "Tags processed={0} (created={1})".format(
                c["tags"], c["tags_created"])
        )

        self.stdout.write(
            "Images processed={}".format(c["images"]))
