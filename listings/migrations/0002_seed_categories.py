from django.db import migrations


def seed_categories(apps, schema_editor):
    Category = apps.get_model("listings", "Category")
    categories = [
        ("Textbooks", "textbooks"),
        ("Calculators", "calculators"),
        ("Lab Coats", "lab-coats"),
        ("Electronics", "electronics"),
        ("Other", "other"),
    ]
    for name, slug in categories:
        Category.objects.get_or_create(slug=slug, defaults={"name": name})


def unseed_categories(apps, schema_editor):
    Category = apps.get_model("listings", "Category")
    Category.objects.filter(
        slug__in=["textbooks", "calculators", "lab-coats", "electronics", "other"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=unseed_categories),
    ]

