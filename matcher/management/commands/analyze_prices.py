from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from matcher.models import BookPrice, Book, BookPriceType


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):

        averages_lower = []
        averages_higher = []

        for book in Book.objects.filter(profiles__url__contains="reknihy.cz", prices__price_type__in=[BookPriceType.USED])\
                .annotate(cnt=Count("prices")).filter(cnt__gt=1).order_by("-cnt").prefetch_related("prices__profile"):
            print()
            prices = {}
            for price in book.prices.all():
                if not price.profile:
                    continue
                if "reknihy.cz" in price.profile.url:
                    prices["reknihy"] = price.price
                else:
                    prices.setdefault(price.price_type, [])
                    prices[price.price_type].append(price.price)

            from pprint import pprint
            if len(prices) > 1:
                pprint(prices)
                reknihy = prices.get("reknihy")
                for k, v in prices.items():
                    if k == "reknihy":
                        continue
                    avg = (sum(v) / len(v)) if isinstance(v, list) else v
                    print(k, avg)
                    if avg and reknihy:
                        diff = int(avg / reknihy * 100)
                        print(f"{diff} %")
                        if diff < 100:
                            averages_lower.append(diff)
                        else:
                            averages_higher.append(diff)

        print("RES")
        if averages_lower:
            avg_low = (sum(averages_lower) / len(averages_lower))
            print(f"{len(averages_lower)}, {avg_low} %")
        if averages_higher:
            avg_high = (sum(averages_higher) / len(averages_higher))
            print(f"{len(averages_higher)}, {avg_high} %")

        aa = sum(averages_lower + averages_higher) / len(averages_lower + averages_higher)
        print(aa)
                

