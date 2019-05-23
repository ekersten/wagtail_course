import requests
import os
from django.conf import settings
from wagtail.images.models import Image
from PIL import Image as PILImage
from wagtail.core.models import Collection

def get_behance_collection():
    if Collection.objects.filter(name='Behance').count() == 0:
        Collection.get_first_root_node().add_child(name='Behance')

    collection = Collection.objects.get(name='Behance')

    return collection

# todo: prevent overwrite
def create_wagtail_image_from_remote(image_url=None, images_folder='original_images', collection=None):
    basename = os.path.basename(image_url)
    db_file_field = os.path.join(images_folder, basename).replace('\\', '/')
    
    destination_image = os.path.join(
        settings.MEDIA_ROOT,
        images_folder,
        os.path.basename(image_url)
    )

    if collection is None:
        collection = get_behance_collection()
    
    r = requests.get(image_url)

    if Image.objects.filter(file=db_file_field).count() == 0:

        if r.status_code == 200:
            with open(destination_image, 'wb') as f:
                f.write(r.content)

            local_image = PILImage.open(destination_image)
            width, height = local_image.size

            img = Image()
            img.file = db_file_field
            img.title = basename
            img.width = width
            img.height = height
            img.collection = collection
            img.save()

            return img

    else:
        return Image.objects.get(file=db_file_field)

    return None
